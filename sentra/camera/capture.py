"""Threaded, double-buffered frame capture worker preventing driver I/O latency."""
import math
import platform
import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from sentra.camera.source import CameraSource, CameraSourceType
from sentra.config.defaults import (
    DEFAULT_CAM_HEIGHT,
    DEFAULT_CAM_WIDTH,
    DEFAULT_MIRROR_MODE,
)


class CameraCapture:
    """
    Asynchronous capture worker running on a dedicated thread.
    Exposes latest frames via thread-safe lock with zero preview stalls.
    """

    def __init__(
        self,
        source: CameraSource,
        width: int = DEFAULT_CAM_WIDTH,
        height: int = DEFAULT_CAM_HEIGHT,
        mirror: bool = DEFAULT_MIRROR_MODE,
    ):
        self.source = source
        self.target_width = width
        self.target_height = height
        self.mirror = mirror

        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._latest_frame: Optional[np.ndarray] = None
        self._frame_timestamp: float = 0.0
        self._frame_count: int = 0
        self._fps: float = 0.0
        self._is_active: bool = False
        self._error_message: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    def start(self) -> bool:
        """Start background frame polling thread."""
        if self._running:
            return True

        if self.source.source_type == CameraSourceType.SYNTHETIC_MOCK:
            self._is_active = True
            self._running = True
            self._thread = threading.Thread(target=self._mock_worker, daemon=True)
            self._thread.start()
            return True

        # Open physical device or stream
        is_stream = self.source.source_type == CameraSourceType.STREAM_URL
        api_preference = cv2.CAP_ANY if is_stream else (cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY)

        try:
            self._cap = cv2.VideoCapture(self.source.target, api_preference)
            if not self._cap or not self._cap.isOpened():
                self._cap = cv2.VideoCapture(self.source.target)

            if not self._cap or not self._cap.isOpened():
                self._is_active = False
                self._error_message = f"Could not connect to camera source: {self.source.display_name}"
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)

            self._is_active = True
            self._error_message = None
            self._running = True
            self._thread = threading.Thread(target=self._capture_worker, daemon=True)
            self._thread.start()
            return True

        except Exception as e:
            self._is_active = False
            self._error_message = str(e)
            return False

    def _capture_worker(self) -> None:
        """Background thread continuously polling video source."""
        fps_counter = 0
        fps_timer = time.time()

        while self._running:
            if not self._cap or not self._cap.isOpened():
                time.sleep(0.05)
                continue

            ret, frame = self._cap.read()
            if not ret or frame is None:
                # If reading from a video file, loop back to the start
                if self.source.source_type == CameraSourceType.VIDEO_FILE:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(0.02)
                    continue
                with self._lock:
                    self._is_active = False
                    self._error_message = "Camera read failed or feed lost"
                time.sleep(0.05)
                continue

            if self.mirror:
                frame = cv2.flip(frame, 1)

            now = time.time()
            fps_counter += 1
            if now - fps_timer >= 1.0:
                self._fps = fps_counter / (now - fps_timer)
                fps_counter = 0
                fps_timer = now

            with self._lock:
                self._latest_frame = frame
                self._frame_timestamp = now
                self._frame_count += 1
                self._is_active = True

            # Throttle slightly to avoid pegging CPU when capture is fast
            time.sleep(0.005)

    def _mock_worker(self) -> None:
        """Generates dynamic synthetic video frames for headless testing and CI."""
        w, h = self.target_width, self.target_height
        t0 = time.time()

        while self._running:
            t = time.time() - t0
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            frame[:] = (20, 24, 30)

            # Draw subtle grid
            for x in range(0, w, 80):
                cv2.line(frame, (x, 0), (x, h), (30, 36, 45), 1)
            for y in range(0, h, 80):
                cv2.line(frame, (0, y), (w, y), (30, 36, 45), 1)

            # Draw animated moving subject (simulated person blob)
            cx = int(w * 0.5 + math.sin(t * 1.5) * (w * 0.3))
            cy = int(h * 0.5 + math.cos(t * 1.0) * (h * 0.2))
            cv2.ellipse(frame, (cx, cy - 40), (25, 45), 0, 0, 360, (60, 160, 240), -1)
            cv2.circle(frame, (cx, cy - 95), 20, (255, 210, 160), -1)

            now = time.time()
            with self._lock:
                self._latest_frame = frame
                self._frame_timestamp = now
                self._frame_count += 1
                self._fps = 30.0

            time.sleep(1.0 / 30.0)

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], float]:
        """Atomically read the most recent captured frame and its timestamp."""
        with self._lock:
            if self._latest_frame is None:
                return None, 0.0
            return self._latest_frame.copy(), self._frame_timestamp

    def stop(self) -> None:
        """Gracefully release camera hardware and stop polling thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        if self._cap:
            self._cap.release()
            self._cap = None

        self._is_active = False
