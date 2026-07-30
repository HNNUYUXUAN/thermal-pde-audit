"""End-to-end experiment orchestration and artifact protocol."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from .classical_solver import (
    FiniteDifferenceStabilityError,
    analytic_field_at,
    solve_analytic,
    solve_classical,
)
from .custom_supa_audit import audit_error_metrics_with_custom_supa
from .error_decomposition import decompose_quantum_error
from .physics_audit import audit_field, error_metrics
from .quantum_solver import solve_quantum
from .reporting import (
    write_error_decomposition_figure,
    write_report,
    write_temperature_figure,
)
from .schema import ThermalExperimentSpec
from .supa_audit import audit_error_metrics_on_supa


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_experiment(
    spec: ThermalExperimentSpec,
    output_dir: Path,
    *,
    user_task: str,
    compare_cpu_gpu: bool = False,
    quantum_steps: int = 1,
    ancilla_qubits: int = 5,
    auxiliary_range: float = 4.0,
    recovery_point: int = 1,
    supa_audit: bool = False,
    custom_supa_executable: Path | None = None,
    error_decomposition: bool = False,
    quantum_profile_selection: dict[str, Any] | None = None,
    input_provenance: dict[str, Any] | None = None,
    reproduce_command: str = "",
) -> dict[str, Any]:
    """Run analytic, classical, and UnitaryLab layers serially."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_lines = [
        f"started={time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"input={json.dumps(spec.to_dict(), ensure_ascii=False)}",
        (
            "input_provenance="
            f"{json.dumps(input_provenance or {}, ensure_ascii=False)}"
        ),
        "stage=analytic begin",
    ]
    _write_json(output_dir / "input.json", spec.to_dict())
    analytic = solve_analytic(spec)
    log_lines.append("stage=analytic success")

    log_lines.append("stage=classical begin")
    try:
        classical = solve_classical(spec)
        log_lines.append("stage=classical success")
    except FiniteDifferenceStabilityError as exc:
        classical = exc.to_dict()
        log_lines.append(f"stage=classical rejected error={exc}")

    quantum_cpu_reference: dict[str, Any] = {}
    if compare_cpu_gpu and spec.device == "gpu":
        log_lines.append("stage=quantum_cpu_reference begin")
        quantum_cpu_reference = solve_quantum(
            spec,
            output_dir,
            device="cpu",
            quantum_steps=quantum_steps,
            ancilla_qubits=ancilla_qubits,
            auxiliary_range=auxiliary_range,
            recovery_point=recovery_point,
        )
        log_lines.append(
            f"stage=quantum_cpu_reference {quantum_cpu_reference['status']}"
        )

    log_lines.append(f"stage=quantum_{spec.device} begin")
    quantum = solve_quantum(
        spec,
        output_dir,
        device=spec.device,
        quantum_steps=quantum_steps,
        ancilla_qubits=ancilla_qubits,
        auxiliary_range=auxiliary_range,
        recovery_point=recovery_point,
    )
    log_lines.append(f"stage=quantum_{spec.device} {quantum['status']}")

    result: dict[str, Any] = {
        "task": spec.task,
        "input": spec.to_dict(),
        "input_provenance": input_provenance or {},
        "analytic": analytic,
        "classical": classical,
        "quantum": quantum,
        "quantum_cpu_reference": quantum_cpu_reference,
        "supa_audit": {},
        "custom_supa_audit": {},
        "error_decomposition": {
            "status": "not_requested",
        },
        "quantum_profile_selection": quantum_profile_selection or {},
        "metrics": {},
    }

    checks: list[dict[str, Any]] = []
    audits: dict[str, Any] = {}
    if classical.get("status") == "success":
        classical_reference = analytic["state_or_field_k"]
        classical_audit = audit_field(
            spec,
            classical["state_or_field_k"],
            classical_reference,
            target="classical",
            includes_boundaries=True,
            finite_difference_ratio=classical["grid"]["stability_ratio"],
        )
        audits["classical"] = classical_audit
        checks.extend(classical_audit["checks"])
        result["metrics"]["classical_vs_analytic"] = error_metrics(
            classical["state_or_field_k"],
            classical_reference,
        )
    else:
        rejection = classical["error"]
        checks.append(
            {
                "name": "finite_difference_stability",
                "target": "classical",
                "passed": False,
                "value": rejection["stability_ratio"],
                "threshold": rejection["threshold"],
                "explanation": rejection["message"],
            }
        )

    if quantum.get("status") == "success":
        quantum_x = np.asarray(quantum["spatial_grid_m"], dtype=float)
        quantum_reference = analytic_field_at(spec, quantum_x).tolist()
        cpu_gpu_diff = None
        if quantum_cpu_reference.get("status") == "success":
            cpu_values = np.asarray(
                quantum_cpu_reference["state_or_field"],
                dtype=float,
            )
            gpu_values = np.asarray(quantum["state_or_field"], dtype=float)
            if cpu_values.shape == gpu_values.shape and cpu_values.size:
                cpu_gpu_diff = float(np.max(np.abs(cpu_values - gpu_values)))
                result["metrics"]["quantum_cpu_gpu_max_abs_diff_k"] = (
                    cpu_gpu_diff
                )
        quantum_audit = audit_field(
            spec,
            quantum["state_or_field"],
            quantum_reference,
            target="quantum",
            includes_boundaries=False,
            cpu_gpu_max_diff_k=cpu_gpu_diff,
        )
        audits["quantum"] = quantum_audit
        checks.extend(quantum_audit["checks"])
        result["metrics"]["quantum_vs_analytic"] = error_metrics(
            quantum["state_or_field"],
            quantum_reference,
        )
        if error_decomposition:
            log_lines.append("stage=error_decomposition begin")
            decomposition = decompose_quantum_error(
                spec,
                quantum,
                ancilla_qubits=ancilla_qubits,
                auxiliary_range=auxiliary_range,
                recovery_point=recovery_point,
                include_recovery=True,
            )
            result["error_decomposition"] = decomposition
            checks.append(
                {
                    "name": "schrodingerization_error_decomposition",
                    "target": "error_decomposition",
                    "passed": decomposition["status"] == "success",
                    "value": {
                        "status": decomposition["status"],
                        "recovery_status": decomposition.get(
                            "recovery_reference",
                            {},
                        ).get("status"),
                    },
                    "threshold": {
                        "status": "success",
                        "recovery_status": "success",
                    },
                    "explanation": (
                        "The same run must produce an independent "
                        "semi-discrete reference and same-parameter "
                        "UnitaryLab recovery diagnostic."
                    ),
                }
            )
            log_lines.append(
                f"stage=error_decomposition {decomposition['status']}"
            )
        if supa_audit:
            log_lines.append("stage=supa_error_audit begin")
            supa_result = audit_error_metrics_on_supa(
                quantum["state_or_field"],
                quantum_reference,
            )
            result["supa_audit"] = supa_result
            checks.append(
                {
                    "name": "supa_error_metric_consistency",
                    "target": "supa_audit",
                    "passed": supa_result["status"] == "success",
                    "value": supa_result.get("consistency", {}),
                    "threshold": {
                        "status": "success",
                        "reduction_vs_roundtrip_cpu": "1e-8",
                        "end_to_end_vs_source_cpu": "1e-5",
                    },
                    "explanation": (
                        "Real torch.supa reductions must match independent "
                        "NumPy metrics."
                    ),
                }
            )
            log_lines.append(f"stage=supa_error_audit {supa_result['status']}")
        if custom_supa_executable is not None:
            log_lines.append("stage=custom_supa_error_audit begin")
            custom_supa_result = audit_error_metrics_with_custom_supa(
                quantum["state_or_field"],
                quantum_reference,
                custom_supa_executable,
            )
            result["custom_supa_audit"] = custom_supa_result
            checks.append(
                {
                    "name": "custom_supa_error_metric_consistency",
                    "target": "custom_supa_audit",
                    "passed": custom_supa_result["status"] == "success",
                    "value": custom_supa_result.get("consistency", {}),
                    "threshold": {
                        "status": "success",
                        "kernel_vs_float32_cpu": "1e-6",
                        "end_to_end_vs_source_float64_cpu": "1e-5",
                    },
                    "explanation": (
                        "The project-owned SUPA reduction kernel must match "
                        "independent NumPy float32 and float64 metrics."
                    ),
                }
            )
            log_lines.append(
                "stage=custom_supa_error_audit "
                f"{custom_supa_result['status']}"
            )
    else:
        checks.append(
            {
                "name": "quantum_execution",
                "target": "quantum",
                "passed": False,
                "value": quantum.get("error"),
                "threshold": "status=success with a non-empty field",
                "explanation": "The real UnitaryLab execution did not succeed.",
            }
        )
        if supa_audit:
            result["supa_audit"] = {
                "status": "not_run",
                "reason": "The quantum field was unavailable.",
            }
        if custom_supa_executable is not None:
            result["custom_supa_audit"] = {
                "status": "not_run",
                "reason": "The quantum field was unavailable.",
            }
        if error_decomposition:
            result["error_decomposition"] = {
                "status": "not_run",
                "reason": "The quantum field was unavailable.",
            }

    audit = {
        "passed": bool(checks and all(item["passed"] for item in checks)),
        "checks": checks,
        "layers": audits,
    }
    result["status"] = "success" if audit["passed"] else "completed_with_failures"
    result["artifacts"] = {
        "input": str(output_dir / "input.json"),
        "result": str(output_dir / "result.json"),
        "audit": str(output_dir / "audit.json"),
        "report": str(output_dir / "report.md"),
        "run_log": str(output_dir / "run.log"),
        "figure": str(output_dir / "temperature_comparison.png"),
    }
    if result["error_decomposition"].get("status") == "success":
        result["artifacts"]["error_decomposition_figure"] = str(
            output_dir / "error_decomposition.png"
        )
    _write_json(output_dir / "result.json", result)
    _write_json(output_dir / "audit.json", audit)
    write_temperature_figure(result, output_dir / "temperature_comparison.png")
    if result["error_decomposition"].get("status") == "success":
        write_error_decomposition_figure(
            result,
            output_dir / "error_decomposition.png",
        )
    write_report(
        spec.to_dict(),
        result,
        audit,
        output_dir / "report.md",
        user_task=user_task,
        reproduce_command=reproduce_command,
    )
    log_lines.extend(
        [
            f"audit_passed={audit['passed']}",
            f"result_status={result['status']}",
            f"finished={time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        ]
    )
    (output_dir / "run.log").write_text(
        "\n".join(log_lines) + "\n",
        encoding="utf-8",
    )
    return result
