"""Interactive timeline drawer, alert event cards, and review/dismiss controls."""
from typing import List, Optional
import pygame

from sentra.config.defaults import (
    COLOR_ALERT_TIER1,
    COLOR_ALERT_TIER2,
    COLOR_ALERT_TIER3,
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_PANEL_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
)
from sentra.events.schemas import AlertTier, EventRecord, ReviewStatus


def render_timeline_panel(
    surface: pygame.Surface,
    events: List[EventRecord],
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    x: int,
    y: int,
    width: int,
    height: int
) -> None:
    """Renders the scrolling event intelligence timeline drawer."""
    # Panel background
    pygame.draw.rect(surface, COLOR_PANEL_BG, (x, y, width, height))
    pygame.draw.line(surface, COLOR_BORDER, (x, y), (x, y + height), 2)

    # Header
    header_text = "EVENT TIMELINE"
    surface.blit(font.render(header_text, True, COLOR_TEXT_PRIMARY), (x + 16, y + 14))

    legend_text = "[C] Confirm | [D] Dismiss"
    surface.blit(small_font.render(legend_text, True, COLOR_TEXT_MUTED), (x + 16, y + 38))
    pygame.draw.line(surface, COLOR_BORDER, (x, y + 58), (x + width, y + 58), 1)

    # Render recent event cards
    card_y = y + 66
    max_cards = min(6, len(events))

    for i in range(max_cards):
        evt = events[-(i + 1)]  # Most recent first

        card_h = 82
        card_w = width - 24
        card_x = x + 12

        # Tier accent color
        if evt.tier == AlertTier.URGENT_REVIEW:
            tier_color = COLOR_ALERT_TIER3
        elif evt.tier == AlertTier.REVIEW:
            tier_color = COLOR_ALERT_TIER2
        else:
            tier_color = COLOR_ALERT_TIER1

        # Card container
        pygame.draw.rect(surface, (28, 36, 48), (card_x, card_y, card_w, card_h), border_radius=6)
        pygame.draw.rect(surface, tier_color, (card_x, card_y, 4, card_h), border_top_left_radius=6, border_bottom_left_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER, (card_x, card_y, card_w, card_h), width=1, border_radius=6)

        # Tier & Event Title
        title_text = f"{evt.event_type.value}"
        surface.blit(small_font.render(title_text, True, tier_color), (card_x + 12, card_y + 8))

        # Time & Status Badge
        time_str = evt.datetime_iso[11:19] + "Z"
        status_color = (0, 230, 118) if evt.review_status == ReviewStatus.CONFIRMED else (
            COLOR_TEXT_MUTED if evt.review_status == ReviewStatus.DISMISSED else COLOR_ALERT_TIER2
        )
        status_str = f"{time_str} • {evt.review_status.value}"
        surface.blit(small_font.render(status_str, True, status_color), (card_x + card_w - 140, card_y + 8))

        # Evidence Note
        evidence_text = evt.evidence_notes[0] if evt.evidence_notes else "Observable visual change detected."
        if len(evidence_text) > 42:
            evidence_text = evidence_text[:39] + "..."
        surface.blit(small_font.render(evidence_text, True, COLOR_TEXT_PRIMARY), (card_x + 12, card_y + 30))

        # Track Tags
        tracks_str = f"Subjects: {evt.track_ids} | Conf: {int(evt.confidence * 100)}%"
        surface.blit(small_font.render(tracks_str, True, COLOR_TEXT_MUTED), (card_x + 12, card_y + 54))

        card_y += card_h + 10
