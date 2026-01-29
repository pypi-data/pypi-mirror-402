"""
Anomaly Aggregator.

Aggregate anomalies by score, reason, and other dimensions.
"""

from typing import Any, Dict, List


class AnomalyAggregator:
    """
    Aggregate anomalies for batch analysis.

    Groups anomalies by score, reason, and other dimensions
    to enable batch processing and trend analysis.

    Example:
        ```python
        aggregator = AnomalyAggregator()
        aggregated = aggregator.aggregate(anomalies, group_by="reason")
        ```
    """

    def aggregate(
        self,
        anomalies: List[Dict[str, Any]],
        group_by: str = "reason",
    ) -> Dict[str, Any]:
        """
        Aggregate anomalies by specified dimension.

        Args:
            anomalies: List of anomalies (dict format)
            group_by: Dimension to group by ("reason", "score", "threshold")

        Returns:
            Aggregated anomalies dictionary
        """
        if group_by == "reason":
            return self._aggregate_by_reason(anomalies)
        elif group_by == "score":
            return self._aggregate_by_score(anomalies)
        elif group_by == "threshold":
            return self._aggregate_by_threshold(anomalies)
        else:
            raise ValueError(f"Unknown group_by: {group_by}")

    def _aggregate_by_reason(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate anomalies by reason."""
        aggregated: Dict[str, Any] = {}

        for anomaly in anomalies:
            if not anomaly.get("is_anomaly", False):
                continue

            reason = anomaly.get("reason", "unknown")
            score = anomaly.get("score", 0.0)

            if reason not in aggregated:
                aggregated[reason] = {
                    "count": 0,
                    "anomalies": [],
                    "total_score": 0.0,
                    "avg_score": 0.0,
                }

            aggregated[reason]["count"] += 1
            aggregated[reason]["anomalies"].append(anomaly)
            aggregated[reason]["total_score"] += score

        # Calculate averages
        for reason in aggregated:
            count = aggregated[reason]["count"]
            aggregated[reason]["avg_score"] = (
                aggregated[reason]["total_score"] / count
            )

        return aggregated

    def _aggregate_by_score(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate anomalies by score ranges."""
        aggregated: Dict[str, Any] = {
            "critical": {"count": 0, "anomalies": [], "range": (0.9, 1.0)},
            "high": {"count": 0, "anomalies": [], "range": (0.7, 0.9)},
            "medium": {"count": 0, "anomalies": [], "range": (0.5, 0.7)},
            "low": {"count": 0, "anomalies": [], "range": (0.0, 0.5)},
        }

        for anomaly in anomalies:
            if not anomaly.get("is_anomaly", False):
                continue

            score = anomaly.get("score", 0.0)

            if score >= 0.9:
                aggregated["critical"]["count"] += 1
                aggregated["critical"]["anomalies"].append(anomaly)
            elif score >= 0.7:
                aggregated["high"]["count"] += 1
                aggregated["high"]["anomalies"].append(anomaly)
            elif score >= 0.5:
                aggregated["medium"]["count"] += 1
                aggregated["medium"]["anomalies"].append(anomaly)
            else:
                aggregated["low"]["count"] += 1
                aggregated["low"]["anomalies"].append(anomaly)

        return aggregated

    def _aggregate_by_threshold(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate anomalies by threshold."""
        aggregated: Dict[str, Any] = {}

        for anomaly in anomalies:
            if not anomaly.get("is_anomaly", False):
                continue

            threshold = anomaly.get("threshold", 0.7)
            threshold_key = f"threshold_{threshold:.2f}"
            score = anomaly.get("score", 0.0)

            if threshold_key not in aggregated:
                aggregated[threshold_key] = {
                    "count": 0,
                    "anomalies": [],
                    "threshold": threshold,
                    "total_score": 0.0,
                    "avg_score": 0.0,
                }

            aggregated[threshold_key]["count"] += 1
            aggregated[threshold_key]["anomalies"].append(anomaly)
            aggregated[threshold_key]["total_score"] += score

        # Calculate averages
        for key in aggregated:
            count = aggregated[key]["count"]
            aggregated[key]["avg_score"] = aggregated[key]["total_score"] / count

        return aggregated

    def get_statistics(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistical summary of anomalies.

        Args:
            anomalies: List of anomalies

        Returns:
            Statistics dictionary
        """
        if not anomalies:
            return {
                "total": 0,
                "anomalies_count": 0,
                "avg_score": 0.0,
                "score_range": {"min": 0.0, "max": 0.0},
            }

        anomaly_scores = [
            a.get("score", 0.0)
            for a in anomalies
            if a.get("is_anomaly", False) and "score" in a
        ]

        return {
            "total": len(anomalies),
            "anomalies_count": len(anomaly_scores),
            "avg_score": (
                sum(anomaly_scores) / len(anomaly_scores) if anomaly_scores else 0.0
            ),
            "score_range": {
                "min": min(anomaly_scores) if anomaly_scores else 0.0,
                "max": max(anomaly_scores) if anomaly_scores else 0.0,
            },
        }

