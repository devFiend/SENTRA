"""Posture analysis and bodily orientation cues for fall and altercation detection."""
from enum import Enum, auto
from typing import Optional, Tuple
from sentra.config.defaults import FALL_ASPECT_RATIO_THRESHOLD
from sentra.vision.tracker import TrackedObject


class PostureState(Enum):
    UPRIGHT = auto()
    CROUCHING = auto()
    PRONE_HORIZONTAL = auto()
    UNKNOWN = auto()


class PostureAnalyzer:
    """
    Evaluates physical posture state and vertical velocity drops from bounding box geometry.
    Zero face recognition or biometric profiling.
    """

    @staticmethod
    def classify_posture(track: TrackedObject) -> PostureState:
        """Classify posture from bounding box aspect ratio (H / W)."""
        ar = track.aspect_ratio
        if ar >= 1.6:
            return PostureState.UPRIGHT
        elif ar >= 1.1:
            return PostureState.CROUCHING
        elif ar < FALL_ASPECT_RATIO_THRESHOLD:
            return PostureState.PRONE_HORIZONTAL
        return PostureState.UNKNOWN

    @staticmethod
    def evaluate_level_drop(track: TrackedObject, window_sec: float = 0.5) -> Tuple[bool, float]:
        """
        Evaluate whether the subject underwent an abrupt vertical level drop.
        Returns (is_dropping, drop_velocity_px_per_sec).
        In screen space, downward motion increases Y.
        """
        if len(track.history) < 2:
            return False, 0.0

        curr_x, curr_y, curr_t = track.history[-1]
        earliest_x, earliest_y, earliest_t = track.history[0]

        # Find position ~window_sec ago
        target_t = curr_t - window_sec
        ref_y = earliest_y
        ref_t = earliest_t

        for hx, hy, ht in reversed(track.history[:-1]):
            if ht <= target_t:
                ref_y = hy
                ref_t = ht
                break

        dt = max(1e-3, curr_t - ref_t)
        delta_y = curr_y - ref_y  # Positive when moving downward
        vertical_speed = delta_y / dt

        is_dropping = (vertical_speed > 300.0)
        return is_dropping, vertical_speed
