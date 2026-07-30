#!/usr/bin/env python3
"""Run the complete local validation contract for the Skill and saved evidence."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def _repository_root() -> Path:
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
    raise SystemExit(
        "Repository checkout not found. Set THERMAL_PDE_AUDIT_ROOT to it."
    )


def main() -> int:
    root = _repository_root()
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [
            str(root / "src"),
            environment.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    commands: list[tuple[str, list[str]]] = [
        (
            "skill-package",
            [sys.executable, str(root / "scripts" / "validate_skill.py")],
        ),
        (
            "framework-free-cpu",
            [sys.executable, str(root / "scripts" / "run_cpu_checks.py")],
        ),
        (
            "quantum-profiles",
            [
                sys.executable,
                "-m",
                "thermal_pde_audit.cli",
                "validate-profiles",
            ],
        ),
        (
            "interaction-records",
            [
                sys.executable,
                "-m",
                "thermal_pde_audit.cli",
                "validate-interactions",
            ],
        ),
        (
            "current-skill-gpu-evidence",
            [
                sys.executable,
                "-m",
                "thermal_pde_audit.cli",
                "validate-result",
                "--result-dir",
                "results/skill_entry_gpu_validation",
                "--require-gpu",
                "--require-supa",
                "--require-custom-supa",
                "--require-error-decomposition",
                "--require-natural-language",
            ],
        ),
    ]
    if importlib.util.find_spec("pytest") is not None:
        commands.append(
            (
                "pytest",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                ],
            )
        )

    for label, command in commands:
        print(f"== {label} ==", flush=True)
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            check=False,
        )
        if completed.returncode != 0:
            print(f"validation_status=failed stage={label}")
            return completed.returncode

    print(f"validation_stages={len(commands)}")
    print("validation_status=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
