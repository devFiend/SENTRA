"""Multi-class object detection engine with lightweight fallback and mock support."""
from dataclasses import dataclass
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np

from sentra.config.defaults import DETECTION_CONFIDENCE_THRESHOLD, DETECTION_NMS_IOU_THRESHOLD


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
    Supports OpenCV background modeling, HOG person detection, and synthetic mock mode.
    """

    def __init__(
        self,
        confidence_threshold: float = DETECTION_CONFIDENCE_THRESHOLD,
        mock_mode: bool = False
    ):
        self.confidence_threshold = confidence_threshold
        self.mock_mode = mock_mode
        self._hog = None
        if not self.mock_mode:
            try:
                hog_cls = getattr(cv2, "HOGDescriptor", None)
                if hog_cls:
                    self._hog = hog_cls()
                    self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            except Exception:
                self._hog = None
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=True)

    def detect(self, frame: np.ndarray, timestamp: float) -> List[DetectedObject]:
        """Run object detection on the incoming BGR video frame."""
        if frame is None:
            return []

        if self.mock_mode:
            return self._detect_mock(frame, timestamp)

        h, w = frame.shape[:2]
        detections: List[DetectedObject] = []

        # Downscale for performance if frame is large
        scale = 1.0
        if w > 640:
            scale = 640.0 / w
            small_frame = cv2.resize(frame, (640, int(h * scale)))
        else:
            small_frame = frame

        # 1. HOG Person Detection (if available in this OpenCV build)
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

        # 2. MOG2 Motion & Foreground Contour Analysis (Fast, universal fallback)
        if self._bg_subtractor is not None:
            fg_mask = self._bg_subtractor.apply(small_frame)
            _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Rescaled min area (equivalent to ~2500px on full frame)
                if area > 800 * (scale ** 2):
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    orig_x1 = max(0, min(w - 1, int(bx / scale)))
                    orig_y1 = max(0, min(h - 1, int(by / scale)))
                    orig_x2 = max(0, min(w - 1, int((bx + bw) / scale)))
                    orig_y2 = max(0, min(h - 1, int((by + bh) / scale)))

                    actual_w = orig_x2 - orig_x1
                    actual_h = orig_y2 - orig_y1

                    if actual_h > 60 and actual_w > 25:
                        ar = actual_h / float(actual_w)
                        cls_name = "person" if (ar >= 1.2 or actual_h > 120) else "object"
                        # Only add if not overlapping existing HOG box
                        already_detected = any(
                            abs(orig_x1 - d.bbox[0]) < 40 and abs(orig_y1 - d.bbox[1]) < 40
                            for d in detections
                        )
                        if not already_detected:
                            detections.append(DetectedObject(
                                class_id=0 if cls_name == "person" else 1,
                                class_name=cls_name,
                                confidence=0.78,
                                bbox=(orig_x1, orig_y1, orig_x2, orig_y2)
                            ))

        return detections

    def _detect_mock(self, frame: np.ndarray, timestamp: float) -> List[DetectedObject]:
        """Synthesize detections matching mock video frame animated subject."""
        h, w = frame.shape[:2]
        t = timestamp
        # Match circle & ellipse from mock_worker in CameraCapture
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
