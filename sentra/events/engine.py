"""Event rule engine coordinating observations, rules, and cooldown suppression."""
import time
from typing import List, Optional
from sentra.events.cooldowns import CooldownManager
from sentra.events.rules import (
    AltercationRule,
    BaseEventRule,
    CrowdingRule,
    FallDetectionRule,
    ZoneIntrusionRule,
)
from sentra.events.schemas import EventRecord
from sentra.vision.observations import ActivityObserver, SecurityZone
from sentra.vision.tracker import TrackedObject


class EventRuleEngine:
    """
    Coordinates multi-frame rule evaluation, candidate filtering, and deduplication.
    """

    def __init__(self, observer: Optional[ActivityObserver] = None):
        self.observer = observer or ActivityObserver()
        self.cooldown_manager = CooldownManager()
        self.rules: List[BaseEventRule] = [
            FallDetectionRule(),
            AltercationRule(),
            ZoneIntrusionRule(),
            CrowdingRule(),
        ]
        self.recent_events: List[EventRecord] = []

    def evaluate_frame(self, tracks: List[TrackedObject], now: Optional[float] = None) -> List[EventRecord]:
        """
        Evaluate all active rules on the current frame tracks.
        Returns deduplicated events that passed cooldown checks.
        """
        t = now if now is not None else time.time()
        confirmed_events: List[EventRecord] = []

        for rule in self.rules:
            candidates = rule.evaluate(tracks, self.observer, t)
            for event in candidates:
                # Deduplication key based on primary track ID or 0
                primary_tid = event.track_ids[0] if event.track_ids else 0

                if self.cooldown_manager.should_trigger(event.event_type, primary_tid, t):
                    self.cooldown_manager.record_trigger(event.event_type, primary_tid, t)
                    confirmed_events.append(event)
                    self.recent_events.append(event)
                    if len(self.recent_events) > 100:
                        self.recent_events.pop(0)

        return confirmed_events
