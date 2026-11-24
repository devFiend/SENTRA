# SENTRA — Quality Assurance & Testing Strategy

> **Verification Protocols, Synthetic Test Feeds, False Positive Benchmarks, and Privacy Audits**

---

## 1. Testing Philosophy

SENTRA's event engine makes decisions that affect physical safety and operator attention. Therefore, tests must verify not only algorithmic correctness under ideal conditions, but also robustness against video noise, occlusions, edge cases, and strict compliance with ethical privacy boundaries.

```
       ┌─────────────────────────────┐
       │   Automated Pytest Suite    │
       │   (Unit + Mock Integration) │
       └──────────────┬──────────────┘
                      │
     ┌────────────────┼────────────────┐
     ▼                ▼                ▼
┌──────────┐    ┌──────────┐     ┌───────────┐
│ Tracking │    │  Event   │     │  Privacy  │
│ Accuracy │    │  Rules   │     │  Audits   │
└──────────┘    └──────────┘     └───────────┘
```

---

## 2. Test Suite Architecture

### 2.1 Unit Tests (`tests/unit/`)
- **`test_env.py`**: Python runtime version check, dependency imports, config constants.
- **`test_camera.py`**: Frame capture lifecycle, mock feed generation, reconnection handling.
- **`test_detector.py`**: Detection output schemas, bounding box clamping, label filtering.
- **`test_tracker.py`**: Kalman filter state prediction, IoU cost matrix, track birth/death lifecycle, ID stability.
- **`test_zones.py`**: Ray-casting point-in-polygon tests, convex and concave zone boundaries.
- **`test_event_rules.py`**: Deterministic simulation of falls, altercations, unattended items, and crowding.
- **`test_cooldowns.py`**: Deduplication sliding window, alert suppression timers.
- **`test_storage.py`**: SQLite schema creation, CRUD operations, query filters, transaction rollbacks.

### 2.2 Integration Tests (`tests/integration/`)
- **`test_pipeline.py`**: End-to-end ingestion: Mock Camera ➔ Detection ➔ Tracker ➔ Event Engine ➔ SQLite.
- **`test_headless.py`**: Running the application headless for 100+ frames to verify zero memory leaks and graceful shutdown.

---

## 3. False-Positive Benchmarks & Edge-Case Datasets

To ensure low alert noise, test datasets must challenge the system with:
1. **Benign Gestures & Actions**:
   - Picking up a dropped pen from the floor (must **not** trigger a sustained fall alert).
   - Friendly hugs or high-fives (must **not** trigger an altercation alert).
   - Sitting down on a chair or couch (smooth level drop without sudden shock).
   - Brief pauses while walking (must **not** trigger loitering/unattended flags).
2. **Environmental Noise**:
   - Flickering fluorescent lighting or sudden shadows.
   - Moving shadows or reflections in glass windows.
   - People carrying backpacks on their backs (must remain associated with the person).

---

## 4. Privacy & Compliance Audit Tests

- **No Face Recognition**: Codebase audit verifying no facial landmark or face embedding models exist in the dependencies or import trees.
- **Default Storage Off**: Automated test verifying that running SENTRA for 200 frames writes zero video files to disk unless opt-in recording is explicitly enabled in settings.
- **Temporary ID Scrubbing**: Test verifying that track IDs reset between sessions and do not persist across restarts.
