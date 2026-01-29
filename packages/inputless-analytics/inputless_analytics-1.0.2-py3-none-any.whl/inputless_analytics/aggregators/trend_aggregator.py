"""
Trend Aggregator.

Analyze trends over time by comparing current data with historical data.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List


class TrendAggregator:
    """
    Analyze trends over time.

    Compares current patterns/anomalies with historical data
    to identify increasing, decreasing, or stable trends.

    Example:
        ```python
        aggregator = TrendAggregator()
        trends = aggregator.analyze_trends(
            current_data=current_patterns,
            historical_data=historical_patterns,
            time_window=timedelta(days=7),
        )
        ```
    """

    def analyze_trends(
        self,
        current_data: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]],
        time_window: timedelta = timedelta(days=7),
    ) -> Dict[str, Any]:
        """
        Analyze trends by comparing current data with historical data.

        Args:
            current_data: Current patterns/anomalies (dict format)
            historical_data: Historical data points (dict format)
            time_window: Time window for trend analysis

        Returns:
            Trend analysis results
        """
        trends: Dict[str, Any] = {
            "current_count": len(current_data),
            "historical_count": len(historical_data),
            "trend_direction": "stable",
            "trend_strength": 0.0,
            "by_type": {},
        }

        if not current_data and not historical_data:
            return trends

        # Analyze trends by type
        current_by_type = self._group_by_type(current_data)
        historical_by_type = self._group_by_type(historical_data)

        for pattern_type in set(list(current_by_type.keys()) + list(historical_by_type.keys())):
            current_count = current_by_type.get(pattern_type, 0)
            historical_count = historical_by_type.get(pattern_type, 0)

            trend_direction = self._calculate_trend_direction(
                current_count, historical_count
            )
            trend_strength = self._calculate_trend_strength(
                current_count, historical_count
            )

            trends["by_type"][pattern_type] = {
                "current": current_count,
                "historical": historical_count,
                "direction": trend_direction,
                "strength": trend_strength,
                "change_percent": (
                    ((current_count - historical_count) / historical_count * 100)
                    if historical_count > 0
                    else 0.0
                ),
            }

        # Overall trend
        overall_trend = self._calculate_overall_trend(
            len(current_data), len(historical_data)
        )
        trends["trend_direction"] = overall_trend["direction"]
        trends["trend_strength"] = overall_trend["strength"]

        return trends

    def _group_by_type(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group data by type and count."""
        grouped: Dict[str, int] = {}

        for item in data:
            item_type = item.get("type", "unknown")
            grouped[item_type] = grouped.get(item_type, 0) + 1

        return grouped

    def _calculate_trend_direction(
        self, current: int, historical: int
    ) -> str:
        """
        Calculate trend direction.

        Args:
            current: Current count
            historical: Historical count

        Returns:
            Trend direction ("increasing", "decreasing", "stable")
        """
        if historical == 0:
            return "increasing" if current > 0 else "stable"

        change_percent = ((current - historical) / historical) * 100

        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"

    def _calculate_trend_strength(self, current: int, historical: int) -> float:
        """
        Calculate trend strength (0.0-1.0).

        Args:
            current: Current count
            historical: Historical count

        Returns:
            Trend strength (0.0-1.0)
        """
        if historical == 0:
            return 1.0 if current > 0 else 0.0

        change_percent = abs(((current - historical) / historical) * 100)
        # Normalize to 0.0-1.0 (100% change = 1.0 strength)
        return min(change_percent / 100.0, 1.0)

    def _calculate_overall_trend(
        self, current: int, historical: int
    ) -> Dict[str, Any]:
        """Calculate overall trend direction and strength."""
        direction = self._calculate_trend_direction(current, historical)
        strength = self._calculate_trend_strength(current, historical)

        return {
            "direction": direction,
            "strength": strength,
        }

