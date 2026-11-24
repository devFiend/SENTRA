"""Global configuration constants and operational thresholds for SENTRA."""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = str(DATA_DIR / "sentra_events.db")

os.makedirs(DATA_DIR, exist_ok=True)

# Application Identity
APP_NAME = "SENTRA"
APP_VERSION = "0.1.0"
WINDOW_TITLE = "SENTRA — Camera-Based Scene Observation & Event Intelligence"

# Display & Rendering
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
TARGET_FPS = 30

# Camera Ingestion Defaults
DEFAULT_CAMERA_INDEX = 0
DEFAULT_CAM_WIDTH = 1280
DEFAULT_CAM_HEIGHT = 720
DEFAULT_MIRROR_MODE = False

# Detection & Tracking Calibration
DETECTION_CONFIDENCE_THRESHOLD = 0.45
DETECTION_NMS_IOU_THRESHOLD = 0.50
MAX_TRACK_AGE_FRAMES = 30
MIN_TRACK_HITS = 3
TRACK_IOU_MATCH_THRESHOLD = 0.30

# Event Observation Thresholds
FALL_VELOCITY_DROP_PX_PER_SEC = 350.0  # Downward vertical speed required to consider a fall
FALL_ASPECT_RATIO_THRESHOLD = 0.90     # Height / Width ratio indicating prone/horizontal posture
FALL_STILLNESS_DURATION_SEC = 3.0      # Sustained floor stillness to confirm fall assistance check

ALTERCATION_CLOSING_SPEED_PX = 380.0   # Closing speed between 2+ subjects indicating rapid convergence
ALTERCATION_IOU_OVERLAP = 0.18         # Bounding box overlap threshold
ALTERCATION_DIRECTION_CHANGES = 5      # Trajectory reversals in sliding window

UNATTENDED_ITEM_STATIONARY_SEC = 30.0  # Time item remains unmoving
UNATTENDED_ITEM_PROXIMITY_PX = 220.0   # Distance to nearest person before marked unattended

CROWD_DENSITY_THRESHOLD = 6            # Default headcount triggering crowd capacity review

# Alert Tiers
TIER_1_OBSERVATION = 1
TIER_2_REVIEW = 2
TIER_3_URGENT_REVIEW = 3

# Visual Palettes (Cybernetic / Modern Surveillance Theme)
COLOR_BACKGROUND = (14, 18, 24)
COLOR_PANEL_BG = (20, 26, 36)
COLOR_BORDER = (40, 52, 72)
COLOR_TEXT_PRIMARY = (240, 244, 250)
COLOR_TEXT_MUTED = (140, 155, 175)

COLOR_PERSON_TRACK = (64, 196, 255)     # Cyan
COLOR_OBJECT_TRACK = (255, 204, 0)      # Amber
COLOR_ZONE_RESTRICTED = (255, 64, 64)   # Hazard Red
COLOR_ZONE_NORMAL = (0, 230, 118)       # Green
COLOR_ALERT_TIER1 = (80, 160, 255)      # Blue/Cyan
COLOR_ALERT_TIER2 = (255, 179, 0)       # Amber
COLOR_ALERT_TIER3 = (255, 45, 85)       # Red/Crimson
