"""
Anomaly detection models for identifying unusual behaviors.

Supports statistical, ML-based, and ensemble detection methods.
"""

from typing import List, Dict, Any, Optional
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats
import uuid

# Optional pyod import
try:
    from pyod.models.iforest import IForest
    from pyod.models.lof import LOF
    PYOD_AVAILABLE = True
except ImportError:
    PYOD_AVAILABLE = False
    IForest = None
    LOF = None

from .types import AnomalyDetectionConfig, Anomaly


class AnomalyDetector:
    """
    Anomaly detection model for identifying unusual behaviors.

    Supports statistical, ML-based, and ensemble detection methods.
    """

    def __init__(self, config: AnomalyDetectionConfig):
        """
        Initialize anomaly detector.

        Args:
            config: Detector configuration

        Raises:
            ValueError: If ML method requested but pyod not available
        """
        self.config = config
        self.scaler = StandardScaler()
        self.statistical_model = None
        self.ml_model = None
        self.ensemble_models = []
        self.event_history: List[Dict[str, Any]] = []
        self.anomaly_history: List[Anomaly] = []

        if config.detection_method == "ml":
            if not PYOD_AVAILABLE:
                raise ValueError(
                    "pyod is required for ML-based anomaly detection. "
                    "Install it with: pip install pyod"
                )
            self.ml_model = IForest(contamination=config.contamination)
        elif config.detection_method == "ensemble":
            if not PYOD_AVAILABLE:
                raise ValueError(
                    "pyod is required for ensemble anomaly detection. "
                    "Install it with: pip install pyod"
                )
            self.ml_model = IForest(contamination=config.contamination)
            self.ensemble_models = [
                IForest(contamination=config.contamination),
                LOF(contamination=config.contamination),
            ]

    def detect(self, events: List[Dict[str, Any]]) -> List[Anomaly]:
        """
        Detect anomalies in events.

        Args:
            events: List of events

        Returns:
            List of detected anomalies
        """
        if not events:
            return []

        anomalies = []

        if self.config.detection_method == "statistical":
            anomalies.extend(self._detect_statistical(events))
        elif self.config.detection_method == "ml":
            anomalies.extend(self._detect_ml(events))
        elif self.config.detection_method == "ensemble":
            anomalies.extend(self._detect_ensemble(events))

        # Filter by sensitivity
        threshold = 1.0 - self.config.sensitivity
        anomalies = [a for a in anomalies if a.anomaly_score >= threshold]

        self.anomaly_history.extend(anomalies)
        return anomalies

    def detect_realtime(self, event: Dict[str, Any]) -> bool:
        """
        Detect anomaly in real-time for single event.

        Args:
            event: Single event

        Returns:
            True if anomaly detected
        """
        if not self.config.real_time_enabled:
            return False

        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.config.window_size:
            self.event_history.pop(0)

        # Need minimum events for detection
        if len(self.event_history) < 10:
            return False

        # Detect using recent history
        recent_events = self.event_history[-self.config.window_size :]
        anomalies = self.detect(recent_events)

        # Check if current event is anomalous
        for anomaly in anomalies:
            # Compare event IDs or content
            if self._events_match(anomaly.event, event):
                return anomaly.anomaly_score >= self.config.alert_threshold

        return False

    def _events_match(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> bool:
        """
        Check if two events match.

        Args:
            event1: First event
            event2: Second event

        Returns:
            True if events match
        """
        # Compare by ID if available, otherwise by type and timestamp
        if "id" in event1 and "id" in event2:
            return event1["id"] == event2["id"]
        return (
            event1.get("type") == event2.get("type")
            and event1.get("timestamp") == event2.get("timestamp")
        )

    def _detect_statistical(self, events: List[Dict[str, Any]]) -> List[Anomaly]:
        """Detect anomalies using statistical methods."""
        anomalies = []

        # Extract features
        features = self._extract_features(events)
        if len(features) == 0:
            return anomalies

        try:
            # Z-score method
            z_scores = np.abs(stats.zscore(features, axis=0, nan_policy="omit"))
            threshold = 3.0 * (1.0 - self.config.sensitivity)  # Adjust threshold

            for i, event in enumerate(events):
                if i < len(z_scores):
                    max_z_score = np.nanmax(z_scores[i]) if len(z_scores[i]) > 0 else 0
                    if max_z_score > threshold:
                        anomaly_score = min(1.0, max_z_score / 5.0)  # Normalize to [0, 1]
                        anomaly = Anomaly(
                            anomaly_id=f"statistical_{uuid.uuid4().hex[:8]}",
                            event=event,
                            anomaly_score=float(anomaly_score),
                            anomaly_type="statistical",
                            detection_method="z_score",
                            timestamp=datetime.now(),
                            severity=self._calculate_severity(anomaly_score),
                        )
                        anomalies.append(anomaly)
        except Exception:
            # Return empty list if statistical analysis fails
            return []

        return anomalies

    def _detect_ml(self, events: List[Dict[str, Any]]) -> List[Anomaly]:
        """Detect anomalies using ML methods."""
        anomalies = []

        if not PYOD_AVAILABLE:
            return anomalies

        # Extract features
        features = self._extract_features(events)
        if len(features) < 10:  # Need minimum samples
            return anomalies

        try:
            # Train model if needed
            if self.ml_model is None:
                self.ml_model = IForest(contamination=self.config.contamination)

            # Fit and predict
            scaled_features = self.scaler.fit_transform(features)
            self.ml_model.fit(scaled_features)
            predictions = self.ml_model.predict(scaled_features)
            scores = self.ml_model.decision_function(scaled_features)

            # Normalize scores to [0, 1]
            min_score = np.min(scores)
            max_score = np.max(scores)
            if max_score > min_score:
                normalized_scores = (scores - min_score) / (max_score - min_score)
            else:
                normalized_scores = scores

            # Create anomalies
            for i, event in enumerate(events):
                if i < len(predictions) and predictions[i] == 1:  # Anomaly
                    anomaly_score = float(normalized_scores[i])
                    anomaly = Anomaly(
                        anomaly_id=f"ml_{uuid.uuid4().hex[:8]}",
                        event=event,
                        anomaly_score=anomaly_score,
                        anomaly_type="ml",
                        detection_method="isolation_forest",
                        timestamp=datetime.now(),
                        severity=self._calculate_severity(anomaly_score),
                    )
                    anomalies.append(anomaly)
        except Exception:
            # Return empty list if ML detection fails
            return []

        return anomalies

    def _detect_ensemble(self, events: List[Dict[str, Any]]) -> List[Anomaly]:
        """Detect anomalies using ensemble methods."""
        anomalies = []

        if not PYOD_AVAILABLE:
            return anomalies

        # Extract features
        features = self._extract_features(events)
        if len(features) < 10:
            return anomalies

        try:
            # Train ensemble models
            scaled_features = self.scaler.fit_transform(features)
            predictions_list = []
            scores_list = []

            for model in self.ensemble_models:
                model.fit(scaled_features)
                predictions = model.predict(scaled_features)
                scores = model.decision_function(scaled_features)
                predictions_list.append(predictions)
                scores_list.append(scores)

            # Combine predictions (voting)
            predictions_array = np.array(predictions_list)
            ensemble_predictions = np.mean(predictions_array, axis=0) >= 0.5
            ensemble_scores = np.mean(scores_list, axis=0)

            # Normalize scores
            min_score = np.min(ensemble_scores)
            max_score = np.max(ensemble_scores)
            if max_score > min_score:
                normalized_scores = (ensemble_scores - min_score) / (max_score - min_score)
            else:
                normalized_scores = ensemble_scores

            # Create anomalies
            for i, event in enumerate(events):
                if i < len(ensemble_predictions) and ensemble_predictions[i]:
                    anomaly_score = float(normalized_scores[i])
                    anomaly = Anomaly(
                        anomaly_id=f"ensemble_{uuid.uuid4().hex[:8]}",
                        event=event,
                        anomaly_score=anomaly_score,
                        anomaly_type="ensemble",
                        detection_method="ensemble",
                        timestamp=datetime.now(),
                        severity=self._calculate_severity(anomaly_score),
                    )
                    anomalies.append(anomaly)
        except Exception:
            # Return empty list if ensemble detection fails
            return []

        return anomalies

    def _extract_features(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract features from events.

        Args:
            events: List of events

        Returns:
            Array of features
        """
        features = []
        for e in events:
            feature_vector = [
                float(e.get("duration", 0)),
                float(e.get("frequency", 0)),
                float(len(e.get("metadata", {}))),
                1.0 if e.get("type") == "click" else 0.0,
                1.0 if e.get("type") == "scroll" else 0.0,
                1.0 if e.get("type") == "error" else 0.0,
                1.0 if e.get("type") == "hover" else 0.0,
            ]
            features.append(feature_vector)

        return np.array(features) if features else np.array([]).reshape(0, 7)

    def _calculate_severity(self, anomaly_score: float) -> str:
        """
        Calculate anomaly severity.

        Args:
            anomaly_score: Anomaly score (0-1)

        Returns:
            Severity level
        """
        if anomaly_score >= 0.9:
            return "critical"
        elif anomaly_score >= 0.7:
            return "high"
        elif anomaly_score >= 0.5:
            return "medium"
        else:
            return "low"

    def create_alert(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create alert for anomalous event.

        Args:
            event: Anomalous event

        Returns:
            Alert dictionary
        """
        anomaly = next(
            (a for a in self.anomaly_history if self._events_match(a.event, event)),
            None,
        )

        if not anomaly:
            return {}

        return {
            "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
            "anomaly_id": anomaly.anomaly_id,
            "severity": anomaly.severity,
            "anomaly_score": anomaly.anomaly_score,
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "action_required": anomaly.severity in ["high", "critical"],
        }

    def train(
        self, training_data: List[Dict[str, Any]], labels: Optional[List[int]] = None
    ) -> None:
        """
        Train anomaly detection models.

        Args:
            training_data: Training events
            labels: Optional anomaly labels (1 = anomaly, 0 = normal)
        """
        features = self._extract_features(training_data)
        if len(features) == 0:
            return

        try:
            scaled_features = self.scaler.fit_transform(features)

            if self.ml_model and PYOD_AVAILABLE:
                self.ml_model.fit(scaled_features)

            for model in self.ensemble_models:
                if PYOD_AVAILABLE:
                    model.fit(scaled_features)
        except Exception:
            # Training failed, models remain untrained
            pass

    def save_model(self, filepath: str) -> None:
        """
        Save trained models to file.

        Args:
            filepath: Path to save models
        """
        import pickle

        model_data = {
            "ml_model": self.ml_model,
            "ensemble_models": self.ensemble_models,
            "scaler": self.scaler,
            "config": self.config.dict(),
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

    def load_model(self, filepath: str) -> None:
        """
        Load trained models from file.

        Args:
            filepath: Path to load models from

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        import pickle

        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)

            self.ml_model = model_data.get("ml_model")
            self.ensemble_models = model_data.get("ensemble_models", [])
            self.scaler = model_data.get("scaler", StandardScaler())
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Invalid model file format: {str(e)}") from e
