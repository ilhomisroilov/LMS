#!/usr/bin/env bash
# Uses the backend virtualenv + installs bot deps into it.
set -e
cd "$(dirname "$0")/../bot"
source ../backend/.venv/bin/activate
pip install -q -r requirements.txt
export $(grep -v '^#' ../.env | xargs) 2>/dev/null || true
python -m main
