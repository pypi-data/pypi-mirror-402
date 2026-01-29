"""
inputless-models - Main exports

ML-powered models for pattern recognition, predictive analytics, and anomaly detection.
"""

from .pattern_recognition import PatternRecognitionModel
from .predictive_analytics import PredictiveModel
from .anomaly_detection import AnomalyDetector
from .model_training import ModelTrainer

# Type definitions
from .types import (
    PatternRecognitionConfig,
    PredictiveConfig,
    AnomalyDetectionConfig,
    Pattern,
    Prediction,
    Anomaly,
)

# Feature implementations
try:
    from .features import (
        PredictiveBehaviorModel,
        BehavioralDNAProfiler,
        BehavioralAnomalyAlerts,
    )

    __all__ = [
        # Main models
        "PatternRecognitionModel",
        "PredictiveModel",
        "AnomalyDetector",
        "ModelTrainer",
        # Configuration classes
        "PatternRecognitionConfig",
        "PredictiveConfig",
        "AnomalyDetectionConfig",
        # Data models
        "Pattern",
        "Prediction",
        "Anomaly",
        # Advanced features
        "PredictiveBehaviorModel",
        "BehavioralDNAProfiler",
        "BehavioralAnomalyAlerts",
    ]
except ImportError:
    # Features not yet fully implemented
    __all__ = [
        # Main models
        "PatternRecognitionModel",
        "PredictiveModel",
        "AnomalyDetector",
        "ModelTrainer",
        # Configuration classes
        "PatternRecognitionConfig",
        "PredictiveConfig",
        "AnomalyDetectionConfig",
        # Data models
        "Pattern",
        "Prediction",
        "Anomaly",
    ]

