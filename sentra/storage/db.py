"""Local SQLite event storage, timeline history, and settings repository."""
import json
import sqlite3
from typing import List, Optional, Tuple
from sentra.config.defaults import DATABASE_PATH
from sentra.events.schemas import AlertTier, EventRecord, EventType, ReviewStatus


class EventDatabase:
    """
    Local SQLite manager with write-ahead logging and atomic event persistence.
    Zero cloud connection or external data exfiltration.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        datetime_iso TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        tier INTEGER NOT NULL,
                        confidence REAL NOT NULL,
                        evidence_json TEXT NOT NULL,
                        track_ids_json TEXT NOT NULL,
                        location_zone TEXT,
                        review_status TEXT NOT NULL,
                        operator_notes TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp DESC)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(review_status)")
        finally:
            conn.close()

    def save_event(self, event: EventRecord) -> None:
        """Persist a single event record atomically."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    INSERT OR REPLACE INTO events (
                        event_id, timestamp, datetime_iso, event_type, tier, confidence,
                        evidence_json, track_ids_json, location_zone, review_status, operator_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.timestamp,
                    event.datetime_iso,
                    event.event_type.value,
                    event.tier.value,
                    event.confidence,
                    json.dumps(event.evidence_notes),
                    json.dumps(event.track_ids),
                    event.location_zone,
                    event.review_status.value,
                    event.operator_notes
                ))
        finally:
            conn.close()

    def get_recent_events(self, limit: int = 50) -> List[EventRecord]:
        """Fetch the most recent event records in descending timestamp order."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        finally:
            conn.close()

        events = []
        for r in rows:
            events.append(EventRecord(
                event_id=r["event_id"],
                timestamp=r["timestamp"],
                datetime_iso=r["datetime_iso"],
                event_type=EventType(r["event_type"]),
                tier=AlertTier(r["tier"]),
                confidence=r["confidence"],
                evidence_notes=json.loads(r["evidence_json"]),
                track_ids=json.loads(r["track_ids_json"]),
                location_zone=r["location_zone"],
                review_status=ReviewStatus(r["review_status"]),
                operator_notes=r["operator_notes"]
            ))
        return events

    def update_review_status(self, event_id: str, status: ReviewStatus, notes: Optional[str] = None) -> bool:
        """Update review confirmation or dismissal for an event."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("""
                    UPDATE events
                    SET review_status = ?, operator_notes = coalesce(?, operator_notes)
                    WHERE event_id = ?
                """, (status.value, notes, event_id))
                return cursor.rowcount > 0
        finally:
            conn.close()
