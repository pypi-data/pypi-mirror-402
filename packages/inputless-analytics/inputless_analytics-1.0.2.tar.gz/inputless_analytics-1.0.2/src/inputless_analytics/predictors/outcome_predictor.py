"""
Outcome Predictor.

Predict business outcomes (conversion, revenue, retention) based on user behavior.
"""

from typing import Any, Dict, List, Optional

from ..utils.scoring import normalize_confidence


class OutcomePredictor:
    """
    Predict business outcomes.

    Predicts conversion, revenue, retention, and other business outcomes
    based on user behavior patterns.

    Example:
        ```python
        predictor = OutcomePredictor()
        predictions = predictor.predict(
            patterns=patterns,
            session_context=session_context,
        )
        ```
    """

    def __init__(self, use_ml_models: bool = False):
        """
        Initialize outcome predictor.

        Args:
            use_ml_models: Whether to use ML models (future integration)
        """
        self.use_ml_models = use_ml_models
        # Future: Initialize ML models from inputless-models

    def predict(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Predict business outcomes.

        Args:
            patterns: List of patterns (dict format)
            session_context: Session context (optional)

        Returns:
            Outcome predictions dictionary
        """
        predictions: Dict[str, Any] = {
            "conversion_probability": self._predict_conversion(patterns),
            "revenue_estimate": self._estimate_revenue(patterns, session_context),
            "retention_probability": self._predict_retention(patterns),
            "lifetime_value_estimate": self._estimate_lifetime_value(
                patterns, session_context
            ),
            "churn_probability": self._predict_churn(patterns),
            "prediction_confidence": self._calculate_prediction_confidence(patterns),
        }

        return predictions

    def _predict_conversion(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Predict conversion probability (0.0-1.0).

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

    def _estimate_revenue(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> float:
        """
        Estimate potential revenue.

        Args:
            patterns: List of patterns
            session_context: Session context

        Returns:
            Estimated revenue (currency units)
        """
        conversion_prob = self._predict_conversion(patterns)
        # Base average order value (in production, get from historical data)
        base_aov = 50.0

        # Adjust based on patterns
        aov_multiplier = 1.0
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    aov_multiplier += 0.2

        estimated_revenue = conversion_prob * base_aov * aov_multiplier
        return max(estimated_revenue, 0.0)

    def _predict_retention(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Predict retention probability (0.0-1.0).

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
                if "high_engagement" in indicators:
                    retention_score += confidence * 0.3
                if "repeat_visit" in indicators:
                    retention_score += confidence * 0.4

        return normalize_confidence(retention_score)

    def _estimate_lifetime_value(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> float:
        """
        Estimate customer lifetime value.

        Args:
            patterns: List of patterns
            session_context: Session context

        Returns:
            Estimated CLV (currency units)
        """
        retention_prob = self._predict_retention(patterns)
        revenue_estimate = self._estimate_revenue(patterns, session_context)

        # Simple CLV calculation: revenue * retention probability * average customer lifespan
        # In production, use more sophisticated models
        avg_customer_lifespan = 12.0  # months
        clv = revenue_estimate * retention_prob * avg_customer_lifespan

        return max(clv, 0.0)

    def _predict_churn(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Predict churn probability (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Churn probability (0.0-1.0)
        """
        churn_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "abandonment" in indicators:
                    churn_score += confidence * 0.4
                if "frustration" in indicators:
                    churn_score += confidence * 0.3
                if "low_engagement" in indicators:
                    churn_score += confidence * 0.2

        return normalize_confidence(churn_score)

    def _calculate_prediction_confidence(
        self, patterns: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall prediction confidence (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Prediction confidence (0.0-1.0)
        """
        if not patterns:
            return 0.0

        confidences = [
            normalize_confidence(p.get("confidence", 0.0))
            for p in patterns
            if "confidence" in p
        ]

        if not confidences:
            return 0.0

        # Average confidence
        return sum(confidences) / len(confidences)

