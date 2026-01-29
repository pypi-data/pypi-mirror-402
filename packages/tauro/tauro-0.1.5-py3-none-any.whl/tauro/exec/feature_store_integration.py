"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field

from loguru import logger  # type: ignore

from tauro.config.contexts import Context
from tauro.feature_store import (
    MaterializedFeatureStore,
    VirtualizedFeatureStore,
    FeatureGroupSchema,
)
from tauro.feature_store.base import FeatureStoreConfig, FeatureStoreMode
from tauro.feature_store.hybrid import HybridFeatureStore
from tauro.feature_store.exceptions import FeatureStoreException
from tauro.io.input import InputLoader
from tauro.io.output import DataOutputManager


@dataclass
class FeatureStoreNodeConfig:
    """Configuration for feature store nodes with agnóstic data source support."""

    type: str = "feature_store"  # Node type identifier
    input: Optional[List[str]] = None  # Input dataset keys (like normal nodes)
    output: Optional[List[str]] = None  # Output dataset keys (like normal nodes)

    # Core operation fields
    operation: str = "write"  # "write", "read", "transform"
    feature_group: Optional[str] = None
    schema: Optional[FeatureGroupSchema] = None  # For write/transform
    feature_names: Optional[List[str]] = None  # For read operations
    storage_path: Optional[str] = None
    storage_format: str = "parquet"
    mode: str = "append"  # "append" or "overwrite"
    backfill: bool = False
    entity_ids: Optional[Dict[str, List[Any]]] = None
    point_in_time: Optional[datetime] = None
    as_dataframe: bool = True

    # Feature Store mode selection
    store_mode: str = "materialized"  # "materialized", "virtualized", or "hybrid"

    # Hybrid mode settings
    hybrid_threshold_rows: int = 10000
    auto_materialize: bool = False

    # Virtualization settings
    enable_virtual_layer: bool = False
    register_virtual_table: bool = True

    selection_strategy: Optional[str] = None
    max_latency_ms: Optional[int] = None  # Maximum acceptable latency
    max_freshness_minutes: Optional[int] = None  # Maximum data age
    min_availability_pct: Optional[float] = None  # Minimum availability % (0-100)
    max_cost_budget: Optional[float] = None  # Maximum cost per query

    prefer_materialized: bool = False  # Prefer pre-computed features
    prefer_indexed: bool = False  # Prefer indexed sources
    prefer_cached: bool = False  # Prefer cached data

    feature_source_mapping: Optional[Dict[str, str]] = field(default_factory=dict)

    custom_scorer: Optional[Callable[[Dict[str, Any]], float]] = None


class FeatureStoreNodeHandler:
    """
    Handler for Feature Store nodes - integrates Feature Store as a native module type.
    """

    def __init__(
        self,
        context: Context,
        store_mode: Optional[str] = None,
        source_registry: Optional[Any] = None,
        default_selector: Optional[Any] = None,
    ):
        """Initialize Feature Store node handler with optional agnóstic source support."""
        self.context = context
        self.input_loader = InputLoader(context)
        self.output_manager = DataOutputManager(context)

        # Agnóstic source components (Fase 1)
        self.source_registry = source_registry or getattr(context, "feature_source_registry", None)
        self.default_selector = default_selector or getattr(
            context, "feature_source_selector", None
        )

        # Determine store mode
        if store_mode is None:
            store_mode = getattr(context, "feature_store_mode", "materialized")

        self.store_mode = FeatureStoreMode(
            store_mode
            if store_mode in ["materialized", "virtualized", "hybrid"]
            else "materialized"
        )

        # Lazy initialize stores
        self._materialized_store: Optional[MaterializedFeatureStore] = None
        self._virtualized_store: Optional[VirtualizedFeatureStore] = None
        self._hybrid_store: Optional[HybridFeatureStore] = None
        self._virtual_layer = None

        log_msg = f"FeatureStoreNodeHandler initialized with mode: {self.store_mode.value}"
        if self.source_registry:
            log_msg += " (agnóstic sources enabled)"
        logger.info(log_msg)

    @property
    def materialized_store(self) -> MaterializedFeatureStore:
        """Lazy-load materialized store"""
        if self._materialized_store is None:
            storage_path = getattr(self.context, "feature_store_path", None)
            storage_format = getattr(self.context, "feature_store_format", "parquet")

            self._materialized_store = MaterializedFeatureStore(
                self.context, storage_path=storage_path, storage_format=storage_format
            )
        return self._materialized_store

    @property
    def virtualized_store(self) -> VirtualizedFeatureStore:
        """Lazy-load virtualized store with agnostic data source support."""
        if self._virtualized_store is None:
            self._virtualized_store = VirtualizedFeatureStore(
                self.context,
                source_registry=self.source_registry,
                default_selector=self.default_selector,
            )
            if self._virtual_layer:
                self._virtualized_store.set_virtual_layer(self._virtual_layer)
        return self._virtualized_store

    @property
    def hybrid_store(self) -> HybridFeatureStore:
        """Lazy-load hybrid store"""
        if self._hybrid_store is None:
            config = FeatureStoreConfig(
                mode=FeatureStoreMode.HYBRID,
                storage_path=getattr(self.context, "feature_store_path", None),
                storage_format=getattr(self.context, "feature_store_format", "parquet"),
                enable_virtualization=True,
                hybrid_threshold_rows=getattr(self.context, "hybrid_threshold_rows", 10000),
                auto_materialize_on_read=getattr(self.context, "auto_materialize", False),
            )
            self._hybrid_store = HybridFeatureStore(self.context, config)
            if self._virtual_layer:
                self._hybrid_store.set_virtual_layer(self._virtual_layer)
        return self._hybrid_store

    def set_virtual_layer(self, virtual_layer: Any) -> None:
        """Configure VirtualDataLayer for feature store integration."""
        self._virtual_layer = virtual_layer

        # Update existing stores if already initialized
        if self._virtualized_store:
            self._virtualized_store.set_virtual_layer(virtual_layer)
        if self._hybrid_store:
            self._hybrid_store.set_virtual_layer(virtual_layer)

        logger.info("VirtualDataLayer configured for feature stores")

    def get_store(self, config: FeatureStoreNodeConfig):
        """Get appropriate store based on configuration."""
        # Config overrides instance mode
        mode_str = config.store_mode or self.store_mode.value

        if mode_str == "hybrid":
            return self.hybrid_store
        elif mode_str == "virtualized":
            store = self.virtualized_store
            # Auto-register as virtual table if enabled
            if (
                config.enable_virtual_layer
                and config.register_virtual_table
                and config.feature_group
            ):
                store.register_as_virtual_table(config.feature_group)
            return store
        else:  # materialized
            return self.materialized_store

    def handle_write_node(
        self, config: FeatureStoreNodeConfig, input_dfs: List[Any]
    ) -> Dict[str, Any]:
        """Handle feature_write node type with agnóstic source support."""
        try:
            if not config.feature_group:
                raise ValueError("feature_group is required for write operations")

            if not config.schema:
                raise ValueError("schema is required for write operations")

            if not input_dfs:
                raise ValueError("input data is required for write operations")

            # Get the first input dataframe (standard node behavior)
            data = input_dfs[0]

            # Get store instance based on configuration
            store = self.get_store(config)

            # Register schema
            store.register_features(config.schema)

            # Write features
            store.write_features(
                feature_group=config.feature_group,
                data=data,
                mode=config.mode,
                backfill=config.backfill,
                **{
                    k: v
                    for k, v in vars(config).items()
                    if k
                    not in [
                        "type",
                        "operation",
                        "feature_group",
                        "input",
                        "output",
                        "feature_names",
                        "schema",
                        "mode",
                        "backfill",
                        "point_in_time",
                        "entity_ids",
                        "as_dataframe",
                        "selection_strategy",
                        "max_latency_ms",
                        "max_freshness_minutes",
                        "min_availability_pct",
                        "max_cost_budget",
                        "prefer_materialized",
                        "prefer_indexed",
                        "prefer_cached",
                        "feature_source_mapping",
                        "custom_scorer",
                        "store_mode",
                        "hybrid_threshold_rows",
                        "auto_materialize",
                        "enable_virtual_layer",
                        "register_virtual_table",
                        "storage_path",
                        "storage_format",
                        "kwargs",
                    ]
                },
            )

            # Return output data for next nodes (like normal nodes do)
            output_data = {
                "status": "success",
                "feature_group": config.feature_group,
                "rows_written": len(data) if hasattr(data, "__len__") else 0,
                "mode": config.mode,
                "backfill": config.backfill,
                "data": data,  # Pass through the data for next nodes
            }

            # If agnóstic sources are enabled, optionally register this written source
            if self.source_registry and config.feature_group:
                try:
                    self._register_written_source_agnostic(config)
                except Exception as e:
                    logger.debug(
                        f"Could not register written features in agnóstic registry: {e}. "
                        f"Continuing without registration."
                    )

            logger.info(f"Feature write completed for feature group: {config.feature_group}")
            return output_data

        except Exception as e:
            logger.error(f"Feature write node failed: {e}")
            raise

    def _register_written_source_agnostic(self, config: FeatureStoreNodeConfig) -> None:
        """Register written features in agnóstic source registry for future reads."""
        try:
            # Optional: Register the written features as a new source
            # This allows future reads to use the newly written materialized features
            source_id = f"written_{config.feature_group}_{config.store_mode}"

            logger.debug(
                f"Registering written feature group '{config.feature_group}' "
                f"as agnóstic source: {source_id}"
            )

            # Note: Actual registration would depend on DataSourceRegistry API
            # This is a placeholder for future integration

        except Exception as e:
            logger.debug(f"Agnóstic source registration not fully implemented: {e}")
            raise

    def handle_read_node(self, config: FeatureStoreNodeConfig) -> Any:
        """Handle feature_read node type with optional agnóstic source selection."""
        try:
            if not config.feature_names:
                raise ValueError("feature_names is required for read operations")

            features = None
            source_selection_info = {}

            # Attempt agnóstic source selection if enabled (Fase 1)
            if self.source_registry and config.selection_strategy:
                try:
                    features, source_selection_info = self._read_features_agnostic(config)
                except Exception as e:
                    logger.warning(
                        f"Agnóstic source selection failed, falling back to traditional store: {e}"
                    )
                    source_selection_info["fallback_reason"] = str(e)

            # Traditional store-based retrieval if agnóstic didn't work
            if features is None:
                store = self.get_store(config)

                # Read features
                features = store.get_features(
                    feature_names=config.feature_names,
                    entity_ids=config.entity_ids,
                    point_in_time=config.point_in_time,
                    as_dataframe=config.as_dataframe,
                )

                if not source_selection_info:
                    source_selection_info["method"] = "traditional_store"
                    source_selection_info["store_mode"] = config.store_mode

            # Return features dataframe (will be stored in output automatically)
            logger.info(
                f"Feature read completed: retrieved {len(config.feature_names)} features. "
                f"Source selection: {source_selection_info}"
            )

            return features
        except Exception as e:
            logger.error(f"Feature read node failed: {e}")
            raise

    def _read_features_agnostic(self, config: FeatureStoreNodeConfig) -> tuple:
        """Read features using agnóstic data source selection."""
        try:
            # Lazy import to avoid circular dependencies
            from tauro.feature_store.source_selection_policy import (
                SelectionCriteria,
                create_selector,
            )

            # Build selection criteria from config
            criteria_kwargs = {}
            if config.max_latency_ms is not None:
                criteria_kwargs["max_latency_ms"] = config.max_latency_ms
            if config.max_freshness_minutes is not None:
                criteria_kwargs["max_freshness_minutes"] = config.max_freshness_minutes
            if config.min_availability_pct is not None:
                criteria_kwargs["min_availability_pct"] = config.min_availability_pct
            if config.max_cost_budget is not None:
                criteria_kwargs["max_cost_budget"] = config.max_cost_budget

            # Add preferences
            criteria_kwargs["prefer_materialized"] = config.prefer_materialized
            criteria_kwargs["prefer_indexed"] = config.prefer_indexed
            criteria_kwargs["custom_scorer"] = config.custom_scorer

            selection_criteria = SelectionCriteria(**criteria_kwargs)

            # Get virtualized store for agnóstic selection
            store = self.virtualized_store

            # Read with agnóstic source selection
            features = store.get_features(
                feature_names=config.feature_names,
                entity_ids=config.entity_ids,
                point_in_time=config.point_in_time,
                as_dataframe=config.as_dataframe,
                selection_criteria=selection_criteria,
                selection_strategy=config.selection_strategy,
            )

            # Build selection info for logging
            selection_info = {
                "method": "agnóstic",
                "strategy": config.selection_strategy,
                "constraints": {
                    "max_latency_ms": config.max_latency_ms,
                    "max_freshness_minutes": config.max_freshness_minutes,
                    "min_availability_pct": config.min_availability_pct,
                    "max_cost_budget": config.max_cost_budget,
                },
            }

            logger.debug(f"Agnóstic source selection info: {selection_info}")

            return features, selection_info

        except ImportError:
            logger.warning(
                "Agnóstic source selection modules not available, "
                "ensure data_source.py and source_selection_policy.py are installed"
            )
            raise
        except Exception as e:
            logger.warning(f"Error during agnóstic source selection: {e}")
            raise

    def handle_transform_node(
        self, config: FeatureStoreNodeConfig, input_dfs: List[Any], transform_func=None
    ) -> Any:
        """Handle feature_transform node type."""
        try:
            if not config.feature_group:
                raise ValueError("feature_group is required for transform operations")

            if not config.schema:
                raise ValueError("schema is required for transform operations")

            if not input_dfs:
                raise ValueError("input data is required for transform operations")

            # Get the first input dataframe
            data = input_dfs[0]

            # Apply transformation if provided
            if transform_func:
                try:
                    data = transform_func(data)
                    logger.debug("Applied custom transformation function")
                except Exception as e:
                    logger.error(f"Transformation failed: {e}")
                    raise

            # Register and write using configured store
            store = self.get_store(config)
            store.register_features(config.schema)

            store.write_features(
                feature_group=config.feature_group,
                data=data,
                mode=config.mode,
                backfill=config.backfill,
            )

            # Return transformed data for next nodes
            logger.info(f"Feature transform completed for feature group: {config.feature_group}")
            return data

        except Exception as e:
            logger.error(f"Feature transform node failed: {e}")
            raise

    def handle_refresh_node(self, config: FeatureStoreNodeConfig) -> Dict[str, Any]:
        """Handle feature_refresh node type - Automates materialization via Tauro Engine."""
        try:
            if not config.feature_group:
                raise ValueError("feature_group is required for refresh operations")

            logger.info(f"Starting auto-materialization refresh for group: {config.feature_group}")

            # Hybrid mode is the most common use case for auto-refresh
            store = self.get_store(config)

            if hasattr(store, "refresh_features"):
                # If it's a Hybrid store, it knows how to pull from Virtual to Materialized
                # If it's Materialized, we pass the virtual store as provider
                provider = None
                if isinstance(store, MaterializedFeatureStore):
                    provider = self.virtualized_store
                elif isinstance(store, HybridFeatureStore):
                    # Hybrid already uses its internal virtualized store
                    pass

                store.refresh_features(config.feature_group, source_provider=provider)
            else:
                raise FeatureStoreException(
                    f"Store mode '{config.store_mode}' does not support refresh operations"
                )

            return {
                "status": "success",
                "feature_group": config.feature_group,
                "operation": "refresh",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Feature refresh node failed: {e}")
            raise

    def handle_feature_store_node(self, node_config: Dict[str, Any], input_dfs: List[Any]) -> Any:
        """Main handler for feature_store node type with agnóstic support."""
        try:
            config = FeatureStoreNodeConfig(**node_config)
        except TypeError as e:
            # Handle case where unknown fields are passed
            logger.debug(f"Could not parse all node config fields: {e}")
            # Try filtering to known fields only
            known_fields = {f.name for f in config.__dataclass_fields__.values()}
            filtered_config = {k: v for k, v in node_config.items() if k in known_fields}
            config = FeatureStoreNodeConfig(**filtered_config)

        logger.info(
            f"Executing feature_store node: {config.operation}"
            f"{' (agnóstic)' if config.selection_strategy else ''}"
        )

        try:
            if config.operation == "write":
                return self.handle_write_node(config, input_dfs)

            elif config.operation == "read":
                return self.handle_read_node(config)

            elif config.operation == "transform":
                return self.handle_transform_node(config, input_dfs)

            elif config.operation == "refresh":
                return self.handle_refresh_node(config)

            else:
                raise ValueError(
                    f"Unknown feature_store operation: {config.operation}. "
                    f"Supported: write, read, transform, refresh"
                )

        except FeatureStoreException as e:
            logger.error(f"Feature Store operation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Feature Store node error: {e}")
            raise


def create_feature_store_handler(context: Context) -> FeatureStoreNodeHandler:
    """
    Factory function to create Feature Store node handler.
    """
    return FeatureStoreNodeHandler(context)
