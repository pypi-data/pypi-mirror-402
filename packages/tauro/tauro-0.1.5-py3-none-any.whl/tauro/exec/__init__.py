"""Tauro Execution Engine public API.
This module re-exports the most commonly used execution components for convenience.
"""

# Commands
from tauro.exec.commands import (
    Command,
    NodeCommand,
    MLNodeCommand,
    ExperimentCommand,
    NodeFunction,
)

# Dependency Resolution
from tauro.exec.dependency_resolver import DependencyResolver

# Executors
from tauro.exec.executor import (
    BaseExecutor,
    BatchExecutor,
    StreamingExecutor,
    HybridExecutor,
    PipelineExecutor,
)

# Node Execution
from tauro.exec.node_executor import (
    NodeExecutor,
    ThreadSafeExecutionState,
)

# MLflow Integration (if available)
try:
    from tauro.exec.mlflow_node_executor import (
        MLflowNodeExecutor,
        create_mlflow_executor,
    )

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    MLflowNodeExecutor = None
    create_mlflow_executor = None

# ML Validation
from tauro.exec.ml_node_validator import MLNodeValidator

# MLOps Integration
from tauro.exec.mlops_auto_config import MLOpsAutoConfigurator
from tauro.exec.mlops_executor_mixin import MLOpsExecutorMixin
from tauro.exec.mlops_integration import (
    MLOpsExecutorIntegration,
    MLInfoConfigLoader,
)

# Pipeline State Management
from tauro.exec.pipeline_state import (
    NodeStatus,
    NodeType,
    NodeExecutionInfo,
    CircuitBreakerState,
    CircuitBreaker,
    UnifiedPipelineState,
)

# Pipeline Validation
from tauro.exec.pipeline_validator import PipelineValidator

# Resilience
from tauro.exec.resilience import RetryPolicy

# Resource Management
from tauro.exec.resource_pool import (
    ResourceHandle,
    ResourcePool,
    get_default_resource_pool,
    reset_default_resource_pool,
)

# Utilities
from tauro.exec.utils import (
    normalize_dependencies,
    extract_dependency_name,
    extract_pipeline_nodes,
    get_node_dependencies,
)

# Feature Store Integration
from tauro.exec.feature_store_executor import (
    FeatureStoreExecutorAdapter,
    write_features_node,
    read_features_node,
    create_feature_store_for_pipeline,
)

# Native Feature Store Integration (no external service)
from tauro.exec.feature_store_integration import (
    FeatureStoreNodeHandler,
    FeatureStoreNodeConfig,
    create_feature_store_handler,
)

__all__ = [
    # Commands
    "Command",
    "NodeCommand",
    "MLNodeCommand",
    "ExperimentCommand",
    "NodeFunction",
    # Dependency Resolution
    "DependencyResolver",
    # Executors
    "BaseExecutor",
    "BatchExecutor",
    "StreamingExecutor",
    "HybridExecutor",
    "PipelineExecutor",
    # Node Execution
    "NodeExecutor",
    "ThreadSafeExecutionState",
    # MLflow Integration
    "MLflowNodeExecutor",
    "create_mlflow_executor",
    "MLFLOW_AVAILABLE",
    # ML Validation
    "MLNodeValidator",
    # MLOps Integration
    "MLOpsAutoConfigurator",
    "MLOpsExecutorMixin",
    "MLOpsExecutorIntegration",
    "MLInfoConfigLoader",
    # Pipeline State Management
    "NodeStatus",
    "NodeType",
    "NodeExecutionInfo",
    "CircuitBreakerState",
    "CircuitBreaker",
    "UnifiedPipelineState",
    # Pipeline Validation
    "PipelineValidator",
    # Resilience
    "RetryPolicy",
    # Resource Management
    "ResourceHandle",
    "ResourcePool",
    "get_default_resource_pool",
    "reset_default_resource_pool",
    # Utilities
    "normalize_dependencies",
    "extract_dependency_name",
    "extract_pipeline_nodes",
    "get_node_dependencies",
    # Feature Store Integration
    "FeatureStoreExecutorAdapter",
    "write_features_node",
    "read_features_node",
    "create_feature_store_for_pipeline",
    "FeatureStoreNodeHandler",
    "FeatureStoreNodeConfig",
    "create_feature_store_handler",
]
