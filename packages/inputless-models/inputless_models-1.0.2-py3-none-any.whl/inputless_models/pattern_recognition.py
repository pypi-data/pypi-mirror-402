"""
Pattern recognition models for identifying behavioral patterns.

Supports sequence, temporal, spatial, behavioral, and correlation pattern recognition.
"""

from typing import List, Dict, Any, Optional
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import uuid

from .types import PatternRecognitionConfig, Pattern


class PatternRecognitionModel:
    """
    ML model for recognizing behavioral patterns.

    Supports sequence, temporal, spatial, behavioral, and correlation patterns.
    """

    def __init__(self, config: PatternRecognitionConfig):
        """
        Initialize pattern recognition model.

        Args:
            config: Model configuration

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.scaler = StandardScaler()
        self.sequence_model = None
        self.temporal_model = None
        self.spatial_model = None
        self.behavioral_model = None
        self.correlation_model = None
        self.patterns_history: List[Pattern] = []
        self.known_sequences: Dict[str, float] = {}  # sequence -> confidence

    def recognize(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Recognize patterns from events.

        Args:
            events: List of behavioral events

        Returns:
            List of recognized patterns

        Raises:
            ValueError: If events list is empty
        """
        if not events:
            return []

        patterns = []

        if "sequence" in self.config.pattern_types:
            patterns.extend(self.get_sequence_patterns(events))

        if "temporal" in self.config.pattern_types:
            patterns.extend(self.get_temporal_patterns(events))

        if "spatial" in self.config.pattern_types:
            patterns.extend(self.get_spatial_patterns(events))

        if "behavioral" in self.config.pattern_types:
            patterns.extend(self.get_behavioral_patterns(events))

        if "correlation" in self.config.pattern_types:
            patterns.extend(self.get_correlation_patterns(events))

        # Filter by confidence
        patterns = [
            p for p in patterns if p.confidence >= self.config.min_pattern_confidence
        ]

        self.patterns_history.extend(patterns)
        return patterns

    def get_sequence_patterns(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Recognize sequence patterns.

        Args:
            events: List of events

        Returns:
            List of sequence patterns
        """
        patterns = []

        if len(events) < self.config.sequence_window:
            return patterns

        # Create sliding windows
        for i in range(len(events) - self.config.sequence_window + 1):
            window = events[i : i + self.config.sequence_window]
            sequence = [e.get("type", "") for e in window]

            # Check if sequence matches known patterns
            pattern = self._match_sequence_pattern(sequence, window)
            if pattern:
                patterns.append(pattern)

        return patterns

    def get_temporal_patterns(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Recognize temporal patterns.

        Args:
            events: List of events

        Returns:
            List of temporal patterns
        """
        patterns = []

        if not events:
            return patterns

        try:
            # Convert to DataFrame
            df = pd.DataFrame(events)
            if "timestamp" not in df.columns:
                return patterns

            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"])

            if len(df) == 0:
                return patterns

            # Parse temporal resolution
            resolution = self.config.temporal_resolution
            if resolution.endswith("min"):
                freq = f"{resolution[:-3]}T"
            elif resolution.endswith("hour"):
                freq = f"{resolution[:-4]}H"
            elif resolution.endswith("day"):
                freq = f"{resolution[:-3]}D"
            else:
                freq = "1T"  # Default to 1 minute

            df["time_bin"] = df["timestamp"].dt.floor(freq)

            # Analyze temporal patterns
            grouped = df.groupby("time_bin")
            for time_bin, group in grouped:
                if len(group) >= self.config.min_cluster_size:
                    pattern = self._create_temporal_pattern(
                        time_bin, group.to_dict("records")
                    )
                    if pattern:
                        patterns.append(pattern)
        except Exception:
            # Return empty list if processing fails
            return patterns

        return patterns

    def get_spatial_patterns(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Recognize spatial patterns (viewport/location-based).

        Args:
            events: List of events

        Returns:
            List of spatial patterns
        """
        patterns = []

        # Extract spatial events
        spatial_events = [
            e for e in events if "viewport" in e or "location" in e or "coordinates" in e
        ]

        if len(spatial_events) < self.config.min_cluster_size:
            return patterns

        # Cluster spatial events
        features = self._extract_spatial_features(spatial_events)
        if len(features) > 0:
            clusters = self._cluster_spatial(features)
            patterns = self._create_spatial_patterns(clusters, spatial_events)

        return patterns

    def get_behavioral_patterns(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Recognize behavioral patterns.

        Args:
            events: List of events

        Returns:
            List of behavioral patterns
        """
        patterns = []

        if len(events) < self.config.min_cluster_size:
            return patterns

        # Extract behavioral features
        behavioral_features = self._extract_behavioral_features(events)

        # Cluster behaviors
        if len(behavioral_features) >= self.config.min_cluster_size:
            clusters = self._cluster_behavioral(behavioral_features)
            patterns = self._create_behavioral_patterns(clusters, events)

        return patterns

    def get_correlation_patterns(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Recognize correlation patterns.

        Args:
            events: List of events

        Returns:
            List of correlation patterns
        """
        patterns = []

        if len(events) < 2:
            return patterns

        # Calculate correlations between event types
        event_matrix = self._build_event_matrix(events)
        if event_matrix.size == 0:
            return patterns

        correlations = self._calculate_correlations(event_matrix)

        # Identify significant correlations
        significant = [
            (a, b, corr)
            for a, b, corr in correlations
            if abs(corr) >= self.config.min_pattern_confidence
        ]

        event_types = list(set(e.get("type", "") for e in events if e.get("type")))

        for event_a_idx, event_b_idx, correlation in significant:
            if event_a_idx < len(event_types) and event_b_idx < len(event_types):
                pattern = self._create_correlation_pattern(
                    event_types[event_a_idx],
                    event_types[event_b_idx],
                    correlation,
                    events,
                )
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _match_sequence_pattern(
        self, sequence: List[str], events: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """
        Match sequence against known patterns.

        Args:
            sequence: Event type sequence
            events: Full event objects

        Returns:
            Pattern if matched, None otherwise
        """
        sequence_str = "->".join(sequence)

        # Check against known sequences
        if sequence_str in self.known_sequences:
            confidence = self.known_sequences[sequence_str]
        else:
            # Calculate confidence based on sequence characteristics
            confidence = self._calculate_sequence_confidence(sequence)
            self.known_sequences[sequence_str] = confidence

        if confidence >= self.config.min_pattern_confidence:
            return Pattern(
                pattern_id=f"seq_{uuid.uuid4().hex[:8]}",
                pattern_type="sequence",
                events=events,
                confidence=confidence,
                frequency=1,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                metadata={"sequence": sequence_str},
            )

        return None

    def _calculate_sequence_confidence(self, sequence: List[str]) -> float:
        """
        Calculate confidence for a sequence pattern.

        Args:
            sequence: Event type sequence

        Returns:
            Confidence score (0-1)
        """
        if not sequence:
            return 0.0

        # Simple heuristic: longer sequences with more unique types are more interesting
        unique_types = len(set(sequence))
        length_factor = min(1.0, len(sequence) / 10.0)
        diversity_factor = min(1.0, unique_types / len(sequence))

        confidence = (length_factor * 0.5 + diversity_factor * 0.5)
        return confidence

    def _create_temporal_pattern(
        self, time_bin: pd.Timestamp, events: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """
        Create temporal pattern.

        Args:
            time_bin: Time bin (pandas Timestamp)
            events: Events in this time bin

        Returns:
            Temporal pattern
        """
        if not events:
            return None

        # Calculate pattern confidence based on event frequency
        frequency = len(events)
        confidence = min(1.0, frequency / 10.0)  # Normalize

        if confidence >= self.config.min_pattern_confidence:
            return Pattern(
                pattern_id=f"temporal_{time_bin.isoformat()}",
                pattern_type="temporal",
                events=events,
                confidence=confidence,
                frequency=frequency,
                first_seen=time_bin.to_pydatetime(),
                last_seen=time_bin.to_pydatetime(),
                metadata={"time_bin": time_bin.isoformat()},
            )

        return None

    def _extract_spatial_features(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract spatial features from events.

        Args:
            events: Events with spatial information

        Returns:
            Array of spatial features
        """
        features = []
        for e in events:
            if "viewport" in e:
                viewport = e["viewport"]
                features.append(
                    [
                        viewport.get("x", 0),
                        viewport.get("y", 0),
                        viewport.get("width", 0),
                        viewport.get("height", 0),
                    ]
                )
            elif "location" in e:
                location = e["location"]
                features.append([location.get("x", 0), location.get("y", 0), 0, 0])
            elif "coordinates" in e:
                coords = e["coordinates"]
                features.append([coords.get("x", 0), coords.get("y", 0), 0, 0])

        return np.array(features) if features else np.array([]).reshape(0, 4)

    def _cluster_spatial(self, features: np.ndarray) -> List[List[int]]:
        """
        Cluster spatial features.

        Args:
            features: Spatial feature array

        Returns:
            List of clusters (each cluster is a list of indices)
        """
        if len(features) < self.config.min_cluster_size:
            return []

        try:
            scaled = self.scaler.fit_transform(features)

            if self.config.clustering_algorithm == "dbscan":
                clustering = DBSCAN(min_samples=self.config.min_cluster_size, eps=0.5)
            elif self.config.clustering_algorithm == "kmeans":
                n_clusters = max(2, len(features) // self.config.min_cluster_size)
                clustering = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            else:  # hierarchical
                n_clusters = max(2, len(features) // self.config.min_cluster_size)
                clustering = AgglomerativeClustering(n_clusters=n_clusters)

            labels = clustering.fit_predict(scaled)

            clusters = {}
            for idx, label in enumerate(labels):
                if label != -1:  # Not noise
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(idx)

            return list(clusters.values())
        except Exception:
            return []

    def _create_spatial_patterns(
        self, clusters: List[List[int]], events: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """
        Create spatial patterns from clusters.

        Args:
            clusters: List of cluster indices
            events: Original events

        Returns:
            List of spatial patterns
        """
        patterns = []
        for cluster_idx, cluster in enumerate(clusters):
            cluster_events = [events[i] for i in cluster if i < len(events)]
            if cluster_events:
                pattern = Pattern(
                    pattern_id=f"spatial_{uuid.uuid4().hex[:8]}",
                    pattern_type="spatial",
                    events=cluster_events,
                    confidence=0.75,
                    frequency=len(cluster_events),
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    metadata={"cluster_size": len(cluster_events)},
                )
                patterns.append(pattern)

        return patterns

    def _extract_behavioral_features(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract behavioral features from events.

        Args:
            events: List of events

        Returns:
            Array of behavioral features
        """
        features = []
        for e in events:
            feature_vector = [
                float(e.get("duration", 0)),
                float(e.get("frequency", 0)),
                float(len(e.get("metadata", {}))),
                1.0 if e.get("type") == "click" else 0.0,
                1.0 if e.get("type") == "scroll" else 0.0,
                1.0 if e.get("type") == "hover" else 0.0,
                1.0 if e.get("type") == "focus" else 0.0,
            ]
            features.append(feature_vector)

        return np.array(features) if features else np.array([]).reshape(0, 7)

    def _cluster_behavioral(self, features: np.ndarray) -> List[List[int]]:
        """
        Cluster behavioral features.

        Args:
            features: Behavioral feature array

        Returns:
            List of clusters
        """
        if len(features) < self.config.min_cluster_size:
            return []

        try:
            scaled = self.scaler.fit_transform(features)

            if self.config.clustering_algorithm == "dbscan":
                clustering = DBSCAN(min_samples=self.config.min_cluster_size, eps=0.5)
            elif self.config.clustering_algorithm == "kmeans":
                n_clusters = max(2, len(features) // self.config.min_cluster_size)
                clustering = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            else:  # hierarchical
                n_clusters = max(2, len(features) // self.config.min_cluster_size)
                clustering = AgglomerativeClustering(n_clusters=n_clusters)

            labels = clustering.fit_predict(scaled)

            clusters = {}
            for idx, label in enumerate(labels):
                if label != -1:
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(idx)

            return list(clusters.values())
        except Exception:
            return []

    def _create_behavioral_patterns(
        self, clusters: List[List[int]], events: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """
        Create behavioral patterns from clusters.

        Args:
            clusters: List of cluster indices
            events: Original events

        Returns:
            List of behavioral patterns
        """
        patterns = []
        for cluster_idx, cluster in enumerate(clusters):
            cluster_events = [events[i] for i in cluster if i < len(events)]
            if cluster_events:
                pattern = Pattern(
                    pattern_id=f"behavioral_{uuid.uuid4().hex[:8]}",
                    pattern_type="behavioral",
                    events=cluster_events,
                    confidence=0.8,
                    frequency=len(cluster_events),
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    metadata={"cluster_size": len(cluster_events)},
                )
                patterns.append(pattern)

        return patterns

    def _build_event_matrix(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Build event co-occurrence matrix.

        Args:
            events: List of events

        Returns:
            Co-occurrence matrix
        """
        event_types = [
            e.get("type", "") for e in events if e.get("type")
        ]  # Filter empty types
        unique_types = list(set(event_types))

        if len(unique_types) == 0:
            return np.array([]).reshape(0, 0)

        matrix = np.zeros((len(unique_types), len(unique_types)))

        for i, type_a in enumerate(unique_types):
            for j, type_b in enumerate(unique_types):
                count = sum(
                    1
                    for k in range(len(events) - 1)
                    if events[k].get("type") == type_a
                    and events[k + 1].get("type") == type_b
                )
                matrix[i][j] = count

        return matrix

    def _calculate_correlations(self, matrix: np.ndarray) -> List[tuple]:
        """
        Calculate correlations between event types.

        Args:
            matrix: Event co-occurrence matrix

        Returns:
            List of (index_a, index_b, correlation) tuples
        """
        correlations = []
        n = matrix.shape[0]

        if n < 2:
            return correlations

        for i in range(n):
            for j in range(i + 1, n):
                try:
                    corr = np.corrcoef(matrix[i], matrix[j])[0, 1]
                    if not np.isnan(corr):
                        correlations.append((i, j, float(corr)))
                except Exception:
                    continue

        return correlations

    def _create_correlation_pattern(
        self,
        event_a: str,
        event_b: str,
        correlation: float,
        events: List[Dict[str, Any]],
    ) -> Optional[Pattern]:
        """
        Create correlation pattern.

        Args:
            event_a: First event type
            event_b: Second event type
            correlation: Correlation coefficient
            events: Original events

        Returns:
            Correlation pattern
        """
        # Sample events for pattern
        sample_events = events[: min(10, len(events))]

        return Pattern(
            pattern_id=f"correlation_{uuid.uuid4().hex[:8]}",
            pattern_type="correlation",
            events=sample_events,
            confidence=abs(correlation),
            frequency=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            metadata={
                "event_a": event_a,
                "event_b": event_b,
                "correlation": correlation,
            },
        )

    def train(
        self, training_data: List[Dict[str, Any]], labels: Optional[List[str]] = None
    ) -> None:
        """
        Train pattern recognition models.

        Args:
            training_data: Training events
            labels: Optional pattern labels
        """
        # Extract sequences from training data
        for i in range(len(training_data) - self.config.sequence_window + 1):
            window = training_data[i : i + self.config.sequence_window]
            sequence = [e.get("type", "") for e in window]
            sequence_str = "->".join(sequence)

            # Update known sequences with higher confidence if labeled
            if labels and i < len(labels):
                confidence = 0.9 if labels[i] == "pattern" else 0.3
            else:
                confidence = self._calculate_sequence_confidence(sequence)

            if sequence_str in self.known_sequences:
                # Average with existing confidence
                self.known_sequences[sequence_str] = (
                    self.known_sequences[sequence_str] + confidence
                ) / 2.0
            else:
                self.known_sequences[sequence_str] = confidence

    def save_model(self, filepath: str) -> None:
        """
        Save trained model to file.

        Args:
            filepath: Path to save model
        """
        import pickle

        model_data = {
            "known_sequences": self.known_sequences,
            "config": self.config.dict(),
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

    def load_model(self, filepath: str) -> None:
        """
        Load trained model from file.

        Args:
            filepath: Path to load model from

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        import pickle

        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)

            self.known_sequences = model_data.get("known_sequences", {})
            # Config is already set in __init__, but we could update it here if needed
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Invalid model file format: {str(e)}") from e
