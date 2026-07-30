#!/usr/bin/env bash
set -euo pipefail

SDK_ENV="/usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh"

if test -f "${SDK_ENV}"; then
  set +u
  # shellcheck disable=SC1090
  source "${SDK_ENV}" >/dev/null
  set -u
fi

echo "date=$(date -Iseconds)"
echo "host=$(hostname)"
echo "python=$(command -v python3)"
python3 --version

echo "compiler_candidates_begin"
for candidate in brcc brcc-clang brclang clang clang++ gcc g++; do
  if command -v "${candidate}" >/dev/null 2>&1; then
    printf "%s=%s\n" "${candidate}" "$(command -v "${candidate}")"
  else
    printf "%s=not_found\n" "${candidate}"
  fi
done
echo "compiler_candidates_end"

python3 - <<'PY'
from __future__ import annotations

import importlib
from pathlib import Path

for package in ("torch", "torch_br"):
    module = importlib.import_module(package)
    print(f"{package}_path={Path(module.__file__).resolve()}")

import torch
import torch_br  # noqa: F401

print(f"torch_supa_device_count={torch.supa.device_count()}")
print(f"torch_has_utils_cpp_extension={hasattr(torch.utils, 'cpp_extension')}")
PY

echo "su_files_begin"
for root in \
  /usr/local/birensupa/sdk/1.11.0.0.rc2 \
  /usr/local/lib/python3.10/dist-packages/torch_br \
  /workspace/quantum; do
  if test -d "${root}"; then
    find "${root}" -type f -name '*.su' -print 2>/dev/null
  fi
done
echo "su_files_end"

echo "kernel_api_hints_begin"
for root in \
  /usr/local/birensupa/sdk/1.11.0.0.rc2 \
  /usr/local/lib/python3.10/dist-packages/torch_br \
  /workspace/quantum; do
  if test -d "${root}"; then
    grep -RInE \
      --include='*.py' \
      --include='*.sh' \
      --include='*.md' \
      --include='*.txt' \
      --include='*.cpp' \
      --include='*.h' \
      '(load_inline|cpp_extension|\\.su\\b|brcc|supa.*kernel|kernel.*supa)' \
      "${root}" 2>/dev/null | head -n 200 || true
  fi
done
echo "kernel_api_hints_end"
