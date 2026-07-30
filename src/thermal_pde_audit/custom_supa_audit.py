"""Audit thermal error metrics with the project-owned SUPA reduction kernel."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from .physics_audit import error_metrics


CUSTOM_REDUCTION_TOLERANCE = 1e-6
CUSTOM_END_TO_END_TOLERANCE = 1e-5
MAX_CUSTOM_FIELD_SIZE = 256
CUSTOM_SUPA_TIMEOUT_S = 60


def _differences(
    actual: dict[str, float],
    reference: dict[str, float],
) -> dict[str, float]:
    return {
        name: abs(float(actual[name]) - float(reference[name]))
        for name in reference
    }


def audit_error_metrics_with_custom_supa(
    actual: list[float] | np.ndarray,
    reference: list[float] | np.ndarray,
    executable: Path,
) -> dict[str, Any]:
    """Run the standalone project-owned SUPA reduction and verify its output."""

    actual_source = np.asarray(actual, dtype=np.float64)
    reference_source = np.asarray(reference, dtype=np.float64)
    base: dict[str, Any] = {
        "backend": "custom_supa_reduction_kernel",
        "device": "supa:0",
        "dtype": "float32",
        "status": "failed",
        "kernel_source": "scripts/supa_error_reduction.su",
        "executable": str(executable),
        "metrics": {},
        "cpu_float32_metrics": {},
        "cpu_source_float64_metrics": {},
        "consistency": {},
        "runtime_s": {},
        "warnings": [
            (
                "The custom kernel is optimized for fields of up to 256 "
                "values using one 256-thread SUPA block and shared-memory "
                "tree reduction."
            ),
            (
                "The kernel accumulates in float32. Independent float32 and "
                "source-float64 checks use separate tolerances."
            ),
        ],
    }
    if (
        actual_source.shape != reference_source.shape
        or actual_source.ndim != 1
        or actual_source.size == 0
        or actual_source.size > MAX_CUSTOM_FIELD_SIZE
        or not np.all(np.isfinite(actual_source))
        or not np.all(np.isfinite(reference_source))
    ):
        base["error"] = {
            "type": "ValueError",
            "message": (
                "Custom SUPA audit requires aligned, finite 1D arrays with "
                f"1..{MAX_CUSTOM_FIELD_SIZE} values."
            ),
            "actual_shape": list(actual_source.shape),
            "reference_shape": list(reference_source.shape),
        }
        return base

    executable = Path(executable)
    if not executable.is_file():
        base["error"] = {
            "type": "FileNotFoundError",
            "message": f"Custom SUPA executable not found: {executable}",
        }
        return base

    actual_float32 = actual_source.astype(np.float32)
    reference_float32 = reference_source.astype(np.float32)
    with tempfile.TemporaryDirectory(
        prefix="thermal-custom-supa-"
    ) as temporary:
        input_path = Path(temporary) / "field_pairs.txt"
        lines = [str(actual_float32.size)]
        lines.extend(
            f"{float(actual_value):.9g} {float(reference_value):.9g}"
            for actual_value, reference_value in zip(
                actual_float32,
                reference_float32,
                strict=True,
            )
        )
        input_path.write_text("\n".join(lines) + "\n", encoding="ascii")
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [str(executable.resolve()), str(input_path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=CUSTOM_SUPA_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            base["runtime_s"] = {
                "subprocess_total": time.perf_counter() - started
            }
            base["error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
            return base
        total_s = time.perf_counter() - started

    base["runtime_s"] = {"subprocess_total": total_s}
    base["process"] = {
        "exit_code": completed.returncode,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        base["error"] = {
            "type": "CustomSupaProcessError",
            "message": "The custom SUPA executable returned a non-zero code.",
        }
        return base
    try:
        raw = json.loads(completed.stdout)
        custom_metrics = {
            "max_abs_error": float(raw["max_abs_error"]),
            "rmse": float(raw["rmse"]),
            "relative_l2_error": float(raw["relative_l2_error"]),
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        base["error"] = {
            "type": type(exc).__name__,
            "message": f"Invalid custom SUPA JSON output: {exc}",
        }
        return base

    cpu_float32 = error_metrics(actual_float32, reference_float32)
    cpu_source = error_metrics(actual_source, reference_source)
    reduction_differences = _differences(custom_metrics, cpu_float32)
    end_to_end_differences = _differences(custom_metrics, cpu_source)
    reduction_passed = all(
        value <= CUSTOM_REDUCTION_TOLERANCE
        for value in reduction_differences.values()
    )
    end_to_end_passed = all(
        value <= CUSTOM_END_TO_END_TOLERANCE
        for value in end_to_end_differences.values()
    )
    consistency = {
        "passed": reduction_passed and end_to_end_passed,
        "kernel_vs_float32_cpu": {
            "passed": reduction_passed,
            "absolute_differences": reduction_differences,
            "threshold": CUSTOM_REDUCTION_TOLERANCE,
        },
        "end_to_end_vs_source_float64_cpu": {
            "passed": end_to_end_passed,
            "absolute_differences": end_to_end_differences,
            "threshold": CUSTOM_END_TO_END_TOLERANCE,
        },
    }
    base.update(
        {
            "status": "success" if consistency["passed"] else "failed",
            "metrics": custom_metrics,
            "raw_kernel_result": raw,
            "cpu_float32_metrics": cpu_float32,
            "cpu_source_float64_metrics": cpu_source,
            "consistency": consistency,
        }
    )
    if not consistency["passed"]:
        base["error"] = {
            "type": "CustomSupaMetricMismatch",
            "message": "Custom SUPA metrics exceeded a consistency tolerance.",
        }
    return base
