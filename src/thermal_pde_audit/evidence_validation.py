"""Framework-free validation of a saved thermal experiment evidence bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = (
    "input.json",
    "result.json",
    "audit.json",
    "report.md",
    "run.log",
    "temperature_comparison.png",
)


def _check(
    name: str,
    passed: bool,
    value: Any,
    expected: Any,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "value": value,
        "expected": expected,
    }


def validate_result_bundle(
    result_dir: Path,
    *,
    require_gpu: bool = False,
    require_supa: bool = False,
    require_custom_supa: bool = False,
    require_error_decomposition: bool = False,
    require_natural_language: bool = False,
) -> dict[str, Any]:
    """Validate result protocol, device evidence, and numerical audit status."""

    result_dir = Path(result_dir)
    checks: list[dict[str, Any]] = []
    missing = [
        name for name in REQUIRED_ARTIFACTS if not (result_dir / name).is_file()
    ]
    checks.append(
        _check(
            "required_artifacts",
            not missing,
            {"missing": missing},
            {"missing": []},
        )
    )
    if missing:
        return {
            "task": "validate_result_bundle",
            "result_dir": str(result_dir),
            "passed": False,
            "checks": checks,
        }

    try:
        result = json.loads(
            (result_dir / "result.json").read_text(encoding="utf-8")
        )
        audit = json.loads(
            (result_dir / "audit.json").read_text(encoding="utf-8")
        )
        input_spec = json.loads(
            (result_dir / "input.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        checks.append(
            _check(
                "json_parse",
                False,
                f"{type(exc).__name__}: {exc}",
                "three valid UTF-8 JSON files",
            )
        )
        return {
            "task": "validate_result_bundle",
            "result_dir": str(result_dir),
            "passed": False,
            "checks": checks,
        }

    checks.append(_check("json_parse", True, "success", "success"))
    checks.append(
        _check(
            "result_and_audit_status",
            result.get("status") == "success" and audit.get("passed") is True,
            {
                "result_status": result.get("status"),
                "audit_passed": audit.get("passed"),
            },
            {"result_status": "success", "audit_passed": True},
        )
    )
    quantum = result.get("quantum", {})
    field = quantum.get("state_or_field", [])
    checks.append(
        _check(
            "quantum_field_protocol",
            (
                quantum.get("status") == "success"
                and isinstance(field, list)
                and len(field) == input_spec.get("spatial_points")
            ),
            {
                "status": quantum.get("status"),
                "field_size": len(field) if isinstance(field, list) else None,
            },
            {
                "status": "success",
                "field_size": input_spec.get("spatial_points"),
            },
        )
    )
    route = quantum.get("device_route_calls", [])
    compatibility = quantum.get("device_route_compatibility", {})
    if require_gpu:
        checks.append(
            _check(
                "gpu_route_evidence",
                (
                    quantum.get("backend") == "unitarylab_gpu"
                    and bool(route)
                    and all(
                        call.get("device") == "gpu"
                        and call.get("requested_device") == "gpu"
                        and call.get("device_matches_requested") is True
                        for call in route
                    )
                    and compatibility.get("requested_device") == "gpu"
                    and compatibility.get("conflict_count") == 0
                    and compatibility.get("all_devices_match_requested")
                    is True
                    and compatibility.get("restored") is True
                ),
                {
                    "backend": quantum.get("backend"),
                    "route": route,
                    "compatibility": compatibility,
                    "restored": compatibility.get("restored"),
                },
                {
                    "backend": "unitarylab_gpu",
                    "device": "gpu",
                    "restored": True,
                },
            )
        )

    profile = result.get("quantum_profile_selection", {})
    checks.append(
        _check(
            "validated_profile_evidence",
            (
                profile.get("status") == "validated_profile"
                and profile.get("selection_mode") == "exact_empirical_match"
            ),
            {
                "status": profile.get("status"),
                "selection_mode": profile.get("selection_mode"),
            },
            {
                "status": "validated_profile",
                "selection_mode": "exact_empirical_match",
            },
        )
    )
    if require_supa:
        supa = result.get("supa_audit", {})
        checks.append(
            _check(
                "torch_supa_evidence",
                (
                    supa.get("status") == "success"
                    and supa.get("device") == "supa:0"
                    and supa.get("consistency", {}).get("passed") is True
                ),
                {
                    "status": supa.get("status"),
                    "device": supa.get("device"),
                    "consistency": supa.get("consistency", {}).get("passed"),
                },
                {
                    "status": "success",
                    "device": "supa:0",
                    "consistency": True,
                },
            )
        )
    if require_custom_supa:
        custom = result.get("custom_supa_audit", {})
        checks.append(
            _check(
                "custom_supa_evidence",
                (
                    custom.get("status") == "success"
                    and custom.get("device") == "supa:0"
                    and custom.get("kernel_source")
                    == "scripts/supa_error_reduction.su"
                    and custom.get("consistency", {}).get("passed") is True
                    and custom.get("raw_kernel_result", {}).get("kernel_mode")
                    == "single_block_tree_reduction"
                    and custom.get("raw_kernel_result", {}).get(
                        "launched_threads"
                    )
                    == 256
                ),
                {
                    "status": custom.get("status"),
                    "device": custom.get("device"),
                    "kernel_source": custom.get("kernel_source"),
                    "consistency": custom.get("consistency", {}).get("passed"),
                    "kernel_mode": custom.get("raw_kernel_result", {}).get(
                        "kernel_mode"
                    ),
                    "launched_threads": custom.get(
                        "raw_kernel_result", {}
                    ).get("launched_threads"),
                },
                {
                    "status": "success",
                    "device": "supa:0",
                    "kernel_source": "scripts/supa_error_reduction.su",
                    "consistency": True,
                    "kernel_mode": "single_block_tree_reduction",
                    "launched_threads": 256,
                },
            )
        )

    if require_error_decomposition:
        decomposition = result.get("error_decomposition", {})
        metrics = decomposition.get("metrics", {})
        required_metric_keys = {
            "semi_discrete_vs_continuous_analytic",
            "same_parameter_recovery_vs_semi_discrete",
            "trotter_vs_same_parameter_recovery",
            "trotter_vs_semi_discrete",
            "trotter_vs_continuous_analytic",
        }
        metric_keys = set(metrics)
        recovery = decomposition.get("recovery_reference", {})
        figure_path = result_dir / "error_decomposition.png"
        figure_signature = (
            figure_path.read_bytes()[:8] if figure_path.is_file() else b""
        )
        checks.append(
            _check(
                "schrodingerization_error_decomposition_evidence",
                (
                    decomposition.get("status") == "success"
                    and recovery.get("status") == "success"
                    and required_metric_keys.issubset(metric_keys)
                    and figure_signature == b"\x89PNG\r\n\x1a\n"
                ),
                {
                    "status": decomposition.get("status"),
                    "recovery_status": recovery.get("status"),
                    "metric_keys": sorted(metric_keys),
                    "figure_signature": figure_signature.hex(),
                },
                {
                    "status": "success",
                    "recovery_status": "success",
                    "metric_keys": sorted(required_metric_keys),
                    "figure_signature": "89504e470d0a1a0a",
                },
            )
        )

    if require_natural_language:
        provenance = result.get("input_provenance", {})
        parsed_spec = provenance.get("spec", {})
        natural_language_report = (result_dir / "report.md").read_text(
            encoding="utf-8"
        )
        natural_language_reproduction = (
            natural_language_report.split("## 复现命令", maxsplit=1)[1]
            if "## 复现命令" in natural_language_report
            else ""
        )
        source_text = provenance.get("source_text", "")
        execution_plan = provenance.get("execution_plan", {})
        plan_flags = {
            "compare_cpu_gpu": "--compare-cpu-gpu",
            "validated_profile": "--validated-profile",
            "supa_audit": "--supa-audit",
            "custom_supa_audit": "--custom-supa-audit",
            "error_decomposition": "--error-decomposition",
        }
        plan_matches_reproduction = all(
            bool(execution_plan.get(name))
            == (flag in natural_language_reproduction)
            for name, flag in plan_flags.items()
        )
        plan_sources = execution_plan.get("sources", {})
        plan_is_controlled = (
            execution_plan.get("validated_profile") is True
            and execution_plan.get("report_level") in {"standard", "full"}
            and all(
                isinstance(execution_plan.get(name), bool)
                for name in plan_flags
            )
            and all(
                isinstance(plan_sources.get(name), str)
                and bool(plan_sources.get(name))
                for name in (*plan_flags, "report_level")
            )
        )
        checks.append(
            _check(
                "natural_language_closed_loop_evidence",
                (
                    provenance.get("mode") == "natural_language"
                    and provenance.get("parser")
                    == "deterministic_whitelist_v1"
                    and provenance.get("status") == "parsed"
                    and isinstance(provenance.get("source_text"), str)
                    and bool(provenance.get("source_text", "").strip())
                    and parsed_spec == input_spec
                    and "no shell or Python code" in provenance.get(
                        "security_boundary",
                        "",
                    )
                    and source_text not in natural_language_reproduction
                    and plan_is_controlled
                    and plan_matches_reproduction
                ),
                {
                    "mode": provenance.get("mode"),
                    "parser": provenance.get("parser"),
                    "status": provenance.get("status"),
                    "source_text_present": bool(
                        provenance.get("source_text", "").strip()
                    ),
                    "parsed_spec_matches_input": parsed_spec == input_spec,
                    "security_boundary": provenance.get("security_boundary"),
                    "source_text_absent_from_reproduction": (
                        source_text not in natural_language_reproduction
                    ),
                    "execution_plan_is_controlled": plan_is_controlled,
                    "execution_plan_matches_reproduction": (
                        plan_matches_reproduction
                    ),
                },
                {
                    "mode": "natural_language",
                    "parser": "deterministic_whitelist_v1",
                    "status": "parsed",
                    "source_text_present": True,
                    "parsed_spec_matches_input": True,
                    "security_boundary": "whitelist only; no code execution",
                    "source_text_absent_from_reproduction": True,
                    "execution_plan_is_controlled": True,
                    "execution_plan_matches_reproduction": True,
                },
            )
        )

    png_signature = (result_dir / "temperature_comparison.png").read_bytes()[
        :8
    ]
    report_text = (result_dir / "report.md").read_text(encoding="utf-8")
    reproduction_section = (
        report_text.split("## 复现命令", maxsplit=1)[1]
        if "## 复现命令" in report_text
        else ""
    )
    controlled_reproduction = (
        "python3 -m thermal_pde_audit.cli run" in reproduction_section
        or "bash scripts/" in reproduction_section
    )
    checks.extend(
        [
            _check(
                "png_signature",
                png_signature == b"\x89PNG\r\n\x1a\n",
                png_signature.hex(),
                "89504e470d0a1a0a",
            ),
            _check(
                "controlled_reproduction_command",
                controlled_reproduction,
                "present" if controlled_reproduction else "missing",
                "report contains a controlled CLI or project-script command",
            ),
        ]
    )
    return {
        "task": "validate_result_bundle",
        "result_dir": str(result_dir),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
