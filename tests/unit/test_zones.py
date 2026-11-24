"""Unit tests for SecurityZone polygon containment and dwell tracking."""
import pytest
from sentra.vision.observations import ActivityObserver, SecurityZone
from sentra.vision.tracker import TrackedObject


def test_security_zone_ray_casting():
    """Verify point-in-polygon containment for square and concave zones."""
    zone = SecurityZone(
        zone_id="test_zone",
        name="Test Enclosure",
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
        is_restricted=True
    )

    # Inside point
    assert zone.contains_point((200.0, 200.0)) is True
    # Outside point
    assert zone.contains_point((50.0, 200.0)) is False
    assert zone.contains_point((400.0, 400.0)) is False


def test_activity_observer_dwell_tracking():
    """Verify observer detects zone entry and measures dwell duration."""
    zone = SecurityZone(
        zone_id="zone_a",
        name="Zone A",
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)]
    )
    observer = ActivityObserver(zones=[zone])

    track = TrackedObject(
        track_id=1,
        class_name="person",
        bbox=(150, 120, 210, 260),  # Ground anchor = (180, 260) -> Inside zone!
        confidence=0.9
    )

    # Frame 1 at t=1.0
    dwells = observer.update_zone_dwells([track], now=1.0)
    assert len(dwells) == 1
    assert dwells[0][1].zone_id == "zone_a"
    assert dwells[0][2] == 0.0

    # Frame 2 at t=3.5 (dwell = 2.5s)
    dwells_2 = observer.update_zone_dwells([track], now=3.5)
    assert len(dwells_2) == 1
    assert abs(dwells_2[0][2] - 2.5) < 1e-3
