"""
Insight data model.

Represents an actionable insight generated from patterns, anomalies, and behavioral data.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class InsightType(str, Enum):
    """Types of insights that can be generated."""

    # Behavioral Insights
    FRUSTRATION = "frustration"
    CONFUSION = "confusion"
    ENGAGEMENT = "engagement"
    ABANDONMENT = "abandonment"
    CONVERSION_INTENT = "conversion_intent"
    CHURN_RISK = "churn_risk"

    # Performance Insights
    PERFORMANCE_ISSUE = "performance_issue"
    SLOW_PAGE = "slow_page"
    ERROR_PATTERN = "error_pattern"

    # User Journey Insights
    JOURNEY_OPTIMIZATION = "journey_optimization"
    DROP_OFF_POINT = "drop_off_point"
    CONVERSION_BLOCKER = "conversion_blocker"

    # Engagement Insights
    HIGH_ENGAGEMENT = "high_engagement"
    LOW_ENGAGEMENT = "low_engagement"
    CONTENT_PREFERENCE = "content_preference"

    # Anomaly Insights
    ANOMALY_DETECTED = "anomaly_detected"
    SECURITY_RISK = "security_risk"
    FRAUD_INDICATOR = "fraud_indicator"

    # Predictive Insights
    CONVERSION_PREDICTION = "conversion_prediction"
    CHURN_PREDICTION = "churn_prediction"
    ENGAGEMENT_PREDICTION = "engagement_prediction"


class Insight(BaseModel):
    """
    An actionable insight generated from patterns and anomalies.

    Insights transform raw pattern/anomaly data into human-readable,
    actionable intelligence that can be used to improve user experience,
    optimize conversions, and prevent issues.
    """

    id: str = Field(..., description="Unique insight identifier")
    type: InsightType = Field(..., description="Type of insight")
    message: str = Field(..., description="Human-readable insight message")
    description: Optional[str] = Field(
        None, description="Detailed description of the insight"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Priority level",
    )

    # Source data (patterns and anomalies are passed as dicts for flexibility)
    # In production, these would be proper Pattern/AnomalyScore objects
    patterns: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Source patterns that generated this insight",
    )
    anomaly_scores: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Source anomaly scores that generated this insight",
    )

    # Context
    session_id: Optional[str] = Field(None, description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Insight timestamp",
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    # Recommendations
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended actions based on this insight",
    )

    # Impact
    estimated_impact: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Estimated impact score (0.0-1.0)",
    )

    # Trend
    trend: Optional[Literal["increasing", "decreasing", "stable"]] = Field(
        None,
        description="Trend direction",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

