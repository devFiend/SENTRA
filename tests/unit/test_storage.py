"""Unit tests for SQLite EventDatabase persistence."""
import os
import tempfile
import pytest
from sentra.events.schemas import AlertTier, EventRecord, EventType, ReviewStatus
from sentra.storage.db import EventDatabase


def test_event_database_crud():
    """Verify event insertion, query, and review status update."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_sentra.db")
        db = EventDatabase(db_path)

        evt = EventRecord.create(
            event_type=EventType.POSSIBLE_FALL,
            tier=AlertTier.URGENT_REVIEW,
            confidence=0.88,
            evidence_notes=["Subject dropped rapidly", "Stationary for 4s"],
            track_ids=[12],
            now=100.0
        )

        db.save_event(evt)

        # Query recent
        recent = db.get_recent_events(limit=10)
        assert len(recent) == 1
        saved = recent[0]
        assert saved.event_id == evt.event_id
        assert saved.event_type == EventType.POSSIBLE_FALL
        assert saved.review_status == ReviewStatus.PENDING

        # Update review status
        updated = db.update_review_status(evt.event_id, ReviewStatus.CONFIRMED, notes="Operator verified fall")
        assert updated is True

        recent_after = db.get_recent_events(limit=1)
        assert recent_after[0].review_status == ReviewStatus.CONFIRMED
        assert recent_after[0].operator_notes == "Operator verified fall"
