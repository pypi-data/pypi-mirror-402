"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
import threading
import time
from functools import wraps

from loguru import logger  # type: ignore

from tauro.feature_store.schema import FeatureGroupSchema, FeatureSchema
from tauro.feature_store.exceptions import (
    FeatureNotFoundError,
    FeatureGroupNotFoundError,
    MetadataError,
)


class FeatureStoreMode(Enum):
    """Modes of operation for Feature Store."""

    MATERIALIZED = "materialized"  # Pre-computed, stored features (Offline)
    VIRTUALIZED = "virtualized"  # Query-on-demand from source
    HYBRID = "hybrid"  # Both strategies, auto-select best
    ONLINE = "online"  # Low-latency serving from KV store (Phase 2)


@dataclass
class FeatureStoreConfig:
    """Configuration for Feature Store mode selection."""

    mode: FeatureStoreMode = FeatureStoreMode.MATERIALIZED

    # Materialized (Offline) settings
    storage_path: Optional[str] = None
    storage_format: str = "parquet"

    # Online Store settings (Phase 2)
    enable_online_store: bool = False
    online_store_type: str = "in_memory"  # Currently only "in_memory" supported
    online_store_config: Dict[str, Any] = field(default_factory=dict)
    sync_to_online: bool = False  # Auto-sync on write_features

    # Virtualized settings
    enable_virtualization: bool = False
    query_executor_type: str = "spark"  # "spark" or "duckdb"

    # Hybrid settings
    hybrid_threshold_rows: int = 10000  # Use materialized if > threshold
    hybrid_cache_ttl: int = 3600  # Cache TTL for hybrid mode
    auto_materialize_on_read: bool = False  # Auto-materialize virtual features

    # Integration with VirtualDataLayer
    register_virtual_tables: bool = True
    virtual_table_prefix: str = "features_"

    # Metadata persistence (Phase 2)
    metadata_path: Optional[str] = None
    metadata_format: str = "parquet"  # "parquet", "delta", or "json"
    auto_save_metadata: bool = True

    # Resilience & Performance settings
    max_retries: int = 3
    retry_backoff_ms: int = 1000
    retry_backoff_multiplier: float = 2.0
    metadata_cache_ttl_seconds: int = 300
    lock_timeout_seconds: float = 30.0
    enable_compression: bool = True

    def __post_init__(self):
        """Validate configuration."""
        # Validate mode-specific settings
        if self.mode == FeatureStoreMode.MATERIALIZED and not self.storage_path:
            logger.warning("Materialized mode without storage_path, using default")
            self.storage_path = "/data/gold/features"

        if self.mode == FeatureStoreMode.VIRTUALIZED and not self.enable_virtualization:
            self.enable_virtualization = True

        if self.mode == FeatureStoreMode.HYBRID:
            self.enable_virtualization = True

        # Validate retry settings
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.retry_backoff_ms < 0:
            raise ValueError("retry_backoff_ms must be >= 0")
        if self.retry_backoff_multiplier <= 1.0:
            logger.warning(
                "retry_backoff_multiplier should be > 1.0 for effective exponential backoff"
            )
        if self.lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds must be > 0")

        logger.debug(
            f"FeatureStoreConfig validated: mode={self.mode.value}, "
            f"retries={self.max_retries}, cache_ttl={self.metadata_cache_ttl_seconds}s"
        )


class FeatureStoreMetadata:
    """Manages feature store metadata and registry with caching and resilience."""

    def __init__(self, context: Any = None, config: Optional[FeatureStoreConfig] = None):
        """Initialize metadata store with caching."""
        self.context = context
        self.config = config or FeatureStoreConfig()
        self._feature_groups: Dict[str, FeatureGroupSchema] = {}
        self._feature_registry: Dict[str, Dict[str, FeatureSchema]] = {}
        self._lineage: Dict[str, List[str]] = {}
        self._last_updated: Dict[str, datetime] = {}
        self._lock = threading.RLock()  # RLock allows re-entrant locking

        # Caching layer for metadata
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_lock = threading.Lock()

        # Phase 2: Load existing metadata if persistence enabled
        if self.context and self.config and self.config.metadata_path:
            self._load_metadata_with_retry()

    def _acquire_lock(self, timeout: Optional[float] = None) -> bool:
        """Acquire lock with timeout support."""
        timeout = timeout or self.config.lock_timeout_seconds
        acquired = self._lock.acquire(timeout=timeout)
        if not acquired:
            logger.warning(f"Failed to acquire metadata lock within {timeout}s")
        return acquired

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if still valid."""
        with self._cache_lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                age = (datetime.now(timezone.utc) - timestamp).total_seconds()
                if age < self.config.metadata_cache_ttl_seconds:
                    logger.debug(f"Cache hit for key '{key}' (age={age:.1f}s)")
                    return value
                else:
                    del self._cache[key]
                    logger.debug(f"Cache expired for key '{key}'")
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """Store value in cache."""
        with self._cache_lock:
            self._cache[key] = (value, datetime.now(timezone.utc))

    def register_feature_group(self, schema: FeatureGroupSchema) -> None:
        """Register a feature group schema with validation and error handling."""
        try:
            schema.validate()
        except Exception as e:
            logger.error(f"Schema validation failed for '{schema.name}': {e}")
            raise

        if not self._acquire_lock():
            raise MetadataError(f"Could not acquire lock to register feature group '{schema.name}'")

        try:
            self._feature_groups[schema.name] = schema
            self._feature_registry[schema.name] = {f.name: f for f in schema.features}
            self._last_updated[schema.name] = datetime.now(timezone.utc)

            # Invalidate cache
            self._set_cache(f"group:{schema.name}", None)

            logger.info(
                f"Registered feature group '{schema.name}' with {len(schema.features)} features"
            )
        finally:
            self._lock.release()

        # Phase 2: Autosave with retry
        if self.config and self.config.auto_save_metadata:
            self._save_metadata_with_retry()

    def get_feature_group(self, name: str) -> FeatureGroupSchema:
        """Retrieve a feature group schema with caching."""
        # Try cache first
        cached = self._get_from_cache(f"group:{name}")
        if cached is not None:
            return cached

        if not self._acquire_lock():
            raise MetadataError(f"Could not acquire lock to retrieve feature group '{name}'")

        try:
            if name not in self._feature_groups:
                raise FeatureGroupNotFoundError(f"Feature group '{name}' not found in registry")
            schema = self._feature_groups[name]
            self._set_cache(f"group:{name}", schema)
            return schema
        finally:
            self._lock.release()

    def get_feature(self, group_name: str, feature_name: str) -> FeatureSchema:
        """Retrieve a specific feature with caching."""
        cache_key = f"feature:{group_name}:{feature_name}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._acquire_lock():
            raise MetadataError(
                f"Could not acquire lock to retrieve feature '{feature_name}' in '{group_name}'"
            )

        try:
            if group_name not in self._feature_registry:
                raise FeatureGroupNotFoundError(f"Feature group '{group_name}' not found")
            if feature_name not in self._feature_registry[group_name]:
                raise FeatureNotFoundError(
                    f"Feature '{feature_name}' not found in group '{group_name}'"
                )
            feature = self._feature_registry[group_name][feature_name]
            self._set_cache(cache_key, feature)
            return feature
        finally:
            self._lock.release()

    def list_feature_groups(self) -> List[str]:
        """List all registered feature groups."""
        with self._lock:
            return list(self._feature_groups.keys())

    def list_features(self, group_name: str) -> List[str]:
        """List features in a feature group."""
        with self._lock:
            if group_name not in self._feature_registry:
                raise FeatureGroupNotFoundError(f"Feature group '{group_name}' not found")
            return list(self._feature_registry[group_name].keys())

    def set_lineage(self, feature_name: str, dependencies: List[str]) -> None:
        """Set data lineage for a feature."""
        if not self._acquire_lock():
            raise MetadataError(f"Could not acquire lock to set lineage for '{feature_name}'")

        try:
            self._lineage[feature_name] = dependencies
            logger.debug(f"Set lineage for {feature_name}: {dependencies}")
        finally:
            self._lock.release()

        # Phase 2: Autosave with retry
        if self.config and self.config.auto_save_metadata:
            self._save_metadata_with_retry()

    def _save_metadata_with_retry(self) -> None:
        """Persist metadata with exponential backoff retry."""
        for attempt in range(self.config.max_retries + 1):
            try:
                self._save_metadata()
                return
            except Exception as e:
                if attempt < self.config.max_retries:
                    backoff_ms = self.config.retry_backoff_ms * (
                        self.config.retry_backoff_multiplier**attempt
                    )
                    logger.warning(
                        f"Metadata save attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}. "
                        f"Retrying in {backoff_ms:.0f}ms..."
                    )
                    time.sleep(backoff_ms / 1000.0)
                else:
                    logger.error(
                        f"Failed to save metadata after {self.config.max_retries + 1} attempts: {e}"
                    )

    def _load_metadata_with_retry(self) -> None:
        """Load metadata with exponential backoff retry."""
        for attempt in range(self.config.max_retries + 1):
            try:
                self._load_metadata()
                return
            except Exception as e:
                if attempt < self.config.max_retries:
                    backoff_ms = self.config.retry_backoff_ms * (
                        self.config.retry_backoff_multiplier**attempt
                    )
                    logger.warning(
                        f"Metadata load attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}. "
                        f"Retrying in {backoff_ms:.0f}ms..."
                    )
                    time.sleep(backoff_ms / 1000.0)
                else:
                    logger.error(
                        f"Failed to load metadata after {self.config.max_retries + 1} attempts: {e}"
                    )

    def clear_cache(self) -> None:
        """Clear metadata cache."""
        with self._cache_lock:
            self._cache.clear()
        logger.debug("Metadata cache cleared")

    def get_lineage(self, feature_name: str) -> List[str]:
        """Get data lineage for a feature."""
        with self._lock:
            return self._lineage.get(feature_name, [])

    def get_last_updated(self, group_name: str) -> Optional[datetime]:
        """Get last update time for a feature group."""
        with self._lock:
            return self._last_updated.get(group_name)

    def _save_metadata(self) -> None:
        """Persist metadata using Tauro IO (sin lock-in)."""
        if not self.context or not self.config or not self.config.metadata_path:
            return

        try:
            from tauro.io.factories import WriterFactory
            import pandas as pd
            import json

            # Prepare metadata table
            rows = []
            with self._lock:
                for name, schema in self._feature_groups.items():
                    rows.append(
                        {
                            "name": name,
                            "schema_json": json.dumps(schema.to_dict()),
                            "last_updated": (
                                self._last_updated.get(name).isoformat()
                                if self._last_updated.get(name)
                                else None
                            ),
                            "lineage": json.dumps(self._lineage.get(name, [])),
                        }
                    )

            if not rows:
                return

            df = pd.DataFrame(rows)
            writer_factory = WriterFactory(self.context)
            writer = writer_factory.get_writer(self.config.metadata_format)

            # Use Tauro IO Writer directly
            writer.write(
                data=df,
                destination=self.config.metadata_path,
                config={"mode": "overwrite"},
            )
            logger.debug(
                f"Metadata persisted to {self.config.metadata_path} ({self.config.metadata_format})"
            )
        except Exception as e:
            logger.error(f"Failed to persist metadata: {e}")

    def _load_metadata(self) -> None:
        """Load metadata from persistent storage using Tauro IO readers."""
        if not self.context or not self.config or not self.config.metadata_path:
            return

        try:
            from tauro.io.factories import ReaderFactory
            import json

            reader_factory = ReaderFactory(self.context)
            reader = reader_factory.get_reader(self.config.metadata_format)

            # Read via Tauro IO
            df = reader.read(self.config.metadata_path, {})

            # Convert to Pandas for easy iteration
            if hasattr(df, "toPandas"):
                df = df.toPandas()

            with self._lock:
                for _, row in df.iterrows():
                    name = row["name"]
                    schema_dict = json.loads(row["schema_json"])
                    schema = FeatureGroupSchema.from_dict(schema_dict)

                    self._feature_groups[name] = schema
                    self._feature_registry[name] = {f.name: f for f in schema.features}

                    if row.get("last_updated"):
                        self._last_updated[name] = datetime.fromisoformat(row["last_updated"])

                    if row.get("lineage"):
                        self._lineage[name] = json.loads(row["lineage"])

            logger.info(
                f"Loaded metadata for {len(self._feature_groups)} groups from {self.config.metadata_path}"
            )
        except Exception as e:
            logger.warning(f"Could not load metadata from {self.config.metadata_path}: {e}")


class BaseFeatureStore(ABC):
    """Abstract base class for Feature Store implementations."""

    def __init__(self, context: Any, config: Optional[FeatureStoreConfig] = None):
        """Initialize Feature Store."""
        self.context = context
        self.config = config or FeatureStoreConfig()
        self.metadata = FeatureStoreMetadata(context=self.context, config=self.config)
        logger.info("BaseFeatureStore initialized")

    @abstractmethod
    def register_features(self, schema: FeatureGroupSchema) -> None:
        """Register a feature group."""
        pass

    @abstractmethod
    def get_features(
        self,
        feature_names: List[str],
        entity_ids: Optional[Dict[str, List[Any]]] = None,
        point_in_time: Optional[datetime] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], Any]:
        """Retrieve features for given entities."""
        pass

    @abstractmethod
    def write_features(
        self,
        feature_group: str,
        data: Dict[str, List[Any]],
        mode: str = "append",
    ) -> None:
        """Write features to the store."""
        pass

    def get_online_features(
        self,
        feature_names: List[str],
        entity_keys: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Retrieve features from online store for real-time serving (Phase 2).
        By default returns empty dict if online store not implemented/enabled.
        """
        return {}

    def health_check(self) -> bool:
        """Check Feature Store health."""
        try:
            return len(self.metadata.list_feature_groups()) > 0
        except Exception as e:
            logger.error(f"Feature Store health check failed: {e}")
            return False


class BaseOnlineStore(ABC):
    """
    Abstract base class for Online Feature Store backends (Phase 2).
    Provides low-latency point lookups for real-time serving.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def get_online_features(
        self,
        feature_group: str,
        entity_keys: Dict[str, Any],
        feature_names: List[str],
    ) -> Dict[str, Any]:
        """Retrieve features for a single entity from online store."""
        pass

    @abstractmethod
    def write_online_features(
        self,
        feature_group: str,
        data: List[Dict[str, Any]],
        entity_keys: List[str],
    ) -> None:
        """Update online store with new feature values."""
        pass

    @abstractmethod
    def delete_online_features(
        self,
        feature_group: str,
        entity_keys: Dict[str, Any],
    ) -> None:
        """Remove features from online store."""
        pass
