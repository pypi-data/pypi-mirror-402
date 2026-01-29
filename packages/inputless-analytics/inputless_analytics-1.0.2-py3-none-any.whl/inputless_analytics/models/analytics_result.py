"""
Analytics result data model.

Represents the complete result of analytics processing including
insights, recommendations, and aggregated metrics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .insight import Insight
from .recommendation import Recommendation


class AnalyticsResult(BaseModel):
    """
    Complete analytics result containing insights and recommendations.

    This is the main output of the analytics engine, containing all
    generated insights, recommendations, and aggregated metrics for
    a session or batch of events.
    """

    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp",
    )

    # Generated insights
    insights: List[Insight] = Field(
        default_factory=list,
        description="Generated insights",
    )

    # Generated recommendations
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Generated recommendations",
    )

    # Aggregated metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated metrics",
    )

    # Analysis summary
    summary: Optional[str] = Field(None, description="Analysis summary")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

