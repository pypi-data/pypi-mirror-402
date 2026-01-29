"""
Insights Generator.

Generates actionable insights from patterns, anomalies, and behavioral data.
"""

import uuid
from typing import Any, Dict, List, Optional

from .models.insight import Insight, InsightType
from .utils.scoring import calculate_impact_score, normalize_confidence


class InsightsGenerator:
    """
    Generate actionable insights from patterns, anomalies, and behavioral data.

    Transforms raw pattern/anomaly data into human-readable, actionable insights
    that can be used to improve user experience, optimize conversions, and prevent issues.

    Example:
        ```python
        generator = InsightsGenerator(
            min_confidence=0.6,
            enable_trends=True,
            enable_predictions=True,
        )

        insights = generator.generate(
            patterns=patterns,
            anomalies=anomalies,
            session_context=session_context,
        )
        ```
    """

    def __init__(
        self,
        min_confidence: float = 0.6,
        enable_trends: bool = True,
        enable_predictions: bool = True,
        enable_emotional_state: bool = True,
    ):
        """
        Initialize insights generator.

        Args:
            min_confidence: Minimum confidence threshold for insights (0.0-1.0)
            enable_trends: Enable trend-based insights
            enable_predictions: Enable predictive insights
            enable_emotional_state: Enable emotional state insights
        """
        self.min_confidence = normalize_confidence(min_confidence)
        self.enable_trends = enable_trends
        self.enable_predictions = enable_predictions
        self.enable_emotional_state = enable_emotional_state

    def generate(
        self,
        patterns: List[Dict[str, Any]],
        anomalies: Optional[List[Dict[str, Any]]] = None,
        session_context: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Insight]:
        """
        Generate insights from patterns and anomalies.

        Args:
            patterns: List of detected patterns (dict format)
            anomalies: List of detected anomalies (optional, dict format)
            session_context: Current session context (optional)
            historical_data: Historical data for trend analysis (optional)

        Returns:
            List of generated insights
        """
        insights: List[Insight] = []

        # Generate pattern-based insights
        pattern_insights = self._generate_pattern_insights(patterns, session_context)
        insights.extend(pattern_insights)

        # Generate anomaly-based insights
        if anomalies:
            anomaly_insights = self._generate_anomaly_insights(
                anomalies, session_context
            )
            insights.extend(anomaly_insights)

        # Generate emotional state insights
        if self.enable_emotional_state and session_context:
            emotional_insights = self._generate_emotional_insights(
                patterns, session_context
            )
            insights.extend(emotional_insights)

        # Generate trend-based insights
        if self.enable_trends and historical_data:
            trend_insights = self._generate_trend_insights(
                patterns, historical_data, session_context
            )
            insights.extend(trend_insights)

        # Generate predictive insights
        if self.enable_predictions:
            predictive_insights = self._generate_predictive_insights(
                patterns, anomalies, session_context
            )
            insights.extend(predictive_insights)

        # Filter by confidence and sort by priority
        insights = [
            i for i in insights if i.confidence >= self.min_confidence
        ]
        insights.sort(key=lambda x: self._priority_score(x), reverse=True)

        return insights

    def _generate_pattern_insights(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> List[Insight]:
        """Generate insights from behavioral patterns."""
        insights: List[Insight] = []

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            pattern_id = pattern.get("id", str(uuid.uuid4()))
            confidence = normalize_confidence(pattern.get("confidence", 0.0))
            indicators = pattern.get("indicators", [])
            metadata = pattern.get("metadata", {})

            if pattern_type == "behavioral":
                # Frustration detection
                if "frustration" in indicators or "rage_click" in indicators:
                    insights.append(
                        Insight(
                            id=f"insight-{pattern_id}",
                            type=InsightType.FRUSTRATION,
                            message="User frustration detected",
                            description=f"User shows signs of frustration: {', '.join(indicators)}",
                            confidence=confidence,
                            priority="high" if confidence > 0.8 else "medium",
                            patterns=[pattern],
                            recommended_actions=[
                                "Show help dialog",
                                "Offer live chat support",
                                "Simplify current task",
                            ],
                            estimated_impact=calculate_impact_score(
                                confidence, "high" if confidence > 0.8 else "medium"
                            ),
                        )
                    )

                # Abandonment risk
                if "abandonment" in indicators or "form_abandonment" in indicators:
                    insights.append(
                        Insight(
                            id=f"insight-{pattern_id}",
                            type=InsightType.ABANDONMENT,
                            message="High abandonment risk detected",
                            description="User shows signs of abandoning current task",
                            confidence=confidence,
                            priority="high",
                            patterns=[pattern],
                            recommended_actions=[
                                "Show exit intent offer",
                                "Display progress indicator",
                                "Offer assistance",
                            ],
                            estimated_impact=calculate_impact_score(confidence, "high"),
                        )
                    )

                # High engagement
                if "high_engagement" in indicators or "deep_engagement" in indicators:
                    insights.append(
                        Insight(
                            id=f"insight-{pattern_id}",
                            type=InsightType.HIGH_ENGAGEMENT,
                            message="User shows high engagement",
                            description="User is highly engaged with content",
                            confidence=confidence,
                            priority="low",
                            patterns=[pattern],
                            recommended_actions=[
                                "Show related content",
                                "Offer newsletter signup",
                                "Present upsell opportunities",
                            ],
                            estimated_impact=calculate_impact_score(confidence, "low"),
                        )
                    )

                # Low engagement
                if "low_engagement" in indicators or "bounce" in indicators:
                    insights.append(
                        Insight(
                            id=f"insight-{pattern_id}",
                            type=InsightType.LOW_ENGAGEMENT,
                            message="User shows low engagement",
                            description="User engagement is below expected levels",
                            confidence=confidence,
                            priority="medium",
                            patterns=[pattern],
                            recommended_actions=[
                                "Improve content relevance",
                                "Enhance visual appeal",
                                "Add interactive elements",
                            ],
                            estimated_impact=calculate_impact_score(confidence, "medium"),
                        )
                    )

            elif pattern_type == "sequence":
                # Conversion intent
                if self._is_conversion_sequence(pattern):
                    insights.append(
                        Insight(
                            id=f"insight-{pattern_id}",
                            type=InsightType.CONVERSION_INTENT,
                            message="Strong conversion intent detected",
                            description="User behavior indicates strong purchase intent",
                            confidence=confidence,
                            priority="high",
                            patterns=[pattern],
                            recommended_actions=[
                                "Show special offers",
                                "Highlight trust signals",
                                "Simplify checkout process",
                            ],
                            estimated_impact=calculate_impact_score(confidence, "high"),
                        )
                    )

            elif pattern_type == "temporal":
                # Performance issues
                pattern_indicators = metadata.get("indicators", [])
                if "slow_interaction" in pattern_indicators:
                    insights.append(
                        Insight(
                            id=f"insight-{pattern_id}",
                            type=InsightType.PERFORMANCE_ISSUE,
                            message="Performance degradation detected",
                            description="User interactions are slower than expected",
                            confidence=confidence,
                            priority="medium",
                            patterns=[pattern],
                            recommended_actions=[
                                "Optimize page performance",
                                "Check server response times",
                                "Investigate network issues",
                            ],
                            estimated_impact=calculate_impact_score(confidence, "medium"),
                        )
                    )

        return insights

    def _generate_anomaly_insights(
        self,
        anomalies: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> List[Insight]:
        """Generate insights from detected anomalies."""
        insights: List[Insight] = []

        for anomaly in anomalies:
            if not anomaly.get("is_anomaly", False):
                continue

            anomaly_id = anomaly.get("id", str(uuid.uuid4()))
            score = normalize_confidence(anomaly.get("score", 0.0))
            reason = anomaly.get("reason", "Unknown anomaly")
            threshold = anomaly.get("threshold", 0.7)

            # Critical anomalies
            if score > 0.9:
                insights.append(
                    Insight(
                        id=f"insight-anomaly-{anomaly_id}",
                        type=InsightType.ANOMALY_DETECTED,
                        message=f"Critical anomaly detected: {reason}",
                        description=f"Anomaly score: {score:.2f} (threshold: {threshold:.2f})",
                        confidence=score,
                        priority="critical",
                        anomaly_scores=[anomaly],
                        recommended_actions=[
                            "Investigate immediately",
                            "Check security logs",
                            "Review user session",
                        ],
                        estimated_impact=calculate_impact_score(score, "critical"),
                    )
                )

            # Security risks
            reason_lower = reason.lower()
            if "security" in reason_lower or "fraud" in reason_lower:
                insights.append(
                    Insight(
                        id=f"insight-security-{anomaly_id}",
                        type=InsightType.SECURITY_RISK,
                        message=f"Security risk detected: {reason}",
                        description=f"Anomaly indicates potential security issue",
                        confidence=score,
                        priority="critical",
                        anomaly_scores=[anomaly],
                        recommended_actions=[
                            "Block suspicious activity",
                            "Require additional authentication",
                            "Alert security team",
                        ],
                        estimated_impact=calculate_impact_score(score, "critical"),
                    )
                )

            # High-score anomalies (but not critical)
            elif score > threshold:
                insights.append(
                    Insight(
                        id=f"insight-anomaly-{anomaly_id}",
                        type=InsightType.ANOMALY_DETECTED,
                        message=f"Anomaly detected: {reason}",
                        description=f"Anomaly score: {score:.2f}",
                        confidence=score,
                        priority="high" if score > 0.8 else "medium",
                        anomaly_scores=[anomaly],
                        recommended_actions=[
                            "Review behavior pattern",
                            "Check for errors",
                            "Monitor closely",
                        ],
                        estimated_impact=calculate_impact_score(
                            score, "high" if score > 0.8 else "medium"
                        ),
                    )
                )

        return insights

    def _generate_emotional_insights(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Dict[str, Any],
    ) -> List[Insight]:
        """Generate insights from emotional state inference."""
        insights: List[Insight] = []

        # Check for emotional state in session context
        emotional_state = session_context.get("emotional_state")
        if not emotional_state:
            return insights

        primary = emotional_state.get("primary")
        confidence = normalize_confidence(emotional_state.get("confidence", 0.0))

        if primary == "frustration" and confidence > 0.7:
            insights.append(
                Insight(
                    id="insight-emotional-frustration",
                    type=InsightType.FRUSTRATION,
                    message="User frustration detected",
                    description=f"Emotional state analysis indicates frustration (confidence: {confidence:.2f})",
                    confidence=confidence,
                    priority="high",
                    recommended_actions=[
                        "Show help immediately",
                        "Offer alternative path",
                        "Provide clear error messages",
                    ],
                    estimated_impact=calculate_impact_score(confidence, "high"),
                    metadata={"emotional_state": emotional_state},
                )
            )

        if primary == "confusion" and confidence > 0.6:
            insights.append(
                Insight(
                    id="insight-emotional-confusion",
                    type=InsightType.CONFUSION,
                    message="User confusion detected",
                    description=f"User appears confused (confidence: {confidence:.2f})",
                    confidence=confidence,
                    priority="medium",
                    recommended_actions=[
                        "Show contextual tooltips",
                        "Simplify interface",
                        "Provide step-by-step guidance",
                    ],
                    estimated_impact=calculate_impact_score(confidence, "medium"),
                    metadata={"emotional_state": emotional_state},
                )
            )

        return insights

    def _generate_trend_insights(
        self,
        patterns: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> List[Insight]:
        """Generate insights from trend analysis."""
        insights: List[Insight] = []

        # Analyze trends in patterns
        # Compare current patterns with historical data
        # Identify increasing/decreasing trends

        # Placeholder implementation
        # In production, this would analyze historical patterns and identify trends

        return insights

    def _generate_predictive_insights(
        self,
        patterns: List[Dict[str, Any]],
        anomalies: Optional[List[Dict[str, Any]]],
        session_context: Optional[Dict[str, Any]],
    ) -> List[Insight]:
        """Generate predictive insights."""
        insights: List[Insight] = []

        # Predict conversion likelihood
        conversion_probability = self._predict_conversion(patterns, session_context)
        if conversion_probability > 0.7:
            insights.append(
                Insight(
                    id="insight-predictive-conversion",
                    type=InsightType.CONVERSION_PREDICTION,
                    message=f"High conversion probability: {conversion_probability:.0%}",
                    description="User behavior indicates high likelihood of conversion",
                    confidence=conversion_probability,
                    priority="high",
                    patterns=patterns,
                    recommended_actions=[
                        "Show conversion-optimized content",
                        "Highlight social proof",
                        "Remove friction points",
                    ],
                    estimated_impact=calculate_impact_score(conversion_probability, "high"),
                )
            )

        # Predict churn risk
        churn_probability = self._predict_churn(patterns, session_context)
        if churn_probability > 0.6:
            insights.append(
                Insight(
                    id="insight-predictive-churn",
                    type=InsightType.CHURN_PREDICTION,
                    message=f"Churn risk detected: {churn_probability:.0%}",
                    description="User behavior indicates risk of churning",
                    confidence=churn_probability,
                    priority="high",
                    patterns=patterns,
                    recommended_actions=[
                        "Re-engage with personalized content",
                        "Offer retention incentives",
                        "Address pain points",
                    ],
                    estimated_impact=calculate_impact_score(churn_probability, "high"),
                )
            )

        return insights

    def _is_conversion_sequence(self, pattern: Dict[str, Any]) -> bool:
        """Check if pattern indicates conversion intent."""
        # Check if pattern contains conversion indicators
        conversion_indicators = [
            "product_view",
            "cart_add",
            "checkout_start",
            "payment_info",
        ]
        metadata = pattern.get("metadata", {})
        indicators = metadata.get("indicators", [])
        return any(indicator in indicators for indicator in conversion_indicators)

    def _predict_conversion(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> float:
        """
        Predict conversion probability (0.0-1.0).

        Args:
            patterns: List of patterns
            session_context: Session context

        Returns:
            Conversion probability (0.0-1.0)
        """
        # Simple heuristic-based prediction
        # In production, use ML model from inputless-models

        conversion_score = 0.0

        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            confidence = normalize_confidence(pattern.get("confidence", 0.0))

            if pattern_type == "sequence" and self._is_conversion_sequence(pattern):
                conversion_score += confidence * 0.3

            if pattern_type == "behavioral":
                indicators = pattern.get("indicators", [])
                if "high_engagement" in indicators:
                    conversion_score += confidence * 0.2

        return normalize_confidence(conversion_score)

    def _predict_churn(
        self,
        patterns: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]],
    ) -> float:
        """
        Predict churn probability (0.0-1.0).

        Args:
            patterns: List of patterns
            session_context: Session context

        Returns:
            Churn probability (0.0-1.0)
        """
        # Simple heuristic-based prediction
        # In production, use ML model from inputless-models

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

    def _priority_score(self, insight: Insight) -> float:
        """Calculate priority score for sorting."""
        from .utils.scoring import calculate_priority_score

        return calculate_priority_score(insight)
