# SENTRA Documentation Suite

> **Local-First Camera-Based Scene Observation & Event Intelligence**  
> *"Observe visible evidence, explain uncertainty, and route important events to a human for review."*

---

## 🧭 Navigation Hub

Welcome to the official developer and operator documentation for **SENTRA**. SENTRA is an open-source, local-first computer vision system that monitors video streams, tracks people and common objects, observes temporal activity patterns (such as falls, crowding, unattended items, and physical altercations), and produces an explainable, evidence-based event timeline with human-in-the-loop controls.

```
                    ┌─────────────────────────┐
                    │      SENTRA CORE        │
                    │   Local-First Vision    │
                    └────────────┬────────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
┌────┴────────────┐     ┌────────┴───────────┐     ┌─────────┴─────────┐
│     VISION      │     │    EVENT ENGINE    │     │   HUMAN REVIEW    │
│  YOLO + Tracker │ ──> │ Rule Evaluation &  │ ──> │ Explainable Alert │
│  + Pose Cues    │     │ Temporal Debounce  │     │ Timeline (Local)  │
└─────────────────┘     └────────────────────┘     └───────────────────┘
```

---

## 📚 Document Registry

| Document | Description | Target Audience |
|---|---|---|
| **[PRD.md](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/PRD.md)** | Full Product Requirements Document: mission, ethical boundaries, alert tiers, functional requirements, and non-goals. | Product Managers, Contributors, Auditors |
| **[ARCHITECTURE.md](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/ARCHITECTURE.md)** | Technical system architecture: decoupled threaded pipeline, bounded queues, memory layout, and module breakdown. | Core Engineers, Systems Architects |
| **[DEVELOPMENT_PHASES.md](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/DEVELOPMENT_PHASES.md)** | Step-by-step roadmap from Phase P0 (setup) to Phase P9 (release), detailing exact deliverables and exit criteria. | Developers, QA Engineers |
| **[EVENT_TAXONOMY_AND_RULES.md](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/EVENT_TAXONOMY_AND_RULES.md)** | Deep dive into detection heuristics: possible altercations, falls, zone intrusions, unattended items, and alert deduplication. | CV Engineers, Event Analysts |
| **[TESTING_STRATEGY.md](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/TESTING_STRATEGY.md)** | Verification protocols: mock camera feeds, synthetic edge cases, false-positive benchmarking, and hardware benchmarks. | QA Engineers, Contributors |
| **[CONTRIBUTING.md](file:///C:/Users/devFiend/Desktop/Web%20Dev%20Projects/SENTRA/docs/CONTRIBUTING.md)** | Contribution standards, local-first development ethics, code formatting, PR workflows, and licensing. | Open-Source Contributors |

---

## 🛡️ Core Tenets & Ethical Boundaries

1. **Local-First & Offline**: Zero network dependency for core operations. No telemetry, no cloud inference, no accounts or mandatory API keys.
2. **Strict Privacy**: **NO** facial recognition, **NO** biometric matching, **NO** demographic categorization, and **NO** emotion detection.
3. **Transparent Uncertainty**: SENTRA never asserts absolute claims about intent or criminality. Events are explicitly tagged as *"Possible..."* and highlight visible evidence factors for human verification.
4. **Human in the Loop**: System actions route to an operator for confirmation or dismissal. SENTRA never takes autonomous punitive or enforcement actions.
5. **Opt-In Storage**: Continuous video recording is disabled by default. Short clips or event metadata are retained only upon explicit operator consent.
