"""
Recommendation data model.

Represents an actionable recommendation generated from insights.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    """Types of recommendations."""

    # UX Recommendations
    UI_IMPROVEMENT = "ui_improvement"
    NAVIGATION_OPTIMIZATION = "navigation_optimization"
    CONTENT_PERSONALIZATION = "content_personalization"

    # Conversion Recommendations
    CONVERSION_OPTIMIZATION = "conversion_optimization"
    CHECKOUT_OPTIMIZATION = "checkout_optimization"
    PRICING_STRATEGY = "pricing_strategy"

    # Engagement Recommendations
    RE_ENGAGEMENT = "re_engagement"
    CONTENT_RECOMMENDATION = "content_recommendation"
    FEATURE_HIGHLIGHT = "feature_highlight"

    # Support Recommendations
    PROACTIVE_SUPPORT = "proactive_support"
    HELP_CONTENT = "help_content"
    TUTORIAL = "tutorial"

    # Performance Recommendations
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"

    # A/B Testing Recommendations
    AB_TEST_VARIANT = "ab_test_variant"
    FEATURE_FLAG = "feature_flag"


class Recommendation(BaseModel):
    """
    A recommendation generated from insights.

    Recommendations transform insights into concrete, implementable actions
    that can improve user experience, increase conversions, and optimize
    business outcomes.
    """

    id: str = Field(..., description="Unique recommendation identifier")
    type: RecommendationType = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    action: str = Field(..., description="Recommended action")

    # Priority and confidence
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Priority level",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )

    # Source insights (passed as dicts for flexibility)
    source_insights: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Source insights that generated this recommendation",
    )

    # Context
    session_id: Optional[str] = Field(None, description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Recommendation timestamp",
    )

    # Implementation details
    implementation: Dict[str, Any] = Field(
        default_factory=dict,
        description="Implementation details (e.g., A/B test config)",
    )

    # Expected impact
    expected_impact: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Expected impact score (0.0-1.0)",
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

