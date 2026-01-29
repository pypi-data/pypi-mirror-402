"""
Behavioral DNA Profiling

Create unique, evolving behavioral "fingerprints" for users without requiring login or PII.
"""

from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np

from ..types import Pattern


class BehavioralDNA(BaseModel):
    """Represents a behavioral DNA profile."""

    profile_id: str = Field(..., description="Unique profile identifier")
    signature: str = Field(..., description="Behavioral signature hash")
    traits: Dict[str, float] = Field(default_factory=dict, description="Behavioral traits")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BehavioralDNAProfiler:
    """
    Behavioral DNA profiler for creating privacy-preserving user fingerprints.

    Generates unique behavioral signatures that evolve with user behavior.
    Enables cross-device matching without cookies or PII.
    """

    def __init__(self, min_events: int = 10):
        """
        Initialize behavioral DNA profiler.

        Args:
            min_events: Minimum number of events required to generate profile
        """
        self.min_events = min_events
        self.profiles: Dict[str, BehavioralDNA] = {}

    def generate_profile(
        self, events: List[Dict[str, Any]], user_id: Optional[str] = None
    ) -> BehavioralDNA:
        """
        Generate behavioral DNA profile from events.

        Args:
            events: List of behavioral events
            user_id: Optional user identifier

        Returns:
            Behavioral DNA profile

        Raises:
            ValueError: If insufficient events provided
        """
        if len(events) < self.min_events:
            raise ValueError(
                f"Insufficient events. Need at least {self.min_events}, got {len(events)}"
            )

        # Extract behavioral traits
        traits = self._extract_traits(events)

        # Generate signature hash
        signature = self._generate_signature(traits)

        # Create or update profile
        profile_id = user_id or f"profile_{signature[:8]}"
        if profile_id in self.profiles:
            profile = self.profiles[profile_id]
            profile.traits = traits
            profile.signature = signature
            profile.updated_at = datetime.now()
        else:
            profile = BehavioralDNA(
                profile_id=profile_id,
                signature=signature,
                traits=traits,
                metadata={"event_count": len(events)},
            )
            self.profiles[profile_id] = profile

        return profile

    def _extract_traits(self, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract behavioral traits from events.

        Args:
            events: List of events

        Returns:
            Dictionary of trait names to scores
        """
        # Calculate trait scores
        click_rate = sum(1 for e in events if e.get("type") == "click") / len(events)
        scroll_rate = sum(1 for e in events if e.get("type") == "scroll") / len(events)
        hover_rate = sum(1 for e in events if e.get("type") == "hover") / len(events)
        error_rate = sum(1 for e in events if e.get("type") == "error") / len(events)

        # Duration traits
        durations = [e.get("duration", 0) for e in events if "duration" in e]
        avg_duration = np.mean(durations) if durations else 0.0
        max_duration = np.max(durations) if durations else 0.0

        # Diversity traits
        unique_types = len(set(e.get("type", "") for e in events if e.get("type")))
        type_diversity = unique_types / len(events) if events else 0.0

        # Behavioral patterns
        hesitation_count = sum(
            1 for e in events if e.get("duration", 0) > 3000
        )  # >3s = hesitation
        hesitation_rate = hesitation_count / len(events) if events else 0.0

        return {
            "click_rate": float(click_rate),
            "scroll_rate": float(scroll_rate),
            "hover_rate": float(hover_rate),
            "error_rate": float(error_rate),
            "avg_duration": float(avg_duration),
            "max_duration": float(max_duration),
            "type_diversity": float(type_diversity),
            "hesitation_rate": float(hesitation_rate),
        }

    def _generate_signature(self, traits: Dict[str, float]) -> str:
        """
        Generate privacy-preserving signature hash from traits.

        Args:
            traits: Behavioral traits

        Returns:
            Signature hash
        """
        # Sort traits for consistent hashing
        sorted_traits = json.dumps(traits, sort_keys=True)
        signature = hashlib.sha256(sorted_traits.encode()).hexdigest()
        return signature

    def find_similar(
        self, profile: BehavioralDNA, threshold: float = 0.8, limit: int = 10
    ) -> List[BehavioralDNA]:
        """
        Find similar behavioral profiles.

        Args:
            profile: Reference profile
            threshold: Similarity threshold (0-1)
            limit: Maximum number of results

        Returns:
            List of similar profiles
        """
        similarities = []
        for other_profile in self.profiles.values():
            if other_profile.profile_id == profile.profile_id:
                continue

            similarity = self._calculate_similarity(profile, other_profile)
            if similarity >= threshold:
                similarities.append((similarity, other_profile))

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in similarities[:limit]]

    def _calculate_similarity(
        self, profile1: BehavioralDNA, profile2: BehavioralDNA
    ) -> float:
        """
        Calculate similarity between two profiles.

        Args:
            profile1: First profile
            profile2: Second profile

        Returns:
            Similarity score (0-1)
        """
        traits1 = profile1.traits
        traits2 = profile2.traits

        # Calculate cosine similarity or trait overlap
        common_traits = set(traits1.keys()) & set(traits2.keys())
        if not common_traits:
            return 0.0

        # Calculate weighted similarity
        similarities = []
        for trait in common_traits:
            val1 = traits1[trait]
            val2 = traits2[trait]
            # Normalized difference
            diff = abs(val1 - val2)
            max_val = max(abs(val1), abs(val2), 1.0)
            similarity = 1.0 - (diff / max_val)
            similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def track_evolution(
        self, user_id: str, time_period: str = "30days"
    ) -> Dict[str, Any]:
        """
        Track profile evolution over time.

        Args:
            user_id: User identifier
            time_period: Time period to analyze

        Returns:
            Evolution metrics
        """
        if user_id not in self.profiles:
            return {}

        profile = self.profiles[user_id]

        # Parse time period
        if time_period.endswith("days"):
            days = int(time_period[:-4])
        else:
            days = 30

        cutoff_date = datetime.now() - timedelta(days=days)

        # Calculate evolution metrics
        evolution = {
            "profile_id": user_id,
            "current_traits": profile.traits,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
            "age_days": (datetime.now() - profile.created_at).days,
        }

        return evolution

    def get_profile(self, user_id: str) -> Optional[BehavioralDNA]:
        """
        Get profile by user ID.

        Args:
            user_id: User identifier

        Returns:
            Profile if found, None otherwise
        """
        return self.profiles.get(user_id)
