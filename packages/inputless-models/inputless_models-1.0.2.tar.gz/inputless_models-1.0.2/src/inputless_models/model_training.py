"""
Model training utilities for inputless-models package.

Provides utilities for training, validation, and model management.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score

from .pattern_recognition import PatternRecognitionModel
from .predictive_analytics import PredictiveModel
from .anomaly_detection import AnomalyDetector
from .types import (
    PatternRecognitionConfig,
    PredictiveConfig,
    AnomalyDetectionConfig,
)


class ModelTrainer:
    """
    Utility class for training and validating models.
    """

    def __init__(self):
        """Initialize model trainer."""
        self.training_history: List[Dict[str, Any]] = []

    def train_pattern_model(
        self,
        training_data: List[Dict[str, Any]],
        labels: Optional[List[str]] = None,
        config: Optional[PatternRecognitionConfig] = None,
        test_size: float = 0.2,
    ) -> Tuple[PatternRecognitionModel, Dict[str, float]]:
        """
        Train pattern recognition model.

        Args:
            training_data: Training events
            labels: Optional pattern labels
            config: Model configuration
            test_size: Proportion of data for testing

        Returns:
            Tuple of (trained model, metrics)
        """
        if config is None:
            config = PatternRecognitionConfig()

        model = PatternRecognitionModel(config)

        # Split data if labels provided
        if labels and len(labels) == len(training_data):
            train_data, test_data, train_labels, test_labels = train_test_split(
                training_data, labels, test_size=test_size, random_state=42
            )
            model.train(train_data, train_labels)
        else:
            model.train(training_data, labels)

        # Calculate metrics (simplified)
        metrics = {
            "training_samples": len(training_data),
            "known_sequences": len(model.known_sequences),
        }

        self.training_history.append(
            {
                "model_type": "pattern_recognition",
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
            }
        )

        return model, metrics

    def train_predictive_model(
        self,
        training_data: List[List[Dict[str, Any]]],
        labels: Dict[str, List[Any]],
        config: Optional[PredictiveConfig] = None,
        test_size: float = 0.2,
    ) -> Tuple[PredictiveModel, Dict[str, Dict[str, float]]]:
        """
        Train predictive model.

        Args:
            training_data: List of event lists (one per sample)
            labels: Labels for different prediction types
            config: Model configuration
            test_size: Proportion of data for testing

        Returns:
            Tuple of (trained model, metrics dictionary)
        """
        if config is None:
            config = PredictiveConfig()

        model = PredictiveModel(config)

        # Split data
        if len(training_data) > 1:
            train_data, test_data = train_test_split(
                training_data, test_size=test_size, random_state=42
            )

            # Split labels accordingly
            train_labels = {}
            test_labels = {}
            for label_type, label_values in labels.items():
                if len(label_values) == len(training_data):
                    train_labels[label_type], test_labels[label_type] = train_test_split(
                        label_values, test_size=test_size, random_state=42
                    )
        else:
            train_data = training_data
            test_data = []
            train_labels = labels
            test_labels = {}

        # Train model
        model.train(train_data, train_labels)

        # Calculate metrics
        metrics = {}
        for label_type in train_labels.keys():
            if test_data and label_type in test_labels:
                # Evaluate on test set
                test_predictions = []
                for events in test_data:
                    if label_type == "conversion":
                        pred = model.predict_conversion(events)
                    elif label_type == "churn":
                        pred = model.predict_churn(events)
                    elif label_type == "abandonment":
                        pred = model.predict_abandonment(events)
                    elif label_type == "behavior":
                        pred = model.predict_behavior(events)
                    elif label_type == "engagement":
                        pred = model.predict_engagement(events)
                    else:
                        continue

                    test_predictions.append(pred.value)

                if test_predictions:
                    # Calculate regression or classification metrics
                    if label_type in ["abandonment", "behavior", "engagement"]:
                        mse = mean_squared_error(test_labels[label_type], test_predictions)
                        r2 = r2_score(test_labels[label_type], test_predictions)
                        metrics[label_type] = {"mse": float(mse), "r2": float(r2)}
                    else:
                        # Classification metrics
                        pred_binary = [1 if p > 0.5 else 0 for p in test_predictions]
                        acc = accuracy_score(test_labels[label_type], pred_binary)
                        prec = precision_score(
                            test_labels[label_type], pred_binary, zero_division=0
                        )
                        rec = recall_score(test_labels[label_type], pred_binary, zero_division=0)
                        f1 = f1_score(test_labels[label_type], pred_binary, zero_division=0)
                        metrics[label_type] = {
                            "accuracy": float(acc),
                            "precision": float(prec),
                            "recall": float(rec),
                            "f1": float(f1),
                        }

        self.training_history.append(
            {
                "model_type": "predictive",
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
            }
        )

        return model, metrics

    def train_anomaly_detector(
        self,
        training_data: List[Dict[str, Any]],
        labels: Optional[List[int]] = None,
        config: Optional[AnomalyDetectionConfig] = None,
        test_size: float = 0.2,
    ) -> Tuple[AnomalyDetector, Dict[str, float]]:
        """
        Train anomaly detector.

        Args:
            training_data: Training events
            labels: Optional anomaly labels (1 = anomaly, 0 = normal)
            config: Detector configuration
            test_size: Proportion of data for testing

        Returns:
            Tuple of (trained detector, metrics)
        """
        if config is None:
            config = AnomalyDetectionConfig()

        detector = AnomalyDetector(config)

        # Initialize test_data and test_labels
        test_data = []
        test_labels = []

        # Split data if labels provided
        if labels and len(labels) == len(training_data):
            train_data, test_data, train_labels, test_labels = train_test_split(
                training_data, labels, test_size=test_size, random_state=42
            )
            detector.train(train_data, train_labels)
        else:
            detector.train(training_data, labels)

        # Calculate metrics
        metrics = {
            "training_samples": len(training_data),
            "anomaly_rate": sum(labels) / len(labels) if labels else 0.0,
        }

        if test_data and test_labels:
            # Evaluate on test set
            test_anomalies = detector.detect(test_data)
            predicted_labels = [
                1 if any(detector._events_match(a.event, e) for a in test_anomalies) else 0
                for e in test_data
            ]

            if predicted_labels:
                acc = accuracy_score(test_labels, predicted_labels)
                prec = precision_score(test_labels, predicted_labels, zero_division=0)
                rec = recall_score(test_labels, predicted_labels, zero_division=0)
                f1 = f1_score(test_labels, predicted_labels, zero_division=0)

                metrics.update(
                    {
                        "test_accuracy": float(acc),
                        "test_precision": float(prec),
                        "test_recall": float(rec),
                        "test_f1": float(f1),
                    }
                )

        self.training_history.append(
            {
                "model_type": "anomaly_detection",
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
            }
        )

        return detector, metrics

    def get_training_history(self) -> List[Dict[str, Any]]:
        """
        Get training history.

        Returns:
            List of training records
        """
        return self.training_history.copy()

    def clear_history(self) -> None:
        """Clear training history."""
        self.training_history.clear()

