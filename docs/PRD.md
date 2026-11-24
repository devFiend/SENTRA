# SENTRA — Product Requirements Document (PRD)

> **Document Version**: 1.0.0 • **Status**: Approved • **Distribution**: Open-Source

---

## 1. Executive Summary

**SENTRA** is a local-first computer vision and scene observation system. It observes live video feeds, detects people and objects, tracks them across frames with short-lived anonymous IDs, identifies notable activity cues over time, and generates an explainable, timestamped event timeline. 

Unlike primitive frame-by-frame motion detectors, SENTRA maintains temporal scene memory to evaluate multi-frame context (e.g., sudden level drops indicating a possible fall, or stationary objects left behind after people depart). Crucially, SENTRA adheres to strict responsible AI boundaries: it does not attempt to "read minds," identify faces, or infer criminal intent. It presents visible evidence with calibrated confidence levels so human operators can make informed decisions.

---

## 2. Vision, Goals & Key Objectives

- **Local-First Autonomous Processing**: Run real-time detection and tracking on consumer/workstation hardware (e.g., laptop CPUs or entry-level mobile GPUs like the Quadro P1000) without external cloud services.
- **Temporal State Observation**: Maintain short-lived track histories to distinguish benign transient movements from sustained events.
- **Multi-Class Scene Intelligence**: Detect people, bags/backpacks, vehicles, and custom user-defined polygonal zones.
- **Explainable Event Generation**: Each generated event provides specific evidence notes (e.g., *"Subject #14 dropped 1.2m in 0.28s and remained stationary on floor for 4.0s"*).
- **Human-Centric Review**: Equip operators with one-click review, confirmation, dismissal, and annotation capabilities.

---

## 3. Strict Non-Goals & Responsible Boundaries

To ensure ethical, safe, and legally compliant operation, the following capabilities are explicitly declared **NON-GOALS**:

| Category | Policy / Constraint |
|---|---|
| **Biometrics & Identity** | ❌ **Strictly Prohibited**: No facial recognition, re-identification, face embeddings, demographic classification (race, gender, age), or license plate OCR. |
| **Intent & Emotion** | ❌ **Strictly Prohibited**: No inference of internal states, aggression, criminality, guilt, or emotional affect from facial expressions or body postures. |
| **Autonomous Action** | ❌ **Strictly Prohibited**: No automatic lockouts, alarm dispatches, physical door locking, or punitive decisions without human review. |
| **Covert Surveillance** | ❌ **Strictly Prohibited**: Visual camera-active indicators must be permanently visible in the UI, accompanied by an immediate stop button. |
| **Unchecked Weapon Claims** | ❌ **Strictly Prohibited**: Objects will not be declared as weapons based solely on visual bounding box class; ambiguity is preserved. |
| **Default Recording** | ❌ **Disabled by Default**: Continuous video recording is off. Event clips are retained only when explicitly configured by the user. |

---

## 4. Primary Use Cases

```
  [Live Video Feed]
          │
          ▼
┌──────────────────┐
│ Object Tracking  │ ──> Track #12 (Person), Track #05 (Backpack)
└─────────┬────────┘
          │
          ├──> [Sudden Height Change + Floor Dwell]  ──> 🚨 Possible Fall Event (Tier 2)
          ├──> [Rapid Convergence + High Velocity]   ──> ⚠️ Possible Altercation (Tier 2)
          ├──> [Owner Leaves + 45s Stationary]       ──> 📦 Unattended Item Event (Tier 1)
          └──> [Crossing Polygon Boundary]           ──> 🛑 Zone Intrusion Event (Tier 2)
```

### 4.1 Possible Physical Altercation
- **Observation**: Multiple people moving into close spatial proximity with rapid velocity spikes, erratic directional shifts, and sustained physical overlap over consecutive frames.
- **Behavior**: Flag a review event explaining observed movement cues without claiming criminality or assault.

### 4.2 Possible Fall
- **Observation**: Sudden vertical bounding box / posture level drop exceeding threshold speed, followed by sustained horizontal ground-level stillness (> 3.0s).
- **Behavior**: Prompt an immediate operator assistance check.

### 4.3 Unattended Item
- **Observation**: A bag, box, or item remains stationary for a configurable duration (e.g., > 30s) after the person who brought it into the scene moves beyond a defined radius.
- **Behavior**: Record a timeline observation without asserting ownership or danger.

### 4.4 Restricted Zone Intrusion
- **Observation**: A person's ground contact point (bottom-center of bounding box) enters a user-defined polygonal zone during active hours.
- **Behavior**: Generate a zone alert with entry timestamp and trajectory snapshot.

### 4.5 Crowding / Capacity Monitoring
- **Observation**: The number of detected people within a defined region exceeds a user-configured limit.
- **Behavior**: Alert on density threshold with live occupancy count.

---

## 5. Event Hierarchy & Alert Tiers

| Tier | Classification | Description | UI Action | Sound / Dispatch |
|:---:|:---|:---|:---|:---|
| **Tier 1** | **Observation** | Passive notable scene event (e.g., zone transit, occupancy change). | Added to timeline list; subtle indicator. | Silent / No interruptive alert. |
| **Tier 2** | **Review** | Notable event with multiple corroborating indicators (e.g., unattended bag, fall candidate). | Amber highlight, badge badge counter incremented. | Soft chime; prompts operator check. |
| **Tier 3** | **Urgent Review** | High-confidence critical event requiring immediate human attention (e.g., severe fall, altercation). | Red visual pulse, pinned top banner, review dialog. | Distinct warning tone; urgent notification. |

---

## 6. Functional Requirements Matrix

| Req ID | Requirement Description | Priority | Target Phase |
|---|---|:---:|:---:|
| **FR-01** | Support webcam (USB/DirectShow), video file playback, and IP RTSP/HTTP streams. | **Must** | P1 |
| **FR-02** | Display real-time video preview with FPS, inference latency, and hardware diagnostics. | **Must** | P1 |
| **FR-03** | Detect people and everyday objects with bounding boxes, labels, and confidence metrics. | **Must** | P2 |
| **FR-04** | Maintain anonymous track IDs across frames with occlusion recovery and count statistics. | **Must** | P3 |
| **FR-05** | Provide user-configurable polygonal security zones with inclusion/exclusion filters. | **Should** | P4 |
| **FR-06** | Structure all observations into immutable event records with timestamps and evidence notes. | **Must** | P5 |
| **FR-07** | Interactive timeline with search, filtering, and operator Confirm / Dismiss controls. | **Must** | P5 / P8 |
| **FR-08** | Configurable local audio alerts and desktop notifications per severity tier. | **Should** | P6 |
| **FR-09** | Local SQLite persistence for event history, zone definitions, and user settings. | **Must** | P5 |
| **FR-10** | Optional post-event short clip recording with user-configurable retention days. | **Later** | P8 |
| **FR-11** | Export event metadata to structured JSON and CSV reports. | **Later** | P8 |

---

## 7. Target Hardware & Performance Constraints

- **Primary Target Workstation**: HP ZBook (Intel Core i7, 32 GB RAM, NVIDIA Quadro P1000 4 GB VRAM / CPU Fallback).
- **Secondary Target**: Standard desktop/laptop running on 4+ core CPU without dedicated GPU.
- **Performance Budget**:
  - Live preview: Consistent **30+ FPS**.
  - Detection & Tracking: **≥ 15 FPS** (with decoupled threaded frame queues to prevent preview stutter).
  - CPU utilization: **< 45%** on modern quad-core processors.
  - VRAM footprint: **< 1.5 GB** when GPU acceleration is active.
