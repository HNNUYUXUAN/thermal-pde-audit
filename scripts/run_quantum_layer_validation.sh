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
  --output results/quantum_layer_validation \
  --device gpu \
  --compare-cpu-gpu \
  --validated-profile \
  --supa-audit \
  --error-decomposition \
  --user-task "使用实测参数档案完成标准热方程量子GPU与SUPA审计闭环"
