"""
Engagement Analyzer.

Analyze user engagement levels, trends, and content preferences.
"""

from typing import Any, Dict, List, Optional

from ..utils.scoring import normalize_confidence


class EngagementAnalyzer:
    """
    Analyze user engagement.

    Analyzes engagement patterns to calculate engagement scores,
    identify trends, content preferences, and interaction frequency.

    Example:
        ```python
        analyzer = EngagementAnalyzer()
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
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze user engagement.

        Args:
            patterns: List of patterns (dict format)
            session_context: Session context (optional)
            historical_data: Historical data for trend analysis (optional)

        Returns:
            Engagement analysis results
        """
        analysis: Dict[str, Any] = {
            "engagement_score": self._calculate_engagement_score(patterns),
            "engagement_trend": self._calculate_trend(patterns, historical_data),
            "content_preferences": self._identify_preferences(patterns),
            "interaction_frequency": self._calculate_frequency(patterns),
            "engagement_level": self._classify_engagement_level(patterns),
        }

        return analysis

    def _calculate_engagement_score(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Calculate overall engagement score (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Engagement score (0.0-1.0)
        """
        engagement_score = 0.0
        pattern_count = 0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    engagement_score += confidence * 0.4
                    pattern_count += 1
                elif "engagement" in indicators:
                    engagement_score += confidence * 0.2
                    pattern_count += 1

            if pattern_type == "frequency":
                # High frequency indicates engagement
                count = pattern.get("count", 0)
                if count > 5:
                    engagement_score += confidence * 0.3
                    pattern_count += 1

        if pattern_count == 0:
            return 0.0

        return normalize_confidence(engagement_score / max(pattern_count, 1))

    def _calculate_trend(
        self,
        patterns: List[Dict[str, Any]],
        historical_data: Optional[List[Dict[str, Any]]],
    ) -> str:
        """
        Calculate engagement trend.

        Args:
            patterns: Current patterns
            historical_data: Historical patterns

        Returns:
            Trend direction ("increasing", "decreasing", "stable")
        """
        if not historical_data:
            return "stable"

        current_score = self._calculate_engagement_score(patterns)
        historical_score = self._calculate_engagement_score(historical_data)

        if current_score > historical_score * 1.1:
            return "increasing"
        elif current_score < historical_score * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _identify_preferences(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Identify content preferences.

        Args:
            patterns: List of patterns

        Returns:
            List of content preference identifiers
        """
        preferences: List[str] = []

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                # Extract content-related indicators
                content_indicators = [
                    ind
                    for ind in indicators
                    if any(
                        keyword in ind.lower()
                        for keyword in ["content", "view", "read", "watch", "preference"]
                    )
                ]
                preferences.extend(content_indicators)

        return list(set(preferences))

    def _calculate_frequency(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Calculate interaction frequency.

        Args:
            patterns: List of patterns

        Returns:
            Interaction frequency (interactions per minute)
        """
        frequency_patterns = [
            p for p in patterns if p.get("type") == "frequency"
        ]

        if not frequency_patterns:
            return 0.0

        total_count = sum(p.get("count", 0) for p in frequency_patterns)
        # Assume average session duration of 5 minutes for calculation
        # In production, use actual session duration from context
        session_duration_minutes = 5.0

        return total_count / session_duration_minutes if session_duration_minutes > 0 else 0.0

    def _classify_engagement_level(
        self, patterns: List[Dict[str, Any]]
    ) -> str:
        """
        Classify engagement level.

        Args:
            patterns: List of patterns

        Returns:
            Engagement level ("high", "medium", "low")
        """
        score = self._calculate_engagement_score(patterns)

        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"

