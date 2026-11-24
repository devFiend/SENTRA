"""Camera source abstractions, URL parsing, and device enumeration."""
from dataclasses import dataclass
from enum import Enum, auto
import os
import platform
from typing import List, Optional, Union
import cv2


class CameraSourceType(Enum):
    DEVICE_INDEX = auto()
    VIDEO_FILE = auto()
    STREAM_URL = auto()
    SYNTHETIC_MOCK = auto()


@dataclass
class CameraSource:
    """Represents a validated video input stream source."""
    source_type: CameraSourceType
    target: Union[int, str]
    display_name: str

    @classmethod
    def from_input(cls, source_arg: Union[int, str], mock_mode: bool = False) -> "CameraSource":
        """Factory creating and classifying a CameraSource from raw CLI argument."""
        if mock_mode:
            return cls(
                source_type=CameraSourceType.SYNTHETIC_MOCK,
                target="mock://synthetic",
                display_name="Synthetic Video Generator"
            )

        if isinstance(source_arg, int):
            return cls(
                source_type=CameraSourceType.DEVICE_INDEX,
                target=source_arg,
                display_name=f"Camera Device #{source_arg}"
            )

        source_str = str(source_arg).strip()
        if source_str.isdigit():
            idx = int(source_str)
            return cls(
                source_type=CameraSourceType.DEVICE_INDEX,
                target=idx,
                display_name=f"Camera Device #{idx}"
            )

        if "://" in source_str:
            return cls(
                source_type=CameraSourceType.STREAM_URL,
                target=source_str,
                display_name=f"Network Stream ({source_str})"
            )

        if os.path.exists(source_str):
            return cls(
                source_type=CameraSourceType.VIDEO_FILE,
                target=source_str,
                display_name=f"File: {os.path.basename(source_str)}"
            )

        # Fallback to device index 0
        return cls(
            source_type=CameraSourceType.DEVICE_INDEX,
            target=0,
            display_name="Default Camera Device #0"
        )

    @staticmethod
    def list_available_cameras(max_tested: int = 6) -> List[int]:
        """Scan system for active video capture indices (DirectShow on Windows)."""
        found = []
        api = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        for idx in range(max_tested):
            try:
                cap = cv2.VideoCapture(idx, api)
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        found.append(idx)
                    cap.release()
            except Exception:
                pass
        return found
