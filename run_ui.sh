#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi
source .venv/bin/activate
exec python -m app.ui
