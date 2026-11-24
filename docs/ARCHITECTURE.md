# SENTRA — Architecture & Engineering Specification

> **System Topology, Concurrency Architecture, and Dataflow Pipelines**

---

## 1. System Overview

SENTRA is structured as a decoupled, multi-threaded reactive pipeline. Video acquisition, AI inference, track association, temporal observation, and UI rendering execute in synchronized threads communicating via bounded, drop-oldest queues. This ensures that camera capture and the UI preview remain buttery-smooth (30–60 FPS) even if heavy computer vision models run at 15–20 FPS on resource-constrained hardware.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SENTRA SYSTEM TOPOLOGY                             │
└─────────────────────────────────────────────────────────────────────────────────┘

 [ Video Source ]  (Webcam / File / RTSP / Mock Feed)
        │
        ▼
 ┌───────────────┐        ┌───────────────────┐
 │ CameraCapture │ ──┬──> │ UI Preview Render │ (60 FPS Display Surface)
 └───────────────┘   │    └───────────────────┘
   (Capture Thread)  │
                     ▼
          [ Bounded Frame Queue ] (Queue size = 2, drop oldest)
                     │
                     ▼
             ┌───────────────┐
             │ VisionDetector│ (YOLOv8 / LiteRT / OpenCV DNN)
             └───────┬───────┘
                     │ Detections (boxes, labels, confidence)
                     ▼
             ┌───────────────┐
             │ ObjectTracker │ (Kalman Filter + IoU Tracker, Anonymous IDs)
             └───────┬───────┘
                     │ Tracks (ID, history, velocity, posture)
                     ▼
             ┌────────────────────┐
             │ ActivityObserver   │ (Level drop, dwell, zones, trajectory)
             └───────┬────────────┘
                     │ Raw Observations
                     ▼
             ┌────────────────────┐
             │ EventRuleEngine    │ (Temporal aggregation, debouncing, cooldowns)
             └───────┬────────────┘
                     │ Deduplicated Event Records
                     ▼
      ┌───────────────────────────────┐
      │                               │
      ▼                               ▼
┌───────────────┐           ┌───────────────────┐
│ Local SQLite  │           │   AlertManager    │
│ Event Storage │           │  (Audio & Desktop)│
└───────────────┘           └───────────────────┘
```

---

## 2. Component Breakdown

### 2.1 Camera Layer (`sentra/camera/`)
- **`source.py`**: Abstraction over hardware devices (DirectShow, MSMF), video files (`.mp4`, `.avi`), and IP streams (RTSP / HTTP MJPEG).
- **`capture.py`**: High-performance capture worker on a dedicated daemon thread. Double-buffered frame grabbing prevents driver blocking.

### 2.2 Vision Layer (`sentra/vision/`)
- **`detector.py`**: Object detection engine supporting YOLO models (YOLOv8n / YOLOv8s) and lightweight CPU backends. Detects classes: `person`, `backpack`, `handbag`, `suitcase`, `bottle`, `cell phone`.
- **`tracker.py`**: Multi-object tracker maintaining temporal track state (anonymous ID, bounding box centroid history, smoothed velocity vector, age, time since last detection). Implements Hungarian/greedy IoU association with Kalman state prediction.
- **`pose.py`**: Posture analyzer for person tracks. Computes aspect ratio, orientation angle, vertical centroid velocity, and ground-level status.
- **`observations.py`**: Atomic observation extractors (e.g., `ZoneObservation`, `LevelDropObservation`, `DwellObservation`, `ProximityClusterObservation`).

### 2.3 Event Engine (`sentra/events/`)
- **`schemas.py`**: Strongly typed data models (`EventRecord`, `AlertTier`, `ReviewStatus`, `EvidenceNote`).
- **`rules.py`**: Composable rule evaluators:
  - `FallDetectionRule`: Triggered by rapid downward vertical velocity + sustained ground posture.
  - `AltercationRule`: Triggered by rapid convergence of 2+ people + erratic velocity swings + close bounding box overlap.
  - `UnattendedItemRule`: Stationary item whose associated person has departed beyond 250 px for > 30s.
  - `ZoneIntrusionRule`: Ground contact point intersecting a polygon boundary.
  - `CrowdingRule`: People count within a zone exceeding configured threshold.
- **`cooldowns.py`**: Sliding-window deduplication and alert suppression to prevent notification spam.
- **`engine.py`**: Pipeline coordinator connecting tracker outputs to active rules and emitting events.

### 2.4 Alert Layer (`sentra/alerts/`)
- **`manager.py`**: Priority dispatcher routing events to UI banners, local audio chimes, and OS notifications.
- **`desktop.py`**: Cross-platform desktop notification integration (Windows toast notifications, macOS alerts, Linux libnotify).

### 2.5 Storage Layer (`sentra/storage/`)
- **`db.py`**: Local SQLite database connection with WAL (Write-Ahead Logging) mode enabled for high concurrency.
- **`repositories.py`**: Event, zone, and setting repositories providing clean CRUD operations and query filters.

### 2.6 User Interface (`sentra/ui/`)
- **`live_view.py`**: Real-time HUD renderer with bounding box overlays, anonymous track ID badges, trajectory trails, and zone polygons.
- **`timeline.py`**: Interactive scrolling event timeline showing timestamp, tier badge, evidence summary, and quick review controls (**Confirm**, **Dismiss**).
- **`settings.py`**: On-screen control panel for zone editing, sensitivity sliders, camera source selection, and privacy controls.

---

## 3. Data Flow & Concurrency Model

```
Thread 1: Camera I/O Thread (30 - 60 Hz)
  cv2.VideoCapture.read() ──> [Atomic Buffer Lock] ──> Frame Available Flag

Thread 2: Vision & Event Processing Thread (15 - 30 Hz)
  Frame Preprocessing ──> YOLO Inference ──> IoU Tracker ──> Rule Engine ──> SQLite

Thread 3: Main UI & Rendering Loop (60 Hz)
  Fetch Latest Frame ──> Blit Overlays ──> Render Timeline ──> Handle User Input
```

### Queue Bounding Policy
To prevent latency buildup when AI inference takes longer than frame intervals:
- Bounded queue capacity = `1` (or `2`).
- When a new frame arrives from the camera, if the queue is full, the oldest frame is discarded immediately.
- This guarantees **zero latency lag** — inference always operates on the most current real-world frame.

---

## 4. Hardware Optimization & Fallback Strategy

For systems such as the user's HP ZBook (Quadro P1000 4 GB VRAM / Intel i7):
1. **CUDA / TensorRT Acceleration**: When an NVIDIA GPU is detected and CUDA is available, YOLO tensors run on device.
2. **OpenVINO / ONNX Runtime / CPU**: Automatic fallback to optimized CPU inference with INT8 or FP16 precision.
3. **Adaptive Frame Skipping**: If inference exceeds 65 ms per frame, the detector automatically skips 1 frame out of 2 while the Kalman filter continues interpolating track trajectories seamlessly.
