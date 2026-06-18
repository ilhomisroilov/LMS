#!/usr/bin/env bash
# One-time backend setup: venv, deps, migrate, seed.
set -e
cd "$(dirname "$0")/../backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
[ -f ../.env ] || cp ../.env.example ../.env
export $(grep -v '^#' ../.env | xargs) 2>/dev/null || true
alembic upgrade head
python -m app.seed
echo "✅ Backend ready. Start it with: scripts/run_backend.sh"
