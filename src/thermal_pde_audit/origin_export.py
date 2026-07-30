"""Export saved remote evidence as Origin-friendly flat data tables."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(
    path: Path,
    headers: list[str],
    rows: Iterable[Iterable[Any]],
) -> int:
    materialized = [list(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(materialized)
    return len(materialized)


def _finite_float_list(value: Any, name: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list.")
    result = [float(item) for item in value]
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"{name} contains NaN or Inf.")
    return result


def _temperature_rows(result: dict[str, Any]) -> list[list[Any]]:
    analytic = result["analytic"]
    classical = result["classical"]
    quantum = result["quantum"]
    cpu = result.get("quantum_cpu_reference") or {}
    x = _finite_float_list(analytic["spatial_grid_m"], "analytic grid")
    analytic_field = _finite_float_list(
        analytic["state_or_field_k"],
        "analytic field",
    )
    classical_field = _finite_float_list(
        classical["state_or_field_k"],
        "classical field",
    )
    gpu_interior = _finite_float_list(
        quantum["state_or_field"],
        "quantum field",
    )
    if not (
        len(x)
        == len(analytic_field)
        == len(classical_field)
        == len(gpu_interior) + 2
    ):
        raise ValueError("Saved fields do not share the controlled grid shape.")
    quantum_x = _finite_float_list(
        quantum["spatial_grid_m"],
        "quantum grid",
    )
    if any(
        abs(left - right) > 1e-12
        for left, right in zip(x[1:-1], quantum_x)
    ):
        raise ValueError("Quantum and analytic interior grids are misaligned.")
    gpu_field = [0.0, *gpu_interior, 0.0]
    cpu_field: list[float | None]
    if cpu.get("status") == "success":
        cpu_field = [
            0.0,
            *_finite_float_list(
                cpu["state_or_field"],
                "quantum CPU field",
            ),
            0.0,
        ]
    else:
        cpu_field = [None] * len(x)
    rows: list[list[Any]] = []
    for index, position in enumerate(x):
        cpu_value = cpu_field[index]
        rows.append(
            [
                index,
                position,
                position * 1000.0,
                1 if index in {0, len(x) - 1} else 0,
                analytic_field[index],
                classical_field[index],
                gpu_field[index],
                cpu_value,
                abs(gpu_field[index] - analytic_field[index]),
                (
                    abs(cpu_value - analytic_field[index])
                    if cpu_value is not None
                    else ""
                ),
                abs(classical_field[index] - analytic_field[index]),
            ]
        )
    return rows


def _error_rows(result: dict[str, Any]) -> list[list[Any]]:
    labels = {
        "semi_discrete_vs_continuous_analytic": (
            "semi_discrete_vs_analytic"
        ),
        "same_parameter_recovery_vs_semi_discrete": (
            "recovery_vs_semi_discrete"
        ),
        "trotter_vs_same_parameter_recovery": "trotter_vs_recovery",
        "trotter_vs_semi_discrete": "trotter_vs_semi_discrete",
        "trotter_vs_continuous_analytic": "trotter_vs_analytic",
    }
    metrics = result["error_decomposition"]["metrics"]
    return [
        [
            index,
            labels[key],
            metric["max_abs_error"],
            metric["rmse"],
            metric["relative_l2_error"],
        ]
        for index, (key, label) in enumerate(labels.items(), start=1)
        if (metric := metrics.get(key)) is not None and label
    ]


def _recorded_elapsed_s(path: Path | None) -> float | None:
    if path is None or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^elapsed_ms=(\d+)$",
        text,
        re.MULTILINE,
    )
    if match:
        return float(match.group(1)) / 1000.0
    started_match = re.search(r"^started=(.+)$", text, re.MULTILINE)
    finished_match = re.search(r"^finished=(.+)$", text, re.MULTILINE)
    if started_match and finished_match:
        started = datetime.strptime(
            started_match.group(1).strip(),
            "%Y-%m-%dT%H:%M:%S%z",
        )
        finished = datetime.strptime(
            finished_match.group(1).strip(),
            "%Y-%m-%dT%H:%M:%S%z",
        )
        elapsed = (finished - started).total_seconds()
        return elapsed if elapsed >= 0 else None
    return None


def _runtime_rows(
    result: dict[str, Any],
    command_log: Path | None,
) -> list[list[Any]]:
    rows = [
        [
            "quantum_cpu",
            result["quantum_cpu_reference"]["backend"],
            "cpu",
            result["quantum_cpu_reference"]["runtime_s"],
            "same parameters as GPU reference",
        ],
        [
            "quantum_gpu",
            result["quantum"]["backend"],
            "gpu",
            result["quantum"]["runtime_s"],
            "small-field GPU reference run",
        ],
        [
            "torch_supa_total",
            result["supa_audit"]["backend"],
            result["supa_audit"]["device"],
            result["supa_audit"]["runtime_s"]["total"],
            "transfer and reduction included",
        ],
        [
            "custom_supa_subprocess",
            result["custom_supa_audit"]["backend"],
            result["custom_supa_audit"]["device"],
            result["custom_supa_audit"]["runtime_s"]["subprocess_total"],
            "fixed single-block 256-thread kernel",
        ],
    ]
    elapsed = _recorded_elapsed_s(command_log)
    if elapsed is not None:
        rows.append(
            [
                "remote_command_total",
                "record_remote_command",
                "cpu+gpu+supa",
                elapsed,
                "end-to-end recorded wall time",
            ]
        )
    return rows


def _audit_rows(audit: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []

    def visit(checks: list[dict[str, Any]], prefix: str = "") -> None:
        for check in checks:
            name = f"{prefix}{check.get('name', 'unnamed')}"
            value = check.get("value")
            threshold = check.get("threshold")
            rows.append(
                [
                    name,
                    check.get("target", ""),
                    1 if check.get("passed") else 0,
                    value if isinstance(value, (int, float)) else "",
                    (
                        threshold
                        if isinstance(threshold, (int, float))
                        else ""
                    ),
                    json.dumps(value, ensure_ascii=False),
                    json.dumps(threshold, ensure_ascii=False),
                ]
            )
            nested = check.get("checks")
            if isinstance(nested, list):
                visit(nested, prefix=f"{name}/")

    visit(audit["checks"])
    return rows


def _working_region_rows(
    paths: list[Path],
) -> tuple[list[list[Any]], list[list[Any]]]:
    confirmed_rows: list[list[Any]] = []
    run_rows: list[list[Any]] = []
    for path in paths:
        data = _load_json(path)
        source = path.parent.name
        threshold = data["strict_relative_l2_threshold"]
        for case in data["cases"]:
            confirmed_nt = case.get("confirmed_quantum_steps")
            confirmed_run = next(
                (
                    run
                    for run in case["runs"]
                    if run["requested_nt"] == confirmed_nt
                ),
                None,
            )
            confirmed_rows.append(
                [
                    source,
                    case["fourier_number"],
                    case["spatial_points"],
                    case["physical_duration_s"],
                    confirmed_nt if confirmed_nt is not None else "",
                    case.get("first_strict_pass", ""),
                    (
                        case.get("confirmed_streak", ["", ""])[0]
                        if case.get("confirmed_streak")
                        else ""
                    ),
                    (
                        case.get("confirmed_streak", ["", ""])[-1]
                        if case.get("confirmed_streak")
                        else ""
                    ),
                    (
                        confirmed_run["metrics_vs_analytic"][
                            "relative_l2_error"
                        ]
                        if confirmed_run
                        else ""
                    ),
                    (
                        confirmed_run["metrics_vs_analytic"]["max_abs_error"]
                        if confirmed_run
                        else ""
                    ),
                    (
                        confirmed_run["metrics_vs_analytic"]["rmse"]
                        if confirmed_run
                        else ""
                    ),
                    confirmed_run["runtime_s"] if confirmed_run else "",
                    threshold,
                    1 if confirmed_run else 0,
                ]
            )
            for run in case["runs"]:
                metrics = run.get("metrics_vs_analytic", {})
                run_rows.append(
                    [
                        source,
                        case["fourier_number"],
                        case["spatial_points"],
                        run["requested_nt"],
                        run["status"],
                        1 if run.get("strict_accuracy_passed") else 0,
                        1 if run.get("physics_audit_passed") else 0,
                        metrics.get("max_abs_error", ""),
                        metrics.get("rmse", ""),
                        metrics.get("relative_l2_error", ""),
                        run.get("runtime_s", ""),
                        run.get("min_k", ""),
                        run.get("max_k", ""),
                    ]
                )
    confirmed_rows.sort(key=lambda row: (row[1], row[2], row[0]))
    key_counts = Counter((row[1], row[2]) for row in confirmed_rows)
    for row in confirmed_rows:
        row.append(1 if key_counts[(row[1], row[2])] > 1 else 0)
    run_rows.sort(key=lambda row: (row[1], row[2], row[3], row[0]))
    return confirmed_rows, run_rows


def export_origin_data(
    result_dir: Path,
    output_dir: Path,
    *,
    working_region_paths: list[Path],
    command_log: Path | None = None,
) -> dict[str, Any]:
    """Export flat numeric CSV tables and a source/hash manifest."""

    result_path = result_dir / "result.json"
    audit_path = result_dir / "audit.json"
    result = _load_json(result_path)
    audit = _load_json(audit_path)
    if result.get("status") != "success" or audit.get("passed") is not True:
        raise ValueError("Only a successful audited result may be exported.")
    output_dir.mkdir(parents=True, exist_ok=True)
    tables: dict[str, int] = {}
    tables["temperature_profile.csv"] = _write_csv(
        output_dir / "temperature_profile.csv",
        [
            "point_index",
            "x_m",
            "x_mm",
            "is_protocol_boundary",
            "analytic_k",
            "classical_fd_k",
            "quantum_gpu_k",
            "quantum_cpu_k",
            "abs_error_quantum_gpu_k",
            "abs_error_quantum_cpu_k",
            "abs_error_classical_fd_k",
        ],
        _temperature_rows(result),
    )
    tables["error_decomposition.csv"] = _write_csv(
        output_dir / "error_decomposition.csv",
        [
            "layer_index",
            "comparison",
            "max_abs_error_k",
            "rmse_k",
            "relative_l2_error",
        ],
        _error_rows(result),
    )
    tables["runtime_comparison.csv"] = _write_csv(
        output_dir / "runtime_comparison.csv",
        ["component", "backend", "device", "runtime_s", "notes"],
        _runtime_rows(result, command_log),
    )
    tables["audit_checks.csv"] = _write_csv(
        output_dir / "audit_checks.csv",
        [
            "check_name",
            "target",
            "passed_1_0",
            "numeric_value",
            "numeric_threshold",
            "value_json",
            "threshold_json",
        ],
        _audit_rows(audit),
    )
    confirmed, runs = _working_region_rows(working_region_paths)
    tables["working_region_confirmed.csv"] = _write_csv(
        output_dir / "working_region_confirmed.csv",
        [
            "source_scan",
            "fourier_number",
            "spatial_points",
            "physical_duration_s",
            "confirmed_nt",
            "first_strict_pass_nt",
            "confirmed_streak_start_nt",
            "confirmed_streak_end_nt",
            "confirmed_relative_l2_error",
            "confirmed_max_abs_error_k",
            "confirmed_rmse_k",
            "confirmed_runtime_s",
            "strict_relative_l2_threshold",
            "resolved_1_0",
            "duplicate_fo_n_key_1_0",
        ],
        confirmed,
    )
    tables["working_region_runs.csv"] = _write_csv(
        output_dir / "working_region_runs.csv",
        [
            "source_scan",
            "fourier_number",
            "spatial_points",
            "quantum_steps_nt",
            "status",
            "strict_accuracy_passed_1_0",
            "physics_audit_passed_1_0",
            "max_abs_error_k",
            "rmse_k",
            "relative_l2_error",
            "runtime_s",
            "min_temperature_k",
            "max_temperature_k",
        ],
        runs,
    )
    unique_profiles: dict[tuple[float, int], list[Any]] = {}
    for row in confirmed:
        unique_profiles.setdefault((float(row[1]), int(row[2])), row)
    unique_rows = sorted(
        unique_profiles.values(),
        key=lambda row: (row[1], row[2]),
    )
    tables["working_region_unique.csv"] = _write_csv(
        output_dir / "working_region_unique.csv",
        [
            "source_scan",
            "fourier_number",
            "spatial_points",
            "physical_duration_s",
            "confirmed_nt",
            "first_strict_pass_nt",
            "confirmed_streak_start_nt",
            "confirmed_streak_end_nt",
            "confirmed_relative_l2_error",
            "confirmed_max_abs_error_k",
            "confirmed_rmse_k",
            "confirmed_runtime_s",
            "strict_relative_l2_threshold",
            "resolved_1_0",
            "duplicate_fo_n_key_1_0",
        ],
        unique_rows,
    )
    tables["fourier_scan_plot.csv"] = _write_csv(
        output_dir / "fourier_scan_plot.csv",
        [
            "fourier_number_x",
            "confirmed_nt_y",
            "confirmed_relative_l2_error_y",
            "confirmed_runtime_s_y",
        ],
        [
            [row[1], row[4], row[8], row[11]]
            for row in unique_rows
            if int(row[2]) == 32
        ],
    )
    tables["grid_scan_plot.csv"] = _write_csv(
        output_dir / "grid_scan_plot.csv",
        [
            "spatial_points_x",
            "confirmed_nt_y",
            "confirmed_relative_l2_error_y",
            "confirmed_runtime_s_y",
        ],
        [
            [row[2], row[4], row[8], row[11]]
            for row in confirmed
            if row[0] == "working_region_grid"
        ],
    )
    metadata_rows = [
        ["result_status", result["status"], "", result_path.as_posix()],
        ["audit_passed", 1, "boolean", audit_path.as_posix()],
        ["task", result["task"], "", result_path.as_posix()],
        [
            "thermal_diffusivity",
            result["input"]["thermal_diffusivity_m2_s"],
            "m2/s",
            result_path.as_posix(),
        ],
        ["length", result["input"]["length_m"], "m", result_path.as_posix()],
        ["duration", result["input"]["duration_s"], "s", result_path.as_posix()],
        [
            "initial_amplitude",
            result["input"]["initial_amplitude_k"],
            "K",
            result_path.as_posix(),
        ],
        [
            "quantum_algorithm",
            result["quantum"]["algorithm"],
            "",
            result_path.as_posix(),
        ],
        [
            "quantum_backend",
            result["quantum"]["backend"],
            "",
            result_path.as_posix(),
        ],
        [
            "boundary_export_rule",
            "zero values added at x=0 and x=L from controlled protocol",
            "",
            result_path.as_posix(),
        ],
    ]
    tables["metadata.csv"] = _write_csv(
        output_dir / "metadata.csv",
        ["key", "value", "unit", "source_file"],
        metadata_rows,
    )
    sources = [result_path, audit_path, *working_region_paths]
    if command_log is not None and command_log.is_file():
        sources.append(command_log)
    manifest = {
        "task": "origin_plot_data_export",
        "status": "success",
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": [
            {
                "path": path.as_posix(),
                "sha256": _sha256(path),
            }
            for path in sources
        ],
        "tables": [
            {
                "path": name,
                "data_rows": rows,
                "sha256": _sha256(output_dir / name),
                "encoding": "UTF-8 with BOM",
                "delimiter": ",",
                "decimal_separator": ".",
            }
            for name, rows in tables.items()
        ],
        "notes": [
            (
                "Quantum fields contain interior nodes; zero boundary rows "
                "are added from the controlled Dirichlet protocol."
            ),
            (
                "Runtime rows record wall-clock measurements from the Biren "
                "competition container."
            ),
            (
                "Working-region rows are empirical exact configurations used "
                "for profile selection."
            ),
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest
