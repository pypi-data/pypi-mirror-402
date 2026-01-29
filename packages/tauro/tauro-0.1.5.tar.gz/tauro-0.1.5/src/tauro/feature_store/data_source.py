"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta, timezone

from loguru import logger  # type: ignore


class SourceType(str, Enum):
    """Types of data sources for feature retrieval."""

    TABLE = "table"  # Unified table (any layer)
    VIEW = "view"  # Database view
    API = "api"  # External API endpoint
    FEATURE_STORE = "feature_store"  # Another feature store
    PARQUET = "parquet"  # Parquet files
    DELTA = "delta"  # Delta tables
    ICEBERG = "iceberg"  # Apache Iceberg tables
    CUSTOM = "custom"  # Custom source via callable


class DataLayer(str, Enum):
    """Data layer classification - for reference only, not enforced."""

    BRONZE = "bronze"  # Raw data
    SILVER = "silver"  # Cleaned/transformed
    GOLD = "gold"  # Business-ready/aggregated
    EXTERNAL = "external"  # External source
    CACHE = "cache"  # Cached results
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class SourceMetrics:
    """Metrics about a data source for intelligent selection."""

    source_id: str
    """Unique identifier for the source"""

    latency_ms: float = 0.0
    """Average latency in milliseconds for data retrieval"""

    freshness_minutes: int = 60
    """How fresh the data is (minutes since last update)"""

    availability_pct: float = 99.9
    """Uptime/availability percentage"""

    cost_per_query: float = 0.0
    """Estimated cost per query in arbitrary units"""

    compute_cost: float = 0.0
    """Cost to compute/transform features"""

    last_updated: Optional[datetime] = None
    """Timestamp of last update in this source"""

    schema_version: str = "1.0"
    """Schema version for compatibility checking"""

    estimated_rows: int = 0
    """Approximate number of rows"""

    indexed: bool = False
    """Whether source supports indexed lookups"""

    materialized: bool = False
    """Whether source is pre-materialized (vs. computed on-demand)"""

    @property
    def cost_score(self) -> float:
        """Combined cost score (lower is better)."""
        return self.cost_per_query + self.compute_cost

    @property
    def freshness_score(self) -> float:
        """Freshness score - lower minutes = higher score (lower is better for age)."""
        return float(self.freshness_minutes)

    @property
    def reliability_score(self) -> float:
        """Reliability score (100 - availability_pct, lower is better)."""
        return 100.0 - self.availability_pct

    def is_fresh(self, max_age_minutes: int) -> bool:
        """Check if source data meets freshness requirement."""
        if not self.last_updated:
            return False
        age = datetime.now(timezone.utc) - self.last_updated
        return age <= timedelta(minutes=max_age_minutes)

    def is_available(self, min_availability_pct: float = 95.0) -> bool:
        """Check if source meets availability requirement."""
        return self.availability_pct >= min_availability_pct


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""

    source_id: str
    """Unique identifier (e.g., 'silver_users', 'api_recommendations')"""

    source_type: SourceType
    """Type of source"""

    data_layer: DataLayer = DataLayer.UNKNOWN
    """Logical data layer (reference only)"""

    location: str = ""
    """Location/path/endpoint (table name, API URL, file path, etc.)"""

    query: Optional[str] = None
    """Query to retrieve features (SQL, GraphQL, etc.) for query-based sources"""

    schema_mapping: Dict[str, str] = field(default_factory=dict)
    """Mapping of feature names to column/field names in source"""

    entity_keys: List[str] = field(default_factory=list)
    """Primary key columns for entity matching"""

    timestamp_column: Optional[str] = None
    """Timestamp column for point-in-time queries"""

    partition_columns: List[str] = field(default_factory=list)
    """Partition columns for filtering"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional source-specific metadata"""

    retry_policy: Dict[str, Any] = field(
        default_factory=lambda: {"max_retries": 3, "backoff_ms": 1000, "backoff_multiplier": 2.0}
    )
    """Retry policy for source access"""

    cache_ttl_seconds: Optional[int] = None
    """Cache TTL for this source (None = no caching)"""

    enabled: bool = True
    """Whether this source is available for selection"""


class DataSourceConnector(ABC):
    """Abstract base class for data source connectors."""

    def __init__(self, config: DataSourceConfig, context: Any):
        """Initialize connector."""
        self.config = config
        self.context = context
        self.metrics = SourceMetrics(source_id=config.source_id)
        logger.info(
            f"DataSourceConnector '{config.source_id}' ({config.source_type.value}) initialized"
        )

    @abstractmethod
    def check_availability(self) -> bool:
        """Check if source is currently available."""
        pass

    @abstractmethod
    def execute_query(self, features: List[str], **kwargs) -> Dict[str, List[Any]]:
        """Execute query to retrieve features."""
        pass

    @abstractmethod
    def get_metrics(self) -> SourceMetrics:
        """Get current metrics for this source."""
        pass

    def validate_schema(self, required_features: List[str]) -> bool:
        """Validate that source can provide required features."""
        for feature in required_features:
            if feature not in self.config.schema_mapping:
                logger.warning(
                    f"Feature '{feature}' not found in source '{self.config.source_id}' schema"
                )
                return False
        return True


class SparkTableConnector(DataSourceConnector):
    """Connector for Spark tables (any layer - Silver, Gold, or custom tables)."""

    def __init__(self, config: DataSourceConfig, context: Any):
        """Initialize Spark table connector."""
        super().__init__(config, context)
        self.spark = getattr(context, "spark", None)
        if not self.spark:
            logger.warning("SparkSession not available in context")

    def check_availability(self) -> bool:
        """Check if Spark table exists and is accessible."""
        if not self.spark:
            return False
        try:
            self.spark.table(self.config.location)
            return True
        except Exception as e:
            logger.debug(f"Source '{self.config.source_id}' unavailable: {e}")
            return False

    def execute_query(self, features: List[str], **kwargs) -> Dict[str, List[Any]]:
        """Execute Spark query to retrieve features."""
        if not self.spark:
            raise ValueError("SparkSession not available")

        try:
            # Build column list with schema mapping
            columns = [self.config.schema_mapping.get(f, f) for f in features]

            # Build WHERE clause if entity_ids provided
            where_clause = ""
            entity_ids = kwargs.get("entity_ids", {})
            if entity_ids:
                conditions = []
                for key, values in entity_ids.items():
                    placeholders = ", ".join([f"'{v}'" for v in values])
                    conditions.append(f"{key} IN ({placeholders})")
                where_clause = " AND ".join(conditions)

            # Build query
            query = f"SELECT {', '.join(columns)} FROM {self.config.location}"
            if where_clause:
                query += f" WHERE {where_clause}"

            # Handle point-in-time
            point_in_time = kwargs.get("point_in_time")
            if point_in_time and self.config.timestamp_column:
                query += f" AND {self.config.timestamp_column} <= '{point_in_time.isoformat()}'"

            logger.debug(f"Executing Spark query: {query[:100]}...")

            df = self.spark.sql(query)

            # Efficiently convert to dictionary format
            try:
                pdf = df.toPandas()
                result = pdf.to_dict(orient="list")
            except Exception as pe:
                logger.warning(f"Pandas conversion failed: {pe}, falling back to row collection")
                rows = df.collect()
                result = {col: [row[col] for row in rows] for col in df.columns}

            self.metrics.last_updated = datetime.now(timezone.utc)
            return result

        except Exception as e:
            raise ValueError(f"Spark query execution failed: {e}") from e

    def get_metrics(self) -> SourceMetrics:
        """Get metrics for Spark source."""
        if self.spark:
            try:
                df = self.spark.table(self.config.location)
                self.metrics.estimated_rows = df.count()
                self.metrics.materialized = True
            except Exception:
                pass
        return self.metrics


class DuckDBTableConnector(DataSourceConnector):
    """Connector for DuckDB tables (lightweight local querying)."""

    def __init__(self, config: DataSourceConfig, context: Any):
        """Initialize DuckDB connector."""
        super().__init__(config, context)
        try:
            import duckdb  # type: ignore

            self.duckdb = duckdb
            self.conn = duckdb.connect(":memory:")
        except ImportError:
            logger.warning("DuckDB not available")
            self.duckdb = None
            self.conn = None

    def check_availability(self) -> bool:
        """Check if DuckDB source is accessible."""
        if not self.conn:
            return False
        try:
            self.conn.execute(f"SELECT 1 FROM {self.config.location} LIMIT 1")
            return True
        except Exception:
            return False

    def execute_query(self, features: List[str], **kwargs) -> Dict[str, List[Any]]:
        """Execute DuckDB query to retrieve features."""
        if not self.conn:
            raise ValueError("DuckDB connection not available")

        try:
            columns = [self.config.schema_mapping.get(f, f) for f in features]

            query = f"SELECT {', '.join(columns)} FROM {self.config.location}"

            entity_ids = kwargs.get("entity_ids", {})
            if entity_ids:
                conditions = []
                for key, values in entity_ids.items():
                    placeholders = ", ".join([f"'{v}'" for v in values])
                    conditions.append(f"{key} IN ({placeholders})")
                query += " WHERE " + " AND ".join(conditions)

            logger.debug(f"Executing DuckDB query: {query[:100]}...")

            result = self.conn.execute(query).fetch_df().to_dict(orient="list")
            self.metrics.last_updated = datetime.now(timezone.utc)
            return result

        except Exception as e:
            raise ValueError(f"DuckDB query execution failed: {e}") from e

    def get_metrics(self) -> SourceMetrics:
        """Get metrics for DuckDB source."""
        if self.conn:
            try:
                count_query = f"SELECT COUNT(*) as cnt FROM {self.config.location}"
                self.metrics.estimated_rows = self.conn.execute(count_query).fetchone()[0]
            except Exception:
                pass
        return self.metrics


class CustomCallableConnector(DataSourceConnector):
    """Connector for custom sources via callable functions."""

    def __init__(
        self,
        config: DataSourceConfig,
        context: Any,
        executor_func: Callable[[List[str], Dict[str, Any]], Dict[str, List[Any]]],
    ):
        """Initialize custom connector."""
        super().__init__(config, context)
        self.executor_func = executor_func

    def check_availability(self) -> bool:
        """Check if custom source is available."""
        try:
            # Try a minimal call
            self.executor_func([], {})
            return True
        except Exception:
            return False

    def execute_query(self, features: List[str], **kwargs) -> Dict[str, List[Any]]:
        """Execute custom query."""
        try:
            return self.executor_func(features, kwargs)
        except Exception as e:
            raise ValueError(f"Custom source execution failed: {e}") from e

    def get_metrics(self) -> SourceMetrics:
        """Get metrics for custom source."""
        return self.metrics


class DataSourceRegistry:
    """Registry and manager for data sources."""

    def __init__(self):
        """Initialize registry."""
        self._sources: Dict[str, DataSourceConfig] = {}
        self._connectors: Dict[str, DataSourceConnector] = {}
        logger.info("DataSourceRegistry initialized")

    def register_source(
        self, config: DataSourceConfig, connector: Optional[DataSourceConnector] = None
    ) -> None:
        """Register a data source."""
        self._sources[config.source_id] = config

        if connector:
            self._connectors[config.source_id] = connector
        else:
            logger.debug(f"Source '{config.source_id}' registered without connector")

        logger.info(f"Data source registered: '{config.source_id}' ({config.source_type.value})")

    def get_source_config(self, source_id: str) -> Optional[DataSourceConfig]:
        """Get source configuration by ID."""
        return self._sources.get(source_id)

    def get_connector(self, source_id: str) -> Optional[DataSourceConnector]:
        """Get connector for a source."""
        return self._connectors.get(source_id)

    def list_sources(self, enabled_only: bool = True) -> List[str]:
        """List all registered sources."""
        if enabled_only:
            return [src_id for src_id, config in self._sources.items() if config.enabled]
        return list(self._sources.keys())

    def get_available_sources(self) -> Dict[str, SourceMetrics]:
        """Get all currently available sources with their metrics."""
        available = {}
        for source_id, connector in self._connectors.items():
            if connector.check_availability():
                available[source_id] = connector.get_metrics()
        return available

    def get_sources_for_features(
        self, feature_names: List[str], required_only: bool = False
    ) -> Dict[str, DataSourceConfig]:
        """Get sources that can provide requested features."""
        compatible = {}

        for source_id, config in self._sources.items():
            if not config.enabled:
                continue

            if not config.schema_mapping:
                continue

            # Check which features this source provides
            provided = [f for f in feature_names if f in config.schema_mapping]

            if required_only:
                if len(provided) == len(feature_names):
                    compatible[source_id] = config
            else:
                if provided:  # At least one feature
                    compatible[source_id] = config

        return compatible
