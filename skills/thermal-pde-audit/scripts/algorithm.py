#!/usr/bin/env python3
"""Run the Thermal PDE Audit Skill entry point."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Natural-language heat-transfer request")
    source.add_argument("--input", type=Path, help="Structured experiment JSON")
    parser.add_argument("--output", type=Path, help="Execute and save to this directory")
    parser.add_argument("--device", choices=("cpu", "gpu"))
    parser.add_argument("--compare-cpu-gpu", action="store_true")
    parser.add_argument("--validated-profile", action="store_true")
    parser.add_argument("--supa-audit", action="store_true")
    parser.add_argument("--custom-supa-audit", action="store_true")
    parser.add_argument("--error-decomposition", action="store_true")
    parser.add_argument(
        "--full-audit",
        action="store_true",
        help="Enable CPU/GPU, validated profile, dual SUPA, and decomposition",
    )
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    root = _repository_root()
    if root is not None:
        source = str(root / "src")
        if source not in sys.path:
            sys.path.insert(0, source)

    try:
        from thermal_pde_audit.cli import main as cli_main
        from thermal_pde_audit.parser import plan_natural_language
    except ModuleNotFoundError as error:
        print(
            json.dumps(
                {
                    "status": "needs_install",
                    "message": (
                        "Install the project package or set "
                        "THERMAL_PDE_AUDIT_ROOT to a repository checkout."
                    ),
                    "error": str(error),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    original_cwd = Path.cwd()
    input_path = args.input.resolve() if args.input else None
    output_path = args.output.resolve() if args.output else None

    execution_flags = {
        "--compare-cpu-gpu": args.compare_cpu_gpu or args.full_audit,
        "--validated-profile": args.validated_profile or args.full_audit,
        "--supa-audit": args.supa_audit or args.full_audit,
        "--custom-supa-audit": args.custom_supa_audit or args.full_audit,
        "--error-decomposition": args.error_decomposition or args.full_audit,
    }
    if args.output is None:
        if args.device or any(execution_flags.values()):
            parser.error("Execution flags require --output.")
        if args.text:
            plan = plan_natural_language(args.text)
            print(json.dumps(plan, ensure_ascii=False, indent=2))
            return 0 if plan["status"] != "rejected" else 2
        return cli_main(["recommend", "--input", str(input_path)])

    if args.text and args.device:
        parser.error("For natural language, state the CPU or GPU in --text.")

    if root is not None:
        os.chdir(root)
    try:
        if execution_flags["--custom-supa-audit"] and root is not None:
            executable = (
                root / "build" / "custom_supa" / "supa_error_reduction.out"
            )
            if not executable.is_file():
                build_script = root / "scripts" / "build_custom_supa_kernel.sh"
                completed = subprocess.run(
                    ["bash", str(build_script)],
                    cwd=root,
                    check=False,
                )
                if completed.returncode != 0:
                    return completed.returncode
        if args.text:
            command = [
                "run-text",
                "--text",
                args.text,
                "--output",
                str(output_path),
            ]
        else:
            command = [
                "run",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            ]
            if args.device:
                command.extend(["--device", args.device])
        for flag, enabled in execution_flags.items():
            if enabled:
                command.append(flag)
        return cli_main(command)
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
