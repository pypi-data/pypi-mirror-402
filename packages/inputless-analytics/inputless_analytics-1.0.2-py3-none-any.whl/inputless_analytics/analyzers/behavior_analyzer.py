"""
Behavior Analyzer.

Analyze user behavior patterns and identify behavioral segments.
"""

from typing import Any, Dict, List, Optional

from ..utils.scoring import normalize_confidence


class BehaviorAnalyzer:
    """
    Analyze user behavior patterns.

    Analyzes behavioral patterns to calculate engagement, frustration,
    conversion probability, and identify behavioral segments.

    Example:
        ```python
        analyzer = BehaviorAnalyzer()
        analysis = analyzer.analyze(
            patterns=patterns,
            session_context=session_context,
        )
        ```
    """

    def analyze(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze user behavior from patterns.

        Args:
            patterns: List of behavioral patterns (dict format)
            session_context: Session context data (optional)

        Returns:
            Behavior analysis results
        """
        analysis: Dict[str, Any] = {
            "engagement_level": self._calculate_engagement(patterns),
            "frustration_level": self._calculate_frustration(patterns),
            "conversion_probability": self._calculate_conversion_probability(patterns),
            "behavioral_segments": self._identify_segments(patterns),
            "intent_state": self._infer_intent_state(patterns, session_context),
        }

        return analysis

    def _calculate_engagement(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Calculate engagement level (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Engagement score (0.0-1.0)
        """
        engagement_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators or "deep_engagement" in indicators:
                    engagement_score += confidence * 0.3

                if "content_interaction" in indicators:
                    engagement_score += confidence * 0.2

        return normalize_confidence(engagement_score)

    def _calculate_frustration(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Calculate frustration level (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Frustration score (0.0-1.0)
        """
        frustration_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "frustration" in indicators or "rage_click" in indicators:
                    frustration_score += confidence * 0.4

                if "rapid_back_navigation" in indicators:
                    frustration_score += confidence * 0.2

        return normalize_confidence(frustration_score)

    def _calculate_conversion_probability(
        self, patterns: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate conversion probability (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Conversion probability (0.0-1.0)
        """
        conversion_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "sequence":
                indicators = pattern.get("indicators", [])
                metadata = pattern.get("metadata", {})
                all_indicators = indicators + metadata.get("indicators", [])

                conversion_indicators = [
                    "product_view",
                    "cart_add",
                    "checkout_start",
                    "payment_info",
                ]

                if any(ind in all_indicators for ind in conversion_indicators):
                    conversion_score += confidence * 0.3

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    conversion_score += confidence * 0.2

        return normalize_confidence(conversion_score)

    def _identify_segments(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Identify behavioral segments.

        Args:
            patterns: List of patterns

        Returns:
            List of behavioral segment identifiers
        """
        segments: List[str] = []

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                segments.extend(indicators)

        # Return unique segments
        return list(set(segments))

    def _infer_intent_state(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> str:
        """
        Infer user intent state.

        Args:
            patterns: List of patterns
            session_context: Session context

        Returns:
            Intent state ("focused", "deliberative", "frustrated", "wandering")
        """
        frustration_level = self._calculate_frustration(patterns)
        engagement_level = self._calculate_engagement(patterns)

        if frustration_level > 0.7:
            return "frustrated"
        elif engagement_level > 0.7:
            return "focused"
        elif engagement_level > 0.4:
            return "deliberative"
        else:
            return "wandering"

