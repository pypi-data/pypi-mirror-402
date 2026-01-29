"""
Analytics Engine.

Main orchestrator for analytics processing, combining insights generation
and recommendations into a unified analytics pipeline.
"""

from typing import Any, Dict, List, Optional

from .insights_generator import InsightsGenerator
from .models.analytics_result import AnalyticsResult
from .recommendations import RecommendationsEngine


class AnalyticsEngine:
    """
    Main analytics engine orchestrating insights and recommendations.

    Combines insights generation and recommendations into a unified pipeline
    for analyzing user behavior and generating actionable intelligence.

    Example:
        ```python
        engine = AnalyticsEngine(
            min_confidence=0.6,
            enable_trends=True,
            enable_predictions=True,
            enable_personalization=True,
        )

        result = engine.analyze(
            patterns=patterns,
            anomalies=anomalies,
            session_context=session_context,
        )

        print(f"Generated {len(result.insights)} insights")
        print(f"Generated {len(result.recommendations)} recommendations")
        ```
    """

    def __init__(
        self,
        min_confidence: float = 0.6,
        enable_trends: bool = True,
        enable_predictions: bool = True,
        enable_personalization: bool = True,
        enable_ab_testing: bool = True,
    ):
        """
        Initialize analytics engine.

        Args:
            min_confidence: Minimum confidence threshold for insights/recommendations (0.0-1.0)
            enable_trends: Enable trend-based insights
            enable_predictions: Enable predictive insights
            enable_personalization: Enable personalized recommendations
            enable_ab_testing: Enable A/B test recommendations
        """
        self.insights_generator = InsightsGenerator(
            min_confidence=min_confidence,
            enable_trends=enable_trends,
            enable_predictions=enable_predictions,
        )

        self.recommendations_engine = RecommendationsEngine(
            enable_personalization=enable_personalization,
            enable_ab_testing=enable_ab_testing,
            min_confidence=min_confidence,
        )

    def analyze(
        self,
        patterns: List[Dict[str, Any]],
        anomalies: Optional[List[Dict[str, Any]]] = None,
        session_context: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsResult:
        """
        Analyze patterns and anomalies to generate insights and recommendations.

        Args:
            patterns: List of detected patterns (dict format)
            anomalies: List of detected anomalies (optional, dict format)
            session_context: Current session context (optional)
            historical_data: Historical data for trend analysis (optional)
            user_context: User context data for personalization (optional)

        Returns:
            AnalyticsResult containing insights, recommendations, and metrics
        """
        # Generate insights
        insights = self.insights_generator.generate(
            patterns=patterns,
            anomalies=anomalies,
            session_context=session_context,
            historical_data=historical_data,
        )

        # Generate recommendations from insights
        recommendations = self.recommendations_engine.generate(
            insights=insights,
            user_context=user_context,
            session_context=session_context,
        )

        # Calculate aggregated metrics
        metrics = self._calculate_metrics(
            patterns=patterns,
            anomalies=anomalies,
            insights=insights,
            recommendations=recommendations,
        )

        # Generate summary
        summary = self._generate_summary(insights, recommendations)

        # Extract session/user IDs from context
        session_id = (
            session_context.get("session_id") if session_context else "unknown"
        )
        user_id = (
            user_context.get("user_id") if user_context else None
        ) or (session_context.get("user_id") if session_context else None)

        return AnalyticsResult(
            session_id=session_id,
            user_id=user_id,
            insights=insights,
            recommendations=recommendations,
            metrics=metrics,
            summary=summary,
            metadata={
                "patterns_count": len(patterns),
                "anomalies_count": len(anomalies) if anomalies else 0,
                "insights_count": len(insights),
                "recommendations_count": len(recommendations),
            },
        )

    def _calculate_metrics(
        self,
        patterns: List[Dict[str, Any]],
        anomalies: Optional[List[Dict[str, Any]]],
        insights: List,
        recommendations: List,
    ) -> Dict[str, Any]:
        """
        Calculate aggregated metrics from analysis.

        Args:
            patterns: List of patterns
            anomalies: List of anomalies
            insights: Generated insights
            recommendations: Generated recommendations

        Returns:
            Dictionary of aggregated metrics
        """
        metrics: Dict[str, Any] = {
            "total_patterns": len(patterns),
            "total_anomalies": len(anomalies) if anomalies else 0,
            "total_insights": len(insights),
            "total_recommendations": len(recommendations),
        }

        # Insight metrics
        if insights:
            metrics["insights"] = {
                "by_priority": {
                    "critical": len([i for i in insights if i.priority == "critical"]),
                    "high": len([i for i in insights if i.priority == "high"]),
                    "medium": len([i for i in insights if i.priority == "medium"]),
                    "low": len([i for i in insights if i.priority == "low"]),
                },
                "avg_confidence": sum(i.confidence for i in insights) / len(insights),
                "avg_impact": (
                    sum(i.estimated_impact for i in insights if i.estimated_impact)
                    / len([i for i in insights if i.estimated_impact])
                    if any(i.estimated_impact for i in insights)
                    else 0.0
                ),
            }

        # Recommendation metrics
        if recommendations:
            metrics["recommendations"] = {
                "by_priority": {
                    "critical": len(
                        [r for r in recommendations if r.priority == "critical"]
                    ),
                    "high": len([r for r in recommendations if r.priority == "high"]),
                    "medium": len(
                        [r for r in recommendations if r.priority == "medium"]
                    ),
                    "low": len([r for r in recommendations if r.priority == "low"]),
                },
                "avg_confidence": (
                    sum(r.confidence for r in recommendations) / len(recommendations)
                ),
                "avg_expected_impact": (
                    sum(
                        r.expected_impact
                        for r in recommendations
                        if r.expected_impact
                    )
                    / len([r for r in recommendations if r.expected_impact])
                    if any(r.expected_impact for r in recommendations)
                    else 0.0
                ),
            }

        # Pattern metrics
        if patterns:
            pattern_types = {}
            for pattern in patterns:
                pattern_type = pattern.get("type", "unknown")
                pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
            metrics["patterns"] = {
                "by_type": pattern_types,
                "avg_confidence": (
                    sum(
                        p.get("confidence", 0.0)
                        for p in patterns
                        if "confidence" in p
                    )
                    / len([p for p in patterns if "confidence" in p])
                    if any("confidence" in p for p in patterns)
                    else 0.0
                ),
            }

        # Anomaly metrics
        if anomalies:
            critical_anomalies = [
                a for a in anomalies if a.get("score", 0.0) > 0.9
            ]
            metrics["anomalies"] = {
                "critical_count": len(critical_anomalies),
                "avg_score": (
                    sum(a.get("score", 0.0) for a in anomalies) / len(anomalies)
                ),
            }

        return metrics

    def _generate_summary(
        self, insights: List, recommendations: List
    ) -> Optional[str]:
        """
        Generate human-readable summary of analysis.

        Args:
            insights: Generated insights
            recommendations: Generated recommendations

        Returns:
            Summary string
        """
        if not insights and not recommendations:
            return "No insights or recommendations generated."

        summary_parts = []

        # Insights summary
        if insights:
            critical = len([i for i in insights if i.priority == "critical"])
            high = len([i for i in insights if i.priority == "high"])
            summary_parts.append(
                f"Generated {len(insights)} insights ({critical} critical, {high} high priority)"
            )

        # Recommendations summary
        if recommendations:
            critical = len([r for r in recommendations if r.priority == "critical"])
            high = len([r for r in recommendations if r.priority == "high"])
            summary_parts.append(
                f"Generated {len(recommendations)} recommendations ({critical} critical, {high} high priority)"
            )

        return ". ".join(summary_parts) + "."

