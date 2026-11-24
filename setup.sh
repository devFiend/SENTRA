#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  SENTRA -- Local-First Scene Observation Setup (Unix)  "
echo "========================================================"

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete! Run with: python3 app/main.py"
