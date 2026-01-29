"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import datetime

from loguru import logger  # type: ignore

from tauro.feature_store.data_source import (
    DataSourceConfig,
    SourceMetrics,
    DataSourceRegistry,
)


class SelectionStrategy(str, Enum):
    """Selection strategies for choosing data sources."""

    LOWEST_COST = "lowest_cost"  # Minimize query cost
    LOWEST_LATENCY = "lowest_latency"  # Minimize retrieval time
    FRESHEST_DATA = "freshest_data"  # Most recently updated
    HIGHEST_AVAILABILITY = "highest_availability"  # Most reliable
    BALANCED = "balanced"  # Weighted combination
    CUSTOM = "custom"  # Custom scoring function
    CACHE_FIRST = "cache_first"  # Prefer cached/materialized sources


@dataclass
class SelectionCriteria:
    """Criteria for selecting a data source."""

    strategy: SelectionStrategy = SelectionStrategy.BALANCED
    """Selection strategy to use"""

    max_latency_ms: Optional[float] = None
    """Maximum acceptable latency in milliseconds"""

    max_freshness_minutes: Optional[int] = None
    """Maximum acceptable data age in minutes"""

    min_availability_pct: float = 95.0
    """Minimum acceptable availability percentage"""

    prefer_materialized: bool = False
    """Prefer pre-materialized sources over on-demand"""

    prefer_indexed: bool = False
    """Prefer sources with index support"""

    max_cost_budget: Optional[float] = None
    """Maximum acceptable cost per query"""

    custom_scorer: Optional[Callable[[SourceMetrics], float]] = None
    """Custom scoring function (lower score = better)"""

    weights: Optional[Dict[str, float]] = None
    """Weights for balanced strategy (cost, latency, freshness, availability)"""

    def __post_init__(self):
        """Validate and initialize criteria."""
        if self.weights is None:
            # Default balanced weights
            self.weights = {
                "cost": 0.25,
                "latency": 0.25,
                "freshness": 0.25,
                "reliability": 0.25,
            }


class SourceSelector(ABC):
    """Abstract base class for source selection policies."""

    def __init__(self, registry: DataSourceRegistry):
        """Initialize selector."""
        self.registry = registry
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select best source for given features."""
        pass

    @abstractmethod
    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources by preference."""
        pass

    def _filter_compatible_sources(
        self, feature_names: List[str], criteria: SelectionCriteria
    ) -> Dict[str, DataSourceConfig]:
        """Filter sources that can provide all requested features."""
        compatible = self.registry.get_sources_for_features(feature_names, required_only=True)

        # Apply availability filter
        available = self.registry.get_available_sources()

        filtered = {}
        for source_id, config in compatible.items():
            # Check basic availability
            if source_id not in available:
                logger.debug(f"Source '{source_id}' not available")
                continue

            metrics = available[source_id]

            # Apply constraints
            if criteria.min_availability_pct and not metrics.is_available(
                criteria.min_availability_pct
            ):
                logger.debug(
                    f"Source '{source_id}' availability {metrics.availability_pct}% "
                    f"below threshold {criteria.min_availability_pct}%"
                )
                continue

            if criteria.max_freshness_minutes and not metrics.is_fresh(
                criteria.max_freshness_minutes
            ):
                logger.debug(
                    f"Source '{source_id}' data too stale "
                    f"({metrics.freshness_minutes}min > {criteria.max_freshness_minutes}min)"
                )
                continue

            if criteria.max_latency_ms and metrics.latency_ms > criteria.max_latency_ms:
                logger.debug(
                    f"Source '{source_id}' latency {metrics.latency_ms}ms "
                    f"exceeds {criteria.max_latency_ms}ms"
                )
                continue

            if criteria.max_cost_budget and metrics.cost_score > criteria.max_cost_budget:
                logger.debug(
                    f"Source '{source_id}' cost {metrics.cost_score} "
                    f"exceeds budget {criteria.max_cost_budget}"
                )
                continue

            filtered[source_id] = config

        return filtered


class CostOptimizedSelector(SourceSelector):
    """Selector that prioritizes lowest cost."""

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select source with lowest cost."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources by cost (ascending)."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if metrics:
                scored.append((source_id, metrics.cost_score))

        return sorted(scored, key=lambda x: x[1])


class LatencyOptimizedSelector(SourceSelector):
    """Selector that prioritizes lowest latency."""

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select source with lowest latency."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources by latency (ascending)."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if metrics:
                scored.append((source_id, metrics.latency_ms))

        return sorted(scored, key=lambda x: x[1])


class FreshnessOptimizedSelector(SourceSelector):
    """Selector that prioritizes freshest data."""

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select source with freshest data."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources by freshness (lower age = better)."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if metrics:
                scored.append((source_id, metrics.freshness_score))

        return sorted(scored, key=lambda x: x[1])


class ReliabilityOptimizedSelector(SourceSelector):
    """Selector that prioritizes highest availability."""

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select source with highest availability."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources by reliability (lower score = better)."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if metrics:
                scored.append((source_id, metrics.reliability_score))

        return sorted(scored, key=lambda x: x[1])


class BalancedSelector(SourceSelector):
    """Selector that balances multiple criteria with weights."""

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select source using weighted scoring."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources using weighted criteria."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if not metrics:
                continue

            # Normalize metrics to 0-1 range for scoring
            # (In production, these would be calibrated per deployment)
            normalized_cost = min(metrics.cost_score / 100.0, 1.0)
            normalized_latency = min(metrics.latency_ms / 5000.0, 1.0)  # Assume max 5s
            normalized_freshness = min(metrics.freshness_score / 1440.0, 1.0)  # Assume max 1 day
            normalized_reliability = metrics.reliability_score / 100.0

            # Calculate weighted score
            weights = criteria.weights or {
                "cost": 0.25,
                "latency": 0.25,
                "freshness": 0.25,
                "reliability": 0.25,
            }

            score = (
                normalized_cost * weights.get("cost", 0)
                + normalized_latency * weights.get("latency", 0)
                + normalized_freshness * weights.get("freshness", 0)
                + normalized_reliability * weights.get("reliability", 0)
            )

            scored.append((source_id, score))

        return sorted(scored, key=lambda x: x[1])


class CacheFirstSelector(SourceSelector):
    """Selector that prefers cached/materialized sources."""

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select cached/materialized source if available."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources, preferring materialized ones."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if not metrics:
                continue

            # Prefer materialized sources (score lower)
            if metrics.materialized:
                score = metrics.latency_ms  # Materialized = low latency
            else:
                score = metrics.latency_ms + 10000  # Penalty for non-materialized

            scored.append((source_id, score))

        return sorted(scored, key=lambda x: x[1])


class CustomSelector(SourceSelector):
    """Selector using custom scoring function."""

    def __init__(self, registry: DataSourceRegistry, scorer: Callable[[str, SourceMetrics], float]):
        """Initialize with custom scorer."""
        super().__init__(registry)
        self.scorer = scorer

    def select_source(self, feature_names: List[str], criteria: SelectionCriteria) -> Optional[str]:
        """Select source using custom scorer."""
        ranked = self.rank_sources(feature_names, criteria)
        if ranked:
            return ranked[0][0]
        return None

    def rank_sources(self, feature_names: List[str], criteria: SelectionCriteria) -> List[tuple]:
        """Rank sources using custom scoring function."""
        compatible = self._filter_compatible_sources(feature_names, criteria)
        available = self.registry.get_available_sources()

        scored = []
        for source_id in compatible:
            metrics = available.get(source_id)
            if metrics:
                score = self.scorer(source_id, metrics)
                scored.append((source_id, score))

        return sorted(scored, key=lambda x: x[1])


def create_selector(
    registry: DataSourceRegistry,
    strategy: SelectionStrategy,
    custom_scorer: Optional[Callable[[str, SourceMetrics], float]] = None,
) -> SourceSelector:
    """Factory function to create a selector."""
    if strategy == SelectionStrategy.LOWEST_COST:
        return CostOptimizedSelector(registry)
    elif strategy == SelectionStrategy.LOWEST_LATENCY:
        return LatencyOptimizedSelector(registry)
    elif strategy == SelectionStrategy.FRESHEST_DATA:
        return FreshnessOptimizedSelector(registry)
    elif strategy == SelectionStrategy.HIGHEST_AVAILABILITY:
        return ReliabilityOptimizedSelector(registry)
    elif strategy == SelectionStrategy.BALANCED:
        return BalancedSelector(registry)
    elif strategy == SelectionStrategy.CACHE_FIRST:
        return CacheFirstSelector(registry)
    elif strategy == SelectionStrategy.CUSTOM:
        if not custom_scorer:
            raise ValueError("custom_scorer required for CUSTOM strategy")
        return CustomSelector(registry, custom_scorer)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
