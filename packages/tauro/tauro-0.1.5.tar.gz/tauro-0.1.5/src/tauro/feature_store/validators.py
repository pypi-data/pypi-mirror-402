"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Any, List, Dict, Optional
from datetime import datetime
import re

from loguru import logger  # type: ignore

from tauro.feature_store.exceptions import SchemaValidationError


class FeatureNameValidator:
    """Validates feature and feature group names."""

    # Pattern for valid identifiers: alphanumeric, underscore, dot (for namespacing)
    VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\.]*$")
    MAX_NAME_LENGTH = 255

    @classmethod
    def validate_feature_name(cls, name: str) -> None:
        """Validate a feature name."""
        if not name or not isinstance(name, str):
            raise SchemaValidationError("Feature name must be a non-empty string")

        if len(name) > cls.MAX_NAME_LENGTH:
            raise SchemaValidationError(
                f"Feature name exceeds max length ({cls.MAX_NAME_LENGTH}): {name}"
            )

        if not cls.VALID_NAME_PATTERN.match(name):
            raise SchemaValidationError(
                f"Invalid feature name '{name}'. Must start with letter/underscore and contain only alphanumeric/underscores/dots."
            )

    @classmethod
    def validate_group_name(cls, name: str) -> None:
        """Validate a feature group name."""
        cls.validate_feature_name(name)


class DataFrameValidator:
    """Validates DataFrames for feature consistency."""

    @staticmethod
    def validate_required_columns(
        df: Any, required_columns: List[str], nullable_ok: bool = False
    ) -> None:
        """
        Validate that DataFrame has required columns.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            nullable_ok: Whether to allow null values

        Raises:
            SchemaValidationError if validation fails
        """
        if not hasattr(df, "columns"):
            raise SchemaValidationError(f"Object does not have columns attribute: {type(df)}")

        df_columns = set(df.columns)

        # Check required columns exist
        missing = set(required_columns) - df_columns
        if missing:
            raise SchemaValidationError(
                f"Missing required columns: {missing}. Available: {df_columns}"
            )

        # Check for nulls if not allowed
        if not nullable_ok:
            null_counts = {}
            try:
                if hasattr(df, "toPandas"):  # Spark DataFrame
                    pdf = df.toPandas()
                    null_counts = pdf[required_columns].isnull().sum().to_dict()
                elif hasattr(df, "isnull"):  # Pandas DataFrame
                    null_counts = df[required_columns].isnull().sum().to_dict()

                columns_with_nulls = {k: v for k, v in null_counts.items() if v > 0}
                if columns_with_nulls:
                    raise SchemaValidationError(
                        f"Columns contain null values (not allowed): {columns_with_nulls}"
                    )
            except SchemaValidationError:
                raise
            except Exception as e:
                logger.warning(f"Could not check null values: {e}")

    @staticmethod
    def validate_row_count(
        df: Any,
        min_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
    ) -> None:
        """Validate DataFrame row count."""
        try:
            if hasattr(df, "count"):
                row_count = df.count()
            elif hasattr(df, "__len__"):
                row_count = len(df)
            else:
                logger.warning("Could not determine row count")
                return

            if min_rows is not None and row_count < min_rows:
                raise SchemaValidationError(f"Row count {row_count} is below minimum {min_rows}")

            if max_rows is not None and row_count > max_rows:
                raise SchemaValidationError(f"Row count {row_count} exceeds maximum {max_rows}")

        except SchemaValidationError:
            raise
        except Exception as e:
            logger.warning(f"Error validating row count: {e}")


class QueryValidator:
    """Validates SQL queries for safety and correctness."""

    # Dangerous SQL keywords to detect
    DANGEROUS_KEYWORDS = {"DROP", "DELETE", "TRUNCATE", "GRANT", "REVOKE", "ALTER"}

    @staticmethod
    def is_select_query(query: str) -> bool:
        """Check if query is a SELECT statement."""
        if not query or not isinstance(query, str):
            return False
        normalized = query.strip().upper()
        return normalized.startswith("SELECT")

    @staticmethod
    def validate_read_only_query(query: str) -> None:
        """
        Validate that query is read-only (no modifications).

        Args:
            query: SQL query to validate

        Raises:
            ValueError if query contains dangerous operations
        """
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        normalized = query.upper()

        # Check for dangerous keywords
        for keyword in QueryValidator.DANGEROUS_KEYWORDS:
            if keyword in normalized:
                raise ValueError(f"Query contains dangerous keyword: {keyword}")

        # Must be a SELECT
        if not QueryValidator.is_select_query(query):
            raise ValueError("Only SELECT queries are allowed")

    @staticmethod
    def validate_query_length(query: str, max_length: int = 100000) -> None:
        """Validate query length to prevent DoS."""
        if not query:
            raise ValueError("Query cannot be empty")

        if len(query) > max_length:
            raise ValueError(
                f"Query exceeds maximum length ({max_length}): {len(query)} characters"
            )

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Basic query sanitization (remove extra whitespace, comments)."""
        if not query:
            return ""

        # Remove SQL comments
        lines = []
        for line in query.split("\n"):
            # Remove inline comments
            if "--" in line:
                line = line[: line.index("--")]
            lines.append(line.strip())

        # Join and clean up
        query = " ".join(line for line in lines if line)
        return query


class EntityKeysValidator:
    """Validates entity keys for feature retrieval."""

    @staticmethod
    def validate_entity_keys(entity_ids: Dict[str, List[Any]], required_keys: List[str]) -> None:
        """
        Validate entity keys dictionary."""
        if not entity_ids:
            if required_keys:
                raise ValueError(f"Required entity keys missing: {required_keys}")
            return

        if not isinstance(entity_ids, dict):
            raise ValueError(f"entity_ids must be a dictionary: {type(entity_ids)}")

        # Check required keys
        provided_keys = set(entity_ids.keys())
        required_set = set(required_keys)
        missing = required_set - provided_keys

        if missing:
            raise ValueError(f"Missing required entity keys: {missing}")

        # Validate values
        for key_name, values in entity_ids.items():
            if not isinstance(values, (list, tuple)):
                raise ValueError(
                    f"Entity key '{key_name}' values must be a list/tuple, got {type(values)}"
                )

            if len(values) == 0:
                raise ValueError(f"Entity key '{key_name}' cannot have empty values")

    @staticmethod
    def validate_point_in_time(point_in_time: datetime) -> None:
        """Validate point-in-time datetime."""
        if not isinstance(point_in_time, datetime):
            raise ValueError(f"point_in_time must be a datetime, got {type(point_in_time)}")

        if point_in_time > datetime.now():
            raise ValueError(f"point_in_time cannot be in the future: {point_in_time}")
