#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_ENV="/usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh"
SOURCE="${PROJECT_ROOT}/scripts/supa_error_reduction.su"
OUTPUT_DIR="${PROJECT_ROOT}/build/custom_supa"
OUTPUT="${OUTPUT_DIR}/supa_error_reduction.out"

if ! test -f "${SDK_ENV}"; then
  echo "SUPA SDK environment script not found: ${SDK_ENV}" >&2
  exit 1
fi

set +u
# shellcheck disable=SC1090
source "${SDK_ENV}" >/dev/null
set -u

if ! command -v brcc >/dev/null 2>&1; then
  echo "brcc compiler is not available after loading the SDK." >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"
brcc -O2 "${SOURCE}" -o "${OUTPUT}"
echo "custom_supa_kernel=${OUTPUT}"
