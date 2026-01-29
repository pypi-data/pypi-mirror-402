"""
Recommendations Engine.

Generates actionable recommendations based on insights and user behavior.
"""

import uuid
from typing import Any, Dict, List, Optional

from .models.insight import Insight, InsightType
from .models.recommendation import Recommendation, RecommendationType
from .utils.scoring import calculate_impact_score, normalize_confidence


class RecommendationsEngine:
    """
    Generate actionable recommendations based on insights and user behavior.

    Transforms insights into concrete, implementable recommendations that can
    improve user experience, increase conversions, and optimize business outcomes.

    Example:
        ```python
        engine = RecommendationsEngine(
            enable_personalization=True,
            enable_ab_testing=True,
        )

        recommendations = engine.generate(
            insights=insights,
            user_context=user_context,
            session_context=session_context,
        )
        ```
    """

    def __init__(
        self,
        enable_personalization: bool = True,
        enable_ab_testing: bool = True,
        min_confidence: float = 0.6,
    ):
        """
        Initialize recommendations engine.

        Args:
            enable_personalization: Enable personalized recommendations
            enable_ab_testing: Enable A/B test recommendations
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.enable_personalization = enable_personalization
        self.enable_ab_testing = enable_ab_testing
        self.min_confidence = normalize_confidence(min_confidence)

    def generate(
        self,
        insights: List[Insight],
        user_context: Optional[Dict[str, Any]] = None,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations from insights.

        Args:
            insights: List of insights
            user_context: User context data (optional)
            session_context: Session context (optional)

        Returns:
            List of recommendations
        """
        recommendations: List[Recommendation] = []

        for insight in insights:
            # Generate recommendations based on insight type
            # Note: insight.type is a string due to use_enum_values=True in Pydantic config
            insight_type = insight.type if isinstance(insight.type, str) else insight.type.value
            
            if insight_type == InsightType.FRUSTRATION.value:
                recommendations.extend(
                    self._generate_frustration_recommendations(insight, user_context)
                )

            elif insight_type == InsightType.ABANDONMENT.value:
                recommendations.extend(
                    self._generate_abandonment_recommendations(insight, user_context)
                )

            elif insight_type == InsightType.CONVERSION_INTENT.value:
                recommendations.extend(
                    self._generate_conversion_recommendations(insight, user_context)
                )

            elif insight_type == InsightType.CHURN_RISK.value:
                recommendations.extend(
                    self._generate_churn_recommendations(insight, user_context)
                )

            elif insight_type == InsightType.PERFORMANCE_ISSUE.value:
                recommendations.extend(
                    self._generate_performance_recommendations(insight, user_context)
                )

            elif insight_type == InsightType.CONFUSION.value:
                recommendations.extend(
                    self._generate_confusion_recommendations(insight, user_context)
                )

        # Filter by confidence and sort by priority
        recommendations = [
            r for r in recommendations if r.confidence >= self.min_confidence
        ]
        recommendations.sort(key=lambda x: self._priority_score(x), reverse=True)

        return recommendations

    def _generate_frustration_recommendations(
        self,
        insight: Insight,
        user_context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Generate recommendations for frustration insights."""
        recommendations = []

        # Proactive support
        recommendations.append(
            Recommendation(
                id=f"rec-frustration-support-{insight.id}",
                type=RecommendationType.PROACTIVE_SUPPORT,
                title="Show Proactive Support",
                description="User shows signs of frustration - offer immediate help",
                action="Show help dialog or live chat",
                priority="high",
                confidence=insight.confidence,
                source_insights=[insight.dict()],
                implementation={
                    "type": "ui_intervention",
                    "component": "help_dialog",
                    "trigger": "immediate",
                },
                expected_impact=calculate_impact_score(insight.confidence, "high"),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        # Simplify interface
        recommendations.append(
            Recommendation(
                id=f"rec-frustration-simplify-{insight.id}",
                type=RecommendationType.UI_IMPROVEMENT,
                title="Simplify Current Task",
                description="Reduce complexity to help frustrated user",
                action="Hide non-essential UI elements",
                priority="medium",
                confidence=insight.confidence * 0.8,
                source_insights=[insight.dict()],
                implementation={
                    "type": "ui_simplification",
                    "hide_elements": ["sidebar", "ads", "recommendations"],
                },
                expected_impact=calculate_impact_score(
                    insight.confidence * 0.8, "medium"
                ),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        return recommendations

    def _generate_abandonment_recommendations(
        self,
        insight: Insight,
        user_context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Generate recommendations for abandonment insights."""
        recommendations = []

        # Exit intent offer
        recommendations.append(
            Recommendation(
                id=f"rec-abandonment-offer-{insight.id}",
                type=RecommendationType.CONVERSION_OPTIMIZATION,
                title="Show Exit Intent Offer",
                description="User is about to abandon - show special offer",
                action="Display discount or special offer on exit intent",
                priority="high",
                confidence=insight.confidence,
                source_insights=[insight.dict()],
                implementation={
                    "type": "exit_intent",
                    "offer_type": "discount",
                    "discount_percent": 10,
                },
                expected_impact=calculate_impact_score(insight.confidence, "high"),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        # Progress indicator
        recommendations.append(
            Recommendation(
                id=f"rec-abandonment-progress-{insight.id}",
                type=RecommendationType.UI_IMPROVEMENT,
                title="Show Progress Indicator",
                description="Display progress to encourage completion",
                action="Show progress bar or step indicator",
                priority="medium",
                confidence=insight.confidence * 0.7,
                source_insights=[insight.dict()],
                implementation={
                    "type": "progress_indicator",
                    "show_percentage": True,
                },
                expected_impact=calculate_impact_score(
                    insight.confidence * 0.7, "medium"
                ),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        return recommendations

    def _generate_conversion_recommendations(
        self,
        insight: Insight,
        user_context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Generate recommendations for conversion intent insights."""
        recommendations = []

        # Remove friction
        recommendations.append(
            Recommendation(
                id=f"rec-conversion-friction-{insight.id}",
                type=RecommendationType.CHECKOUT_OPTIMIZATION,
                title="Remove Checkout Friction",
                description="User has strong conversion intent - remove barriers",
                action="Simplify checkout process, remove unnecessary fields",
                priority="high",
                confidence=insight.confidence,
                source_insights=[insight.dict()],
                implementation={
                    "type": "checkout_optimization",
                    "remove_fields": ["company", "newsletter"],
                    "enable_guest_checkout": True,
                },
                expected_impact=calculate_impact_score(insight.confidence, "high"),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        # Show trust signals
        recommendations.append(
            Recommendation(
                id=f"rec-conversion-trust-{insight.id}",
                type=RecommendationType.CONVERSION_OPTIMIZATION,
                title="Highlight Trust Signals",
                description="Show security badges, reviews, guarantees",
                action="Display trust badges and social proof",
                priority="medium",
                confidence=insight.confidence * 0.8,
                source_insights=[insight.dict()],
                implementation={
                    "type": "trust_signals",
                    "show_badges": ["ssl", "money_back", "reviews"],
                },
                expected_impact=calculate_impact_score(
                    insight.confidence * 0.8, "medium"
                ),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        return recommendations

    def _generate_churn_recommendations(
        self,
        insight: Insight,
        user_context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Generate recommendations for churn risk insights."""
        recommendations = []

        # Re-engagement campaign
        recommendations.append(
            Recommendation(
                id=f"rec-churn-reengage-{insight.id}",
                type=RecommendationType.RE_ENGAGEMENT,
                title="Launch Re-engagement Campaign",
                description="User shows churn risk - re-engage with personalized content",
                action="Send personalized email or in-app message",
                priority="high",
                confidence=insight.confidence,
                source_insights=[insight.dict()],
                implementation={
                    "type": "re_engagement",
                    "channel": "email",
                    "personalization": True,
                },
                expected_impact=calculate_impact_score(insight.confidence, "high"),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        # Retention offer
        recommendations.append(
            Recommendation(
                id=f"rec-churn-offer-{insight.id}",
                type=RecommendationType.CONVERSION_OPTIMIZATION,
                title="Offer Retention Incentive",
                description="Provide special offer to retain at-risk user",
                action="Show retention offer or loyalty program",
                priority="high",
                confidence=insight.confidence * 0.9,
                source_insights=[insight.dict()],
                implementation={
                    "type": "retention_offer",
                    "offer_type": "discount",
                    "discount_percent": 15,
                },
                expected_impact=calculate_impact_score(
                    insight.confidence * 0.9, "high"
                ),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        return recommendations

    def _generate_performance_recommendations(
        self,
        insight: Insight,
        user_context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Generate recommendations for performance issues."""
        recommendations = []

        # Optimize page performance
        recommendations.append(
            Recommendation(
                id=f"rec-performance-optimize-{insight.id}",
                type=RecommendationType.PERFORMANCE_OPTIMIZATION,
                title="Optimize Page Performance",
                description="Page performance is affecting user experience",
                action="Optimize images, reduce JavaScript bundle size, enable caching",
                priority="medium",
                confidence=insight.confidence,
                source_insights=[insight.dict()],
                implementation={
                    "type": "performance_optimization",
                    "actions": [
                        "compress_images",
                        "lazy_load_content",
                        "enable_caching",
                    ],
                },
                expected_impact=calculate_impact_score(insight.confidence, "medium"),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        return recommendations

    def _generate_confusion_recommendations(
        self,
        insight: Insight,
        user_context: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Generate recommendations for confusion insights."""
        recommendations = []

        # Show help content
        recommendations.append(
            Recommendation(
                id=f"rec-confusion-help-{insight.id}",
                type=RecommendationType.HELP_CONTENT,
                title="Show Contextual Help",
                description="User appears confused - provide guidance",
                action="Show contextual tooltips or help content",
                priority="medium",
                confidence=insight.confidence,
                source_insights=[insight.dict()],
                implementation={
                    "type": "help_content",
                    "format": "tooltip",
                    "contextual": True,
                },
                expected_impact=calculate_impact_score(insight.confidence, "medium"),
                session_id=insight.session_id,
                user_id=insight.user_id,
            )
        )

        return recommendations

    def _priority_score(self, recommendation: Recommendation) -> float:
        """Calculate priority score for sorting."""
        from .utils.scoring import calculate_priority_score

        return calculate_priority_score(recommendation)
