"""
Pattern Aggregator.

Aggregate patterns by type, indicators, and other dimensions.
"""

from typing import Any, Dict, List


class PatternAggregator:
    """
    Aggregate patterns for batch analysis.

    Groups patterns by type, indicators, and other dimensions
    to enable batch processing and trend analysis.

    Example:
        ```python
        aggregator = PatternAggregator()
        aggregated = aggregator.aggregate(patterns, group_by="type")
        ```
    """

    def aggregate(
        self,
        patterns: List[Dict[str, Any]],
        group_by: str = "type",
    ) -> Dict[str, Any]:
        """
        Aggregate patterns by specified dimension.

        Args:
            patterns: List of patterns (dict format)
            group_by: Dimension to group by ("type", "indicators", "confidence")

        Returns:
            Aggregated patterns dictionary
        """
        aggregated: Dict[str, Any] = {}

        if group_by == "type":
            return self._aggregate_by_type(patterns)
        elif group_by == "indicators":
            return self._aggregate_by_indicators(patterns)
        elif group_by == "confidence":
            return self._aggregate_by_confidence(patterns)
        else:
            raise ValueError(f"Unknown group_by: {group_by}")

    def _aggregate_by_type(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate patterns by type."""
        aggregated: Dict[str, Any] = {}

        for pattern in patterns:
            pattern_type = pattern.get("type", "unknown")
            confidence = pattern.get("confidence", 0.0)

            if pattern_type not in aggregated:
                aggregated[pattern_type] = {
                    "count": 0,
                    "patterns": [],
                    "total_confidence": 0.0,
                    "avg_confidence": 0.0,
                }

            aggregated[pattern_type]["count"] += 1
            aggregated[pattern_type]["patterns"].append(pattern)
            aggregated[pattern_type]["total_confidence"] += confidence

        # Calculate averages
        for pattern_type in aggregated:
            count = aggregated[pattern_type]["count"]
            aggregated[pattern_type]["avg_confidence"] = (
                aggregated[pattern_type]["total_confidence"] / count
            )

        return aggregated

    def _aggregate_by_indicators(
        self, patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate patterns by indicators."""
        aggregated: Dict[str, Any] = {}

        for pattern in patterns:
            indicators = pattern.get("indicators", [])
            confidence = pattern.get("confidence", 0.0)

            # Create a key from sorted indicators
            indicator_key = ",".join(sorted(indicators)) if indicators else "none"

            if indicator_key not in aggregated:
                aggregated[indicator_key] = {
                    "count": 0,
                    "patterns": [],
                    "indicators": indicators,
                    "total_confidence": 0.0,
                    "avg_confidence": 0.0,
                }

            aggregated[indicator_key]["count"] += 1
            aggregated[indicator_key]["patterns"].append(pattern)
            aggregated[indicator_key]["total_confidence"] += confidence

        # Calculate averages
        for key in aggregated:
            count = aggregated[key]["count"]
            aggregated[key]["avg_confidence"] = (
                aggregated[key]["total_confidence"] / count
            )

        return aggregated

    def _aggregate_by_confidence(
        self, patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate patterns by confidence ranges."""
        aggregated: Dict[str, Any] = {
            "high": {"count": 0, "patterns": [], "range": (0.8, 1.0)},
            "medium": {"count": 0, "patterns": [], "range": (0.5, 0.8)},
            "low": {"count": 0, "patterns": [], "range": (0.0, 0.5)},
        }

        for pattern in patterns:
            confidence = pattern.get("confidence", 0.0)

            if confidence >= 0.8:
                aggregated["high"]["count"] += 1
                aggregated["high"]["patterns"].append(pattern)
            elif confidence >= 0.5:
                aggregated["medium"]["count"] += 1
                aggregated["medium"]["patterns"].append(pattern)
            else:
                aggregated["low"]["count"] += 1
                aggregated["low"]["patterns"].append(pattern)

        return aggregated

    def get_statistics(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistical summary of patterns.

        Args:
            patterns: List of patterns

        Returns:
            Statistics dictionary
        """
        if not patterns:
            return {
                "total": 0,
                "by_type": {},
                "avg_confidence": 0.0,
                "confidence_range": {"min": 0.0, "max": 0.0},
            }

        confidences = [
            p.get("confidence", 0.0) for p in patterns if "confidence" in p
        ]

        by_type = self._aggregate_by_type(patterns)

        return {
            "total": len(patterns),
            "by_type": {k: v["count"] for k, v in by_type.items()},
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "confidence_range": {
                "min": min(confidences) if confidences else 0.0,
                "max": max(confidences) if confidences else 0.0,
            },
        }

