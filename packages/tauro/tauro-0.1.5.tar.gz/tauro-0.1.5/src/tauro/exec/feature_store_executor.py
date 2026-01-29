"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from loguru import logger  # type: ignore

from tauro.config.contexts import Context
from tauro.feature_store import (
    MaterializedFeatureStore,
    VirtualizedFeatureStore,
    HybridFeatureStore,
    FeatureStoreConfig,
    FeatureStoreMode,
)
from tauro.feature_store.schema import FeatureGroupSchema
from tauro.io.input import InputLoader
from tauro.io.output import DataOutputManager


class FeatureStoreExecutorAdapter:
    """Adapter for executing feature store operations within pipeline context."""

    def __init__(self, context: Context):
        """Initialize Feature Store Executor Adapter."""
        self.context = context
        self.input_loader = InputLoader(context)
        self.output_manager = DataOutputManager(context)
        self.materialized_store = None
        self.virtualized_store = None
        self.hybrid_store = None
        self.active_store = None

        logger.info("FeatureStoreExecutorAdapter initialized with pipeline context")

    def create_materialized_store(
        self, storage_path: Optional[str] = None, storage_format: str = "parquet"
    ) -> MaterializedFeatureStore:
        """Create materialized feature store with executor context."""
        self.materialized_store = MaterializedFeatureStore(
            self.context, storage_path=storage_path, storage_format=storage_format
        )
        self.active_store = self.materialized_store
        return self.materialized_store

    def create_virtualized_store(self) -> VirtualizedFeatureStore:
        """Create virtualized feature store with executor context."""
        self.virtualized_store = VirtualizedFeatureStore(self.context)
        self.active_store = self.virtualized_store
        return self.virtualized_store

    def create_hybrid_store(
        self, config: Optional[FeatureStoreConfig] = None
    ) -> HybridFeatureStore:
        """Create hybrid feature store with executor context."""
        self.hybrid_store = HybridFeatureStore(self.context, config=config)
        self.active_store = self.hybrid_store
        return self.hybrid_store

    def create_store_from_config(self, config: FeatureStoreConfig) -> Any:
        """Create appropriate feature store based on configuration mode."""
        if config.mode == FeatureStoreMode.MATERIALIZED:
            return self.create_materialized_store(
                storage_path=config.storage_path, storage_format=config.storage_format
            )
        elif config.mode == FeatureStoreMode.VIRTUALIZED:
            return self.create_virtualized_store()
        elif config.mode == FeatureStoreMode.HYBRID:
            return self.create_hybrid_store(config=config)
        else:
            # Fallback to materialized
            return self.create_materialized_store()

    def write_features_from_output(
        self,
        feature_group: str,
        output_key: str,
        schema: FeatureGroupSchema,
        mode: str = "append",
        backfill: bool = False,
        **write_options,
    ) -> None:
        """Write features from pipeline output to materialized store."""
        if not self.active_store:
            self.create_materialized_store()

        try:
            # Register feature group schema
            self.active_store.register_features(schema)

            # Get output data from context
            if (
                hasattr(self.context, "execution_outputs")
                and output_key in self.context.execution_outputs
            ):
                data = self.context.execution_outputs[output_key]

                # Write to store (usually only materialized supports this)
                self.active_store.write_features(
                    feature_group=feature_group,
                    data=data,
                    mode=mode,
                    backfill=backfill,
                    **write_options,
                )

                logger.info(
                    f"Successfully wrote features to '{feature_group}' "
                    f"from output '{output_key}'"
                )
            else:
                raise ValueError(f"Output key '{output_key}' not found in execution context")

        except Exception as e:
            logger.error(f"Failed to write features from output: {e}")
            raise

    def read_features_as_input(
        self,
        input_key: str,
        feature_names: List[str],
        entity_ids: Optional[Dict[str, List[Any]]] = None,
        point_in_time: Optional[datetime] = None,
        as_dataframe: bool = True,
    ) -> Any:
        """Read features from store and register as pipeline input."""
        if not self.active_store:
            self.create_materialized_store()

        try:
            features_data = self.active_store.get_features(
                feature_names=feature_names,
                entity_ids=entity_ids,
                point_in_time=point_in_time,
            )
            if as_dataframe and isinstance(features_data, dict):
                import pandas as pd

                features_data = pd.DataFrame(features_data)

            if not hasattr(self.context, "feature_store_inputs"):
                self.context.feature_store_inputs = {}

            self.context.feature_store_inputs[input_key] = features_data

            logger.info(f"Retrieved {len(feature_names)} features as input '{input_key}'")

            return features_data

        except Exception as e:
            logger.error(f"Failed to read features as input: {e}")
            raise

    def refresh_feature_group(
        self,
        feature_group: str,
        store_mode: str = "hybrid",
    ) -> Dict[str, Any]:
        """Perform automated materialization for a feature group."""
        try:
            # Initialize appropriate store
            if store_mode == "hybrid":
                store = self.create_hybrid_store()
            else:
                store = self.create_materialized_store()

            logger.info(
                f"Triggering materialization refresh for '{feature_group}' (mode={store_mode})"
            )

            # Hybrid stores already have both materialized and virtualized
            if hasattr(store, "refresh_features"):
                # If it's a separate Materialized store, we need to provide a virtualized source if possible
                provider = None
                if store_mode == "materialized":
                    # Try to create a virtualized store to act as provider
                    provider = VirtualizedFeatureStore(self.context)

                store.refresh_features(feature_group, source_provider=provider)

            return {
                "status": "success",
                "feature_group": feature_group,
                "refreshed_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to refresh feature group '{feature_group}': {e}")
            raise


def write_features_node(
    context: Context,
    feature_group: str,
    output_key: str,
    schema: FeatureGroupSchema,
    storage_path: Optional[str] = None,
    mode: str = "append",
    backfill: bool = False,
    **write_options,
) -> None:
    """Pipeline node function for writing features to materialized store."""
    adapter = FeatureStoreExecutorAdapter(context)

    if storage_path:
        adapter.create_materialized_store(storage_path=storage_path)
    else:
        adapter.create_materialized_store()

    adapter.write_features_from_output(
        feature_group=feature_group,
        output_key=output_key,
        schema=schema,
        mode=mode,
        backfill=backfill,
        **write_options,
    )


def read_features_node(
    context: Context,
    input_key: str,
    feature_names: List[str],
    storage_path: Optional[str] = None,
    entity_ids: Optional[Dict[str, List[Any]]] = None,
    point_in_time: Optional[datetime] = None,
    as_dataframe: bool = True,
) -> Any:
    """Pipeline node function for reading features from materialized store."""
    adapter = FeatureStoreExecutorAdapter(context)

    if storage_path:
        adapter.create_materialized_store(storage_path=storage_path)
    else:
        adapter.create_materialized_store()

    return adapter.read_features_as_input(
        input_key=input_key,
        feature_names=feature_names,
        entity_ids=entity_ids,
        point_in_time=point_in_time,
        as_dataframe=as_dataframe,
    )


def refresh_features_node(
    context: Context,
    feature_group: str,
    store_mode: str = "hybrid",
) -> Dict[str, Any]:
    """Pipeline node function for automated feature materialization."""
    adapter = FeatureStoreExecutorAdapter(context)
    return adapter.refresh_feature_group(feature_group, store_mode=store_mode)


def create_feature_store_for_pipeline(context: Context) -> FeatureStoreExecutorAdapter:
    """Create a feature store adapter for use in pipeline execution."""
    return FeatureStoreExecutorAdapter(context)
