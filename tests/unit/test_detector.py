"""Unit tests for VisionDetector and DetectedObject."""
import numpy as np
import pytest
from sentra.vision.detector import DetectedObject, VisionDetector


def test_detected_object_properties():
    """Verify geometry, aspect ratio, and centroid calculations."""
    obj = DetectedObject(class_id=0, class_name="person", confidence=0.88, bbox=(100, 100, 200, 350))
    assert obj.width == 100
    assert obj.height == 250
    assert obj.centroid == (150.0, 225.0)
    assert obj.aspect_ratio == 2.5


def test_vision_detector_mock_mode():
    """Verify mock vision detector generates valid detections on synthetic frame."""
    detector = VisionDetector(mock_mode=True)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    dets = detector.detect(frame, timestamp=1.0)
    assert len(dets) >= 1
    assert dets[0].class_name == "person"
    assert dets[0].confidence > 0.8
