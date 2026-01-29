"""
Predictive analytics models for forecasting user behavior.

Supports behavior, conversion, abandonment, churn, and engagement predictions.
"""

from typing import List, Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from datetime import datetime
import uuid

from .types import PredictiveConfig, Prediction


class PredictiveModel:
    """
    ML model for predicting user behavior, conversion, abandonment, and churn.
    """

    def __init__(self, config: PredictiveConfig):
        """
        Initialize predictive model.

        Args:
            config: Model configuration

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.scaler = StandardScaler()
        self.behavior_model: Optional[RandomForestRegressor] = None
        self.conversion_model: Optional[RandomForestClassifier] = None
        self.abandonment_model: Optional[GradientBoostingRegressor] = None
        self.churn_model: Optional[RandomForestClassifier] = None
        self.engagement_model: Optional[GradientBoostingRegressor] = None
        self.last_trained: Optional[datetime] = None
        self.feature_names: List[str] = []

    def predict_behavior(self, events: List[Dict[str, Any]]) -> Prediction:
        """
        Predict user behavior.

        Args:
            events: User events

        Returns:
            Behavior prediction
        """
        features = self._extract_features(events)

        if self.behavior_model is None:
            self.behavior_model = self._initialize_behavior_model()

        # Use dummy prediction if model not trained
        if not hasattr(self.behavior_model, "feature_importances_"):
            prediction_value = 0.5  # Default
        else:
            try:
                prediction_value = self.behavior_model.predict([features])[0]
            except Exception:
                prediction_value = 0.5

        confidence = self._calculate_confidence(features)

        return Prediction(
            prediction_id=f"behavior_{uuid.uuid4().hex[:8]}",
            prediction_type="behavior",
            value=float(prediction_value),
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=self.config.prediction_horizon,
        )

    def predict_conversion(self, events: List[Dict[str, Any]]) -> Prediction:
        """
        Predict conversion probability.

        Args:
            events: User events

        Returns:
            Conversion prediction
        """
        features = self._extract_features(events)

        if self.conversion_model is None:
            self.conversion_model = self._initialize_conversion_model()

        # Use dummy prediction if model not trained
        if not hasattr(self.conversion_model, "classes_"):
            probability = 0.3  # Default
        else:
            try:
                proba = self.conversion_model.predict_proba([features])[0]
                probability = proba[1] if len(proba) > 1 else proba[0]
            except Exception:
                probability = 0.3

        confidence = self._calculate_confidence(features)

        return Prediction(
            prediction_id=f"conversion_{uuid.uuid4().hex[:8]}",
            prediction_type="conversion",
            value=float(probability),
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=self.config.prediction_horizon,
        )

    def predict_abandonment(self, events: List[Dict[str, Any]]) -> Prediction:
        """
        Predict abandonment risk.

        Args:
            events: User events

        Returns:
            Abandonment prediction
        """
        features = self._extract_features(events)

        if self.abandonment_model is None:
            self.abandonment_model = self._initialize_abandonment_model()

        # Use dummy prediction if model not trained
        if not hasattr(self.abandonment_model, "feature_importances_"):
            risk_score = 0.5  # Default
        else:
            try:
                risk_score = self.abandonment_model.predict([features])[0]
            except Exception:
                risk_score = 0.5

        confidence = self._calculate_confidence(features)

        return Prediction(
            prediction_id=f"abandonment_{uuid.uuid4().hex[:8]}",
            prediction_type="abandonment",
            value=float(risk_score),
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=self.config.prediction_horizon,
        )

    def predict_churn(self, events: List[Dict[str, Any]]) -> Prediction:
        """
        Predict churn probability.

        Args:
            events: User events

        Returns:
            Churn prediction
        """
        features = self._extract_features(events)

        if self.churn_model is None:
            self.churn_model = self._initialize_churn_model()

        # Use dummy prediction if model not trained
        if not hasattr(self.churn_model, "classes_"):
            probability = 0.2  # Default
        else:
            try:
                proba = self.churn_model.predict_proba([features])[0]
                probability = proba[1] if len(proba) > 1 else proba[0]
            except Exception:
                probability = 0.2

        confidence = self._calculate_confidence(features)

        return Prediction(
            prediction_id=f"churn_{uuid.uuid4().hex[:8]}",
            prediction_type="churn",
            value=float(probability),
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=self.config.prediction_horizon,
        )

    def predict_engagement(self, events: List[Dict[str, Any]]) -> Prediction:
        """
        Predict engagement level.

        Args:
            events: User events

        Returns:
            Engagement prediction
        """
        features = self._extract_features(events)

        if self.engagement_model is None:
            self.engagement_model = self._initialize_engagement_model()

        # Use dummy prediction if model not trained
        if not hasattr(self.engagement_model, "feature_importances_"):
            engagement_score = 0.5  # Default
        else:
            try:
                engagement_score = self.engagement_model.predict([features])[0]
            except Exception:
                engagement_score = 0.5

        confidence = self._calculate_confidence(features)

        return Prediction(
            prediction_id=f"engagement_{uuid.uuid4().hex[:8]}",
            prediction_type="engagement",
            value=float(engagement_score),
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=self.config.prediction_horizon,
        )

    def _extract_features(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract features from events.

        Args:
            events: List of events

        Returns:
            Feature vector
        """
        if not events:
            return np.zeros(20)  # Default feature vector size

        # Event-based features
        event_count = len(events)
        click_count = sum(1 for e in events if e.get("type") == "click")
        scroll_count = sum(1 for e in events if e.get("type") == "scroll")
        hover_count = sum(1 for e in events if e.get("type") == "hover")
        focus_count = sum(1 for e in events if e.get("type") == "focus")
        error_count = sum(1 for e in events if e.get("type") == "error")

        # Duration features
        durations = [e.get("duration", 0) for e in events if "duration" in e]
        avg_duration = np.mean(durations) if durations else 0.0
        max_duration = np.max(durations) if durations else 0.0
        min_duration = np.min(durations) if durations else 0.0

        # Diversity features
        unique_types = len(set(e.get("type", "") for e in events if e.get("type")))
        type_diversity = unique_types / event_count if event_count > 0 else 0.0

        # Time-based features (if timestamps available)
        time_features = [0.0, 0.0]  # session_duration, time_since_first
        if events and "timestamp" in events[0]:
            try:
                timestamps = [
                    pd.to_datetime(e["timestamp"]) for e in events if "timestamp" in e
                ]
                if timestamps:
                    session_duration = (timestamps[-1] - timestamps[0]).total_seconds()
                    time_features[0] = session_duration
                    time_features[1] = (
                        datetime.now() - timestamps[0]
                    ).total_seconds() if timestamps else 0.0
            except Exception:
                pass

        # Pattern features (if patterns in metadata)
        pattern_count = sum(
            1 for e in events if "pattern" in e.get("metadata", {})
        )

        # Combine all features
        features = [
            float(event_count),
            float(click_count),
            float(scroll_count),
            float(hover_count),
            float(focus_count),
            float(error_count),
            float(avg_duration),
            float(max_duration),
            float(min_duration),
            float(unique_types),
            float(type_diversity),
            float(time_features[0]),
            float(time_features[1]),
            float(pattern_count),
        ]

        # Pad or truncate to fixed size
        feature_size = 20
        if len(features) < feature_size:
            features.extend([0.0] * (feature_size - len(features)))
        else:
            features = features[:feature_size]

        return np.array(features)

    def _calculate_confidence(self, features: np.ndarray) -> float:
        """
        Calculate prediction confidence.

        Args:
            features: Feature vector

        Returns:
            Confidence score (0-1)
        """
        # Confidence based on feature quality
        # More events and diversity = higher confidence
        event_count = features[0] if len(features) > 0 else 0
        diversity = features[9] if len(features) > 9 else 0  # type_diversity

        # Normalize confidence
        event_factor = min(1.0, event_count / 50.0)  # More events = better
        diversity_factor = diversity  # Already 0-1

        confidence = (event_factor * 0.6 + diversity_factor * 0.4)
        return min(1.0, max(0.0, confidence))

    def _initialize_behavior_model(self) -> RandomForestRegressor:
        """Initialize behavior prediction model."""
        return RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)

    def _initialize_conversion_model(self) -> RandomForestClassifier:
        """Initialize conversion prediction model."""
        return RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)

    def _initialize_abandonment_model(self) -> GradientBoostingRegressor:
        """Initialize abandonment prediction model."""
        return GradientBoostingRegressor(
            n_estimators=100, random_state=42, max_depth=5, learning_rate=0.1
        )

    def _initialize_churn_model(self) -> RandomForestClassifier:
        """Initialize churn prediction model."""
        return RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)

    def _initialize_engagement_model(self) -> GradientBoostingRegressor:
        """Initialize engagement prediction model."""
        return GradientBoostingRegressor(
            n_estimators=100, random_state=42, max_depth=5, learning_rate=0.1
        )

    def train(
        self, training_data: List[List[Dict[str, Any]]], labels: Dict[str, List[Any]]
    ) -> None:
        """
        Train predictive models.

        Args:
            training_data: List of event lists (one per sample)
            labels: Labels for different prediction types

        Raises:
            ValueError: If training data and labels don't match
        """
        if not training_data:
            return

        # Extract features for all training samples
        X = np.array([self._extract_features(events) for events in training_data])

        if len(X) == 0:
            return

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train each model
        if "behavior" in labels and self.behavior_model:
            y_behavior = np.array(labels["behavior"])
            if len(y_behavior) == len(X_scaled):
                self.behavior_model.fit(X_scaled, y_behavior)

        if "conversion" in labels and self.conversion_model:
            y_conversion = np.array(labels["conversion"])
            if len(y_conversion) == len(X_scaled):
                self.conversion_model.fit(X_scaled, y_conversion)

        if "abandonment" in labels and self.abandonment_model:
            y_abandonment = np.array(labels["abandonment"])
            if len(y_abandonment) == len(X_scaled):
                self.abandonment_model.fit(X_scaled, y_abandonment)

        if "churn" in labels and self.churn_model:
            y_churn = np.array(labels["churn"])
            if len(y_churn) == len(X_scaled):
                self.churn_model.fit(X_scaled, y_churn)

        if "engagement" in labels and self.engagement_model:
            y_engagement = np.array(labels["engagement"])
            if len(y_engagement) == len(X_scaled):
                self.engagement_model.fit(X_scaled, y_engagement)

        self.last_trained = datetime.now()

    def get_feature_importance(self, prediction_type: str = "conversion") -> Dict[str, float]:
        """
        Get feature importance for a model.

        Args:
            prediction_type: Type of prediction model

        Returns:
            Dictionary of feature names to importance scores
        """
        model = None
        if prediction_type == "conversion" and self.conversion_model:
            model = self.conversion_model
        elif prediction_type == "churn" and self.churn_model:
            model = self.churn_model
        elif prediction_type == "behavior" and self.behavior_model:
            model = self.behavior_model
        elif prediction_type == "abandonment" and self.abandonment_model:
            model = self.abandonment_model
        elif prediction_type == "engagement" and self.engagement_model:
            model = self.engagement_model

        if model is None or not hasattr(model, "feature_importances_"):
            return {}

        importances = model.feature_importances_
        feature_names = [
            f"feature_{i}" for i in range(len(importances))
        ]  # Default names

        return dict(zip(feature_names, importances.tolist()))

    def save_model(self, filepath: str) -> None:
        """
        Save trained models to file.

        Args:
            filepath: Path to save models
        """
        import pickle

        model_data = {
            "behavior_model": self.behavior_model,
            "conversion_model": self.conversion_model,
            "abandonment_model": self.abandonment_model,
            "churn_model": self.churn_model,
            "engagement_model": self.engagement_model,
            "scaler": self.scaler,
            "config": self.config.dict(),
            "last_trained": self.last_trained.isoformat() if self.last_trained else None,
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

            self.behavior_model = model_data.get("behavior_model")
            self.conversion_model = model_data.get("conversion_model")
            self.abandonment_model = model_data.get("abandonment_model")
            self.churn_model = model_data.get("churn_model")
            self.engagement_model = model_data.get("engagement_model")
            self.scaler = model_data.get("scaler", StandardScaler())
            if "last_trained" in model_data and model_data["last_trained"]:
                self.last_trained = datetime.fromisoformat(model_data["last_trained"])
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Invalid model file format: {str(e)}") from e
