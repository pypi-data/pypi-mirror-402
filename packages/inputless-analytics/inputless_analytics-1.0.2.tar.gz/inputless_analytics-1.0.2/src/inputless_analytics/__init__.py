"""
inputless-analytics - Main exports.

Analytics engine for generating insights and recommendations.
"""

from .analytics_engine import AnalyticsEngine
from .correlation_finder import CorrelationFinder
from .insights_generator import InsightsGenerator
from .recommendations import RecommendationsEngine
from .trend_analyzer import TrendAnalyzer

# Aggregators
from .aggregators import (
    AnomalyAggregator,
    PatternAggregator,
    TrendAggregator,
)

# Analyzers
from .analyzers import (
    BehaviorAnalyzer,
    ConversionAnalyzer,
    EngagementAnalyzer,
    RetentionAnalyzer,
)

# Predictors
from .predictors import (
    BehaviorPredictor,
    OutcomePredictor,
)

# Models
from .models import (
    AnalyticsResult,
    Insight,
    InsightType,
    Recommendation,
    RecommendationType,
)

__all__ = [
    # Main classes
    "AnalyticsEngine",
    "InsightsGenerator",
    "RecommendationsEngine",
    "TrendAnalyzer",
    "CorrelationFinder",
    # Aggregators
    "PatternAggregator",
    "AnomalyAggregator",
    "TrendAggregator",
    # Analyzers
    "BehaviorAnalyzer",
    "EngagementAnalyzer",
    "ConversionAnalyzer",
    "RetentionAnalyzer",
    # Predictors
    "BehaviorPredictor",
    "OutcomePredictor",
    # Models
    "Insight",
    "InsightType",
    "Recommendation",
    "RecommendationType",
    "AnalyticsResult",
]
