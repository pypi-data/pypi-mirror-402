"""
Behavior Predictor.

Predict future user behavior based on current patterns.
"""

from typing import Any, Dict, List, Optional

from ..utils.scoring import normalize_confidence


class BehaviorPredictor:
    """
    Predict future user behavior.

    Uses heuristic-based prediction (with ML integration hooks)
    to predict future user behavior based on current patterns.

    Example:
        ```python
        predictor = BehaviorPredictor()
        predictions = predictor.predict(
            patterns=patterns,
            session_context=session_context,
        )
        ```
    """

    def __init__(self, use_ml_models: bool = False):
        """
        Initialize behavior predictor.

        Args:
            use_ml_models: Whether to use ML models (future integration)
        """
        self.use_ml_models = use_ml_models
        # Future: Initialize ML models from inputless-models

    def predict(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]] = None,
        prediction_horizon: str = "short_term",
    ) -> Dict[str, Any]:
        """
        Predict future user behavior.

        Args:
            patterns: List of patterns (dict format)
            session_context: Session context (optional)
            prediction_horizon: Prediction horizon ("short_term", "medium_term", "long_term")

        Returns:
            Behavior predictions dictionary
        """
        predictions: Dict[str, Any] = {
            "next_action_probability": self._predict_next_action(patterns),
            "session_duration": self._predict_session_duration(patterns),
            "engagement_trajectory": self._predict_engagement_trajectory(patterns),
            "conversion_likelihood": self._predict_conversion_likelihood(patterns),
            "churn_probability": self._predict_churn_probability(patterns),
            "prediction_confidence": self._calculate_prediction_confidence(patterns),
        }

        return predictions

    def _predict_next_action(self, patterns: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Predict next user action.

        Args:
            patterns: List of patterns

        Returns:
            Dictionary of action probabilities
        """
        action_probabilities: Dict[str, float] = {
            "continue_browsing": 0.3,
            "add_to_cart": 0.2,
            "checkout": 0.1,
            "leave": 0.2,
            "search": 0.2,
        }

        # Adjust based on current patterns
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "sequence":
                indicators = pattern.get("indicators", [])
                if "checkout_start" in indicators:
                    action_probabilities["checkout"] += confidence * 0.3
                    action_probabilities["leave"] -= confidence * 0.1

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    action_probabilities["continue_browsing"] += confidence * 0.2
                    action_probabilities["leave"] -= confidence * 0.1

        # Normalize probabilities
        total = sum(action_probabilities.values())
        if total > 0:
            action_probabilities = {
                k: normalize_confidence(v / total) for k, v in action_probabilities.items()
            }

        return action_probabilities

    def _predict_session_duration(self, patterns: List[Dict[str, Any]]) -> float:
        """
        Predict session duration in minutes.

        Args:
            patterns: List of patterns

        Returns:
            Predicted session duration (minutes)
        """
        base_duration = 5.0  # Base 5 minutes

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    base_duration += confidence * 10.0

            if pattern_type == "temporal":
                duration = pattern.get("duration", 0)
                if duration > 0:
                    base_duration += duration / 60.0  # Convert to minutes

        return max(base_duration, 1.0)  # Minimum 1 minute

    def _predict_engagement_trajectory(
        self, patterns: List[Dict[str, Any]]
    ) -> str:
        """
        Predict engagement trajectory.

        Args:
            patterns: List of patterns

        Returns:
            Trajectory ("increasing", "decreasing", "stable")
        """
        engagement_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                confidence = normalize_confidence(pattern.get("confidence", 0.0))
                if "high_engagement" in indicators:
                    engagement_score += confidence

        if engagement_score > 0.7:
            return "increasing"
        elif engagement_score < 0.3:
            return "decreasing"
        else:
            return "stable"

    def _predict_conversion_likelihood(
        self, patterns: List[Dict[str, Any]]
    ) -> float:
        """
        Predict conversion likelihood (0.0-1.0).

        Args:
            patterns: List of patterns

        Returns:
            Conversion likelihood (0.0-1.0)
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
                ]

                if any(ind in all_indicators for ind in conversion_indicators):
                    conversion_score += confidence * 0.4

        return normalize_confidence(conversion_score)

    def _predict_churn_probability(self, patterns: List[Dict[str, Any]]) -> float:
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

        # Average confidence weighted by pattern count
        return sum(confidences) / len(confidences)

