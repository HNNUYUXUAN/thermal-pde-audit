#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_ENV="/usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh"

cd "${PROJECT_ROOT}"
if test -f "${SDK_ENV}"; then
  set +u
  # shellcheck disable=SC1090
  source "${SDK_ENV}" >/dev/null
  set -u
fi
export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python3 -m thermal_pde_audit.cli run \
  --input examples/standard_heat.json \
  --output results/standard_heat_verified \
  --device gpu \
  --compare-cpu-gpu \
  --quantum-steps 32 \
  --ancilla-qubits 8 \
  --auxiliary-range 16 \
  --recovery-point 1 \
  --user-task "标准尺度一维热传导的32步Trotter壁仞GPU验证"
