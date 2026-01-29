# inputless-analytics

Analytics engine for generating insights and recommendations from behavioral patterns and anomalies.

## Purpose

High-level analytics engine that transforms patterns, anomalies, and behavioral data into actionable insights and recommendations. Integrates with pattern recognition, predictive models, and graph analysis to provide intelligent analytics.

## Features

- **Insight Generation**: Transform patterns and anomalies into actionable insights
- **Recommendation Engine**: Generate personalized recommendations based on insights
- **Emotional State Analysis**: Detect frustration, confusion, engagement, and other emotional states
- **Predictive Analytics**: Predict conversion likelihood, churn risk, and engagement
- **Trend Analysis**: Identify behavioral trends over time
- **Real-time Processing**: Generate insights with <100ms latency for single sessions

## Installation

### Using Poetry (Development)

```bash
cd packages/python-core/analytics
poetry install
poetry run python example_usage.py
```

### Using pip (Production)

```bash
pip install inputless-analytics
```

## Dependencies

- `pydantic` - Data validation and models
- `numpy` - Numerical computing
- `pandas` - Data processing
- `scipy` - Statistical analysis
- `statsmodels` - Advanced statistics
- `scikit-learn` - Machine learning utilities
- `statsforecast` - Time series forecasting

## Usage

### Basic Usage

```python
from inputless_analytics import AnalyticsEngine

# Initialize analytics engine
engine = AnalyticsEngine(
    min_confidence=0.6,
    enable_trends=True,
    enable_predictions=True,
    enable_personalization=True,
)

# Example patterns (from context engine)
patterns = [
    {
        "id": "pattern-1",
        "type": "behavioral",
        "confidence": 0.85,
        "indicators": ["frustration", "rage_click"],
        "metadata": {},
    },
    {
        "id": "pattern-2",
        "type": "sequence",
        "confidence": 0.75,
        "indicators": ["product_view", "cart_add", "checkout_start"],
        "metadata": {"indicators": ["product_view", "cart_add", "checkout_start"]},
    },
]

# Example anomalies
anomalies = [
    {
        "id": "anomaly-1",
        "score": 0.92,
        "threshold": 0.7,
        "is_anomaly": True,
        "reason": "Unusual click pattern detected",
    }
]

# Session context
session_context = {
    "session_id": "session-123",
    "user_id": "user-456",
    "emotional_state": {
        "primary": "frustration",
        "confidence": 0.8,
    },
}

# Analyze and generate insights/recommendations
result = engine.analyze(
    patterns=patterns,
    anomalies=anomalies,
    session_context=session_context,
)

# Access results
print(f"Generated {len(result.insights)} insights")
print(f"Generated {len(result.recommendations)} recommendations")

# Process insights
for insight in result.insights:
    if insight.priority == "critical":
        print(f"Critical: {insight.message}")
        print(f"Actions: {insight.recommended_actions}")

# Process recommendations
for rec in result.recommendations:
    if rec.priority == "high":
        print(f"Recommendation: {rec.title}")
        print(f"Action: {rec.action}")
        print(f"Implementation: {rec.implementation}")
```

### Using Individual Components

```python
from inputless_analytics import InsightsGenerator, RecommendationsEngine

# Generate insights only
insights_generator = InsightsGenerator(
    min_confidence=0.6,
    enable_trends=True,
    enable_predictions=True,
)

insights = insights_generator.generate(
    patterns=patterns,
    anomalies=anomalies,
    session_context=session_context,
)

# Generate recommendations from insights
recommendations_engine = RecommendationsEngine(
    enable_personalization=True,
    enable_ab_testing=True,
)

recommendations = recommendations_engine.generate(
    insights=insights,
    user_context=user_context,
    session_context=session_context,
)
```

## Module Structure

```
src/
├── __init__.py              # Main exports
├── analytics_engine.py      # Main orchestrator
├── insights_generator.py    # Insight generation
├── recommendations.py       # Recommendation engine
├── trend_analyzer.py       # Advanced trend analysis
├── correlation_finder.py   # Correlation discovery
├── aggregators/
│   ├── __init__.py
│   ├── pattern_aggregator.py  # Pattern aggregation
│   ├── anomaly_aggregator.py  # Anomaly aggregation
│   └── trend_aggregator.py    # Trend aggregation
├── analyzers/
│   ├── __init__.py
│   ├── behavior_analyzer.py  # Behavioral analysis
│   ├── engagement_analyzer.py # Engagement analysis
│   ├── conversion_analyzer.py # Conversion analysis
│   └── retention_analyzer.py # Retention analysis
├── predictors/
│   ├── __init__.py
│   ├── behavior_predictor.py  # Behavior prediction
│   └── outcome_predictor.py   # Outcome prediction
├── models/
│   ├── __init__.py
│   ├── insight.py          # Insight data model
│   ├── recommendation.py   # Recommendation data model
│   └── analytics_result.py # Analytics result model
└── utils/
    ├── __init__.py
    └── scoring.py          # Scoring utilities
```

## Capabilities

### Insight Types

- **Behavioral Insights**: Frustration, confusion, engagement, abandonment
- **Performance Insights**: Performance issues, slow pages, error patterns
- **User Journey Insights**: Journey optimization, drop-off points, conversion blockers
- **Anomaly Insights**: Anomaly detection, security risks, fraud indicators
- **Predictive Insights**: Conversion prediction, churn prediction, engagement prediction

### Recommendation Types

- **UX Recommendations**: UI improvements, navigation optimization, content personalization
- **Conversion Recommendations**: Conversion optimization, checkout optimization, pricing strategy
- **Engagement Recommendations**: Re-engagement, content recommendations, feature highlights
- **Support Recommendations**: Proactive support, help content, tutorials
- **Performance Recommendations**: Performance optimization, resource optimization
- **A/B Testing Recommendations**: A/B test variants, feature flags

## Data Models

### Insight

```python
from inputless_analytics import Insight, InsightType

insight = Insight(
    id="insight-1",
    type=InsightType.FRUSTRATION,
    message="User frustration detected",
    description="User shows signs of frustration",
    confidence=0.85,
    priority="high",
    patterns=[...],
    recommended_actions=["Show help dialog", "Offer live chat"],
    estimated_impact=0.75,
)
```

### Recommendation

```python
from inputless_analytics import Recommendation, RecommendationType

recommendation = Recommendation(
    id="rec-1",
    type=RecommendationType.PROACTIVE_SUPPORT,
    title="Show Proactive Support",
    description="User shows signs of frustration - offer immediate help",
    action="Show help dialog or live chat",
    priority="high",
    confidence=0.85,
    implementation={
        "type": "ui_intervention",
        "component": "help_dialog",
        "trigger": "immediate",
    },
    expected_impact=0.75,
)
```

### Analytics Result

```python
from inputless_analytics import AnalyticsResult

result = AnalyticsResult(
    session_id="session-123",
    user_id="user-456",
    insights=[...],
    recommendations=[...],
    metrics={
        "total_patterns": 5,
        "total_anomalies": 1,
        "total_insights": 3,
        "total_recommendations": 2,
    },
    summary="Generated 3 insights (1 critical, 1 high priority)...",
)
```

## Integration

The analytics package integrates with:

- **inputless-context**: Receives patterns and anomalies from context engine
- **inputless-models**: Uses ML models for predictive analytics (future)
- **inputless-graph**: Uses graph data for correlation analysis (future)
- **inputless-engines**: Uses AI engines for advanced reasoning (future)

## Performance

- **Real-time Processing**: <100ms for single session analysis
- **Batch Processing**: Supports large-scale batch analysis
- **Scalability**: Handles high-volume pattern/anomaly data

## Distribution

**PyPI package**: `inputless-analytics`  
**Version**: 1.0.0+  
**Registry**: PyPI

## Advanced Features

### Aggregators

Aggregate patterns and anomalies for batch analysis:

```python
from inputless_analytics import PatternAggregator, AnomalyAggregator

# Aggregate patterns by type
pattern_agg = PatternAggregator()
aggregated = pattern_agg.aggregate(patterns, group_by="type")
stats = pattern_agg.get_statistics(patterns)

# Aggregate anomalies by reason
anomaly_agg = AnomalyAggregator()
aggregated = anomaly_agg.aggregate(anomalies, group_by="reason")
stats = anomaly_agg.get_statistics(anomalies)
```

### Analyzers

Specialized analyzers for different use cases:

```python
from inputless_analytics import (
    BehaviorAnalyzer,
    EngagementAnalyzer,
    ConversionAnalyzer,
    RetentionAnalyzer,
)

# Behavior analysis
behavior_analyzer = BehaviorAnalyzer()
behavior_analysis = behavior_analyzer.analyze(patterns, session_context)
print(f"Engagement: {behavior_analysis['engagement_level']}")
print(f"Frustration: {behavior_analysis['frustration_level']}")

# Engagement analysis
engagement_analyzer = EngagementAnalyzer()
engagement_analysis = engagement_analyzer.analyze(patterns, session_context)
print(f"Engagement score: {engagement_analysis['engagement_score']}")
print(f"Trend: {engagement_analysis['engagement_trend']}")

# Conversion analysis
conversion_analyzer = ConversionAnalyzer()
conversion_analysis = conversion_analyzer.analyze(patterns, session_context)
print(f"Conversion probability: {conversion_analysis['conversion_probability']}")
print(f"Funnel stage: {conversion_analysis['funnel_stage']}")

# Retention analysis
retention_analyzer = RetentionAnalyzer()
retention_analysis = retention_analyzer.analyze(patterns, session_context)
print(f"Churn risk: {retention_analysis['churn_risk']}")
print(f"Retention probability: {retention_analysis['retention_probability']}")
```

### Predictors

Predict future behavior and outcomes:

```python
from inputless_analytics import BehaviorPredictor, OutcomePredictor

# Behavior prediction
behavior_predictor = BehaviorPredictor()
predictions = behavior_predictor.predict(patterns, session_context)
print(f"Next action: {predictions['next_action_probability']}")
print(f"Session duration: {predictions['session_duration']} minutes")

# Outcome prediction
outcome_predictor = OutcomePredictor()
outcomes = outcome_predictor.predict(patterns, session_context)
print(f"Conversion probability: {outcomes['conversion_probability']}")
print(f"Estimated revenue: ${outcomes['revenue_estimate']:.2f}")
print(f"CLV estimate: ${outcomes['lifetime_value_estimate']:.2f}")
```

### Trend Analysis

Analyze trends over time:

```python
from inputless_analytics import TrendAnalyzer
from datetime import timedelta

trend_analyzer = TrendAnalyzer()
trends = trend_analyzer.analyze(
    current_data=current_patterns,
    historical_data=historical_patterns,
    time_window=timedelta(days=7),
)

print(f"Trend direction: {trends['trend_direction']}")
print(f"Trend strength: {trends['trend_strength']}")
for pattern_type, type_data in trends['by_type'].items():
    print(f"{pattern_type}: {type_data['direction']} ({type_data['change_percent']:.1f}%)")
```

### Correlation Discovery

Find correlations between patterns and outcomes:

```python
from inputless_analytics import CorrelationFinder

correlation_finder = CorrelationFinder()
correlations = correlation_finder.find(
    patterns=patterns,
    anomalies=anomalies,
    outcomes=outcomes,
)

print(f"Pattern correlations: {correlations['pattern_correlations']}")
print(f"Anomaly correlations: {correlations['anomaly_correlations']}")
print(f"Pattern-outcome correlations: {correlations['pattern_outcome_correlations']}")
```

## Examples

See `src/example_usage.py` for complete usage examples including:
- Basic usage
- Frustration detection
- Conversion optimization

