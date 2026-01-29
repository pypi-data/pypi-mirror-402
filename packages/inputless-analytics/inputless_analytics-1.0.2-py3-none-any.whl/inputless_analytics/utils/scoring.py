"""
Scoring utilities for insights and recommendations.
"""

from typing import Literal

from ..models.insight import Insight
from ..models.recommendation import Recommendation


def calculate_priority_score(
    item: Insight | Recommendation,
) -> float:
    """
    Calculate priority score for sorting insights/recommendations.

    Args:
        item: Insight or Recommendation object

    Returns:
        Priority score (higher = more important)
    """
    priority_weights = {
        "critical": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0,
    }
    weight = priority_weights.get(item.priority, 2.0)
    return weight * item.confidence


def normalize_confidence(confidence: float) -> float:
    """
    Normalize confidence score to 0.0-1.0 range.

    Args:
        confidence: Raw confidence score

    Returns:
        Normalized confidence (0.0-1.0)
    """
    return max(0.0, min(1.0, confidence))


def calculate_impact_score(
    confidence: float,
    priority: Literal["low", "medium", "high", "critical"],
    base_impact: float = 0.5,
) -> float:
    """
    Calculate estimated impact score based on confidence and priority.

    Args:
        confidence: Confidence score (0.0-1.0)
        priority: Priority level
        base_impact: Base impact score (default: 0.5)

    Returns:
        Impact score (0.0-1.0)
    """
    priority_multipliers = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.6,
        "low": 0.4,
    }
    multiplier = priority_multipliers.get(priority, 0.6)
    return normalize_confidence(base_impact * multiplier * confidence)

