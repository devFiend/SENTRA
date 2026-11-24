"""Unit tests for FallDetectionRule, AltercationRule, ZoneIntrusionRule, and CrowdingRule."""
import pytest
from sentra.events.rules import (
    AltercationRule,
    CrowdingRule,
    FallDetectionRule,
    ZoneIntrusionRule,
)
from sentra.events.schemas import AlertTier, EventType
from sentra.vision.observations import ActivityObserver, SecurityZone
from sentra.vision.tracker import TrackedObject


def test_fall_detection_rule_simulation():
    """Verify sudden vertical drop followed by ground stillness triggers POSSIBLE_FALL."""
    rule = FallDetectionRule()
    observer = ActivityObserver()

    # Track initially upright at t=0.0: (100, 100, 160, 280) -> cy = 190
    track = TrackedObject(track_id=1, class_name="person", bbox=(100, 100, 160, 280), confidence=0.9)
    track.history = [(130.0, 190.0, 0.0)]

    # Step 1: Sudden rapid downward drop at t=0.3: cy drops to 380 (+190px in 0.3s = 633 px/s)
    # Bounding box inverts: height=50, width=150 (prone) -> aspect_ratio = 0.33
    track.bbox = (100, 355, 250, 405)
    track.history.append((175.0, 380.0, 0.3))
    track.velocity = (0.0, 0.0)
    track.speed = 0.0

    evts_drop = rule.evaluate([track], observer, now=0.3)
    assert len(evts_drop) == 0  # Candidate registered, must verify floor stillness

    # Step 2: Subject remains stationary on floor for 3.5s (t=3.8)
    track.history.append((175.0, 380.0, 3.8))
    evts_confirmed = rule.evaluate([track], observer, now=3.8)

    assert len(evts_confirmed) == 1
    evt = evts_confirmed[0]
    assert evt.event_type == EventType.POSSIBLE_FALL
    assert evt.tier == AlertTier.URGENT_REVIEW
    assert evt.track_ids == [1]
    assert "rapid downward vertical drop" in evt.evidence_notes[0]


def test_altercation_rule_simulation():
    """Verify two people rapidly converging with bounding box overlap triggers POSSIBLE_ALTERCATION."""
    rule = AltercationRule()
    observer = ActivityObserver()

    # Two people close together with high relative closing speed and IoU overlap
    p1 = TrackedObject(track_id=1, class_name="person", bbox=(200, 200, 280, 400), confidence=0.9, is_confirmed=True)
    p1.velocity = (300.0, 0.0)
    p1.speed = 300.0

    p2 = TrackedObject(track_id=2, class_name="person", bbox=(230, 200, 310, 400), confidence=0.9, is_confirmed=True)
    p2.velocity = (-300.0, 0.0)
    p2.speed = 300.0

    evts = rule.evaluate([p1, p2], observer, now=1.0)

    assert len(evts) == 1
    evt = evts[0]
    assert evt.event_type == EventType.POSSIBLE_ALTERCATION
    assert evt.tier == AlertTier.REVIEW
    assert set(evt.track_ids) == {1, 2}


def test_zone_intrusion_rule():
    """Verify ground anchor crossing restricted zone triggers ZONE_INTRUSION."""
    zone = SecurityZone(
        zone_id="restricted_vault",
        name="Vault",
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
        is_restricted=True
    )
    rule = ZoneIntrusionRule()
    observer = ActivityObserver(zones=[zone])

    track = TrackedObject(track_id=5, class_name="person", bbox=(140, 120, 200, 260), confidence=0.9)

    evts = rule.evaluate([track], observer, now=1.0)
    assert len(evts) == 1
    assert evts[0].event_type == EventType.ZONE_INTRUSION
    assert evts[0].location_zone == "Vault"
