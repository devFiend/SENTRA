"""Unit tests for ObjectTracker, IoU matching, and track persistence."""
import pytest
from sentra.vision.detector import DetectedObject
from sentra.vision.tracker import ObjectTracker, compute_iou


def test_iou_calculation():
    """Verify bounding box IoU calculation accuracy."""
    box_a = (100, 100, 200, 200)  # Area = 10000
    box_b = (100, 100, 200, 200)  # Identical
    assert compute_iou(box_a, box_b) == 1.0

    box_c = (300, 300, 400, 400)  # Disjoint
    assert compute_iou(box_a, box_c) == 0.0

    box_d = (150, 100, 250, 200)  # 50% overlap width
    assert 0.3 < compute_iou(box_a, box_d) < 0.4


def test_object_tracker_association_and_stability():
    """Verify tracker maintains stable anonymous IDs across consecutive frames."""
    tracker = ObjectTracker(iou_threshold=0.3)

    # Frame 1: Person at (100, 100, 180, 300)
    det1 = DetectedObject(class_id=0, class_name="person", confidence=0.9, bbox=(100, 100, 180, 300))
    tracks_f1 = tracker.update([det1], timestamp=1.0)

    assert len(tracks_f1) == 1
    t1_id = tracks_f1[0].track_id

    # Frame 2: Person shifts slightly to (105, 102, 185, 302)
    det2 = DetectedObject(class_id=0, class_name="person", confidence=0.92, bbox=(105, 102, 185, 302))
    tracks_f2 = tracker.update([det2], timestamp=1.033)

    assert len(tracks_f2) == 1
    assert tracks_f2[0].track_id == t1_id  # Stable ID preserved!
    assert tracks_f2[0].age_frames == 2
    assert tracks_f2[0].speed > 0.0
