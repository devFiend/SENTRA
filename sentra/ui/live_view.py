"""Live camera viewport overlays: bounding boxes, trajectories, zones, and status bar."""
import math
from typing import List, Tuple
import pygame

from sentra.config.defaults import (
    COLOR_ALERT_TIER1,
    COLOR_ALERT_TIER2,
    COLOR_ALERT_TIER3,
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_OBJECT_TRACK,
    COLOR_PANEL_BG,
    COLOR_PERSON_TRACK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_ZONE_NORMAL,
    COLOR_ZONE_RESTRICTED,
)
from sentra.vision.observations import SecurityZone
from sentra.vision.tracker import TrackedObject


def render_live_overlays(
    surface: pygame.Surface,
    tracks: List[TrackedObject],
    zones: List[SecurityZone],
    show_zones: bool,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    view_width: int,
    view_height: int
) -> None:
    """Render bounding boxes, velocity vectors, anonymous badges, and security zones."""

    # 1. Render Security Zones
    if show_zones:
        for zone in zones:
            if not zone.active or len(zone.polygon) < 3:
                continue

            color = COLOR_ZONE_RESTRICTED if zone.is_restricted else COLOR_ZONE_NORMAL
            pts = [(int(p[0]), int(p[1])) for p in zone.polygon]
            pygame.draw.polygon(surface, color, pts, width=2)

            # Zone label
            lx, ly = pts[0]
            label_text = f"ZONE: {zone.name} ({'RESTRICTED' if zone.is_restricted else 'ACTIVE'})"
            lbl_surf = small_font.render(label_text, True, color)
            surface.blit(lbl_surf, (lx + 5, ly + 5))

    # 2. Render Tracked Subjects
    for track in tracks:
        x1, y1, x2, y2 = track.bbox
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)

        color = COLOR_PERSON_TRACK if track.class_name == "person" else COLOR_OBJECT_TRACK

        # Bounding box
        pygame.draw.rect(surface, color, (x1, y1, w, h), width=2, border_radius=4)

        # Centroid motion trajectory trail
        if len(track.history) >= 2:
            pts = [(int(p[0]), int(p[1])) for p in track.history]
            pygame.draw.lines(surface, color, False, pts, width=2)

        # Ground anchor dot
        gx, gy = int(track.ground_anchor[0]), int(track.ground_anchor[1])
        pygame.draw.circle(surface, color, (gx, gy), 4)

        # Track badge tag
        tag = f"#{track.track_id} {track.class_name.upper()} ({int(track.speed)} px/s)"
        tag_surf = small_font.render(tag, True, COLOR_BACKGROUND)
        tag_w = tag_surf.get_width() + 8
        tag_h = tag_surf.get_height() + 4

        pygame.draw.rect(surface, color, (x1, max(0, y1 - tag_h), tag_w, tag_h), border_radius=3)
        surface.blit(tag_surf, (x1 + 4, max(2, y1 - tag_h + 2)))


def render_top_status_bar(
    surface: pygame.Surface,
    fps: float,
    active_tracks_count: int,
    is_paused: bool,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    screen_width: int
) -> None:
    """Render top operational diagnostics and privacy assurance indicator."""
    bar_h = 36
    pygame.draw.rect(surface, COLOR_PANEL_BG, (0, 0, screen_width, bar_h))
    pygame.draw.line(surface, COLOR_BORDER, (0, bar_h), (screen_width, bar_h), 1)

    # Privacy Camera Status Indicator (Green dot)
    status_color = (0, 230, 118) if not is_paused else (255, 179, 0)
    pygame.draw.circle(surface, status_color, (20, 18), 6)
    cam_status_text = "CAMERA ACTIVE • 100% LOCAL (NO CLOUD)" if not is_paused else "PAUSED"
    surface.blit(small_font.render(cam_status_text, True, COLOR_TEXT_PRIMARY), (32, 11))

    # Diagnostics
    diag_text = f"FPS: {fps:04.1f} | TRACKS: {active_tracks_count} | RECORDING: OFF"
    diag_surf = small_font.render(diag_text, True, COLOR_TEXT_MUTED)
    surface.blit(diag_surf, (screen_width - diag_surf.get_width() - 20, 11))
