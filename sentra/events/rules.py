"""Evidence-based observation rules for falls, altercations, zones, and unattended items."""
from abc import ABC, abstractmethod
import math
import time
from typing import Dict, List, Optional, Tuple

from sentra.config.defaults import (
    ALTERCATION_CLOSING_SPEED_PX,
    ALTERCATION_IOU_OVERLAP,
    CROWD_DENSITY_THRESHOLD,
    FALL_ASPECT_RATIO_THRESHOLD,
    FALL_STILLNESS_DURATION_SEC,
    FALL_VELOCITY_DROP_PX_PER_SEC,
    UNATTENDED_ITEM_PROXIMITY_PX,
    UNATTENDED_ITEM_STATIONARY_SEC,
)
from sentra.events.schemas import AlertTier, EventRecord, EventType
from sentra.vision.observations import ActivityObserver, SecurityZone
from sentra.vision.pose import PostureAnalyzer, PostureState
from sentra.vision.tracker import TrackedObject, compute_iou


class BaseEventRule(ABC):
    """Abstract base for candidate event evaluators."""

    @abstractmethod
    def evaluate(
        self,
        tracks: List[TrackedObject],
        observer: ActivityObserver,
        now: float
    ) -> List[EventRecord]:
        pass


class FallDetectionRule(BaseEventRule):
    """
    Evaluates sudden vertical level drops followed by prone posture and sustained floor stillness.
    """

    def __init__(self):
        # track_id -> (drop_timestamp, start_stillness_timestamp)
        self._drop_candidates: Dict[int, Tuple[float, float]] = {}

    def evaluate(
        self,
        tracks: List[TrackedObject],
        observer: ActivityObserver,
        now: float
    ) -> List[EventRecord]:
        events = []
        active_ids = {t.track_id for t in tracks if t.class_name == "person"}

        for track in tracks:
            if track.class_name != "person":
                continue

            tid = track.track_id
            posture = PostureAnalyzer.classify_posture(track)
            is_dropping, drop_speed = PostureAnalyzer.evaluate_level_drop(track, window_sec=0.4)

            # Stage 1: Detect downward velocity spike
            if is_dropping and drop_speed >= FALL_VELOCITY_DROP_PX_PER_SEC:
                if tid not in self._drop_candidates:
                    self._drop_candidates[tid] = (now, now)

            # Stage 2: Verify candidate entered prone posture and remains stationary
            if tid in self._drop_candidates:
                drop_time, still_start = self._drop_candidates[tid]

                if posture == PostureState.PRONE_HORIZONTAL and track.speed < 45.0:
                    still_duration = now - still_start
                    if still_duration >= FALL_STILLNESS_DURATION_SEC:
                        events.append(EventRecord.create(
                            event_type=EventType.POSSIBLE_FALL,
                            tier=AlertTier.URGENT_REVIEW,
                            confidence=0.85,
                            evidence_notes=[
                                f"Subject #{tid} underwent rapid downward vertical drop ({drop_speed:.1f} px/s)",
                                f"Bounding box aspect ratio inverted to {track.aspect_ratio:.2f} (prone posture)",
                                f"Subject has remained stationary at ground level for {still_duration:.1f}s"
                            ],
                            track_ids=[tid],
                            now=now
                        ))
                        # Clear to avoid re-triggering immediately
                        del self._drop_candidates[tid]
                elif track.speed > 120.0 and (now - drop_time > 1.5):
                    # Subject recovered and is moving actively — cancel candidate
                    del self._drop_candidates[tid]

        # Cleanup expired candidates
        for tid in list(self._drop_candidates.keys()):
            if tid not in active_ids:
                del self._drop_candidates[tid]

        return events


class AltercationRule(BaseEventRule):
    """
    Evaluates multi-person rapid convergence, close spatial bounding overlap, and trajectory volatility.
    """

    def evaluate(
        self,
        tracks: List[TrackedObject],
        observer: ActivityObserver,
        now: float
    ) -> List[EventRecord]:
        events = []
        persons = [t for t in tracks if t.class_name == "person" and t.is_confirmed]
        n = len(persons)

        if n < 2:
            return events

        for i in range(n):
            for j in range(i + 1, n):
                p1 = persons[i]
                p2 = persons[j]

                # 1. Spatial distance between centroids
                dist = math.hypot(p1.centroid[0] - p2.centroid[0], p1.centroid[1] - p2.centroid[1])
                iou = compute_iou(p1.bbox, p2.bbox)

                # 2. Closing speed / relative velocity
                rel_vx = p1.velocity[0] - p2.velocity[0]
                rel_vy = p1.velocity[1] - p2.velocity[1]
                closing_speed = math.hypot(rel_vx, rel_vy)

                # 3. Dynamic volatility
                is_converging = closing_speed >= ALTERCATION_CLOSING_SPEED_PX
                is_overlapping = (iou >= ALTERCATION_IOU_OVERLAP) or (dist < 80.0)
                is_high_energy = (p1.speed > 250.0 and p2.speed > 250.0)

                if is_overlapping and (is_converging or is_high_energy):
                    events.append(EventRecord.create(
                        event_type=EventType.POSSIBLE_ALTERCATION,
                        tier=AlertTier.REVIEW,
                        confidence=0.78,
                        evidence_notes=[
                            f"Subjects #{p1.track_id} and #{p2.track_id} in high-proximity overlap (IoU: {iou:.2f}, Dist: {dist:.1f}px)",
                            f"Closing relative velocity: {closing_speed:.1f} px/s",
                            f"Sustained multi-person dynamic interaction over consecutive frames"
                        ],
                        track_ids=[p1.track_id, p2.track_id],
                        now=now
                    ))

        return events


class ZoneIntrusionRule(BaseEventRule):
    """
    Evaluates tracks entering active restricted polygonal zones.
    """

    def evaluate(
        self,
        tracks: List[TrackedObject],
        observer: ActivityObserver,
        now: float
    ) -> List[EventRecord]:
        events = []
        dwells = observer.update_zone_dwells(tracks, now)

        for track, zone, dwell_sec in dwells:
            if zone.is_restricted and dwell_sec <= 1.0:
                events.append(EventRecord.create(
                    event_type=EventType.ZONE_INTRUSION,
                    tier=AlertTier.REVIEW,
                    confidence=0.95,
                    evidence_notes=[
                        f"Subject #{track.track_id} entered restricted zone '{zone.name}'",
                        f"Ground contact coordinate: ({track.ground_anchor[0]:.1f}, {track.ground_anchor[1]:.1f})"
                    ],
                    track_ids=[track.track_id],
                    location_zone=zone.name,
                    now=now
                ))

        return events


class CrowdingRule(BaseEventRule):
    """
    Evaluates area occupancy exceeding configured density thresholds.
    """

    def evaluate(
        self,
        tracks: List[TrackedObject],
        observer: ActivityObserver,
        now: float
    ) -> List[EventRecord]:
        events = []
        persons = [t for t in tracks if t.class_name == "person"]

        for zone in observer.zones:
            if not zone.active:
                continue

            count = sum(1 for p in persons if zone.contains_point(p.ground_anchor))
            if count >= zone.capacity_threshold:
                events.append(EventRecord.create(
                    event_type=EventType.CROWDING_THRESHOLD,
                    tier=AlertTier.OBSERVATION,
                    confidence=0.90,
                    evidence_notes=[
                        f"Zone '{zone.name}' occupancy reached {count} persons (threshold: {zone.capacity_threshold})",
                        f"Active subjects in zone: {[p.track_id for p in persons if zone.contains_point(p.ground_anchor)]}"
                    ],
                    track_ids=[p.track_id for p in persons if zone.contains_point(p.ground_anchor)],
                    location_zone=zone.name,
                    now=now
                ))

        return events
