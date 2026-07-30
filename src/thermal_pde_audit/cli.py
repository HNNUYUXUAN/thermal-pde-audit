"""Command-line entry points for parsing and running experiments."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from .benchmark import run_experiment
from .capability import capability_summary
from .evidence_validation import validate_result_bundle
from .interaction_validation import validate_interaction_records
from .parser import parse_natural_language, plan_natural_language
from .profile_evidence import validate_quantum_profile_evidence
from .quantum_policy import QuantumProfileError, recommend_quantum_profile
from .schema import ThermalExperimentSpec, ThermalSpecValidationError


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _add_execution_arguments(
    command: argparse.ArgumentParser,
    *,
    allow_device_override: bool,
) -> None:
    command.add_argument("--output", type=Path, required=True)
    if allow_device_override:
        command.add_argument("--device", choices=("cpu", "gpu"))
    command.add_argument("--compare-cpu-gpu", action="store_true")
    command.add_argument("--quantum-steps", type=int, default=1)
    command.add_argument("--ancilla-qubits", type=int, default=5)
    command.add_argument("--auxiliary-range", type=float, default=4.0)
    command.add_argument("--recovery-point", type=int, default=1)
    command.add_argument("--supa-audit", action="store_true")
    command.add_argument("--custom-supa-audit", action="store_true")
    command.add_argument("--error-decomposition", action="store_true")
    command.add_argument("--validated-profile", action="store_true")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thermal-pde-audit")
    subcommands = parser.add_subparsers(dest="command", required=True)

    parse_command = subcommands.add_parser(
        "parse",
        help="parse constrained natural language to a JSON experiment spec",
    )
    parse_command.add_argument("--text", required=True)

    plan_command = subcommands.add_parser(
        "plan-text",
        help="return a whitelisted execution plan or clarification questions",
    )
    plan_command.add_argument("--text", required=True)

    run_command = subcommands.add_parser(
        "run",
        help="run analytic, classical, quantum, audit, and reporting layers",
    )
    run_command.add_argument("--input", type=Path, required=True)
    _add_execution_arguments(run_command, allow_device_override=True)
    run_command.add_argument("--user-task")

    run_text_command = subcommands.add_parser(
        "run-text",
        help=(
            "parse constrained natural language and execute the same controlled "
            "experiment workflow"
        ),
    )
    run_text_command.add_argument("--text", required=True)
    _add_execution_arguments(
        run_text_command,
        allow_device_override=False,
    )

    recommend_command = subcommands.add_parser(
        "recommend",
        help="return an exact empirically validated quantum parameter profile",
    )
    recommend_command.add_argument("--input", type=Path, required=True)

    validate_command = subcommands.add_parser(
        "validate-result",
        help="validate a saved six-artifact result and device evidence",
    )
    validate_command.add_argument("--result-dir", type=Path, required=True)
    validate_command.add_argument("--require-gpu", action="store_true")
    validate_command.add_argument("--require-supa", action="store_true")
    validate_command.add_argument("--require-custom-supa", action="store_true")
    validate_command.add_argument(
        "--require-error-decomposition",
        action="store_true",
    )
    validate_command.add_argument(
        "--require-natural-language",
        action="store_true",
    )

    subcommands.add_parser(
        "validate-profiles",
        help="cross-check exact quantum profiles against saved scan evidence",
    )
    interactions_command = subcommands.add_parser(
        "validate-interactions",
        help="validate saved Agent/Skill transcripts and cited evidence",
    )
    interactions_command.add_argument(
        "--interactions-dir",
        type=Path,
        default=Path("results/interactions"),
    )
    subcommands.add_parser("capabilities", help="show the controlled boundary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "parse":
            _print_json(parse_natural_language(args.text).to_dict())
            return 0
        if args.command == "plan-text":
            plan = plan_natural_language(args.text)
            _print_json(plan)
            return 2 if plan["status"] == "rejected" else 0
        if args.command == "capabilities":
            _print_json(capability_summary())
            return 0
        if args.command == "recommend":
            spec = ThermalExperimentSpec.from_dict(_load_json(args.input))
            _print_json(recommend_quantum_profile(spec))
            return 0
        if args.command == "validate-result":
            validation = validate_result_bundle(
                args.result_dir,
                require_gpu=args.require_gpu,
                require_supa=args.require_supa,
                require_custom_supa=args.require_custom_supa,
                require_error_decomposition=args.require_error_decomposition,
                require_natural_language=args.require_natural_language,
            )
            _print_json(validation)
            return 0 if validation["passed"] else 1
        if args.command == "validate-profiles":
            validation = validate_quantum_profile_evidence()
            _print_json(validation)
            return 0 if validation["passed"] else 1
        if args.command == "validate-interactions":
            validation = validate_interaction_records(args.interactions_dir)
            _print_json(validation)
            return 0 if validation["passed"] else 1
        if args.command in {"run", "run-text"}:
            input_provenance: dict[str, Any]
            if args.command == "run":
                raw = _load_json(args.input)
                if args.device:
                    raw["device"] = args.device
                spec = ThermalExperimentSpec.from_dict(raw)
                input_reference = args.input
                user_task = args.user_task or f"Run {args.input}"
                input_provenance = {
                    "mode": "json_file",
                    "input_path": str(args.input),
                }
                compare_cpu_gpu = args.compare_cpu_gpu
                validated_profile = args.validated_profile
                supa_audit = args.supa_audit
                custom_supa_audit = args.custom_supa_audit
                error_decomposition = args.error_decomposition
            else:
                parsed = parse_natural_language(args.text)
                spec = parsed.spec
                input_reference = args.output / "input.json"
                user_task = parsed.source_text
                parsed_plan = parsed.execution_plan.to_dict()
                overrides = {
                    "compare_cpu_gpu": args.compare_cpu_gpu,
                    "validated_profile": args.validated_profile,
                    "supa_audit": args.supa_audit,
                    "custom_supa_audit": args.custom_supa_audit,
                    "error_decomposition": args.error_decomposition,
                }
                resolved_plan = dict(parsed_plan)
                resolved_sources = dict(parsed_plan["sources"])
                for name, enabled in overrides.items():
                    if enabled and not resolved_plan[name]:
                        resolved_plan[name] = True
                        resolved_sources[name] = "cli_override:true"
                if resolved_plan["custom_supa_audit"]:
                    resolved_plan["supa_audit"] = True
                    if not parsed_plan["supa_audit"]:
                        resolved_sources["supa_audit"] = (
                            "derived:custom_supa_requires_supa"
                        )
                resolved_plan["sources"] = resolved_sources
                compare_cpu_gpu = bool(resolved_plan["compare_cpu_gpu"])
                validated_profile = bool(resolved_plan["validated_profile"])
                supa_audit = bool(resolved_plan["supa_audit"])
                custom_supa_audit = bool(
                    resolved_plan["custom_supa_audit"]
                )
                error_decomposition = bool(
                    resolved_plan["error_decomposition"]
                )
                input_provenance = {
                    "mode": "natural_language",
                    "parser": "deterministic_whitelist_v1",
                    **parsed.to_dict(),
                    "execution_plan": resolved_plan,
                }
            profile_selection: dict[str, Any] = {}
            quantum_steps = args.quantum_steps
            ancilla_qubits = args.ancilla_qubits
            auxiliary_range = args.auxiliary_range
            recovery_point = args.recovery_point
            if validated_profile:
                profile_selection = recommend_quantum_profile(
                    spec,
                    validate_environment=True,
                )
                selected = profile_selection["parameters"]
                quantum_steps = selected["quantum_steps"]
                ancilla_qubits = selected["ancilla_qubits"]
                auxiliary_range = selected["auxiliary_range"]
                recovery_point = selected["recovery_point"]
            reproduce = (
                "python3 -m thermal_pde_audit.cli run "
                f"--input {shlex.quote(str(input_reference))} "
                f"--output {shlex.quote(str(args.output))} "
                f"--device {spec.device} "
                f"--quantum-steps {quantum_steps} "
                f"--ancilla-qubits {ancilla_qubits} "
                f"--auxiliary-range {auxiliary_range} "
                f"--recovery-point {recovery_point}"
            )
            if compare_cpu_gpu:
                reproduce += " --compare-cpu-gpu"
            if validated_profile:
                reproduce += " --validated-profile"
            if supa_audit:
                reproduce += " --supa-audit"
            if custom_supa_audit:
                reproduce += " --custom-supa-audit"
            if error_decomposition:
                reproduce += " --error-decomposition"
            result = run_experiment(
                spec,
                args.output,
                user_task=user_task,
                compare_cpu_gpu=compare_cpu_gpu,
                quantum_steps=quantum_steps,
                ancilla_qubits=ancilla_qubits,
                auxiliary_range=auxiliary_range,
                recovery_point=recovery_point,
                supa_audit=supa_audit,
                custom_supa_executable=(
                    Path("build/custom_supa/supa_error_reduction.out")
                    if custom_supa_audit
                    else None
                ),
                error_decomposition=error_decomposition,
                quantum_profile_selection=profile_selection,
                input_provenance=input_provenance,
                reproduce_command=reproduce,
            )
            _print_json(
                {
                    "status": result["status"],
                    "audit_passed": result["status"] == "success",
                    "artifacts": result["artifacts"],
                }
            )
            return 0 if result["status"] == "success" else 1
    except ThermalSpecValidationError as exc:
        _print_json(exc.to_dict())
        return 2
    except QuantumProfileError as exc:
        _print_json(exc.to_dict())
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        _print_json(
            {
                "status": "failed",
                "error": {
                    "code": "INPUT_READ_ERROR",
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            }
        )
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
