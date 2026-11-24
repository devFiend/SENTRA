"""Privacy assurance controls and runtime settings."""
from dataclasses import dataclass


@dataclass
class PrivacySettings:
    """Operator privacy controls: recording state, retention, and camera controls."""
    recording_enabled: bool = False
    retention_days: int = 7
    blur_unconfirmed_faces: bool = False
    show_camera_active_led: bool = True
