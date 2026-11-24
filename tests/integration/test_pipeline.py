"""Integration test for full end-to-end headless SENTRA execution."""
import os
import pytest
from app.main import run


def test_sentra_headless_integration_pipeline():
    """Verify camera, detector, tracker, rules engine, storage, and UI loop execute cleanly for 20 frames."""
    exit_code = run(
        headless=True,
        max_frames=20,
        mock_camera=True,
        camera_source_arg=0
    )
    assert exit_code == 0
