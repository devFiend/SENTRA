"""Unit tests for CameraSource and CameraCapture."""
import time
import pytest
from sentra.camera.capture import CameraCapture
from sentra.camera.source import CameraSource, CameraSourceType


def test_camera_source_parsing():
    """Verify source factory correctly identifies indices, URLs, files, and mock."""
    s_idx = CameraSource.from_input("0")
    assert s_idx.source_type == CameraSourceType.DEVICE_INDEX
    assert s_idx.target == 0

    s_url = CameraSource.from_input("http://192.168.1.10:8080/video")
    assert s_url.source_type == CameraSourceType.STREAM_URL
    assert "192.168.1.10" in s_url.target

    s_mock = CameraSource.from_input(0, mock_mode=True)
    assert s_mock.source_type == CameraSourceType.SYNTHETIC_MOCK


def test_mock_camera_capture_lifecycle():
    """Verify synthetic mock camera starts, generates frames, and terminates cleanly."""
    source = CameraSource.from_input(0, mock_mode=True)
    capture = CameraCapture(source, width=640, height=480)

    assert capture.start() is True
    assert capture.is_active is True

    # Allow worker thread to generate frames
    time.sleep(0.1)
    frame, ts = capture.get_latest_frame()

    assert frame is not None
    assert frame.shape == (480, 640, 3)
    assert ts > 0.0
    assert capture.frame_count > 0

    capture.stop()
    assert capture.is_active is False
