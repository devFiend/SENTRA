# Contributing to SENTRA

Thank you for your interest in contributing to **SENTRA**! SENTRA is dedicated to building local-first, privacy-respecting computer vision and event intelligence tools.

---

## 🏛️ Code of Conduct & Ethical Commitments

Contributors must strictly respect SENTRA's core responsible AI charter:
1. **Never add biometric identification**: PRs introducing face recognition, demographic profiling, emotion detection, or identity matching will be rejected immediately.
2. **Local-first only**: No telemetry, analytics pings, or mandatory cloud dependencies.
3. **Transparent uncertainty**: Always structure event records with explicit confidence metrics and observable visual evidence.

---

## 🛠️ Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/devFiend/SENTRA.git
   cd SENTRA
   ```
2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the automated test suite**:
   ```bash
   pytest tests/ -v
   ```

---

## 🧪 Testing Your Changes

Before opening a pull request, ensure all tests pass cleanly:
```bash
pytest tests/ -v
python app/main.py --headless --mock-camera --test-frames 30
```

---

## 📝 Pull Request Guidelines

- Include clear unit tests for new observation rules or tracking features.
- Update documentation in `docs/` if adding new configuration parameters or event types.
- Follow PEP 8 style guidelines with clear type annotations.
