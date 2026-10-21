#!/usr/bin/env bash
# GKMKB teammate setup for macOS / Linux (Debian/Ubuntu apt or macOS brew).
# Run from anywhere:  bash scripts/setup.sh      Add --yes to skip prompts.
set -euo pipefail
cd "$(dirname "$0")/.."

YES=0; [ "${1:-}" = "--yes" ] && YES=1

have() { command -v "$1" >/dev/null 2>&1; }

pm_install() {  # label, apt-pkg, brew-pkg
  if [ "$YES" -eq 0 ]; then read -r -p "$1 missing. Install? (y/n) " a; [ "$a" = "y" ] || { echo "$1 required"; exit 1; }; fi
  if have brew; then brew install "$3"
  elif have apt-get; then sudo apt-get update && sudo apt-get install -y "$2"
  else echo "Install $1 by hand, then re-run."; exit 1; fi
}

have git     || pm_install git git git
have python3 || pm_install python3 python3 python@3.12
python3 -c 'import venv' 2>/dev/null || pm_install python3-venv python3-venv python@3.12
have node    || pm_install node nodejs node
have gh      || pm_install "GitHub CLI" gh gh
have docker  || echo "[todo] Install Docker (Docker Desktop or docker.io + compose plugin) by hand."

[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
[ -f requirements.txt ]     && .venv/bin/python -m pip install -r requirements.txt
[ -f requirements-dev.txt ] && .venv/bin/python -m pip install -r requirements-dev.txt

if [ -f dashboard/package.json ]; then (cd dashboard && npm install); else echo "[skip] dashboard/package.json not created yet"; fi

[ -f .env ] || { [ -f .env.example ] && cp .env.example .env && echo "[ok] .env created"; } || true

if have docker && [ -f docker-compose.yml ]; then docker compose pull || echo "[warn] docker compose pull failed"; fi

if have git && { [ -z "$(git config --global user.name)" ] || [ -z "$(git config --global user.email)" ]; }; then
  echo "[todo] Set your git name and email (once):"
  echo '       git config --global user.name "Your Name"'
  echo '       git config --global user.email "you@example.com"'
fi

if have gh && ! gh auth status >/dev/null 2>&1; then echo "[todo] Run: gh auth login"; fi

if find . -name 'test_*.py' -not -path './.venv/*' | grep -q .; then .venv/bin/python -m pytest -q; else echo "[skip] no tests yet"; fi

echo "Setup done. Activate env:  source .venv/bin/activate"
echo "Workflow skills (optional, once): see docs/WorkflowSetup.md"
echo "Next: read docs/Onboarding.md. It tells you exactly what to do and what not to do."
