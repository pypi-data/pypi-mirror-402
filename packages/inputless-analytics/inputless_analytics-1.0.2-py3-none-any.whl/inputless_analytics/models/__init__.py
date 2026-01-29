"""
Analytics data models.
"""

from .insight import Insight, InsightType
from .recommendation import Recommendation, RecommendationType
from .analytics_result import AnalyticsResult

__all__ = [
    "Insight",
    "InsightType",
    "Recommendation",
    "RecommendationType",
    "AnalyticsResult",
]

