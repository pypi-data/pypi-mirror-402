"""
Type definitions for inputless-models package.

Pydantic models for configurations and data structures.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# Configuration Models

class PatternRecognitionConfig(BaseModel):
    """Configuration for pattern recognition."""

    sequence_window: int = Field(10, ge=1, le=100, description="Window size for sequence patterns")
    temporal_resolution: str = Field(
        "1min", pattern=r"^\d+(min|hour|day)$", description="Temporal resolution for time-based patterns"
    )
    min_pattern_confidence: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for patterns"
    )
    pattern_types: List[str] = Field(
        default=["sequence", "temporal", "spatial", "behavioral", "correlation"],
        description="Types of patterns to recognize",
    )
    clustering_algorithm: str = Field(
        "dbscan", pattern="^(dbscan|kmeans|hierarchical)$", description="Clustering algorithm to use"
    )
    min_cluster_size: int = Field(3, ge=2, description="Minimum cluster size")


class PredictiveConfig(BaseModel):
    """Configuration for predictive models."""

    prediction_horizon: int = Field(7, ge=1, le=365, description="Prediction horizon in days")
    model_type: str = Field(
        "ensemble", pattern="^(ensemble|rf|gbm|lstm)$", description="Type of model to use"
    )
    features: List[str] = Field(
        default=["events", "patterns", "context"], description="Features to use for prediction"
    )
    retrain_frequency: str = Field(
        "weekly", pattern="^(daily|weekly|monthly)$", description="How often to retrain models"
    )
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for predictions"
    )


class AnomalyDetectionConfig(BaseModel):
    """Configuration for anomaly detection."""

    detection_method: str = Field(
        "ensemble", pattern="^(statistical|ml|ensemble)$", description="Detection method to use"
    )
    sensitivity: float = Field(0.8, ge=0.0, le=1.0, description="Detection sensitivity")
    real_time_enabled: bool = Field(True, description="Enable real-time detection")
    alert_threshold: float = Field(
        0.9, ge=0.0, le=1.0, description="Threshold for generating alerts"
    )
    window_size: int = Field(100, ge=10, le=1000, description="Window size for real-time detection")
    contamination: float = Field(
        0.1, ge=0.0, le=0.5, description="Expected proportion of anomalies"
    )


# Data Models

class Pattern(BaseModel):
    """Represents a recognized pattern."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: str = Field(..., description="Type of pattern (sequence, temporal, spatial, etc.)")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Events in the pattern")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Pattern confidence score")
    frequency: int = Field(..., ge=0, description="How often this pattern occurs")
    first_seen: datetime = Field(default_factory=datetime.now, description="When pattern was first seen")
    last_seen: datetime = Field(default_factory=datetime.now, description="When pattern was last seen")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional pattern metadata")


class Prediction(BaseModel):
    """Represents a prediction."""

    prediction_id: str = Field(..., description="Unique prediction identifier")
    prediction_type: str = Field(
        ..., description="Type of prediction (behavior, conversion, abandonment, churn, engagement)"
    )
    value: float = Field(..., description="Predicted value or probability")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence score")
    timestamp: datetime = Field(default_factory=datetime.now, description="When prediction was made")
    horizon: int = Field(..., ge=1, description="Prediction horizon in days")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional prediction metadata")


class Anomaly(BaseModel):
    """Represents a detected anomaly."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    event: Dict[str, Any] = Field(..., description="The anomalous event")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score (0-1)")
    anomaly_type: str = Field(..., description="Type of anomaly")
    detection_method: str = Field(..., description="Method used to detect the anomaly")
    timestamp: datetime = Field(default_factory=datetime.now, description="When anomaly was detected")
    severity: str = Field(
        "medium", pattern="^(low|medium|high|critical)$", description="Anomaly severity level"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional anomaly metadata")

