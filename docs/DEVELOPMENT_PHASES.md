# SENTRA — Development Phases Roadmap

> **Engineering Milestones, Deliverables, and Quality Acceptance Criteria**

---

## 🗺️ Phases Summary

```
[P0: Setup] ──> [P1: Camera] ──> [P2: Detection] ──> [P3: Tracking]
                                                           │
┌──────────────────────────────────────────────────────────┘
▼
[P4: Observations] ──> [P5: Events] ──> [P6: Alerts]
                                           │
┌──────────────────────────────────────────┘
▼
[P7: Activity Research] ──> [P8: UI & Privacy] ──> [P9: Release]
```

---

## Phase Details & Exit Criteria

### 🚀 Phase P0: Foundation & Environment Setup
- **Objective**: Establish modular workspace, configuration defaults, virtual environment, and logging.
- **Deliverables**:
  - Directory layout matching SENTRA architecture.
  - Pinned `requirements.txt` and `pyproject.toml`.
  - Global `config/defaults.py` with calibrated operational thresholds.
  - Structured console & file logging with log rotation.
  - Baseline sanity test suite in `tests/unit/test_env.py`.
- **Done When**: `pytest tests/` runs and passes cleanly; virtual environment auto-forwards.

---

### 📷 Phase P1: Threaded Camera Capture & Preview
- **Objective**: Rock-solid, non-blocking camera ingestion supporting USB webcams, files, and mock generators.
- **Deliverables**:
  - `CameraSource` abstraction (`sentra/camera/source.py`).
  - Threaded double-buffered `CameraCapture` (`sentra/camera/capture.py`).
  - Synthetic test frame generator for headless automated testing.
  - Live preview loop with real-time FPS counter and graceful shutdown (`app/main.py`).
- **Done When**: 60-frame preview runs smoothly without memory leaks or dropped thread deadlocks.

---

### 🔍 Phase P2: Multi-Object Detection Engine
- **Objective**: Integrate lightweight object detector for people and common contextual props.
- **Deliverables**:
  - `VisionDetector` interface supporting YOLO / ONNX / OpenCV DNN (`sentra/vision/detector.py`).
  - Class filtering for security contexts (`person`, `backpack`, `handbag`, `suitcase`, `bottle`).
  - Detection bounding box visualization with confidence tags and color-coded labels.
- **Done When**: Live video renders accurate bounding boxes with inference latency < 50ms on workstation hardware.

---

### 🎯 Phase P3: Anonymous Multi-Object Tracking
- **Objective**: Assign stable, short-lived anonymous IDs across frames to eliminate duplication.
- **Deliverables**:
  - IoU + Kalman Filter `ObjectTracker` (`sentra/vision/tracker.py`).
  - Trajectory centroid history buffer (last 30 frames).
  - Velocity estimation (pixels/sec in screen space).
  - People counter (current occupancy, total entrants).
- **Done When**: A person crossing the field of view retains a stable ID across brief occlusions without flickering.

---

### 📐 Phase P4: Spatial Zones & Activity Observations
- **Objective**: Enable user-defined polygonal zones and extract low-level physical observations.
- **Deliverables**:
  - Polygonal zone geometry editor with point-in-polygon testing (`sentra/vision/observations.py`).
  - Dwell time counter per track inside designated zones.
  - Sudden level drop detector (vertical centroid delta / bounding box aspect ratio).
  - Unattended stationary object detector.
- **Done When**: Unit tests verify zone containment, dwell thresholds, and vertical drop metrics.

---

### ⚡ Phase P5: Event Engine & Local Persistence
- **Objective**: Combine observations into structured, explainable event records stored in SQLite.
- **Deliverables**:
  - Strongly typed `EventRecord` schema with `AlertTier` classification (`sentra/events/schemas.py`).
  - Rules engine evaluating compound conditions with sliding-window debouncing (`sentra/events/engine.py`).
  - Local SQLite event store with indexed timestamps and review status (`sentra/storage/db.py`).
  - In-memory event timeline buffer.
- **Done When**: Candidate events generate explainable evidence notes and persist to local SQLite.

---

### 🔔 Phase P6: Alert Dispatcher & Local Notifications
- **Objective**: Dispatch local notifications and audio alerts without alert fatigue.
- **Deliverables**:
  - `AlertManager` with tier-based routing (`sentra/alerts/manager.py`).
  - Synthesized procedural audio cues (subtle chime for Tier 2 Review; urgent alert tone for Tier 3).
  - Cooldown and deduplication suppression matrix (`sentra/events/cooldowns.py`).
  - Cross-platform desktop notification service (`sentra/alerts/desktop.py`).
- **Done When**: Multiple rapid triggers in 5 seconds produce a single grouped alert record without sound stacking.

---

### 🔬 Phase P7: Advanced Activity Research (Altercations & Falls)
- **Objective**: Formulate heuristic multi-cue activity recognition for physical altercations and falls.
- **Deliverables**:
  - Multi-person altercation detector (`sentra/events/rules.py`):
    - Spatial convergence rate + velocity variance + bounding box overlap.
  - Multi-stage fall detector:
    - Rapid downward velocity + aspect ratio inversion (height < width) + ground stillness.
  - Transparent uncertainty scoring and explicit *"Possible..."* evidence labeling.
- **Done When**: Test clips with staged movement validate fall/altercation detection with logged evidence strings.

---

### 🖥️ Phase P8: Interactive UI & Privacy Controls
- **Objective**: Deliver a comprehensive desktop operator interface with live video, overlays, timeline, and privacy indicators.
- **Deliverables**:
  - Split-pane interface: Live Camera View + Event Timeline Drawer (`sentra/ui/live_view.py`).
  - Event review controls: **Confirm**, **Dismiss**, and **Add Operator Note**.
  - Visible Camera-Active privacy badge and emergency Stop button.
  - User settings dialog for alert sensitivities, zone polygons, and data retention policies.
- **Done When**: Operator can review events, toggle privacy states, and adjust zone boundaries interactively.

---

### 📦 Phase P9: Packaging, Release & Documentation
- **Objective**: Provide automated launchers, CI/CD workflows, documentation, and open-source licensing.
- **Deliverables**:
  - Windows launcher script (`setup.bat` and `run.bat`).
  - Cross-platform shell launcher (`setup.sh`).
  - GitHub Actions CI workflow executing pytest across matrix.
  - Complete `README.md`, `LICENSE` (Apache 2.0 / MIT), and contribution guides.
- **Done When**: Fresh clone on a clean machine installs and runs out of the box with zero errors.
