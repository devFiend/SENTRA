#!/usr/bin/env python3
"""
SENTRA — Local-First Camera-Based Scene Observation & Event Intelligence
Application Entry Point and Reactive Pipeline Coordinator
"""
import argparse
import os
import sys
import time

# Auto-detect and forward to local virtual environment if run from global python
if sys.prefix == sys.base_prefix:
    _venv_win = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "Scripts", "python.exe")
    _venv_nix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "bin", "python")
    _target_py = _venv_win if os.path.exists(_venv_win) else (_venv_nix if os.path.exists(_venv_nix) else None)
    if _target_py and os.path.abspath(sys.executable).lower() != os.path.abspath(_target_py).lower():
        import subprocess
        sys.exit(subprocess.call([_target_py] + sys.argv))

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import pygame

from sentra.alerts.desktop import DesktopNotifier
from sentra.alerts.manager import AlertManager
from sentra.camera.capture import CameraCapture
from sentra.camera.source import CameraSource
from sentra.config.defaults import (
    COLOR_BACKGROUND,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    TARGET_FPS,
    WINDOW_TITLE,
)
from sentra.events.engine import EventRuleEngine
from sentra.events.schemas import ReviewStatus
from sentra.storage.db import EventDatabase
from sentra.ui.live_view import render_live_overlays, render_top_status_bar
from sentra.ui.timeline import render_timeline_panel
from sentra.vision.detector import VisionDetector
from sentra.vision.observations import ActivityObserver, SecurityZone
from sentra.vision.tracker import ObjectTracker


def run(
    headless: bool = False,
    max_frames: int = 0,
    mock_camera: bool = False,
    camera_source_arg: object = DEFAULT_CAMERA_INDEX
) -> int:
    """Initialize camera, vision pipeline, event engine, storage, and UI loop."""
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    pygame.init()
    pygame.font.init()

    # Layout dimensions: Main Viewport (920px) + Timeline Drawer (360px) = 1280px
    screen_w = DEFAULT_WINDOW_WIDTH
    screen_h = DEFAULT_WINDOW_HEIGHT
    viewport_w = 920
    timeline_w = 360

    if not headless:
        screen = pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption(WINDOW_TITLE)
    else:
        screen = pygame.Surface((screen_w, screen_h))

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Segoe UI", 16, bold=True)
    small_font = pygame.font.SysFont("Segoe UI", 13)

    print(f"[SENTRA] Initializing camera source: {camera_source_arg}...")
    source = CameraSource.from_input(camera_source_arg, mock_mode=mock_camera)
    capture = CameraCapture(source, width=viewport_w, height=screen_h - 36)
    if not capture.start():
        print(f"[SENTRA ERROR] {capture.error_message}")
        return 1

    print("[SENTRA] Initializing vision detector and object tracker...")
    detector = VisionDetector(mock_mode=mock_camera)
    tracker = ObjectTracker()

    print("[SENTRA] Initializing zones, rule engine, and local database...")
    default_zones = [
        SecurityZone(
            zone_id="zone_restricted_alpha",
            name="Restricted Zone Alpha",
            polygon=[(620, 160), (880, 160), (880, 520), (620, 520)],
            is_restricted=True,
            active=True
        ),
        SecurityZone(
            zone_id="zone_lobby_center",
            name="Lobby Transit Corridor",
            polygon=[(80, 200), (450, 200), (450, 600), (80, 600)],
            is_restricted=False,
            active=True,
            capacity_threshold=4
        )
    ]
    observer = ActivityObserver(zones=default_zones)
    event_engine = EventRuleEngine(observer=observer)
    database = EventDatabase()
    alert_manager = AlertManager()

    # Pre-populate timeline with recent persisted events from SQLite
    saved_events = database.get_recent_events(limit=10)
    for evt in reversed(saved_events):
        event_engine.recent_events.append(evt)

    running = True
    frame_count = 0
    is_paused = False
    show_zones = True

    print("[SENTRA] Reactive pipeline running! Press [ESC] to quit.")

    try:
        while running:
            # Handle Pygame user input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_SPACE:
                        is_paused = not is_paused
                    elif event.key == pygame.K_z:
                        show_zones = not show_zones
                    elif event.key == pygame.K_m:
                        alert_manager.toggle_mute()
                    elif event.key == pygame.K_c:
                        # Confirm latest event
                        if event_engine.recent_events:
                            latest = event_engine.recent_events[-1]
                            latest.review_status = ReviewStatus.CONFIRMED
                            database.update_review_status(latest.event_id, ReviewStatus.CONFIRMED)
                    elif event.key == pygame.K_d:
                        # Dismiss latest event
                        if event_engine.recent_events:
                            latest = event_engine.recent_events[-1]
                            latest.review_status = ReviewStatus.DISMISSED
                            database.update_review_status(latest.event_id, ReviewStatus.DISMISSED)

            if not is_paused:
                # 1. Fetch live frame
                frame_bgr, ts = capture.get_latest_frame()

                if frame_bgr is not None:
                    # 2. Vision Detection
                    detections = detector.detect(frame_bgr, ts)

                    # 3. Anonymous Tracking
                    tracks = tracker.update(detections, ts)

                    # 4. Multi-Frame Event Rule Evaluation
                    new_events = event_engine.evaluate_frame(tracks, ts)

                    # 5. Persist and Dispatch Alerts
                    for evt in new_events:
                        database.save_event(evt)
                        alert_manager.dispatch(evt)
                        DesktopNotifier.notify(evt)
            else:
                tracks = list(tracker.tracks.values())
                frame_bgr, ts = capture.get_latest_frame()

            # --- Presentation Rendering ---
            screen.fill(COLOR_BACKGROUND)

            # Draw camera feed in the main viewport
            if frame_bgr is not None:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                # Resize to fit viewport height beneath status bar
                view_h = screen_h - 36
                frame_resized = cv2.resize(frame_rgb, (viewport_w, view_h))
                frame_surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                screen.blit(frame_surf, (0, 36))

            # Draw live bounding boxes, tracks, and zones
            render_live_overlays(
                screen,
                tracks=tracks if 'tracks' in locals() else [],
                zones=default_zones,
                show_zones=show_zones,
                font=font,
                small_font=small_font,
                view_width=viewport_w,
                view_height=screen_h
            )

            # Draw top diagnostics and privacy status bar
            render_top_status_bar(
                screen,
                fps=capture.fps,
                active_tracks_count=len(tracks) if 'tracks' in locals() else 0,
                is_paused=is_paused,
                font=font,
                small_font=small_font,
                screen_width=screen_w
            )

            # Draw right-hand timeline drawer
            render_timeline_panel(
                screen,
                events=event_engine.recent_events,
                font=font,
                small_font=small_font,
                x=viewport_w,
                y=36,
                width=timeline_w,
                height=screen_h - 36
            )

            if not headless:
                pygame.display.flip()

            clock.tick(TARGET_FPS)
            frame_count += 1

            if max_frames > 0 and frame_count >= max_frames:
                print(f"[SENTRA] Reached requested max_frames={max_frames}, exiting cleanly.")
                running = False

    finally:
        capture.stop()
        pygame.quit()

    return 0


def main():
    parser = argparse.ArgumentParser(description="SENTRA — Scene Observation & Event Intelligence")
    parser.add_argument("--headless", action="store_true", help="Run in headless SDL mode")
    parser.add_argument("--test-frames", type=int, default=0, help="Run for N frames and exit")
    parser.add_argument("--mock-camera", action="store_true", help="Use synthetic mock video generator")
    parser.add_argument("--camera", type=str, default=str(DEFAULT_CAMERA_INDEX), help="Camera index (0, 1, 2) or stream URL (http://..., rtsp://...)")
    parser.add_argument("--list-cameras", action="store_true", help="Scan and list detected camera devices")
    args = parser.parse_args()

    if args.list_cameras:
        print("[SENTRA] Scanning for connected camera devices...")
        cams = CameraSource.list_available_cameras()
        if cams:
            print(f"[SENTRA] Found {len(cams)} camera device(s): {cams}")
            for c in cams:
                print(f"  -> Camera index: {c} (Run with: python app/main.py --camera {c})")
        else:
            print("[SENTRA] No physical camera devices detected.")
        return 0

    return run(
        headless=args.headless,
        max_frames=args.test_frames,
        mock_camera=args.mock_camera,
        camera_source_arg=args.camera
    )


if __name__ == "__main__":
    sys.exit(main())
