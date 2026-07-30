#!/usr/bin/env python3
"""Map a controlled heat solver's empirical Fo/grid/Trotter working region."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

from thermal_pde_audit.classical_solver import analytic_field_at
from thermal_pde_audit.physics_audit import audit_field, error_metrics
from thermal_pde_audit.quantum_solver import solve_quantum
from thermal_pde_audit.schema import ThermalExperimentSpec


ROOT = Path(__file__).resolve().parents[1]
T = TypeVar("T")


def _csv_values(raw: str, converter: Callable[[str], T]) -> list[T]:
    values = [converter(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("At least one value is required.")
    return values


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _safe_time_steps(fourier_number: float, spatial_points: int) -> int:
    """Return an explicit-FD step count satisfying r <= 0.5."""

    return max(1, math.ceil(2.0 * fourier_number * (spatial_points + 1) ** 2))


def _spec_for_case(
    base: dict[str, Any],
    fourier_number: float,
    spatial_points: int,
) -> ThermalExperimentSpec:
    raw = dict(base)
    raw["duration_s"] = (
        fourier_number
        * float(raw["length_m"]) ** 2
        / float(raw["thermal_diffusivity_m2_s"])
    )
    raw["spatial_points"] = spatial_points
    raw["time_steps"] = max(
        int(raw["time_steps"]),
        _safe_time_steps(fourier_number, spatial_points),
    )
    raw["device"] = "cpu"
    return ThermalExperimentSpec.from_dict(raw)


def _plot(report: dict[str, Any], output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 5))
    point_counts = sorted({row["spatial_points"] for row in report["cases"]})
    fourier_numbers = sorted(
        {row["fourier_number"] for row in report["cases"]}
    )
    if len(fourier_numbers) == 1 and len(point_counts) > 1:
        resolved = [
            row
            for row in sorted(
                report["cases"],
                key=lambda row: row["spatial_points"],
            )
            if row["confirmed_quantum_steps"] is not None
        ]
        axis.plot(
            [row["spatial_points"] for row in resolved],
            [row["confirmed_quantum_steps"] for row in resolved],
            "o-",
            label=f"Fo={fourier_numbers[0]:g}",
        )
        axis.set_xlabel("Interior spatial points")
        axis.set_xscale("log", base=2)
    else:
        for spatial_points in point_counts:
            rows = sorted(
                (
                    row
                    for row in report["cases"]
                    if row["spatial_points"] == spatial_points
                ),
                key=lambda row: row["fourier_number"],
            )
            resolved = [
                row
                for row in rows
                if row["confirmed_quantum_steps"] is not None
            ]
            if resolved:
                axis.plot(
                    [row["fourier_number"] for row in resolved],
                    [row["confirmed_quantum_steps"] for row in resolved],
                    "o-",
                    label=f"{spatial_points} interior points",
                )
            for row in rows:
                if row["confirmed_quantum_steps"] is None:
                    axis.scatter(
                        row["fourier_number"],
                        max(report["candidate_quantum_steps"]),
                        marker="x",
                        color="red",
                    )
        axis.set_xlabel("Fourier number")
    axis.set_ylabel("Confirmed Trotter steps")
    axis.set_yscale("log", base=2)
    axis.grid(alpha=0.25)
    axis.legend()
    axis.set_title(
        "Empirical working region "
        f"(relative L2 <= {report['strict_relative_l2_threshold']})"
    )
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "examples" / "standard_heat.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--fourier",
        default="0.001,0.005,0.01,0.02,0.04,0.06,0.08,0.1",
    )
    parser.add_argument("--spatial-points", default="32")
    parser.add_argument("--quantum-steps", default="1,2,4,8,16,32,64")
    parser.add_argument("--ancilla-qubits", type=int, default=8)
    parser.add_argument("--auxiliary-range", type=float, default=16.0)
    parser.add_argument("--recovery-point", type=int, default=1)
    parser.add_argument("--strict-relative-l2", type=float, default=0.02)
    parser.add_argument("--consecutive-passes", type=int, default=2)
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.output = args.output.resolve()

    fourier_values = _csv_values(args.fourier, float)
    spatial_values = _csv_values(args.spatial_points, int)
    quantum_steps = _csv_values(args.quantum_steps, int)
    if (
        any(value <= 0 for value in fourier_values)
        or any(value < 4 or value & (value - 1) for value in spatial_values)
        or any(value < 1 for value in quantum_steps)
        or args.consecutive_passes < 1
    ):
        parser.error(
            "Fo and Nt must be positive; spatial points must be powers of two "
            "of at least four; consecutive passes must be positive."
        )

    base = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    report: dict[str, Any] = {
        "task": "empirical_quantum_working_region",
        "status": "running",
        "input_template": str(args.input),
        "device": "cpu",
        "fourier_numbers": fourier_values,
        "spatial_points": spatial_values,
        "candidate_quantum_steps": quantum_steps,
        "ancilla_qubits": args.ancilla_qubits,
        "auxiliary_range": args.auxiliary_range,
        "recovery_point": args.recovery_point,
        "strict_relative_l2_threshold": args.strict_relative_l2,
        "confirmation_rule": (
            f"{args.consecutive_passes} consecutive candidate Nt values must "
            "pass the full physics audit and strict relative-L2 threshold."
        ),
        "cases": [],
    }
    checkpoint = args.output / "working_region.json"

    for spatial_points in spatial_values:
        for fourier_number in fourier_values:
            spec = _spec_for_case(base, fourier_number, spatial_points)
            case: dict[str, Any] = {
                "fourier_number": fourier_number,
                "spatial_points": spatial_points,
                "physical_duration_s": spec.duration_s,
                "classical_time_steps": spec.time_steps,
                "runs": [],
                "first_strict_pass": None,
                "confirmed_quantum_steps": None,
            }
            consecutive = 0
            current_streak: list[int] = []
            for candidate_nt in quantum_steps:
                print(
                    f"case Fo={fourier_number:g} N={spatial_points} "
                    f"Nt={candidate_nt}",
                    flush=True,
                )
                run_dir = (
                    args.output
                    / "raw"
                    / f"fo{fourier_number:g}_n{spatial_points}_nt{candidate_nt}"
                )
                result = solve_quantum(
                    spec,
                    run_dir,
                    device="cpu",
                    quantum_steps=candidate_nt,
                    ancilla_qubits=args.ancilla_qubits,
                    auxiliary_range=args.auxiliary_range,
                    recovery_point=args.recovery_point,
                )
                row: dict[str, Any] = {
                    "requested_nt": candidate_nt,
                    "status": result["status"],
                    "runtime_s": result["runtime_s"],
                    "artifact_directory": str(run_dir.relative_to(ROOT)),
                    "route": result.get("device_route_calls", []),
                    "route_compatibility": result.get(
                        "device_route_compatibility",
                        {},
                    ),
                    "log_handler_cleanup": result.get(
                        "algorithm_log_handler_cleanup",
                        {},
                    ),
                    "strict_accuracy_passed": False,
                }
                if result["status"] == "success":
                    reference = analytic_field_at(
                        spec,
                        result["spatial_grid_m"],
                    )
                    metrics = error_metrics(
                        result["state_or_field"],
                        reference,
                    )
                    physics = audit_field(
                        spec,
                        result["state_or_field"],
                        reference.tolist(),
                        target="quantum_working_region",
                        includes_boundaries=False,
                    )
                    strict_passed = (
                        physics["passed"]
                        and metrics["relative_l2_error"]
                        <= args.strict_relative_l2
                    )
                    row.update(
                        {
                            "metrics_vs_analytic": metrics,
                            "physics_audit_passed": physics["passed"],
                            "strict_accuracy_passed": strict_passed,
                            "min_k": float(min(result["state_or_field"])),
                            "max_k": float(max(result["state_or_field"])),
                            "effective_nt": (
                                result["device_route_calls"][0].get("Nt")
                                if result.get("device_route_calls")
                                else None
                            ),
                        }
                    )
                else:
                    row["error"] = result.get("error")
                case["runs"].append(row)

                if row["strict_accuracy_passed"]:
                    consecutive += 1
                    current_streak.append(candidate_nt)
                    if case["first_strict_pass"] is None:
                        case["first_strict_pass"] = candidate_nt
                else:
                    consecutive = 0
                    current_streak = []
                    case["first_strict_pass"] = None
                if consecutive >= args.consecutive_passes:
                    case["confirmed_quantum_steps"] = candidate_nt
                    case["confirmed_streak"] = current_streak[
                        -args.consecutive_passes :
                    ]
                    break

            report["cases"].append(case)
            _write_json(checkpoint, report)
            print(
                f"completed Fo={fourier_number:g} N={spatial_points} "
                f"confirmed={case['confirmed_quantum_steps']}",
                flush=True,
            )

    unresolved = [
        {
            "fourier_number": row["fourier_number"],
            "spatial_points": row["spatial_points"],
        }
        for row in report["cases"]
        if row["confirmed_quantum_steps"] is None
    ]
    report.update(
        {
            "status": (
                "completed" if not unresolved else "completed_with_unresolved"
            ),
            "resolved_cases": len(report["cases"]) - len(unresolved),
            "unresolved_cases": unresolved,
            "elapsed_s": time.perf_counter() - started,
            "limitations": [
                (
                    "This is an empirical map for the installed versions and "
                    "controlled sine/Dirichlet problem, not a convergence theorem."
                ),
                (
                    "Candidate Nt values are discrete powers of two and a "
                    "non-monotonic failure can occur between passing values."
                ),
                (
                    "Raw UnitaryLab plots and logs are retained remotely under "
                    "the reported raw directories."
                ),
            ],
        }
    )
    _write_json(checkpoint, report)
    _plot(report, args.output / "working_region.png")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
