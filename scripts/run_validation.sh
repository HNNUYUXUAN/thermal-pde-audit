#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
if python3 -c "import pytest" >/dev/null 2>&1; then
  python3 -m pytest -q
else
  echo "pytest_not_installed=true"
  echo "fallback=python3 scripts/run_cpu_checks.py"
  python3 scripts/run_cpu_checks.py
fi
