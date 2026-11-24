"""Multi-class object detection engine with MediaPipe Pose Landmarker and robust fallback."""
from dataclasses import dataclass
import os
from pathlib import Path
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np

from sentra.config.defaults import DETECTION_CONFIDENCE_THRESHOLD, BASE_DIR


@dataclass
class DetectedObject:
    """Represents a single bounding box detection within a frame."""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)

    @property
    def width(self) -> int:
        return max(1, self.bbox[2] - self.bbox[0])

    @property
    def height(self) -> int:
        return max(1, self.bbox[3] - self.bbox[1])

    @property
    def centroid(self) -> Tuple[float, float]:
        return (
            (self.bbox[0] + self.bbox[2]) * 0.5,
            (self.bbox[1] + self.bbox[3]) * 0.5
        )

    @property
    def aspect_ratio(self) -> float:
        """Height / Width ratio (e.g. > 1.8 for standing person)."""
        return float(self.height) / float(self.width)


class VisionDetector:
    """
    Object detection provider.
    Evaluates people and common context props (backpack, handbag, suitcase).
    Supports MediaPipe Pose Landmarker, HOG person detection, and MOG2 foreground modeling.
    """

    def __init__(
        self,
        confidence_threshold: float = DETECTION_CONFIDENCE_THRESHOLD,
        mock_mode: bool = False
    ):
        self.confidence_threshold = confidence_threshold
        self.mock_mode = mock_mode
        self._landmarker = None
        self._hog = None
        self._bg_subtractor = None

        if not self.mock_mode:
            self._init_mediapipe()
            if self._landmarker is None:
                self._init_hog()
            self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=25, detectShadows=True
            )

    def _init_mediapipe(self) -> None:
        """Initialize MediaPipe Pose Landmarker for high-accuracy human detection."""
        try:
            import mediapipe as mp
            from mediapipe.tasks.python import BaseOptions, vision

            model_path = BASE_DIR / "models" / "pose_landmarker_lite.task"
            if not model_path.exists():
                model_path.parent.mkdir(parents=True, exist_ok=True)
                import urllib.request
                url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
                urllib.request.urlretrieve(url, str(model_path))

            if model_path.exists():
                options = vision.PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=str(model_path)),
                    running_mode=vision.RunningMode.IMAGE,
                    num_poses=6,
                    min_pose_detection_confidence=0.45,
                    min_pose_presence_confidence=0.45
                )
                self._landmarker = vision.PoseLandmarker.create_from_options(options)
                print("[SENTRA] MediaPipe Pose Landmarker initialized.")
        except Exception as e:
            print(f"[SENTRA] MediaPipe Pose Landmarker bypassed ({e}); using OpenCV pipeline.")
            self._landmarker = None

    def _init_hog(self) -> None:
        """Initialize OpenCV HOG person detector if available."""
        try:
            hog_cls = getattr(cv2, "HOGDescriptor", None)
            if hog_cls:
                self._hog = hog_cls()
                self._hog.setSVMDetector(cv2.HOGDescriptor.getDefaultPeopleDetector())
        except Exception:
            self._hog = None

    def detect(self, frame: np.ndarray, timestamp: float) -> List[DetectedObject]:
        """Run object detection on the incoming BGR video frame."""
        if frame is None:
            return []

        if self.mock_mode:
            return self._detect_mock(frame, timestamp)

        h, w = frame.shape[:2]
        detections: List[DetectedObject] = []

        # 1. MediaPipe Pose Landmarker (Accurate single/multi person body detection)
        if self._landmarker is not None:
            try:
                import mediapipe as mp
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                res = self._landmarker.detect(mp_img)

                if res and res.pose_landmarks:
                    for pose in res.pose_landmarks:
                        xs = [lm.x for lm in pose]
                        ys = [lm.y for lm in pose]
                        visibilities = [lm.visibility for lm in pose if hasattr(lm, "visibility")]
                        mean_vis = float(np.mean(visibilities)) if visibilities else 0.85

                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)

                        # 12% padding to comfortably enclose head, hands, and feet
                        pad_w = (max_x - min_x) * 0.12
                        pad_h = (max_y - min_y) * 0.12

                        x1 = max(0, int((min_x - pad_w) * w))
                        y1 = max(0, int((min_y - pad_h) * h))
                        x2 = min(w - 1, int((max_x + pad_w) * w))
                        y2 = min(h - 1, int((max_y + pad_h) * h))

                        box_w = x2 - x1
                        box_h = y2 - y1

                        if box_w >= 30 and box_h >= 60:
                            detections.append(DetectedObject(
                                class_id=0,
                                class_name="person",
                                confidence=round(min(1.0, max(0.5, mean_vis)), 2),
                                bbox=(x1, y1, x2, y2)
                            ))

                    if detections:
                        return detections
            except Exception:
                pass

        # 2. HOG Person Detection (Fallback when MediaPipe is unavailable)
        scale = 1.0
        if w > 640:
            scale = 640.0 / w
            small_frame = cv2.resize(frame, (640, int(h * scale)))
        else:
            small_frame = frame

        if self._hog is not None:
            try:
                boxes, weights = self._hog.detectMultiScale(
                    small_frame,
                    winStride=(8, 8),
                    padding=(4, 4),
                    scale=1.05
                )

                for (bx, by, bw, bh), weight in zip(boxes, weights):
                    conf = float(weight) if isinstance(weight, (int, float)) else float(weight[0])
                    orig_x1 = max(0, min(w - 1, int(bx / scale)))
                    orig_y1 = max(0, min(h - 1, int(by / scale)))
                    orig_x2 = max(0, min(w - 1, int((bx + bw) / scale)))
                    orig_y2 = max(0, min(h - 1, int((by + bh) / scale)))

                    if orig_x2 > orig_x1 and orig_y2 > orig_y1:
                        detections.append(DetectedObject(
                            class_id=0,
                            class_name="person",
                            confidence=min(1.0, max(0.5, conf)),
                            bbox=(orig_x1, orig_y1, orig_x2, orig_y2)
                        ))
            except Exception:
                pass

        # 3. MOG2 Motion Foreground Analysis with Contour Union Merging (Fallback)
        if not detections and self._bg_subtractor is not None:
            fg_mask = self._bg_subtractor.apply(small_frame)
            _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            raw_boxes = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1200 * (scale ** 2):
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    raw_boxes.append((
                        max(0, min(w - 1, int(bx / scale))),
                        max(0, min(h - 1, int(by / scale))),
                        max(0, min(w - 1, int((bx + bw) / scale))),
                        max(0, min(h - 1, int((by + bh) / scale)))
                    ))

            # Merge adjacent / fragmented body parts into unified human bounding boxes
            merged_boxes = self._merge_overlapping_boxes(raw_boxes, proximity_px=50)
            for bx1, by1, bx2, by2 in merged_boxes:
                bh = by2 - by1
                bw = bx2 - bx1
                if bh > 90 and bw > 35:
                    ar = bh / float(bw)
                    cls_name = "person" if (ar >= 1.2 or bh > 140) else "object"
                    detections.append(DetectedObject(
                        class_id=0 if cls_name == "person" else 1,
                        class_name=cls_name,
                        confidence=0.75,
                        bbox=(bx1, by1, bx2, by2)
                    ))

        return detections

    @staticmethod
    def _merge_overlapping_boxes(
        boxes: List[Tuple[int, int, int, int]],
        proximity_px: int = 40
    ) -> List[Tuple[int, int, int, int]]:
        """Merge bounding boxes that overlap or are situated close together."""
        if not boxes:
            return []

        merged = []
        remaining = list(boxes)

        while remaining:
            curr = remaining.pop(0)
            x1, y1, x2, y2 = curr
            changed = True
            while changed:
                changed = False
                unmerged = []
                for other in remaining:
                    ox1, oy1, ox2, oy2 = other
                    # Check proximity overlap
                    if not (x2 + proximity_px < ox1 or ox2 + proximity_px < x1 or
                            y2 + proximity_px < oy1 or oy2 + proximity_px < y1):
                        # Merge boxes
                        x1 = min(x1, ox1)
                        y1 = min(y1, oy1)
                        x2 = max(x2, ox2)
                        y2 = max(y2, oy2)
                        changed = True
                    else:
                        unmerged.append(other)
                remaining = unmerged
            merged.append((x1, y1, x2, y2))

        return merged

    def _detect_mock(self, frame: np.ndarray, timestamp: float) -> List[DetectedObject]:
        """Synthesize detections matching mock video frame animated subject."""
        h, w = frame.shape[:2]
        t = timestamp
        import math
        cx = int(w * 0.5 + math.sin(t * 1.5) * (w * 0.3))
        cy = int(h * 0.5 + math.cos(t * 1.0) * (h * 0.2))

        x1 = max(0, cx - 35)
        y1 = max(0, cy - 120)
        x2 = min(w, cx + 35)
        y2 = min(h, cy + 50)

        return [
            DetectedObject(
                class_id=0,
                class_name="person",
                confidence=0.92,
                bbox=(x1, y1, x2, y2)
            )
        ]
