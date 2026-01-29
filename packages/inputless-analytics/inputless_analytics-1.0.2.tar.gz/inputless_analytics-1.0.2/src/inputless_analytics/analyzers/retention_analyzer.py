"""
Retention Analyzer.

Analyze user retention, churn risk, and re-engagement opportunities.
"""

from typing import Any, Dict, List, Optional

from ..utils.scoring import normalize_confidence


class RetentionAnalyzer:
    """
    Analyze user retention and churn risk.

    Analyzes patterns to identify retention probability, churn risk,
    re-engagement opportunities, and loyalty indicators.

    Example:
        ```python
        analyzer = RetentionAnalyzer()
        analysis = analyzer.analyze(
            patterns=patterns,
            session_context=session_context,
            historical_data=historical_data,
        )
        ```
    """

    def analyze(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze user retention and churn risk.

        Args:
            patterns: List of patterns (dict format)
            session_context: Session context (optional)
            historical_data: Historical data for trend analysis (optional)

        Returns:
            Retention analysis results
        """
        analysis: Dict[str, Any] = {
            "retention_probability": self._calculate_retention_probability(patterns),
            "churn_risk": self._calculate_churn_risk(patterns),
            "re_engagement_opportunities": self._identify_re_engagement_opportunities(
                patterns
            ),
            "loyalty_indicators": self._identify_loyalty_indicators(patterns),
            "retention_trend": self._calculate_retention_trend(
                patterns, historical_data
            ),
        }

        return analysis

    def _calculate_retention_probability(
        self, patterns: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate retention probability (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Retention probability (0.0-1.0)
        """
        retention_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                # Positive retention indicators
                if "high_engagement" in indicators:
                    retention_score += confidence * 0.3

                if "repeat_visit" in indicators:
                    retention_score += confidence * 0.4

                if "content_preference" in indicators:
                    retention_score += confidence * 0.2

            if pattern_type == "frequency":
                # High frequency indicates retention
                count = pattern.get("count", 0)
                if count > 3:
                    retention_score += confidence * 0.3

        return normalize_confidence(retention_score)

    def _calculate_churn_risk(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Calculate churn risk (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Churn risk score (0.0-1.0)
        """
        churn_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                # Negative retention indicators
                if "abandonment" in indicators:
                    churn_score += confidence * 0.4

                if "frustration" in indicators:
                    churn_score += confidence * 0.3

                if "low_engagement" in indicators:
                    churn_score += confidence * 0.2

            if pattern_type == "temporal":
                # Long inactivity periods
                duration = pattern.get("duration", 0)
                if duration > 300:  # 5 minutes of inactivity
                    churn_score += confidence * 0.2

        return normalize_confidence(churn_score)

    def _identify_re_engagement_opportunities(
        self, patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Identify re-engagement opportunities.

        Args:
            patterns: List of patterns

        Returns:
            List of re-engagement opportunity identifiers
        """
        opportunities: List[str] = []

        churn_risk = self._calculate_churn_risk(patterns)

        if churn_risk > 0.6:
            opportunities.append("high_priority_re_engagement")

        # Check for specific patterns that indicate re-engagement opportunities
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "abandonment" in indicators:
                    opportunities.append("exit_intent_offer")
                if "low_engagement" in indicators:
                    opportunities.append("personalized_content")

        return list(set(opportunities))

    def _identify_loyalty_indicators(
        self, patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Identify loyalty indicators.

        Args:
            patterns: List of patterns

        Returns:
            List of loyalty indicator identifiers
        """
        indicators: List[str] = []

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                pattern_indicators = pattern.get("indicators", [])
                if "repeat_visit" in pattern_indicators:
                    indicators.append("repeat_visitor")
                if "high_engagement" in pattern_indicators:
                    indicators.append("highly_engaged")
                if "content_preference" in pattern_indicators:
                    indicators.append("content_loyalty")

            if pattern_type == "frequency":
                count = pattern.get("count", 0)
                if count > 5:
                    indicators.append("frequent_user")

        return list(set(indicators))

    def _calculate_retention_trend(
        self,
        patterns: List[Dict[str, Any]],
        historical_data: Optional[List[Dict[str, Any]]],
    ) -> str:
        """
        Calculate retention trend.

        Args:
            patterns: Current patterns
            historical_data: Historical patterns

        Returns:
            Trend direction ("improving", "declining", "stable")
        """
        if not historical_data:
            return "stable"

        current_retention = self._calculate_retention_probability(patterns)
        historical_retention = self._calculate_retention_probability(historical_data)

        if current_retention > historical_retention * 1.1:
            return "improving"
        elif current_retention < historical_retention * 0.9:
            return "declining"
        else:
            return "stable"

