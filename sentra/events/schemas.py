"""Strongly typed event records, severity alert tiers, and evidence notes."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
import time
from typing import List, Optional, Tuple


class EventType(Enum):
    POSSIBLE_FALL = "POSSIBLE_FALL"
    POSSIBLE_ALTERCATION = "POSSIBLE_ALTERCATION"
    UNATTENDED_ITEM = "UNATTENDED_ITEM"
    ZONE_INTRUSION = "ZONE_INTRUSION"
    CROWDING_THRESHOLD = "CROWDING_THRESHOLD"
    SCENE_OCCUPANCY_CHANGE = "SCENE_OCCUPANCY_CHANGE"


class AlertTier(Enum):
    OBSERVATION = 1      # Tier 1: Passive timeline log
    REVIEW = 2           # Tier 2: Operator notification warranting checking
    URGENT_REVIEW = 3    # Tier 3: Prompt immediate human check


class ReviewStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"


@dataclass
class EventRecord:
    """Immutable evidence-based observation event record."""
    event_id: str
    timestamp: float
    datetime_iso: str
    event_type: EventType
    tier: AlertTier
    confidence: float
    evidence_notes: List[str]
    track_ids: List[int]
    location_zone: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.PENDING
    operator_notes: Optional[str] = None

    @classmethod
    def create(
        cls,
        event_type: EventType,
        tier: AlertTier,
        confidence: float,
        evidence_notes: List[str],
        track_ids: List[int],
        location_zone: Optional[str] = None,
        now: Optional[float] = None
    ) -> "EventRecord":
        t = now if now is not None else time.time()
        dt_str = datetime.fromtimestamp(t, tz=timezone.utc).isoformat()
        short_id = f"evt_{int(t)}_{abs(hash((event_type.value, tuple(track_ids), t))) % 10000:04d}"

        return cls(
            event_id=short_id,
            timestamp=t,
            datetime_iso=dt_str,
            event_type=event_type,
            tier=tier,
            confidence=min(1.0, max(0.0, confidence)),
            evidence_notes=evidence_notes,
            track_ids=track_ids,
            location_zone=location_zone,
            review_status=ReviewStatus.PENDING
        )
