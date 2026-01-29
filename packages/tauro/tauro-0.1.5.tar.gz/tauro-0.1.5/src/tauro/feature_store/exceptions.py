"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Optional


class FeatureStoreException(Exception):
    """Base exception for Feature Store operations."""

    def __init__(
        self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None
    ):
        """Initialize exception with optional error code and details."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN"
        self.details = details or {}

    def __str__(self) -> str:
        """Return formatted error message."""
        base_msg = f"[{self.error_code}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base_msg} ({details_str})"
        return base_msg


class FeatureNotFoundError(FeatureStoreException):
    """Raised when a requested feature is not found in the store."""

    def __init__(
        self, message: str, feature_name: Optional[str] = None, group_name: Optional[str] = None
    ):
        details = {}
        if feature_name:
            details["feature"] = feature_name
        if group_name:
            details["group"] = group_name
        super().__init__(message, error_code="FEATURE_NOT_FOUND", details=details)


class FeatureGroupNotFoundError(FeatureStoreException):
    """Raised when a requested feature group is not found."""

    def __init__(self, message: str, group_name: Optional[str] = None):
        details = {"group": group_name} if group_name else {}
        super().__init__(message, error_code="GROUP_NOT_FOUND", details=details)


class SchemaValidationError(FeatureStoreException):
    """Raised when feature schema validation fails."""

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        validation_errors: Optional[list] = None,
    ):
        details = {}
        if schema_name:
            details["schema"] = schema_name
        if validation_errors:
            details["errors_count"] = len(validation_errors)
        super().__init__(message, error_code="SCHEMA_VALIDATION_ERROR", details=details)


class FeatureMaterializationError(FeatureStoreException):
    """Raised when materialization of features fails."""

    def __init__(
        self, message: str, feature_group: Optional[str] = None, attempt: Optional[int] = None
    ):
        details = {}
        if feature_group:
            details["feature_group"] = feature_group
        if attempt:
            details["attempt"] = attempt
        super().__init__(message, error_code="MATERIALIZATION_ERROR", details=details)


class VirtualizationQueryError(FeatureStoreException):
    """Raised when on-demand query execution fails."""

    def __init__(self, message: str, query: Optional[str] = None, executor: Optional[str] = None):
        details = {}
        if executor:
            details["executor"] = executor
        if query:
            details["query_length"] = len(query)
        super().__init__(message, error_code="VIRTUALIZATION_QUERY_ERROR", details=details)


class MetadataError(FeatureStoreException):
    """Raised when metadata operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None):
        details = {"operation": operation} if operation else {}
        super().__init__(message, error_code="METADATA_ERROR", details=details)


class FeatureRegistryError(FeatureStoreException):
    """Raised when feature registry operations fail."""

    def __init__(self, message: str, registry_op: Optional[str] = None):
        details = {"operation": registry_op} if registry_op else {}
        super().__init__(message, error_code="REGISTRY_ERROR", details=details)


class DataSourceError(FeatureStoreException):
    """Raised when data source operations fail."""

    def __init__(
        self, message: str, source_id: Optional[str] = None, retries: Optional[int] = None
    ):
        details = {}
        if source_id:
            details["source_id"] = source_id
        if retries is not None:
            details["retries"] = retries
        super().__init__(message, error_code="DATA_SOURCE_ERROR", details=details)


class LockAcquisitionError(FeatureStoreException):
    """Raised when lock acquisition fails."""

    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        details = {}
        if timeout_seconds:
            details["timeout"] = f"{timeout_seconds}s"
        super().__init__(message, error_code="LOCK_ACQUISITION_ERROR", details=details)
