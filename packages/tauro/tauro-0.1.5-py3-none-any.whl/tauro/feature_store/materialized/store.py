"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from loguru import logger  # type: ignore

from tauro.feature_store.base import BaseFeatureStore, FeatureStoreConfig
from tauro.feature_store.schema import FeatureGroupSchema
from tauro.feature_store.exceptions import (
    FeatureMaterializationError,
    FeatureNotFoundError,
)
from tauro.io.input import InputLoader
from tauro.io.output import DataOutputManager


class MaterializedFeatureStore(BaseFeatureStore):
    """
    Feature Store with physical data materialization.
    """

    def __init__(
        self,
        context: Any,
        storage_path: Optional[str] = None,
        storage_format: str = "parquet",
        config: Optional[FeatureStoreConfig] = None,
    ):
        """
        Initialize Materialized Feature Store with Tauro IO integration.
        """
        self.config = config or FeatureStoreConfig()
        super().__init__(context, config=self.config)
        self.storage_format = storage_format or self.config.storage_format
        self.storage_path = (
            storage_path or self.config.storage_path or self._get_default_storage_path()
        )

        # ✅ Initialize Tauro IO managers for agnóstic input/output
        self.input_loader = InputLoader(context)
        self.output_manager = DataOutputManager(context)

        # Phase 2: Initialize Online Store if enabled
        self.online_store = None
        if self.config.enable_online_store:
            try:
                from tauro.feature_store.online import create_online_store

                # Fixed: create_online_store expects a single config dictionary
                self.online_store = create_online_store(self.config.online_store_config)
                logger.info(f"Online store enabled: {self.config.online_store_type}")
            except Exception as e:
                logger.error(f"Failed to initialize online store: {e}")

        # Ensure storage directory exists
        self._ensure_storage_exists()

        self._feature_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"MaterializedFeatureStore initialized with Tauro IO "
            f"(format={storage_format}, path={self.storage_path})"
        )

    def _get_default_storage_path(self) -> str:
        """Get default storage path from context or use standard location."""
        if hasattr(self.context, "feature_store_path"):
            return self.context.feature_store_path
        return "/data/gold/features"

    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        try:
            p = Path(self.storage_path)
            p.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Feature store storage path ensured: {self.storage_path}")
        except Exception as e:
            logger.warning(f"Could not create local storage path: {e}")

    def register_features(self, schema: FeatureGroupSchema) -> None:
        """Register and prepare materialized feature group."""
        try:
            self.metadata.register_feature_group(schema)
            logger.info(f"Materialized feature group registered: {schema.name}")
        except Exception as e:
            raise FeatureMaterializationError(
                f"Failed to register feature group '{schema.name}': {e}"
            ) from e

    def write_features(
        self,
        feature_group: str,
        data: Union[Dict[str, List[Any]], Any],
        mode: str = "append",
        backfill: bool = False,
        **write_options,
    ) -> None:
        """Write features to materialized store with retry logic and validation."""
        # Validate inputs
        if not feature_group:
            raise FeatureMaterializationError("feature_group name cannot be empty")
        if mode not in ("append", "overwrite", "ignore"):
            raise FeatureMaterializationError(f"Invalid write mode: {mode}")

        # Retry loop for transient failures
        last_exception = None
        for attempt in range(self.config.max_retries + 1):
            try:
                schema = self.metadata.get_feature_group(feature_group)

                # Convert data to DataFrame if needed
                df = self._prepare_dataframe(data, schema)

                # Determine storage location and format
                storage_path = write_options.get("path", f"{self.storage_path}/{feature_group}")
                storage_format = write_options.get("format", self.storage_format)

                # Use writer factory for direct write (Agnostic Tauro IO)
                from tauro.io.factories import WriterFactory

                writer_factory = WriterFactory(self.context)
                writer = writer_factory.get_writer(storage_format)

                # Prepare writer config
                writer_config = {
                    "mode": mode,
                    "table_name": feature_group,
                    "schema": "gold",
                }

                # Add backfill metadata
                if backfill:
                    writer_config["backfill"] = True

                # Add any additional partition or write options
                writer_config.update(
                    {k: v for k, v in write_options.items() if k not in ["format", "path"]}
                )

                # Direct write via Tauro IO writer
                writer.write(df, storage_path, writer_config)

                # Phase 2: Sync to online store if enabled
                if self.config.sync_to_online and self.online_store:
                    self._sync_to_online_store(feature_group, df, schema)

                # Phase 2: Monitor feature drift
                self._monitor_feature_drift(feature_group, df)

                logger.info(
                    f"Successfully wrote features to '{feature_group}' "
                    f"(mode={mode}, format={storage_format}, path={storage_path}, backfill={backfill})"
                )
                return  # Success, exit retry loop

            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    backoff_ms = self.config.retry_backoff_ms * (
                        self.config.retry_backoff_multiplier**attempt
                    )
                    logger.warning(
                        f"Write attempt {attempt + 1}/{self.config.max_retries + 1} failed for '{feature_group}': {e}. "
                        f"Retrying in {backoff_ms:.0f}ms..."
                    )
                    time.sleep(backoff_ms / 1000.0)
                else:
                    logger.error(
                        f"Failed to write features to '{feature_group}' after {self.config.max_retries + 1} attempts"
                    )

        # If we get here, all retries failed
        raise FeatureMaterializationError(
            f"Failed to write features to '{feature_group}': {last_exception}"
        ) from last_exception

    def _sync_to_online_store(
        self, feature_group: str, df: Any, schema: FeatureGroupSchema
    ) -> None:
        """
        Helper to sync DataFrame data to the online store backend.
        Uses batching to improve reliability and performance.
        """
        try:
            # Convert Spark/Pandas DataFrame to list of dicts for the online store
            data_to_sync = []
            if hasattr(df, "toPandas"):  # Spark
                data_to_sync = df.toPandas().to_dict(orient="records")
            elif hasattr(df, "to_dict"):  # Pandas
                data_to_sync = df.to_dict(orient="records")
            else:
                logger.warning(f"Unsupported DataFrame type for online sync: {type(df)}")
                return

            if not data_to_sync:
                logger.debug(f"No data to sync for '{feature_group}'")
                return

            # Batch processing for online store updates
            batch_size = self.config.online_store_config.get("batch_size", 1000)
            for i in range(0, len(data_to_sync), batch_size):
                batch = data_to_sync[i : i + batch_size]
                self.online_store.write_online_features(
                    feature_group=feature_group,
                    data=batch,
                    entity_keys=schema.entity_keys,
                )

            logger.info(f"Synced {len(data_to_sync)} records to online store for '{feature_group}'")
        except Exception as e:
            # Don't fail the whole write operation if online sync fails
            logger.error(f"Error syncing features to online store: {e}")

    def _monitor_feature_drift(self, feature_group: str, df: Any) -> None:
        """Calculate and log feature statistics for drift monitoring (Phase 2)."""
        try:
            # Check if mlops is available
            try:
                from tauro.mlops.events import emit_event, EventType
            except ImportError:
                return

            stats = self._calculate_drift_stats(df)

            if stats:
                emit_event(
                    EventType.METRIC_LOGGED,
                    data={
                        "component": "feature_store",
                        "operation": "write_features",
                        "feature_group": feature_group,
                        "drift_stats": stats,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                logger.debug(f"Drift metrics emitted for {feature_group}")
        except Exception as e:
            logger.warning(f"Could not monitor drift for {feature_group}: {e}")

    def _calculate_drift_stats(self, df: Any) -> Dict[str, Any]:
        """Calculate numerical statistics for different DataFrame types."""
        if not hasattr(df, "describe"):
            return {}

        if hasattr(df, "toPandas"):  # Spark
            return self._get_spark_drift_stats(df)

        if hasattr(df, "to_dict"):  # Pandas
            return self._get_pandas_drift_stats(df)

        return {}

    def _get_spark_drift_stats(self, df: Any) -> Dict[str, Any]:
        """Extract drift stats from Spark DataFrame."""
        stats = {}
        try:
            desc = df.describe().toPandas().set_index("summary")
            for col in desc.columns:
                try:
                    mean_val = desc.loc["mean", col] if "mean" in desc.index else None
                    if mean_val is not None:
                        stats[col] = {
                            "mean": float(mean_val),
                            "std": float(desc.loc["stddev", col])
                            if "stddev" in desc.index
                            else None,
                        }
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass
        return stats

    def _get_pandas_drift_stats(self, df: Any) -> Dict[str, Any]:
        """Extract drift stats from Pandas DataFrame."""
        stats = {}
        try:
            desc = df.describe()
            for col in desc.columns:
                try:
                    stats[col] = {
                        "mean": float(desc.loc["mean", col]) if "mean" in desc.index else None,
                        "std": float(desc.loc["std", col]) if "std" in desc.index else None,
                    }
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass
        return stats

    def get_features(
        self,
        feature_names: List[str],
        entity_ids: Optional[Dict[str, List[Any]]] = None,
        point_in_time: Optional[datetime] = None,
        as_dataframe: bool = False,
        **kwargs,
    ) -> Union[Dict[str, Any], Any]:
        """Retrieve features from materialized store."""
        groups_features = self._group_feature_refs(feature_names)
        dataframes = self._load_group_dataframes(groups_features, entity_ids, point_in_time)

        if not dataframes:
            raise FeatureNotFoundError("No features found matching the criteria")

        combined_df = (
            dataframes[0][1] if len(dataframes) == 1 else self._join_dataframes(dataframes)
        )

        return combined_df if as_dataframe else self._dataframe_to_dict(combined_df, feature_names)

    def get_online_features(
        self,
        feature_names: List[str],
        entity_keys: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Retrieve features from the online store backend (Phase 2)."""
        if not self.online_store:
            logger.warning("Online store not enabled in this FeatureStore instance")
            return {}

        # Parse feature references group.feature
        groups_features = self._group_feature_refs(feature_names)
        result = {}

        for group_name, features in groups_features.items():
            try:
                group_data = self.online_store.get_online_features(
                    feature_group=group_name,
                    entity_keys=entity_keys,
                    feature_names=features,
                )
                # Prefix result keys with group name if needed or just return as is
                for f_name, f_val in group_data.items():
                    result[f"{group_name}.{f_name}"] = f_val
            except Exception as e:
                logger.error(f"Error retrieving online features for {group_name}: {e}")

        return result

    def _group_feature_refs(self, feature_names: List[str]) -> Dict[str, List[str]]:
        """Parse and group feature references 'group.feature' into a dict."""
        groups_features: Dict[str, List[str]] = {}
        for feature_ref in feature_names:
            try:
                group_name, feature_name = feature_ref.split(".")
            except ValueError:
                raise FeatureNotFoundError(
                    f"Invalid feature reference format: {feature_ref}. Expected 'group.feature'"
                )
            groups_features.setdefault(group_name, []).append(feature_name)
        return groups_features

    def _load_group_dataframes(
        self,
        groups_features: Dict[str, List[str]],
        entity_ids: Optional[Dict[str, List[Any]]],
        point_in_time: Optional[datetime],
    ) -> List[tuple]:
        """Load dataframes for each feature group using InputLoader and return list of (group_name, df)."""
        dataframes: List[tuple] = []
        for group_name, features in groups_features.items():
            try:
                input_config = {
                    "format": self.storage_format,
                    "filepath": str(Path(self.storage_path) / group_name),
                }

                if entity_ids or point_in_time:
                    input_config["partition_filter"] = self._build_filter_expression(
                        entity_ids, point_in_time, group_name
                    )

                # Ensure context has input_config mapping
                self.context.input_config = getattr(self.context, "input_config", {}) or {}
                self.context.input_config[group_name] = input_config

                dfs = self.input_loader.load_inputs([group_name], fail_fast=True)
                if dfs and dfs[0] is not None:
                    df = dfs[0]
                    dataframes.append((group_name, df))
                    logger.debug(f"Retrieved {len(features)} features from '{group_name}'")
            except Exception as e:
                logger.error(f"Failed to retrieve features from '{group_name}': {e}")
                raise
        return dataframes

    def _build_filter_expression(
        self,
        entity_ids: Optional[Dict[str, List[Any]]],
        point_in_time: Optional[datetime],
        group_name: str,
    ) -> Optional[str]:
        """Build filter expression for feature retrieval."""
        filters = []

        # Entity filters
        if entity_ids:
            for key, values in entity_ids.items():
                values_str = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in values)
                filters.append(f"{key} IN ({values_str})")

        # Point-in-time filter
        if point_in_time:
            try:
                schema = self.metadata.get_feature_group(group_name)
                if hasattr(schema, "timestamp_key") and schema.timestamp_key:
                    timestamp_str = point_in_time.isoformat()
                    filters.append(f"{schema.timestamp_key} <= '{timestamp_str}'")
            except Exception as e:
                logger.warning(f"Could not apply point-in-time filter: {e}")

        return " AND ".join(filters) if filters else None

    def _join_dataframes(self, dataframes: List[tuple]) -> Any:
        """Join multiple dataframes on entity keys."""
        if not dataframes:
            return None

        # Start with first dataframe
        result = dataframes[0][1]

        # Join with remaining dataframes
        for group_name, df in dataframes[1:]:
            try:
                schema = self.metadata.get_feature_group(group_name)
                join_keys = getattr(schema, "entity_keys", [])

                if not join_keys:
                    logger.warning(f"No entity keys defined for {group_name}, skipping join")
                    continue

                if hasattr(result, "join"):
                    # Spark DataFrame
                    result = result.join(df, on=join_keys, how="inner")
                elif hasattr(result, "merge"):
                    # Pandas DataFrame
                    result = result.merge(df, on=join_keys, how="inner")
                else:
                    logger.warning(f"Cannot join dataframes of type {type(result)}")
                    return result
            except Exception as e:
                logger.warning(f"Failed to join dataframe for '{group_name}': {e}")

        return result

    def _dataframe_to_dict(self, df: Any, feature_names: List[str]) -> Dict[str, Any]:
        """Convert DataFrame to dictionary format."""
        result = {}

        try:
            if hasattr(df, "toPandas"):
                # Spark DataFrame
                pdf = df.toPandas()
                for col in pdf.columns:
                    # Match requested feature names
                    matching_refs = [fn for fn in feature_names if fn.endswith(f".{col}")]
                    if matching_refs:
                        result[matching_refs[0]] = pdf[col].tolist()
            elif hasattr(df, "to_dict"):
                # Pandas DataFrame
                for col in df.columns:
                    matching_refs = [fn for fn in feature_names if fn.endswith(f".{col}")]
                    if matching_refs:
                        result[matching_refs[0]] = df[col].tolist()
            else:
                logger.warning(f"Unknown DataFrame type: {type(df)}")
        except Exception as e:
            logger.error(f"Failed to convert DataFrame to dict: {e}")

        return result

    def _prepare_dataframe(
        self, data: Union[Dict[str, List[Any]], Any], schema: FeatureGroupSchema
    ) -> Any:
        """Convert data to DataFrame suitable for Tauro IO."""
        # If already a DataFrame, return as-is
        if hasattr(data, "select") or hasattr(data, "columns"):
            return data

        # Convert dict to DataFrame
        if isinstance(data, dict):
            try:
                # Try Spark first
                spark = getattr(self.context, "spark", None)
                if spark:
                    # Validate data
                    self._validate_features(data, schema)

                    # Convert to Spark DataFrame
                    records = self._lists_to_records(data)
                    return spark.createDataFrame(records)
                else:
                    # Fallback to Pandas
                    try:
                        import pandas as pd

                        self._validate_features(data, schema)
                        return pd.DataFrame(data)
                    except ImportError:
                        raise FeatureMaterializationError(
                            "Neither Spark nor Pandas available to create DataFrame"
                        )
            except Exception as e:
                raise FeatureMaterializationError(
                    f"Failed to convert data to DataFrame: {e}"
                ) from e

        raise FeatureMaterializationError(
            f"Unsupported data type: {type(data)}. Expected dict or DataFrame"
        )

    def _validate_features(self, data: Dict[str, List[Any]], schema: FeatureGroupSchema) -> None:
        """Validate feature data against schema."""
        feature_names = self.metadata.list_features(schema.name)
        provided_names = set(data.keys())

        if not provided_names.issubset(set(feature_names)):
            unknown = provided_names - set(feature_names)
            raise ValueError(f"Unknown features: {unknown}")

    def _lists_to_records(self, data: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Convert lists format to records format."""
        if not data:
            return []

        # Get length from first feature list
        length = len(next(iter(data.values())))
        records = [{} for _ in range(length)]

        for feature_name, values in data.items():
            if len(values) != length:
                raise ValueError(f"Feature '{feature_name}' has mismatched length")
            for i, value in enumerate(values):
                records[i][feature_name] = value

        return records

    def refresh_features(self, feature_group: str, source_provider: Optional[Any] = None) -> None:
        """
        Refresh materialized features from source or provided data provider.
        """
        try:
            schema = self.metadata.get_feature_group(feature_group)
            logger.info(f"Refreshing materialized feature group: {feature_group}")

            # If a source provider is given (like in Hybrid mode), pull data from it
            if source_provider and hasattr(source_provider, "get_features"):
                feature_names = [f"{feature_group}.{f.name}" for f in schema.features]

                # Fetch data from provider (Virtualized)
                logger.debug(f"Pulling data from {type(source_provider).__name__} for refresh")
                data = source_provider.get_features(feature_names, as_dataframe=True)

                if data is not None:
                    # Write back to materialized store with overwrite
                    self.write_features(feature_group, data, mode="overwrite")
                    logger.info(
                        f"Successfully refreshed feature group '{feature_group}' from source provider"
                    )
                else:
                    logger.warning(
                        f"Source provider returned no data for group '{feature_group}' refresh"
                    )
            else:
                logger.info(f"Manual refresh triggered for {feature_group}. No provider specified.")

        except Exception as e:
            logger.error(f"Failed to refresh features: {e}")
            raise

    def get_storage_info(self, feature_group: Optional[str] = None) -> Dict[str, Any]:
        """Get storage information for feature groups."""
        info = {}

        groups = [feature_group] if feature_group else self.metadata.list_feature_groups()

        for group in groups:
            group_path = Path(self.storage_path) / group
            try:
                if group_path.exists():
                    info[group] = {
                        "materialized": True,
                        "path": str(group_path),
                        "format": self.storage_format,
                    }
            except Exception as e:
                logger.error(f"Failed to get storage info for {group}: {e}")

        return info

    def list_feature_groups(self) -> List[str]:
        """List all materialized feature groups."""
        return self.metadata.list_feature_groups()

    def delete_feature_group(self, feature_group: str) -> None:
        """Delete a materialized feature group."""
        try:
            group_path = Path(self.storage_path) / feature_group
            if group_path.exists():
                import shutil

                shutil.rmtree(group_path)
                logger.info(f"Deleted feature group: {feature_group}")
        except Exception as e:
            logger.error(f"Failed to delete feature group '{feature_group}': {e}")
            raise

    def load_input_features(self, input_keys: List[str]) -> List[Any]:
        """
        Load input features using Tauro IO catalog pattern.
        """
        try:
            if not input_keys:
                logger.warning("No input keys provided to load_input_features")
                return []

            logger.debug(f"Loading input features from catalog: {input_keys}")

            # Use Tauro IO InputLoader for agnóstic format support
            loaded_data = []
            for key in input_keys:
                try:
                    # Get input config from context
                    input_config = self.context.get("input_config", {})
                    if key not in input_config:
                        raise ValueError(
                            f"Input key '{key}' not found in input_config. "
                            f"Available keys: {list(input_config.keys())}"
                        )

                    input_spec = input_config[key]
                    format_type = input_spec.get("format", "parquet")
                    filepath = input_spec.get("filepath")

                    # Use ReaderFactory for agnóstic format support
                    from tauro.io.factories import ReaderFactory

                    reader_factory = ReaderFactory(self.context)
                    reader = reader_factory.get_reader(format_type)

                    # Read the data
                    df = reader.read(filepath, input_spec)
                    loaded_data.append(df)

                    logger.info(f"Loaded input feature '{key}' from {format_type}: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to load input feature '{key}': {e}")
                    raise

            return loaded_data

        except Exception as e:
            raise FeatureMaterializationError(
                f"Failed to load input features {input_keys}: {e}"
            ) from e

    def _write_single_destination(
        self,
        key: str,
        config: Dict[str, Any],
        group: str,
        df: Any,
        factory: Any,
        mode: str,
        backfill: bool,
    ) -> str:
        """Helper to write to a single output destination."""
        if key not in config:
            logger.warning(f"Output key '{key}' not found in output_config.")
            return "skipped"
        spec = config[key]
        fmt = spec.get("format", self.storage_format)
        path = spec.get("filepath", f"{self.storage_path}/{group}")
        writer = factory.get_writer(fmt)
        writer_config = {"mode": mode, "table_name": group, "schema": "gold"}
        if backfill:
            writer_config["backfill"] = True
        writer_config.update({k: v for k, v in spec.items() if k not in ["format", "filepath"]})
        writer.write(df, path, writer_config)
        logger.info(f"Successfully wrote '{group}' to output '{key}' ({fmt}): {path}")
        return path

    def write_features_to_catalog(
        self,
        feature_group: str,
        data: Union[Dict[str, List[Any]], Any],
        output_keys: Optional[List[str]] = None,
        mode: str = "append",
        backfill: bool = False,
    ) -> Dict[str, str]:
        """Write features using Tauro IO output catalog pattern."""
        results = {}
        try:
            schema = self.metadata.get_feature_group(feature_group)
            df = self._prepare_dataframe(data, schema)
            output_config = self.context.get("output_config", {})
            if not output_config:
                raise ValueError("No output_config defined in context.")

            keys = output_keys or list(output_config.keys())
            from tauro.io.factories import WriterFactory

            factory = WriterFactory(self.context)

            for key in keys:
                try:
                    results[key] = self._write_single_destination(
                        key, output_config, feature_group, df, factory, mode, backfill
                    )
                except Exception as e:
                    logger.error(f"Failed to write to output '{key}': {e}")
                    results[key] = f"error: {str(e)}"

            if self.config.sync_to_online and self.online_store:
                try:
                    self._sync_to_online_store(feature_group, df, schema)
                except Exception as e:
                    logger.warning(f"Online sync failed: {e}")
            try:
                self._monitor_feature_drift(feature_group, df)
            except Exception as e:
                logger.warning(f"Drift monitoring failed: {e}")

            return results
        except Exception as e:
            raise FeatureMaterializationError(f"Failed to write features to catalog: {e}") from e

    def get_input_catalog(self) -> Dict[str, Any]:
        """
        Get available input sources from catalog.
        """
        return self.context.get("input_config", {})

    def get_output_catalog(self) -> Dict[str, Any]:
        """
        Get available output destinations from catalog.
        """
        return self.context.get("output_config", {})

    def list_input_sources(self) -> List[str]:
        """
        List all available input source keys.
        """
        return list(self.get_input_catalog().keys())

    def list_output_destinations(self) -> List[str]:
        """
        List all available output destination keys.
        """
        return list(self.get_output_catalog().keys())

    def write_features_batch(
        self,
        feature_groups_data: Dict[str, Any],
        output_keys: Optional[List[str]] = None,
        mode: str = "append",
    ) -> Dict[str, Dict[str, str]]:
        """
        Write multiple feature groups to outputs in batch.
        """
        batch_results = {}

        try:
            logger.info(f"Writing {len(feature_groups_data)} feature groups in batch")

            for feature_group, data in feature_groups_data.items():
                try:
                    write_results = self.write_features_to_catalog(
                        feature_group=feature_group,
                        data=data,
                        output_keys=output_keys,
                        mode=mode,
                    )
                    batch_results[feature_group] = write_results
                except Exception as e:
                    logger.error(f"Failed to write feature group '{feature_group}': {e}")
                    batch_results[feature_group] = {"error": str(e)}

            logger.info(f"Batch write completed for {len(batch_results)} groups")
            return batch_results

        except Exception as e:
            raise FeatureMaterializationError(f"Batch write failed: {e}") from e
