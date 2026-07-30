#!/usr/bin/env python3
"""Check whether the Thermal PDE Audit Skill can run in this environment."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


def _repository_root() -> Path | None:
    configured = os.environ.get("THERMAL_PDE_AUDIT_ROOT")
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend(Path(__file__).resolve().parents)
    for candidate in candidates:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "thermal_pde_audit").is_dir()
        ):
            return candidate.resolve()
    return None


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _torch_supa() -> dict[str, Any]:
    if not _module_available("torch"):
        return {"available": False, "device_count": 0}
    try:
        import torch
        import torch_br  # noqa: F401

        supa = getattr(torch, "supa", None)
        if supa is None:
            return {"available": False, "device_count": 0}
        count = int(supa.device_count())
        return {"available": count > 0, "device_count": count}
    except Exception as error:
        return {
            "available": False,
            "device_count": 0,
            "error": f"{type(error).__name__}: {error}",
        }


def main() -> int:
    root = _repository_root()
    if root is not None:
        source = str(root / "src")
        if source not in sys.path:
            sys.path.insert(0, source)

    modules = {
        name: _module_available(name)
        for name in (
            "thermal_pde_audit",
            "numpy",
            "scipy",
            "matplotlib",
            "pytest",
            "unitarylab",
            "unitarylab_algorithms",
            "torch",
            "torch_br",
        )
    }
    repository_files: dict[str, bool] = {}
    if root is not None:
        repository_files = {
            "standard_input": (root / "examples" / "standard_heat.json").is_file(),
            "current_skill_gpu_result": (
                root / "results" / "skill_entry_gpu_validation" / "result.json"
            ).is_file(),
            "demo_script": (root / "scripts" / "run_demo.sh").is_file(),
            "validation_script": (
                root / "scripts" / "run_cpu_checks.py"
            ).is_file(),
        }

    core_ready = all(
        modules[name]
        for name in ("thermal_pde_audit", "numpy", "scipy", "matplotlib")
    )
    quantum_cpu_ready = core_ready and all(
        modules[name] for name in ("unitarylab", "unitarylab_algorithms")
    )
    torch_supa = _torch_supa()
    report: dict[str, Any] = {
        "skill": "thermal-pde-audit",
        "python": sys.version.split()[0],
        "mode": "repository" if root is not None else "installed_package",
        "repository_root": str(root) if root is not None else None,
        "modules": modules,
        "torch_supa": torch_supa,
        "supa_sdk_env": Path(
            "/usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh"
        ).is_file(),
        "repository_files": repository_files,
        "capabilities": {
            "core_ready": core_ready,
            "quantum_cpu_ready": quantum_cpu_ready,
            "biren_gpu_ready": (
                quantum_cpu_ready
                and bool(torch_supa["available"])
                and int(torch_supa["device_count"]) > 0
            ),
        },
        "status": "ready" if core_ready else "needs_install",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if core_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
