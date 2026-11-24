"""Unit tests for Phase P0: Environment, dependencies, and configuration constants."""
import sys
import pytest


def test_python_version():
    """Verify supported Python runtime version (3.10+)."""
    assert sys.version_info >= (3, 10), "SENTRA requires Python 3.10 or higher"


def test_core_imports():
    """Verify required core dependencies import cleanly."""
    import cv2
    import numpy as np
    import pygame

    assert cv2.__version__ is not None
    assert np.__version__ is not None
    assert pygame.__version__ is not None


def test_config_constants():
    """Verify SENTRA configuration constants are populated and valid."""
    from sentra.config.defaults import (
        APP_NAME,
        APP_VERSION,
        DEFAULT_CAM_WIDTH,
        DEFAULT_CAM_HEIGHT,
        FALL_VELOCITY_DROP_PX_PER_SEC,
        ALTERCATION_CLOSING_SPEED_PX,
        TIER_1_OBSERVATION,
        TIER_2_REVIEW,
        TIER_3_URGENT_REVIEW,
    )

    assert APP_NAME == "SENTRA"
    assert APP_VERSION == "0.1.0"
    assert DEFAULT_CAM_WIDTH > 0 and DEFAULT_CAM_HEIGHT > 0
    assert FALL_VELOCITY_DROP_PX_PER_SEC > 0
    assert ALTERCATION_CLOSING_SPEED_PX > 0
    assert TIER_1_OBSERVATION < TIER_2_REVIEW < TIER_3_URGENT_REVIEW
