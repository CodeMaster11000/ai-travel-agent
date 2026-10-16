#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it before continuing."
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

mkdir -p data
echo
echo "Python dependencies installed."
echo "Next, install/start Ollama and run: ollama pull qwen2.5:3b"
echo "Then use ./run_api.sh and ./run_ui.sh in separate terminals."
