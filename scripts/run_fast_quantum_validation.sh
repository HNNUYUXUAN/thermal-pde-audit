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

bash scripts/build_custom_supa_kernel.sh
python3 -m thermal_pde_audit.cli run \
  --input examples/minimal_heat.json \
  --output results/fast_quantum_validation \
  --device gpu \
  --compare-cpu-gpu \
  --validated-profile \
  --supa-audit \
  --custom-supa-audit \
  --error-decomposition \
  --user-task "运行短时一维热传导量子GPU、torch.supa和自定义SUPA核验证"
