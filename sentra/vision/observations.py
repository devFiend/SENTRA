"""Spatial zones and low-level physical observation extractors."""
from dataclasses import dataclass, field
import math
import time
from typing import Dict, List, Optional, Tuple
from sentra.vision.tracker import TrackedObject


@dataclass
class SecurityZone:
    """User-defined polygonal region of interest on the camera plane."""
    zone_id: str
    name: str
    polygon: List[Tuple[int, int]]  # Ordered list of (x, y) vertices
    is_restricted: bool = False
    active: bool = True
    capacity_threshold: int = 5

    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Ray-casting algorithm to test if a point is inside the polygon."""
        if len(self.polygon) < 3:
            return False

        px, py = point
        inside = False
        n = len(self.polygon)

        p1x, p1y = self.polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = self.polygon[i % n]
            if py > min(p1y, p2y):
                if py <= max(p1y, p2y):
                    if px <= max(p1x, p2x):
                        if p1y != p2y:
                            x_inters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or px <= x_inters:
                                inside = not inside
            p1x, p1y = p2x, p2y

        return inside


class ActivityObserver:
    """
    Extracts multi-track spatial observations, zone intersections, and dwell times.
    """

    def __init__(self, zones: Optional[List[SecurityZone]] = None):
        self.zones: List[SecurityZone] = zones or []
        self.track_zone_dwell: Dict[Tuple[int, str], float] = {}  # (track_id, zone_id) -> start_time
        self.item_stationary_time: Dict[int, float] = {}          # prop track_id -> first_seen_stationary_time

    def update_zone_dwells(self, tracks: List[TrackedObject], now: float) -> List[Tuple[TrackedObject, SecurityZone, float]]:
        """
        Evaluate which tracks are currently located inside active security zones.
        Returns list of (track, zone, dwell_duration_seconds).
        """
        dwells = []
        active_pairs = set()

        for track in tracks:
            anchor = track.ground_anchor
            for zone in self.zones:
                if not zone.active:
                    continue

                if zone.contains_point(anchor):
                    pair = (track.track_id, zone.zone_id)
                    active_pairs.add(pair)

                    if pair not in self.track_zone_dwell:
                        self.track_zone_dwell[pair] = now

                    dwell_sec = now - self.track_zone_dwell[pair]
                    dwells.append((track, zone, dwell_sec))

        # Clean expired pairs
        for pair in list(self.track_zone_dwell.keys()):
            if pair not in active_pairs:
                del self.track_zone_dwell[pair]

        return dwells
