"""Cross-platform desktop notifications and console event logger."""
import sys
from sentra.events.schemas import AlertTier, EventRecord


class DesktopNotifier:
    """
    Delivers local OS notifications without external cloud or third-party webhooks.
    """

    @staticmethod
    def notify(event: EventRecord) -> None:
        """Present desktop notification or structured console alert."""
        tier_label = event.tier.name.replace("_", " ")
        msg = f"[{tier_label}] {event.event_type.value}: {event.evidence_notes[0] if event.evidence_notes else 'Event observed'}"

        # Standard console notification
        print(f"[SENTRA ALERT] {msg}")
