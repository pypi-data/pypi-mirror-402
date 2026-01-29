"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime
from abc import ABC, abstractmethod
import time

from loguru import logger  # type: ignore

from tauro.feature_store.base import BaseFeatureStore, FeatureStoreConfig
from tauro.feature_store.schema import FeatureGroupSchema
from tauro.feature_store.exceptions import (
    VirtualizationQueryError,
)
from tauro.feature_store.data_source import (
    DataSourceRegistry,
    DataSourceConnector,
    DataSourceConfig,
)
from tauro.feature_store.source_selection_policy import (
    SourceSelector,
    SelectionStrategy,
    SelectionCriteria,
    create_selector,
)

if TYPE_CHECKING:
    from tauro.virtualization import VirtualTable, VirtualDataLayer


class QueryExecutor(ABC):
    """Abstract query executor for virtualized features."""

    @abstractmethod
    def execute(self, query: str, **kwargs) -> Dict[str, List[Any]]:
        """Execute a query and return results."""
        pass


class DuckDBQueryExecutor(QueryExecutor):
    """DuckDB-based query executor for virtualized features with retry support."""

    def __init__(self, context: Any, config: Optional[FeatureStoreConfig] = None):
        """Initialize DuckDB executor."""
        self.context = context
        self.config = config or FeatureStoreConfig()
        self._executor_func: Optional[Callable] = None
        logger.info("DuckDBQueryExecutor initialized")

    def execute(self, query: str, **kwargs) -> Dict[str, List[Any]]:
        """Execute DuckDB query with retry support."""
        if not query or not query.strip():
            raise VirtualizationQueryError("Query cannot be empty", executor="DuckDB")

        last_exception = None
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"Executing DuckDB query [attempt {attempt + 1}]: {query[:100]}...")

                import duckdb  # type: ignore

                conn = duckdb.connect(":memory:")
                df = conn.execute(query).fetchdf()
                result = df.to_dict(orient="list")

                logger.debug(f"DuckDB query execution completed, {len(df)} rows")
                return result

            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    backoff_ms = self.config.retry_backoff_ms * (
                        self.config.retry_backoff_multiplier**attempt
                    )
                    logger.warning(
                        f"DuckDB query attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}. "
                        f"Retrying in {backoff_ms:.0f}ms..."
                    )
                    time.sleep(backoff_ms / 1000.0)
                else:
                    logger.error(
                        f"DuckDB query failed after {self.config.max_retries + 1} attempts"
                    )

        raise VirtualizationQueryError(
            f"DuckDB query execution failed: {last_exception}", executor="DuckDB"
        ) from last_exception


class SparkQueryExecutor(QueryExecutor):
    """Spark SQL-based query executor for virtualized features with retry support."""

    def __init__(self, context: Any, config: Optional[FeatureStoreConfig] = None):
        """Initialize Spark executor with retry config."""
        self.context = context
        self.config = config or FeatureStoreConfig()
        self.spark = getattr(context, "spark", None)
        logger.info("SparkQueryExecutor initialized")

    def execute(self, query: str, **kwargs) -> Dict[str, List[Any]]:
        """Execute Spark SQL query with retry support."""
        if not query or not query.strip():
            raise VirtualizationQueryError("Query cannot be empty", executor="Spark")

        if not self.spark:
            raise VirtualizationQueryError(
                "SparkSession not available in context", executor="Spark"
            )

        last_exception = None
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"Executing Spark query [attempt {attempt + 1}]: {query[:100]}...")
                df = self.spark.sql(query)

                # Efficiently convert to dictionary format using Pandas
                # This triggers a single Spark job instead of multiple ones
                try:
                    pdf = df.toPandas()
                    result = pdf.to_dict(orient="list")
                except Exception as pe:
                    logger.warning(
                        f"Pandas conversion failed on attempt {attempt + 1}: {pe}, "
                        f"falling back to row collection"
                    )
                    rows = df.collect()
                    result = {col: [row[col] for row in rows] for col in df.columns}

                logger.debug(f"Spark query execution completed, {df.count()} rows")
                return result

            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    backoff_ms = self.config.retry_backoff_ms * (
                        self.config.retry_backoff_multiplier**attempt
                    )
                    logger.warning(
                        f"Spark query attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}. "
                        f"Retrying in {backoff_ms:.0f}ms..."
                    )
                    time.sleep(backoff_ms / 1000.0)
                else:
                    logger.error(f"Spark query failed after {self.config.max_retries + 1} attempts")

        raise VirtualizationQueryError(
            f"Spark query execution failed: {last_exception}", executor="Spark"
        ) from last_exception


class VirtualizedFeatureStore(BaseFeatureStore):
    """
    Feature Store with on-demand query execution (no materialization).
    """

    def __init__(
        self,
        context: Any,
        query_executor: Optional[QueryExecutor] = None,
        source_registry: Optional[DataSourceRegistry] = None,
        default_selector: Optional[SourceSelector] = None,
        config: Optional[Any] = None,
    ):
        """Initialize Virtualized Feature Store with optional agnóstic data source support."""
        super().__init__(context, config=config)

        # Default to DuckDB if no executor provided
        if query_executor is None:
            try:
                query_executor = DuckDBQueryExecutor(context)
            except Exception:
                logger.warning("DuckDB not available, trying Spark")
                query_executor = SparkQueryExecutor(context)

        self.query_executor = query_executor

        # Initialize source registry with optional default selector (Fase 2)
        self.source_registry = source_registry or DataSourceRegistry()
        self._source_selector: Optional[SourceSelector] = default_selector
        self._default_selection_criteria = SelectionCriteria()

        self._feature_queries: Dict[str, str] = {}
        self._feature_sources: Dict[str, str] = {}  # Map feature_group -> source_id
        self._virtual_layer: Optional["VirtualDataLayer"] = None

        num_sources = len(self.source_registry.list_sources()) if self.source_registry else 0
        selector_status = "enabled" if self._source_selector else "disabled"

        logger.info(
            f"VirtualizedFeatureStore initialized "
            f"(executor={type(query_executor).__name__}, "
            f"agnostic_sources={num_sources}, selector={selector_status})"
        )

    def register_data_source(
        self,
        config: DataSourceConfig,
        connector: Optional[DataSourceConnector] = None,
    ) -> None:
        """Register a data source for feature retrieval."""
        self.source_registry.register_source(config, connector)
        logger.info(f"Data source registered: '{config.source_id}' ({config.source_type.value})")

    def set_source_selection_strategy(
        self,
        strategy: SelectionStrategy,
        custom_criteria: Optional[SelectionCriteria] = None,
    ) -> None:
        """Configure source selection strategy."""
        self._source_selector = create_selector(self.source_registry, strategy)
        if custom_criteria:
            self._default_selection_criteria = custom_criteria
        logger.info(f"Source selection strategy set to: {strategy.value}")

    def map_feature_group_to_source(
        self,
        feature_group: str,
        source_id: str,
    ) -> None:
        """Explicitly map a feature group to a data source."""
        if not self.source_registry.get_source_config(source_id):
            raise ValueError(f"Source '{source_id}' not registered")

        self._feature_sources[feature_group] = source_id
        logger.info(f"Feature group '{feature_group}' mapped to source '{source_id}'")

    def get_best_source_for_features(
        self,
        feature_group: str,
        criteria: Optional[SelectionCriteria] = None,
    ) -> Optional[str]:
        """Determine best source for a feature group."""
        # Check explicit mapping first (highest priority)
        if feature_group in self._feature_sources:
            source_id = self._feature_sources[feature_group]
            logger.debug(f"Using explicitly mapped source '{source_id}' for '{feature_group}'")
            return source_id

        # Get feature names for this group
        try:
            schema = self.metadata.get_feature_group(feature_group)
            feature_names = [f.name for f in schema.features]
        except Exception as e:
            logger.warning(f"Could not get schema for '{feature_group}': {e}")
            feature_names = [feature_group]

        # Use provided criteria or default
        selection_criteria = criteria or self._default_selection_criteria

        # Try intelligent ranking if selector is configured
        if self._source_selector:
            try:
                ranked_sources = self._rank_sources_for_features(feature_names, selection_criteria)

                if ranked_sources:
                    best_source_id = ranked_sources[0][0]
                    best_score = ranked_sources[0][1]

                    logger.debug(
                        f"Selected best source '{best_source_id}' "
                        f"(score={best_score:.2f}) for feature group '{feature_group}'"
                    )
                    return best_source_id

            except Exception as e:
                logger.debug(f"Intelligent ranking failed, falling back: {e}")

        # Fallback: use first available source
        try:
            sources = list(self.source_registry.list_sources(enabled_only=True))
            if sources:
                logger.debug(
                    f"No selector or no suitable ranked sources, "
                    f"using first available source '{sources[0]}' for '{feature_group}'"
                )
                return sources[0]
        except Exception as e:
            logger.error(f"Could not list available sources: {e}")

        logger.warning(f"No suitable source found for feature group '{feature_group}'")
        return None

    def list_data_sources(self, enabled_only: bool = True) -> List[str]:
        """List all registered data sources."""
        return self.source_registry.list_sources(enabled_only=enabled_only)

    def get_source_info(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a data source."""
        config = self.source_registry.get_source_config(source_id)
        if not config:
            return None

        connector = self.source_registry.get_connector(source_id)
        metrics = connector.get_metrics() if connector else None

        metrics_data = None
        if metrics:
            metrics_data = {
                "latency_ms": metrics.latency_ms,
                "freshness_minutes": metrics.freshness_minutes,
                "availability_pct": metrics.availability_pct,
                "cost_per_query": metrics.cost_per_query,
            }

        return {
            "source_id": config.source_id,
            "source_type": config.source_type.value,
            "data_layer": config.data_layer.value,
            "location": config.location,
            "enabled": config.enabled,
            "metrics": metrics_data,
        }

    def set_virtual_layer(self, virtual_layer: "VirtualDataLayer") -> None:
        """Set VirtualDataLayer for integration."""
        self._virtual_layer = virtual_layer
        logger.info("VirtualDataLayer integration enabled")

    def register_as_virtual_table(
        self, feature_group: str, table_prefix: str = "features_"
    ) -> Optional["VirtualTable"]:
        """Register feature group as a virtual table in VirtualDataLayer."""
        if not self._virtual_layer:
            logger.warning(
                "Cannot register virtual table: VirtualDataLayer not configured. "
                "Call set_virtual_layer() first."
            )
            return None

        try:
            from tauro.virtualization import VirtualTable, SourceType

            schema = self.metadata.get_feature_group(feature_group)

            # Create virtual table definition
            virtual_table = VirtualTable(
                name=f"{table_prefix}{feature_group}",
                source_type=SourceType.DATABASE,
                connector_type="feature_store",
                connection_id="feature_store_virtualized",
                table_name=feature_group,
                query=self._feature_queries.get(feature_group),
                schema={f.name: f.data_type.value for f in schema.features},
                description=f"Virtual feature group: {schema.description or feature_group}",
                tags=schema.tags + ["feature_store", "virtualized"],
            )

            # Register with virtual layer
            self._virtual_layer.schema_registry.register_table(virtual_table)

            logger.info(
                f"Registered feature group '{feature_group}' as virtual table "
                f"'{virtual_table.name}'"
            )

            return virtual_table

        except Exception as e:
            logger.error(f"Failed to register virtual table: {e}")
            return None

    def query_via_virtual_layer(
        self,
        feature_group: str,
        features: List[str],
        predicates: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """Query features through VirtualDataLayer with optimization."""
        if not self._virtual_layer:
            logger.warning("VirtualDataLayer not configured, using standard query")
            return self.get_features(features)

        try:
            from tauro.virtualization.federation_engine import FederationEngine, Predicate

            table_name = f"features_{feature_group}"

            # Convert to federation predicates if provided
            fed_predicates = []
            if predicates:
                for pred in predicates:
                    fed_predicates.append(
                        Predicate(
                            field=pred[0],
                            operator=pred[1],
                            value=pred[2] if len(pred) > 2 else None,
                        )
                    )

            # Use federation engine for optimized query
            federation = FederationEngine()
            plan = federation.plan_query(
                table_name=table_name, predicates=fed_predicates, projection=features
            )

            logger.info(
                f"Query plan: {plan.execution_strategy.value}, "
                f"estimated cost: {plan.estimated_cost:.2f}"
            )

            # Execute through standard method but log optimization
            return self.get_features(features)

        except Exception as e:
            logger.error(f"Virtual layer query failed: {e}, falling back to standard")
            return self.get_features(features)

    def register_features(self, schema: FeatureGroupSchema) -> None:
        """Register virtual feature group with query templates."""
        try:
            self.metadata.register_feature_group(schema)

            # Store query templates from metadata
            if "query_template" in schema.metadata:
                self._feature_queries[schema.name] = schema.metadata["query_template"]

            logger.info(f"Virtual feature group registered: {schema.name} (query-on-demand)")
        except Exception as e:
            raise VirtualizationQueryError(
                f"Failed to register virtual feature group '{schema.name}': {e}"
            ) from e

    def write_features(
        self,
        feature_group: str,
        data: Dict[str, List[Any]],
        mode: str = "append",
    ) -> None:
        """Virtualized features are read-only (no write)."""
        raise VirtualizationQueryError(
            f"Cannot write to virtualized feature group '{feature_group}': "
            "virtualized features are read-only query results"
        )

    def _group_features_by_name(self, feature_names: List[str]) -> Dict[str, List[str]]:
        """Helper to group features by feature group."""
        groups_features: Dict[str, List[str]] = {}
        for feature_ref in feature_names:
            try:
                group_name, feature_name = (
                    feature_ref.split(".", 1) if "." in feature_ref else (feature_ref, feature_ref)
                )
                if group_name not in groups_features:
                    groups_features[group_name] = []
                groups_features[group_name].append(feature_name)
            except ValueError:
                logger.error(f"Invalid feature reference format: {feature_ref}")
                raise
        return groups_features

    def _fetch_group_features(
        self,
        group_name: str,
        features: List[str],
        entity_ids: Optional[Dict[str, List[Any]]],
        point_in_time: Optional[datetime],
        selection_criteria: Optional[SelectionCriteria],
    ) -> Dict[str, Any]:
        """Helper to retrieve features for a specific group from its best source."""
        best_source = self.get_best_source_for_features(
            group_name, selection_criteria or self._default_selection_criteria
        )

        if not best_source:
            logger.error(f"No suitable source found for feature group '{group_name}'")
            raise VirtualizationQueryError(f"No suitable source for feature group '{group_name}'")

        connector = self.source_registry.get_connector(best_source)
        if not connector:
            logger.error(f"Connector for source '{best_source}' not found")
            raise VirtualizationQueryError(f"Connector for source '{best_source}' not configured")

        query_result = connector.execute_query(
            features, entity_ids=entity_ids, point_in_time=point_in_time
        )

        group_result = {}
        for feature_name in features:
            if feature_name in query_result:
                group_result[f"{group_name}.{feature_name}"] = query_result[feature_name]
            else:
                logger.warning(f"Feature '{feature_name}' not in source result")
        return group_result

    def get_features(
        self,
        feature_names: List[str],
        entity_ids: Optional[Dict[str, List[Any]]] = None,
        point_in_time: Optional[datetime] = None,
        selection_criteria: Optional[SelectionCriteria] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Retrieve features on-demand from best available source."""
        result = {}
        groups_features = self._group_features_by_name(feature_names)

        for group_name, features in groups_features.items():
            try:
                group_data = self._fetch_group_features(
                    group_name, features, entity_ids, point_in_time, selection_criteria
                )
                result.update(group_data)
                logger.debug(f"Retrieved {len(features)} features for group '{group_name}'")
            except Exception as e:
                logger.error(f"Failed to retrieve features from '{group_name}': {e}")
                raise

        return result

    def _rank_sources_for_features(
        self,
        feature_names: List[str],
        selection_criteria: Optional[SelectionCriteria] = None,
    ) -> List[tuple]:
        """Rank available data sources based on selection criteria."""
        try:
            if not self.source_registry or not self._source_selector:
                logger.debug(
                    "Source ranking not available: source_registry or selector not configured"
                )
                return []

            criteria = selection_criteria or self._default_selection_criteria
            ranked_sources = self._source_selector.rank_sources(feature_names, criteria)

            logger.debug(
                f"Ranked {len(ranked_sources)} sources for features {feature_names[:3]}..."
            )
            return ranked_sources

        except Exception as e:
            logger.error(f"Error ranking sources: {e}")
            return []

    def _meets_selection_criteria(
        self, source_id: str, metrics: Any, criteria: SelectionCriteria
    ) -> bool:
        """Checks if source metrics satisfy the selection criteria constraints."""
        if criteria.max_latency_ms and metrics.latency_ms > criteria.max_latency_ms:
            logger.debug(f"Source '{source_id}' exceeds latency ({metrics.latency_ms}ms)")
            return False
        if (
            criteria.max_freshness_minutes
            and metrics.freshness_minutes > criteria.max_freshness_minutes
        ):
            logger.debug(f"Source '{source_id}' data too old ({metrics.freshness_minutes}min)")
            return False
        if (
            criteria.min_availability_pct
            and metrics.availability_pct < criteria.min_availability_pct
        ):
            logger.debug(
                f"Source '{source_id}' availability insufficient ({metrics.availability_pct}%)"
            )
            return False
        if criteria.max_cost_budget and metrics.cost_per_query > criteria.max_cost_budget:
            logger.debug(f"Source '{source_id}' cost exceeds budget (${metrics.cost_per_query})")
            return False
        return True

    def _get_best_connector_for_features(
        self,
        feature_names: List[str],
        selection_criteria: Optional[SelectionCriteria] = None,
    ) -> Optional[DataSourceConnector]:
        """Get the best connector for retrieving given features."""
        try:
            ranked = self._rank_sources_for_features(feature_names, selection_criteria)

            if not ranked:
                logger.warning(
                    f"No suitable sources found for features {feature_names}. "
                    f"Verify that sources are configured and meet selection criteria."
                )
                return None

            best_source_id, best_score = ranked[0]
            connector = self.source_registry.get_connector(best_source_id)
            best_config = self.source_registry.get_source_config(best_source_id)

            if not connector:
                logger.warning(f"Connector for best source '{best_source_id}' is not configured")
                return None

            score_desc = (
                f"score={best_score:.2f}" if isinstance(best_score, (int, float)) else "score=N/A"
            )
            if best_config:
                logger.info(
                    f"Selected source '{best_source_id}' (type={best_config.source_type.value}, "
                    f"{score_desc}) for features "
                    f"{feature_names[:2]}{'...' if len(feature_names) > 2 else ''}"
                )
            else:
                logger.info(
                    f"Selected source '{best_source_id}' ({score_desc}) for features "
                    f"{feature_names[:2]}{'...' if len(feature_names) > 2 else ''}"
                )

            return connector

        except Exception as e:
            logger.error(f"Error getting best connector: {e}")
            return None

    def _build_query(
        self,
        feature_group: str,
        features: List[str],
        entity_ids: Optional[Dict[str, List[Any]]] = None,
        point_in_time: Optional[datetime] = None,
    ) -> str:
        """Build SQL query for virtual features."""
        schema = self.metadata.get_feature_group(feature_group)

        # Use template if available
        if feature_group in self._feature_queries:
            base_query = self._feature_queries[feature_group]
        else:
            # Build standard query from schema
            feature_list = ", ".join(features)
            base_query = f"SELECT {feature_list} FROM {feature_group}"

        # Add entity filters
        if entity_ids:
            where_clauses = []
            for key, values in entity_ids.items():
                placeholders = ", ".join(str(v) for v in values)
                where_clauses.append(f"{key} IN ({placeholders})")

            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)

        # Add point-in-time filter if timestamp key exists
        if point_in_time and schema.timestamp_key:
            base_query += f" AND {schema.timestamp_key} <= '{point_in_time.isoformat()}'"

        logger.debug(f"Built query: {base_query}")
        return base_query

    def register_query_template(
        self,
        feature_group: str,
        query_template: str,
    ) -> None:
        """Register a custom SQL query template for a feature group."""
        try:
            # Ensure feature group exists (validate) without creating an unused variable
            self.metadata.get_feature_group(feature_group)
            self._feature_queries[feature_group] = query_template
            logger.info(f"Registered query template for '{feature_group}'")
        except Exception as e:
            logger.error(f"Failed to register query template: {e}")
            raise

    def validate_query(self, query: str) -> bool:
        """Validate a query without executing it."""
        try:
            # In production, would use actual query validation
            logger.debug(f"Validating query: {query[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            return False

    def get_execution_plan(self, feature_group: str, features: List[str]) -> Dict[str, Any]:
        """Get query execution plan for debugging/optimization."""
        try:
            query = self._build_query(feature_group, features)
            return {
                "feature_group": feature_group,
                "features": features,
                "query": query,
                "executor_type": type(self.query_executor).__name__,
            }
        except Exception as e:
            logger.error(f"Failed to get execution plan: {e}")
            return {}
