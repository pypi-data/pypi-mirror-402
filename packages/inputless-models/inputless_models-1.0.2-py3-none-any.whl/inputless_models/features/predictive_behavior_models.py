"""
Predictive Behavior Models

Predict user actions before they happen, not just analyze what already occurred.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field

from ..predictive_analytics import PredictiveModel, PredictiveConfig
from ..types import Prediction


class NextActionPrediction(BaseModel):
    """Represents a next action prediction."""

    action_type: str = Field(..., description="Predicted action type")
    probability: float = Field(..., ge=0.0, le=1.0, description="Prediction probability")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionOutcomePrediction(BaseModel):
    """Represents a session outcome prediction."""

    outcome: str = Field(..., description="Predicted outcome (convert, abandon, browse, etc.)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Outcome probability")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.now)


class PredictiveBehaviorModel:
    """
    Predictive behavior model for forecasting user actions.

    Uses sequence patterns and behavioral analysis to predict next actions
    and session outcomes.
    """

    def __init__(self, config: Optional[PredictiveConfig] = None):
        """
        Initialize predictive behavior model.

        Args:
            config: Model configuration
        """
        if config is None:
            config = PredictiveConfig()

        self.config = config
        self.predictive_model = PredictiveModel(config)
        self.action_sequences: Dict[str, int] = {}  # sequence -> frequency
        self.outcome_patterns: Dict[str, float] = {}  # pattern -> outcome_probability

    def predict_next_action(
        self, events: List[Dict[str, Any]], top_k: int = 5
    ) -> List[NextActionPrediction]:
        """
        Predict next user action.

        Args:
            events: Current event sequence
            top_k: Number of top predictions to return

        Returns:
            List of next action predictions
        """
        if not events:
            return []

        # Extract recent sequence
        recent_events = events[-10:] if len(events) > 10 else events
        sequence = [e.get("type", "") for e in recent_events]
        sequence_str = "->".join(sequence)

        # Find similar sequences in history
        similar_sequences = self._find_similar_sequences(sequence_str)

        # Predict next action based on patterns
        predictions = []
        for next_action, probability in similar_sequences.items():
            confidence = self._calculate_action_confidence(sequence, next_action)
            predictions.append(
                NextActionPrediction(
                    action_type=next_action,
                    probability=probability,
                    confidence=confidence,
                )
            )

        # Sort by probability and return top_k
        predictions.sort(key=lambda x: x.probability, reverse=True)
        return predictions[:top_k]

    def predict_session_outcome(
        self, events: List[Dict[str, Any]]
    ) -> SessionOutcomePrediction:
        """
        Predict session outcome.

        Args:
            events: Session events

        Returns:
            Session outcome prediction
        """
        # Use predictive model for conversion/abandonment
        conversion_pred = self.predictive_model.predict_conversion(events)
        abandonment_pred = self.predictive_model.predict_abandonment(events)

        # Determine most likely outcome
        outcomes = {
            "convert": conversion_pred.value,
            "abandon": abandonment_pred.value,
            "browse": 1.0 - max(conversion_pred.value, abandonment_pred.value),
        }

        most_likely = max(outcomes.items(), key=lambda x: x[1])

        return SessionOutcomePrediction(
            outcome=most_likely[0],
            probability=most_likely[1],
            confidence=(conversion_pred.confidence + abandonment_pred.confidence) / 2.0,
        )

    def _find_similar_sequences(
        self, sequence: str
    ) -> Dict[str, float]:
        """
        Find similar sequences and their next actions.

        Args:
            sequence: Current sequence

        Returns:
            Dictionary of next_action -> probability
        """
        # Simple pattern matching based on sequence history
        # In production, this would use more sophisticated sequence alignment

        next_actions = {}
        for seq, frequency in self.action_sequences.items():
            if sequence in seq or self._sequences_similar(sequence, seq):
                # Extract next action from sequence
                parts = seq.split("->")
                if len(parts) > len(sequence.split("->")):
                    next_action = parts[len(sequence.split("->"))]
                    # Weight by frequency
                    if next_action not in next_actions:
                        next_actions[next_action] = 0.0
                    next_actions[next_action] += frequency

        # Normalize probabilities
        total = sum(next_actions.values())
        if total > 0:
            next_actions = {k: v / total for k, v in next_actions.items()}

        return next_actions

    def _sequences_similar(self, seq1: str, seq2: str, threshold: float = 0.7) -> bool:
        """
        Check if two sequences are similar.

        Args:
            seq1: First sequence
            seq2: Second sequence
            threshold: Similarity threshold

        Returns:
            True if sequences are similar
        """
        parts1 = seq1.split("->")
        parts2 = seq2.split("->")

        # Check if seq1 is a prefix of seq2
        if len(parts1) <= len(parts2):
            matches = sum(1 for a, b in zip(parts1, parts2) if a == b)
            similarity = matches / len(parts1) if parts1 else 0.0
            return similarity >= threshold

        return False

    def _calculate_action_confidence(
        self, sequence: List[str], next_action: str
    ) -> float:
        """
        Calculate confidence for next action prediction.

        Args:
            sequence: Current sequence
            next_action: Predicted next action

        Returns:
            Confidence score (0-1)
        """
        # Confidence based on sequence length and pattern frequency
        sequence_str = "->".join(sequence + [next_action])
        frequency = self.action_sequences.get(sequence_str, 0)

        # Normalize confidence
        max_frequency = max(self.action_sequences.values()) if self.action_sequences else 1
        confidence = min(1.0, frequency / max_frequency) if max_frequency > 0 else 0.5

        return confidence

    def get_feature_importance(
        self, prediction_type: str = "conversion"
    ) -> Dict[str, float]:
        """
        Get feature importance for predictions.

        Args:
            prediction_type: Type of prediction

        Returns:
            Dictionary of feature names to importance scores
        """
        return self.predictive_model.get_feature_importance(prediction_type)

    def update_sequences(self, events: List[Dict[str, Any]]) -> None:
        """
        Update sequence patterns from events.

        Args:
            events: New events to learn from
        """
        if len(events) < 2:
            return

        # Extract sequences
        for i in range(len(events) - 1):
            sequence = f"{events[i].get('type', '')}->{events[i+1].get('type', '')}"
            self.action_sequences[sequence] = self.action_sequences.get(sequence, 0) + 1
