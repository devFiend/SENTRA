# SENTRA

```
  ███████╗███████╗███╗   ██╗████████╗██████╗  █████╗ 
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝███████║
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██╔══██║
  ███████║███████╗██║ ╚████║   ██║   ██║  ██║██║  ██║
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
  Camera-Based Scene Observation & Event Intelligence
```

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Local-First](https://img.shields.io/badge/Privacy-100%25_Local--First-brightgreen.svg)](#privacy-guarantees)
[![Open Source](https://img.shields.io/badge/Open_Source-True-blue.svg)](#)

> **"Observe visible evidence, explain uncertainty, and route important events to a human for review."**

SENTRA is a local-first computer vision system that monitors video streams, tracks people and common objects with short-lived anonymous IDs, detects temporal activity patterns (such as falls, crowding, unattended items, and physical altercations), and compiles an explainable, timestamped event timeline with human-in-the-loop review.

---

## 🌟 Key Features

- **100% Local-First & Zero Telemetry**: Operates completely offline without cloud APIs, mandatory user accounts, or external network calls.
- **Explainable Event Intelligence**: Generates structured event records backed by explicit visual evidence notes (e.g., *"Subject #12 dropped 1.4m in 0.25s and remained prone for 4.2s"*).
- **Multi-Frame Temporal Rules**: Detects multi-frame scenarios such as sudden falls, physical altercations, unattended items, and restricted zone intrusions.
- **Anonymous Tracking**: High-performance IoU + Kalman filter tracker that maintains temporary tracks without biometric face recognition.
- **Configurable Alert Tiers**: 3-tier notification structure (Observation, Review, Urgent Review) with sliding-window deduplication to avoid alert fatigue.
- **Human-Centric Review**: Interactive timeline equipped with one-click **Confirm**, **Dismiss**, and **Annotate** controls.

---

## 🛡️ Responsible AI & Privacy Guarantees

SENTRA is built from the ground up on strict ethical principles:
- ❌ **NO Face Recognition**: Never identifies individuals or creates biometric facial embeddings.
- ❌ **NO Emotion or Demographics**: Never makes assumptions about intent, emotion, or demographics.
- ❌ **NO Autonomous Actions**: Never initiates punitive decisions, automatic lockouts, or dispatch.
- 🔒 **Opt-In Storage**: Continuous video recording is disabled by default.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11, 3.12, or 3.14
- Web camera, IP stream, or video file

### 2. Installation
```bash
git clone https://github.com/devFiend/SENTRA.git
cd SENTRA

python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux / macOS

pip install -r requirements.txt
```

### 3. Launching SENTRA
```bash
# Launch live camera observation
python app/main.py

# Launch using a specific camera index (e.g., iPhone / Camo)
python app/main.py --camera 1

# Launch in synthetic mock video mode (for automated testing / demos)
python app/main.py --mock-camera
```

---

## 📖 Documentation Suite

The complete technical specification and developer guides are available in `docs/`:
- **[PRD & Product Roadmap](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/PRD.md)**
- **[System Architecture & Pipeline](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/ARCHITECTURE.md)**
- **[Development Phases (P0–P9)](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/DEVELOPMENT_PHASES.md)**
- **[Event Taxonomy & Rules](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/EVENT_TAXONOMY_AND_RULES.md)**
- **[Testing & Benchmarking Strategy](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/TESTING_STRATEGY.md)**
- **[Contributing Guidelines](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/CONTRIBUTING.md)**

---

## 📄 License
Licensed under the [Apache License, Version 2.0](LICENSE).
