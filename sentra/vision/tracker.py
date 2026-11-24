"""Multi-object anonymous tracker with IoU association and trajectory analysis."""
from dataclasses import dataclass, field
import math
import time
from typing import Dict, List, Optional, Tuple

from sentra.config.defaults import (
    MAX_TRACK_AGE_FRAMES,
    MIN_TRACK_HITS,
    TRACK_IOU_MATCH_THRESHOLD,
)
from sentra.vision.detector import DetectedObject


@dataclass
class TrackedObject:
    """Represents a temporally stable anonymous track across video frames."""
    track_id: int
    class_name: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    history: List[Tuple[float, float, float]] = field(default_factory=list)  # (cx, cy, ts)
    velocity: Tuple[float, float] = (0.0, 0.0)  # (vx, vy) in px/sec
    speed: float = 0.0
    age_frames: int = 1
    hits: int = 1
    time_since_update: float = 0.0
    is_confirmed: bool = False

    @property
    def centroid(self) -> Tuple[float, float]:
        return (
            (self.bbox[0] + self.bbox[2]) * 0.5,
            (self.bbox[1] + self.bbox[3]) * 0.5
        )

    @property
    def ground_anchor(self) -> Tuple[float, float]:
        """Bottom-center coordinate representing ground plane contact point."""
        return (
            (self.bbox[0] + self.bbox[2]) * 0.5,
            float(self.bbox[3])
        )

    @property
    def width(self) -> int:
        return max(1, self.bbox[2] - self.bbox[0])

    @property
    def height(self) -> int:
        return max(1, self.bbox[3] - self.bbox[1])

    @property
    def aspect_ratio(self) -> float:
        """Height / Width ratio."""
        return float(self.height) / float(self.width)

    def update(self, detection: DetectedObject, timestamp: float) -> None:
        """Update track state with a newly associated detection."""
        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.age_frames += 1
        self.hits += 1
        self.time_since_update = 0.0

        if self.hits >= MIN_TRACK_HITS:
            self.is_confirmed = True

        cx, cy = self.centroid
        self.history.append((cx, cy, timestamp))
        if len(self.history) > 30:
            self.history.pop(0)

        # Estimate smoothed velocity from recent centroid history
        if len(self.history) >= 2:
            prev_x, prev_y, prev_t = self.history[-2]
            dt = max(1e-3, timestamp - prev_t)
            vx = (cx - prev_x) / dt
            vy = (cy - prev_y) / dt
            self.velocity = (vx, vy)
            self.speed = math.hypot(vx, vy)


def compute_iou(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
    """Calculate Intersection-over-Union between two bounding boxes."""
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    inter_w = max(0, x_b - x_a)
    inter_h = max(0, y_b - y_a)
    inter_area = inter_w * inter_h

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union_area = float(area_a + area_b - inter_area)

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class ObjectTracker:
    """
    Associates frame detections across time into anonymous tracked subjects.
    Maintains temporary IDs and velocity histories without storing biometrics.
    """

    def __init__(
        self,
        iou_threshold: float = TRACK_IOU_MATCH_THRESHOLD,
        max_age_frames: int = MAX_TRACK_AGE_FRAMES
    ):
        self.iou_threshold = iou_threshold
        self.max_age_frames = max_age_frames
        self._next_id: int = 1
        self.tracks: Dict[int, TrackedObject] = {}
        self.total_tracked_count: int = 0

    def update(self, detections: List[DetectedObject], timestamp: float) -> List[TrackedObject]:
        """Update tracker with frame detections and return active confirmed tracks."""
        active_track_ids = list(self.tracks.keys())
        unmatched_detections = set(range(len(detections)))
        matched_pairs: List[Tuple[int, int]] = []

        if active_track_ids and detections:
            # Build IoU cost matrix
            matches = []
            for t_id in active_track_ids:
                track = self.tracks[t_id]
                for d_idx, det in enumerate(detections):
                    if track.class_name == det.class_name:
                        iou = compute_iou(track.bbox, det.bbox)
                        if iou >= self.iou_threshold:
                            matches.append((iou, t_id, d_idx))

            # Greedy sort by highest IoU overlap
            matches.sort(key=lambda x: x[0], reverse=True)
            used_tracks = set()
            used_dets = set()

            for iou, t_id, d_idx in matches:
                if t_id not in used_tracks and d_idx not in used_dets:
                    used_tracks.add(t_id)
                    used_dets.add(d_idx)
                    matched_pairs.append((t_id, d_idx))
                    unmatched_detections.discard(d_idx)

        # Update matched tracks
        for t_id, d_idx in matched_pairs:
            self.tracks[t_id].update(detections[d_idx], timestamp)

        # Increment age for unmatched tracks
        matched_track_ids = {p[0] for p in matched_pairs}
        for t_id in list(self.tracks.keys()):
            if t_id not in matched_track_ids:
                self.tracks[t_id].time_since_update += 1.0
                if self.tracks[t_id].time_since_update > self.max_age_frames:
                    del self.tracks[t_id]

        # Birth new tracks for remaining detections
        for d_idx in unmatched_detections:
            det = detections[d_idx]
            new_id = self._next_id
            self._next_id += 1
            self.total_tracked_count += 1

            track = TrackedObject(
                track_id=new_id,
                class_name=det.class_name,
                bbox=det.bbox,
                confidence=det.confidence
            )
            track.history.append((det.centroid[0], det.centroid[1], timestamp))
            self.tracks[new_id] = track

        return list(self.tracks.values())
