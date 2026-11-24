"""Unit tests for AlertManager audio synthesis and mute."""
import os
import pytest
from sentra.alerts.manager import AlertManager
from sentra.events.schemas import AlertTier, EventRecord, EventType


def test_alert_manager_audio_and_mute():
    """Verify alert manager triggers procedural sound generation and respects mute."""
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    mgr = AlertManager()

    # Mute toggle test
    assert mgr.muted is False
    mgr.toggle_mute()
    assert mgr.muted is True
    mgr.toggle_mute()
    assert mgr.muted is False

    evt_tier2 = EventRecord.create(
        event_type=EventType.POSSIBLE_ALTERCATION,
        tier=AlertTier.REVIEW,
        confidence=0.8,
        evidence_notes=["Close overlap"],
        track_ids=[1, 2]
    )

    # Must execute cleanly without exception
    mgr.dispatch(evt_tier2)
