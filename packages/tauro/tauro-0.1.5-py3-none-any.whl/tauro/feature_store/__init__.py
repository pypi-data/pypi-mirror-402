from tauro.feature_store.base import (
    BaseFeatureStore,
    FeatureStoreMetadata,
    FeatureStoreMode,
    FeatureStoreConfig,
)
from tauro.feature_store.materialized import MaterializedFeatureStore
from tauro.feature_store.virtualized import (
    VirtualizedFeatureStore,
    QueryExecutor,
    DuckDBQueryExecutor,
    SparkQueryExecutor,
)
from tauro.feature_store.hybrid import HybridFeatureStore
from tauro.feature_store.schema import (
    DataType,
    FeatureType,
    FeatureSchema,
    FeatureGroupSchema,
)
from tauro.feature_store.exceptions import (
    FeatureStoreException,
    FeatureNotFoundError,
    FeatureGroupNotFoundError,
    SchemaValidationError,
    FeatureMaterializationError,
    VirtualizationQueryError,
    MetadataError,
    FeatureRegistryError,
    DataSourceError,
    LockAcquisitionError,
)

# Data source abstraction (NEW)
from tauro.feature_store.data_source import (
    DataSourceRegistry,
    DataSourceConfig,
    DataSourceConnector,
    SourceType,
    DataLayer,
    SourceMetrics,
    SparkTableConnector,
    DuckDBTableConnector,
    CustomCallableConnector,
)

# Source selection policies (NEW)
from tauro.feature_store.source_selection_policy import (
    SourceSelector,
    SelectionStrategy,
    SelectionCriteria,
    CostOptimizedSelector,
    LatencyOptimizedSelector,
    FreshnessOptimizedSelector,
    ReliabilityOptimizedSelector,
    BalancedSelector,
    CacheFirstSelector,
    CustomSelector,
    create_selector,
)

# Connection pooling and resilience utilities
from tauro.feature_store.connection_pool import (
    ConnectionPool,
    PooledConnection,
)

# Validation utilities
from tauro.feature_store.validators import (
    FeatureNameValidator,
    DataFrameValidator,
    QueryValidator,
    EntityKeysValidator,
)

# Pipeline integration is now in tauro.exec module for better context handling
# Import here for backward compatibility
try:
    from tauro.exec.feature_store_executor import (
        FeatureStoreExecutorAdapter,
        write_features_node,
        read_features_node,
        create_feature_store_for_pipeline,
    )

    _EXEC_INTEGRATION_AVAILABLE = True
except ImportError:
    _EXEC_INTEGRATION_AVAILABLE = False
    FeatureStoreExecutorAdapter = None
    write_features_node = None
    read_features_node = None
    create_feature_store_for_pipeline = None

__all__ = [
    # Base classes
    "BaseFeatureStore",
    "FeatureStoreMetadata",
    "FeatureStoreMode",
    "FeatureStoreConfig",
    # Store implementations
    "MaterializedFeatureStore",
    "VirtualizedFeatureStore",
    "HybridFeatureStore",
    # Query executors
    "QueryExecutor",
    "DuckDBQueryExecutor",
    "SparkQueryExecutor",
    # Schema types
    "DataType",
    "FeatureType",
    "FeatureSchema",
    "FeatureGroupSchema",
    # Exceptions
    "FeatureStoreException",
    "FeatureNotFoundError",
    "FeatureGroupNotFoundError",
    "SchemaValidationError",
    "FeatureMaterializationError",
    "VirtualizationQueryError",
    "MetadataError",
    "FeatureRegistryError",
    "DataSourceError",
    "LockAcquisitionError",
    # Data source abstraction
    "DataSourceRegistry",
    "DataSourceConfig",
    "DataSourceConnector",
    "SourceType",
    "DataLayer",
    "SourceMetrics",
    "SparkTableConnector",
    "DuckDBTableConnector",
    "CustomCallableConnector",
    # Source selection
    "SourceSelector",
    "SelectionStrategy",
    "SelectionCriteria",
    "CostOptimizedSelector",
    "LatencyOptimizedSelector",
    "FreshnessOptimizedSelector",
    "ReliabilityOptimizedSelector",
    "BalancedSelector",
    "CacheFirstSelector",
    "CustomSelector",
    "create_selector",
    # Connection pooling & resilience
    "ConnectionPool",
    "PooledConnection",
    # Validation utilities
    "FeatureNameValidator",
    "DataFrameValidator",
    "QueryValidator",
    "EntityKeysValidator",
    # Pipeline integration (from tauro.exec)
    "FeatureStoreExecutorAdapter",
    "write_features_node",
    "read_features_node",
    "create_feature_store_for_pipeline",
]
