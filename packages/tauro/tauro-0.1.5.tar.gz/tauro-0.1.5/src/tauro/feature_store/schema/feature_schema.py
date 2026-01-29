"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import re

from loguru import logger  # type: ignore


class DataType(str, Enum):
    """Supported feature data types."""

    INT = "int"
    BIGINT = "bigint"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    DATE = "date"
    DECIMAL = "decimal"
    ARRAY = "array"
    MAP = "map"
    STRUCT = "struct"


class FeatureType(str, Enum):
    """Types of features in the store."""

    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEXT = "text"
    VECTOR = "vector"
    TIMESERIES = "timeseries"
    COMPLEX = "complex"


@dataclass
class FeatureSchema:
    """Schema definition for a feature."""

    name: str
    """Feature name, must be unique within feature group"""

    data_type: DataType
    """Data type of the feature"""

    feature_type: FeatureType
    """Semantic type of the feature"""

    description: str = ""
    """Human-readable feature description"""

    nullable: bool = True
    """Whether the feature can be null"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata (units, ranges, distributions)"""

    def validate(self) -> bool:
        """Validate feature schema."""
        if not self.name:
            raise ValueError("Feature name cannot be empty")
        if not re.match(r"^[a-zA-Z_]\w*$", self.name):
            raise ValueError(
                f"Invalid feature name '{self.name}'. "
                "Must start with a letter/underscore and contain only alphanumeric/underscores."
            )
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "feature_type": self.feature_type.value,
            "description": self.description,
            "nullable": self.nullable,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureSchema":
        """Create FeatureSchema from dictionary."""
        return cls(
            name=data["name"],
            data_type=DataType(data["data_type"]),
            feature_type=FeatureType(data["feature_type"]),
            description=data.get("description", ""),
            nullable=data.get("nullable", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FeatureGroupSchema:
    """Schema definition for a feature group."""

    name: str
    """Feature group name"""

    version: int = 1
    """Schema version for evolution tracking"""

    entity_keys: List[str] = field(default_factory=list)
    """Primary key columns for the entity"""

    features: List[FeatureSchema] = field(default_factory=list)
    """List of feature schemas in this group"""

    timestamp_key: Optional[str] = None
    """Optional timestamp column for point-in-time queries"""

    description: str = ""
    """Feature group description"""

    tags: Dict[str, str] = field(default_factory=dict)
    """Tags for organization and discovery"""

    owner: str = "unknown"
    """Owner of the feature group"""

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """Creation timestamp"""

    def add_feature(self, feature: FeatureSchema) -> None:
        """Add a feature to the group."""
        if any(f.name == feature.name for f in self.features):
            raise ValueError(f"Feature '{feature.name}' already exists in group '{self.name}'")
        self.features.append(feature)
        logger.debug(f"Added feature '{feature.name}' to group '{self.name}'")

    def get_feature(self, name: str) -> Optional[FeatureSchema]:
        """Retrieve a feature by name."""
        return next((f for f in self.features if f.name == name), None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "entity_keys": self.entity_keys,
            "features": [f.to_dict() for f in self.features],
            "timestamp_key": self.timestamp_key,
            "description": self.description,
            "tags": self.tags,
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureGroupSchema":
        """Create FeatureGroupSchema from dictionary."""
        features = [FeatureSchema.from_dict(f) for f in data.get("features", [])]

        # Handle datetime parsing
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            name=data["name"],
            version=data.get("version", 1),
            entity_keys=data.get("entity_keys", []),
            features=features,
            timestamp_key=data.get("timestamp_key"),
            description=data.get("description", ""),
            tags=data.get("tags", {}),
            owner=data.get("owner", "unknown"),
            created_at=created_at,
        )

    def validate(self) -> bool:
        """Validate schema integrity."""
        if not self.name:
            raise ValueError("Feature group name is required")

        if not re.match(r"^[a-zA-Z_]\w*$", self.name):
            raise ValueError(
                f"Invalid feature group name '{self.name}'. "
                "Must start with a letter/underscore and contain only alphanumeric/underscores."
            )

        if not self.entity_keys:
            logger.warning(f"Feature group '{self.name}' has no entity keys")

        if not self.features:
            raise ValueError(f"Feature group '{self.name}' has no features")

        # Validate each feature and check for duplicates
        seen_features = set()
        for feature in self.features:
            feature.validate()
            if feature.name in seen_features:
                raise ValueError(f"Duplicate feature name '{feature.name}' in group '{self.name}'")
            seen_features.add(feature.name)

        # Ensure entity keys and timestamp keys exist in features or as extra columns
        # (Usually entity keys are part of the features or at least present in the data)

        if self.timestamp_key and self.timestamp_key not in seen_features:
            logger.debug(
                f"Timestamp key '{self.timestamp_key}' is not in feature list (expected in raw data)"
            )

        return True
