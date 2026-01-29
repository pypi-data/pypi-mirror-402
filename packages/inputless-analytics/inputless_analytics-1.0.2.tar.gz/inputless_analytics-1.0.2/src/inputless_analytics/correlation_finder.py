"""
Correlation Finder.

Discover correlations between patterns, anomalies, and outcomes.
"""

from typing import Any, Dict, List, Optional


class CorrelationFinder:
    """
    Discover correlations between patterns, anomalies, and outcomes.

    Identifies relationships between different patterns, anomalies,
    and business outcomes to enable deeper insights.

    Example:
        ```python
        finder = CorrelationFinder()
        correlations = finder.find(
            patterns=patterns,
            anomalies=anomalies,
            outcomes=outcomes,
        )
        ```
    """

    def find(
        self,
        patterns: List[Dict[str, Any]],
        anomalies: Optional[List[Dict[str, Any]]] = None,
        outcomes: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Find correlations between patterns, anomalies, and outcomes.

        Args:
            patterns: List of patterns (dict format)
            anomalies: List of anomalies (optional, dict format)
            outcomes: List of outcomes (optional, dict format)

        Returns:
            Correlation analysis results
        """
        correlations: Dict[str, Any] = {
            "pattern_correlations": self._find_pattern_correlations(patterns),
            "anomaly_correlations": (
                self._find_anomaly_correlations(anomalies) if anomalies else {}
            ),
            "pattern_outcome_correlations": (
                self._find_pattern_outcome_correlations(patterns, outcomes)
                if outcomes
                else {}
            ),
            "insights": [],
        }

        # Generate correlation insights
        correlations["insights"] = self._generate_correlation_insights(correlations)

        return correlations

    def _find_pattern_correlations(
        self, patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find correlations between patterns.

        Args:
            patterns: List of patterns

        Returns:
            Pattern correlation results
        """
        correlations: Dict[str, Any] = {}

        # Group patterns by type
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for pattern in patterns:
            pattern_type = pattern.get("type", "unknown")
            if pattern_type not in by_type:
                by_type[pattern_type] = []
            by_type[pattern_type].append(pattern)

        # Find correlations between types
        type_list = list(by_type.keys())
        for i, type1 in enumerate(type_list):
            for type2 in type_list[i + 1 :]:
                correlation_key = f"{type1}_{type2}"
                correlation_strength = self._calculate_correlation_strength(
                    by_type[type1], by_type[type2]
                )

                if correlation_strength > 0.3:
                    correlations[correlation_key] = {
                        "type1": type1,
                        "type2": type2,
                        "strength": correlation_strength,
                        "count1": len(by_type[type1]),
                        "count2": len(by_type[type2]),
                    }

        return correlations

    def _find_anomaly_correlations(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find correlations between anomalies.

        Args:
            anomalies: List of anomalies

        Returns:
            Anomaly correlation results
        """
        correlations: Dict[str, Any] = {}

        # Group anomalies by reason
        by_reason: Dict[str, List[Dict[str, Any]]] = {}
        for anomaly in anomalies:
            if not anomaly.get("is_anomaly", False):
                continue

            reason = anomaly.get("reason", "unknown")
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(anomaly)

        # Find correlations between reasons
        reason_list = list(by_reason.keys())
        for i, reason1 in enumerate(reason_list):
            for reason2 in reason_list[i + 1 :]:
                correlation_key = f"{reason1}_{reason2}"
                correlation_strength = self._calculate_correlation_strength(
                    by_reason[reason1], by_reason[reason2]
                )

                if correlation_strength > 0.3:
                    correlations[correlation_key] = {
                        "reason1": reason1,
                        "reason2": reason2,
                        "strength": correlation_strength,
                        "count1": len(by_reason[reason1]),
                        "count2": len(by_reason[reason2]),
                    }

        return correlations

    def _find_pattern_outcome_correlations(
        self,
        patterns: List[Dict[str, Any]],
        outcomes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Find correlations between patterns and outcomes.

        Args:
            patterns: List of patterns
            outcomes: List of outcomes

        Returns:
            Pattern-outcome correlation results
        """
        correlations: Dict[str, Any] = {}

        # Simple correlation: patterns that co-occur with positive outcomes
        positive_outcomes = [
            o for o in outcomes if o.get("outcome_type") == "positive"
        ]

        if not positive_outcomes:
            return correlations

        # Find patterns that correlate with positive outcomes
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            pattern_id = pattern.get("id", "")

            # Simple heuristic: if pattern has high confidence and positive indicators
            confidence = pattern.get("confidence", 0.0)
            indicators = pattern.get("indicators", [])

            positive_indicators = [
                "high_engagement",
                "conversion_intent",
                "satisfaction",
            ]

            if confidence > 0.7 and any(
                ind in indicators for ind in positive_indicators
            ):
                correlations[f"pattern_{pattern_id}"] = {
                    "pattern_id": pattern_id,
                    "pattern_type": pattern_type,
                    "correlation_strength": confidence,
                    "outcome_type": "positive",
                }

        return correlations

    def _calculate_correlation_strength(
        self, data1: List[Dict[str, Any]], data2: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate correlation strength between two datasets (0.0-1.0).

        Args:
            data1: First dataset
            data2: Second dataset

        Returns:
            Correlation strength (0.0-1.0)
        """
        if not data1 or not data2:
            return 0.0

        # Simple co-occurrence correlation
        # In production, use statistical correlation methods
        count1 = len(data1)
        count2 = len(data2)

        # Normalize by the smaller count
        min_count = min(count1, count2)
        max_count = max(count1, count2)

        if max_count == 0:
            return 0.0

        # Correlation strength based on relative sizes
        correlation = min_count / max_count

        return correlation

    def _generate_correlation_insights(
        self, correlations: Dict[str, Any]
    ) -> List[str]:
        """
        Generate insights from correlation analysis.

        Args:
            correlations: Correlation results

        Returns:
            List of correlation insights
        """
        insights: List[str] = []

        pattern_correlations = correlations.get("pattern_correlations", {})
        if pattern_correlations:
            insights.append(
                f"Found {len(pattern_correlations)} significant pattern correlations"
            )

        anomaly_correlations = correlations.get("anomaly_correlations", {})
        if anomaly_correlations:
            insights.append(
                f"Found {len(anomaly_correlations)} significant anomaly correlations"
            )

        pattern_outcome = correlations.get("pattern_outcome_correlations", {})
        if pattern_outcome:
            insights.append(
                f"Found {len(pattern_outcome)} pattern-outcome correlations"
            )

        return insights

