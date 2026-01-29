"""
Trend Analyzer.

Advanced trend analysis for identifying patterns over time.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .aggregators.trend_aggregator import TrendAggregator


class TrendAnalyzer:
    """
    Advanced trend analysis.

    Analyzes trends over time to identify increasing, decreasing,
    or stable patterns in user behavior.

    Example:
        ```python
        analyzer = TrendAnalyzer()
        trends = analyzer.analyze(
            current_data=current_patterns,
            historical_data=historical_patterns,
            time_window=timedelta(days=7),
        )
        ```
    """

    def __init__(self):
        """Initialize trend analyzer."""
        self.aggregator = TrendAggregator()

    def analyze(
        self,
        current_data: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]],
        time_window: Optional[timedelta] = None,
    ) -> Dict[str, Any]:
        """
        Analyze trends over time.

        Args:
            current_data: Current patterns/anomalies (dict format)
            historical_data: Historical data points (dict format)
            time_window: Time window for trend analysis (default: 7 days)

        Returns:
            Trend analysis results
        """
        if time_window is None:
            time_window = timedelta(days=7)

        # Use trend aggregator
        trends = self.aggregator.analyze_trends(
            current_data=current_data,
            historical_data=historical_data,
            time_window=time_window,
        )

        # Add additional trend insights
        trends["insights"] = self._generate_trend_insights(trends)
        trends["recommendations"] = self._generate_trend_recommendations(trends)

        return trends

    def _generate_trend_insights(self, trends: Dict[str, Any]) -> List[str]:
        """
        Generate insights from trend analysis.

        Args:
            trends: Trend analysis results

        Returns:
            List of trend insights
        """
        insights: List[str] = []

        trend_direction = trends.get("trend_direction", "stable")
        trend_strength = trends.get("trend_strength", 0.0)

        if trend_direction == "increasing" and trend_strength > 0.5:
            insights.append(
                f"Strong increasing trend detected (strength: {trend_strength:.2f})"
            )
        elif trend_direction == "decreasing" and trend_strength > 0.5:
            insights.append(
                f"Strong decreasing trend detected (strength: {trend_strength:.2f})"
            )

        # Analyze by type
        by_type = trends.get("by_type", {})
        for pattern_type, type_data in by_type.items():
            direction = type_data.get("direction", "stable")
            change_percent = type_data.get("change_percent", 0.0)

            if abs(change_percent) > 20:
                insights.append(
                    f"{pattern_type}: {direction} trend ({change_percent:.1f}% change)"
                )

        return insights

    def _generate_trend_recommendations(
        self, trends: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations from trend analysis.

        Args:
            trends: Trend analysis results

        Returns:
            List of trend recommendations
        """
        recommendations: List[str] = []

        trend_direction = trends.get("trend_direction", "stable")

        if trend_direction == "decreasing":
            recommendations.append("Investigate causes of declining trends")
            recommendations.append("Consider intervention strategies")

        if trend_direction == "increasing":
            recommendations.append("Leverage positive trends for optimization")
            recommendations.append("Scale successful patterns")

        return recommendations

