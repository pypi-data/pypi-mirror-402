"""
Conversion Analyzer.

Analyze conversion funnels and identify optimization opportunities.
"""

from typing import Any, Dict, List, Optional

from ..utils.scoring import normalize_confidence


class ConversionAnalyzer:
    """
    Analyze conversion funnels and optimization opportunities.

    Analyzes patterns to identify conversion probability, funnel stages,
    drop-off points, and optimization opportunities.

    Example:
        ```python
        analyzer = ConversionAnalyzer()
        analysis = analyzer.analyze(
            patterns=patterns,
            session_context=session_context,
        )
        ```
    """

    # Conversion funnel stages
    FUNNEL_STAGES = [
        "awareness",
        "interest",
        "consideration",
        "intent",
        "evaluation",
        "purchase",
    ]

    # Conversion indicators by stage
    STAGE_INDICATORS = {
        "awareness": ["page_view", "landing"],
        "interest": ["scroll", "time_on_page"],
        "consideration": ["product_view", "content_view"],
        "intent": ["cart_add", "wishlist"],
        "evaluation": ["checkout_start", "form_start"],
        "purchase": ["payment_info", "checkout_complete"],
    }

    def analyze(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze conversion funnel.

        Args:
            patterns: List of patterns (dict format)
            session_context: Session context (optional)

        Returns:
            Conversion analysis results
        """
        analysis: Dict[str, Any] = {
            "conversion_probability": self._calculate_probability(patterns),
            "funnel_stage": self._identify_stage(patterns),
            "drop_off_points": self._identify_drop_offs(patterns),
            "optimization_opportunities": self._identify_opportunities(patterns),
            "funnel_progress": self._calculate_funnel_progress(patterns),
        }

        return analysis

    def _calculate_probability(self, patterns: List[Dict[str, Any]]) -> float:
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

                # Check for conversion sequence
                conversion_sequence = [
                    "product_view",
                    "cart_add",
                    "checkout_start",
                    "payment_info",
                ]

                sequence_match = sum(
                    1 for ind in conversion_sequence if ind in all_indicators
                )
                if sequence_match >= 2:
                    conversion_score += confidence * (sequence_match / len(conversion_sequence))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    conversion_score += confidence * 0.2

        return normalize_confidence(conversion_score)

    def _identify_stage(self, patterns: List[Dict[str, Any]]) -> str:
        """
        Identify current funnel stage.

        Args:
            patterns: List of patterns

        Returns:
            Current funnel stage
        """
        # Collect all indicators from patterns
        all_indicators: List[str] = []
        for pattern in patterns:
            indicators = pattern.get("indicators", [])
            metadata = pattern.get("metadata", {})
            all_indicators.extend(indicators)
            all_indicators.extend(metadata.get("indicators", []))

        # Find the highest stage reached
        for stage in reversed(self.FUNNEL_STAGES):
            stage_indicators = self.STAGE_INDICATORS.get(stage, [])
            if any(ind in all_indicators for ind in stage_indicators):
                return stage

        return "awareness"  # Default to first stage

    def _identify_drop_offs(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Identify drop-off points.

        Args:
            patterns: List of patterns

        Returns:
            List of drop-off point identifiers
        """
        drop_offs: List[str] = []

        # Check for abandonment patterns
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "abandonment" in indicators or "form_abandonment" in indicators:
                    # Identify which stage was abandoned
                    stage = self._identify_stage([pattern])
                    drop_offs.append(f"{stage}_abandonment")

        return list(set(drop_offs))

    def _identify_opportunities(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Identify optimization opportunities.

        Args:
            patterns: List of patterns

        Returns:
            List of optimization opportunity identifiers
        """
        opportunities: List[str] = []

        # Check for frustration at conversion stages
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "frustration" in indicators:
                    stage = self._identify_stage([pattern])
                    opportunities.append(f"reduce_friction_{stage}")

        # Check for low engagement at key stages
        current_stage = self._identify_stage(patterns)
        if current_stage in ["intent", "evaluation"]:
            opportunities.append("enhance_trust_signals")
            opportunities.append("simplify_checkout")

        return list(set(opportunities))

    def _calculate_funnel_progress(
        self, patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate funnel progress.

        Args:
            patterns: List of patterns

        Returns:
            Funnel progress dictionary
        """
        current_stage = self._identify_stage(patterns)
        stage_index = self.FUNNEL_STAGES.index(current_stage) if current_stage in self.FUNNEL_STAGES else 0

        return {
            "current_stage": current_stage,
            "stage_index": stage_index,
            "total_stages": len(self.FUNNEL_STAGES),
            "progress_percent": (stage_index / len(self.FUNNEL_STAGES)) * 100,
        }

