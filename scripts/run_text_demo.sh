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
python3 -m thermal_pde_audit.cli run-text \
  --text "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用32个空间点和50个时间步；使用GPU做完整验证，进行CPU/GPU对照、SUPA与自定义SUPA审计、误差分层并生成报告" \
  --output results/natural_language_gpu_validation
