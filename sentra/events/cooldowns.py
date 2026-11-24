"""Sliding-window deduplication and alert suppression manager."""
import time
from typing import Dict, Tuple
from sentra.events.schemas import EventType


class CooldownManager:
    """
    Suppresses redundant event spam by enforcing per-type and per-track cooldown intervals.
    """

    def __init__(self):
        # Default cooldown windows in seconds
        self.cooldown_durations: Dict[EventType, float] = {
            EventType.POSSIBLE_FALL: 45.0,
            EventType.POSSIBLE_ALTERCATION: 30.0,
            EventType.UNATTENDED_ITEM: 60.0,
            EventType.ZONE_INTRUSION: 15.0,
            EventType.CROWDING_THRESHOLD: 40.0,
            EventType.SCENE_OCCUPANCY_CHANGE: 10.0,
        }
        # (EventType, primary_track_id) -> last_triggered_timestamp
        self._last_triggers: Dict[Tuple[EventType, int], float] = {}

    def should_trigger(self, event_type: EventType, track_id: int, now: float) -> bool:
        """Returns True if the event is permitted to fire, or False if currently on cooldown."""
        key = (event_type, track_id)
        if key not in self._last_triggers:
            return True

        last_time = self._last_triggers[key]
        duration = self.cooldown_durations.get(event_type, 30.0)
        return (now - last_time) >= duration

    def record_trigger(self, event_type: EventType, track_id: int, now: float) -> None:
        """Mark an event as triggered at the given timestamp."""
        key = (event_type, track_id)
        self._last_triggers[key] = now
