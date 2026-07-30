#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="${1:-/workspace/thermal-pde-audit}"
LOG_PATH="${2:-${PROJECT_ROOT}/results/run_logs/environment_probe.log}"
SDK_ENV="/usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh"

mkdir -p "$(dirname "${LOG_PATH}")"

run_probe() {
  echo "probe_started=$(date -Iseconds)"
  echo "hostname=$(hostname)"
  echo "uname=$(uname -a)"
  if command -v lsb_release >/dev/null 2>&1; then
    lsb_release -a 2>&1
  elif test -f /etc/os-release; then
    cat /etc/os-release
  fi

  echo "python_path=$(command -v python3 || true)"
  python3 --version 2>&1

  echo "sdk_env=${SDK_ENV}"
  if test -f "${SDK_ENV}"; then
    # The vendor setup script reads optional variables such as C_INCLUDE_PATH
    # before defining them, so nounset must be disabled only while sourcing it.
    set +u
    # shellcheck disable=SC1090
    source "${SDK_ENV}" >/dev/null
    set -u
    echo "sdk_env_loaded=true"
  else
    echo "sdk_env_loaded=false"
  fi

  python3 - <<'PY'
import importlib
import importlib.metadata
import sys
import traceback

print(f"python_executable={sys.executable}")
print(f"python_prefix={sys.prefix}")

for name in ("torch", "torch_br", "unitarylab", "unitarylab_algorithms"):
    try:
        module = importlib.import_module(name)
        print(f"{name}_path={getattr(module, '__file__', None)}")
        try:
            print(f"{name}_version={importlib.metadata.version(name)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{name}_version={getattr(module, '__version__', 'unknown')}")
    except Exception as exc:
        print(f"{name}_import_error={type(exc).__name__}: {exc}")
        traceback.print_exc()

try:
    import torch
    import torch_br  # noqa: F401
    print(f"torch_version={torch.__version__}")
    print(f"torch_supa_device_count={torch.supa.device_count()}")
except Exception as exc:
    print(f"torch_supa_error={type(exc).__name__}: {exc}")
    traceback.print_exc()
PY

  echo "brsmi_begin"
  if command -v brsmi >/dev/null 2>&1; then
    timeout 20s brsmi 2>&1 || echo "brsmi_exit=$?"
  else
    echo "brsmi_not_found"
  fi
  echo "brsmi_end"

  echo "dev_biren_begin"
  if test -d /dev/biren; then
    ls -la /dev/biren 2>&1
  else
    echo "/dev/biren missing"
  fi
  echo "dev_biren_end"

  echo "quantum_examples_begin"
  if test -d /workspace/quantum/examples; then
    find /workspace/quantum/examples -maxdepth 4 -type f -print 2>&1 | sort
  else
    echo "/workspace/quantum/examples missing"
  fi
  echo "quantum_examples_end"
  echo "probe_finished=$(date -Iseconds)"
}

set +e
run_probe 2>&1 | tee "${LOG_PATH}"
probe_status=${PIPESTATUS[0]}
set -e
echo "probe_exit_code=${probe_status}" | tee -a "${LOG_PATH}"
exit "${probe_status}"
