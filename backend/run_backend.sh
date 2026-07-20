#!/usr/bin/env bash
set -euo pipefail

echo "Starting EDUAI backend (uvicorn)" 
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
