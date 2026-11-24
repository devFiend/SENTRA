"""Unit tests for CooldownManager deduplication."""
import pytest
from sentra.events.cooldowns import CooldownManager
from sentra.events.schemas import EventType


def test_cooldown_manager_suppression_and_expiration():
    """Verify repeated triggers are suppressed until cooldown duration passes."""
    cm = CooldownManager()
    cm.cooldown_durations[EventType.POSSIBLE_FALL] = 30.0

    # Initial check permitted
    assert cm.should_trigger(EventType.POSSIBLE_FALL, track_id=1, now=10.0) is True

    # Record trigger at t=10.0
    cm.record_trigger(EventType.POSSIBLE_FALL, track_id=1, now=10.0)

    # Next check at t=15.0 (within 30s cooldown) -> Must be suppressed!
    assert cm.should_trigger(EventType.POSSIBLE_FALL, track_id=1, now=15.0) is False

    # Different track ID -> Permitted!
    assert cm.should_trigger(EventType.POSSIBLE_FALL, track_id=2, now=15.0) is True

    # At t=42.0 (32s later) -> Cooldown expired, permitted again!
    assert cm.should_trigger(EventType.POSSIBLE_FALL, track_id=1, now=42.0) is True
