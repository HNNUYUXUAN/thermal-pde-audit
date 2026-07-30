"""Physics checks and numerical error metrics."""

from __future__ import annotations

from typing import Any

import numpy as np

from .schema import ThermalExperimentSpec


THRESHOLDS = {
    "boundary_residual_k": 1e-8,
    "max_range_relative": 1e-5,
    "decay_relative": 1e-8,
    "max_abs_error_k": 15.0,
    "relative_l2_error": 0.20,
    "cpu_gpu_max_diff_relative": 1e-5,
    "finite_difference_r": 0.5,
}


def error_metrics(
    actual: np.ndarray | list[float],
    reference: np.ndarray | list[float],
) -> dict[str, float]:
    """Compute max absolute, RMSE, and relative L2 error."""

    actual_array = np.asarray(actual, dtype=float)
    reference_array = np.asarray(reference, dtype=float)
    if actual_array.shape != reference_array.shape or actual_array.size == 0:
        raise ValueError("Actual/reference arrays must be non-empty and aligned.")
    delta = actual_array - reference_array
    denominator = np.linalg.norm(reference_array)
    return {
        "max_abs_error": float(np.max(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "relative_l2_error": (
            float(np.linalg.norm(delta) / denominator)
            if denominator > 0
            else (0.0 if np.linalg.norm(delta) == 0 else float("inf"))
        ),
    }


def _check(
    name: str,
    passed: bool,
    value: Any,
    threshold: Any,
    explanation: str,
    target: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "target": target,
        "passed": bool(passed),
        "value": value,
        "threshold": threshold,
        "explanation": explanation,
    }


def audit_field(
    spec: ThermalExperimentSpec,
    field_k: list[float],
    reference_k: list[float],
    *,
    target: str,
    includes_boundaries: bool,
    finite_difference_ratio: float | None = None,
    cpu_gpu_max_diff_k: float | None = None,
) -> dict[str, Any]:
    """Audit one final temperature field against physics and a reference."""

    field = np.asarray(field_k, dtype=float)
    reference = np.asarray(reference_k, dtype=float)
    checks: list[dict[str, Any]] = []

    finite = bool(field.size > 0 and np.all(np.isfinite(field)))
    checks.append(
        _check(
            "finite_nonempty_field",
            finite,
            {"size": int(field.size), "all_finite": finite},
            {"min_size": 1, "all_finite": True},
            "The result must not be empty and must contain no NaN or Inf.",
            target,
        )
    )
    if not finite or field.shape != reference.shape:
        checks.append(
            _check(
                "aligned_reference_shape",
                False,
                {"field": list(field.shape), "reference": list(reference.shape)},
                "equal non-empty shapes",
                "Error metrics require aligned result and reference arrays.",
                target,
            )
        )
        return {"passed": False, "thresholds": THRESHOLDS, "checks": checks}

    if includes_boundaries:
        boundary_residual = float(max(abs(field[0]), abs(field[-1])))
        boundary_explanation = (
            "Residual uses the two boundary nodes returned by the solver."
        )
    else:
        boundary_residual = 0.0
        boundary_explanation = (
            "UnitaryLab returned interior nodes only. This residual is for the "
            "zero Dirichlet values applied by the controlled protocol, not an "
            "independent boundary value emitted by UnitaryLab."
        )
    checks.append(
        _check(
            "boundary_residual",
            boundary_residual <= THRESHOLDS["boundary_residual_k"],
            boundary_residual,
            THRESHOLDS["boundary_residual_k"],
            boundary_explanation,
            target,
        )
    )

    tolerance = max(1.0, abs(spec.initial_amplitude_k)) * THRESHOLDS[
        "max_range_relative"
    ]
    max_value = float(np.max(field))
    min_value = float(np.min(field))
    range_passed = (
        min_value >= -tolerance
        and max_value <= spec.initial_amplitude_k + tolerance
    )
    checks.append(
        _check(
            "maximum_principle_range",
            range_passed,
            {"min_k": min_value, "max_k": max_value},
            {
                "min_k": -tolerance,
                "max_k": spec.initial_amplitude_k + tolerance,
            },
            "Positive diffusion with zero boundaries must not create a new extremum.",
            target,
        )
    )

    decay_limit = spec.initial_amplitude_k * (
        1.0 + THRESHOLDS["decay_relative"]
    )
    checks.append(
        _check(
            "positive_diffusivity_decay",
            float(np.max(np.abs(field))) <= decay_limit,
            float(np.max(np.abs(field))),
            decay_limit,
            "The final field amplitude must not exceed the initial amplitude.",
            target,
        )
    )

    metrics = error_metrics(field, reference)
    checks.extend(
        [
            _check(
                "max_abs_error",
                metrics["max_abs_error"] <= THRESHOLDS["max_abs_error_k"],
                metrics["max_abs_error"],
                THRESHOLDS["max_abs_error_k"],
                "Maximum pointwise error against the analytic solution.",
                target,
            ),
            _check(
                "rmse",
                metrics["rmse"] <= THRESHOLDS["max_abs_error_k"],
                metrics["rmse"],
                THRESHOLDS["max_abs_error_k"],
                "Root-mean-square error against the analytic solution.",
                target,
            ),
            _check(
                "relative_l2_error",
                metrics["relative_l2_error"]
                <= THRESHOLDS["relative_l2_error"],
                metrics["relative_l2_error"],
                THRESHOLDS["relative_l2_error"],
                "Relative L2 error against the analytic solution.",
                target,
            ),
        ]
    )

    if cpu_gpu_max_diff_k is not None:
        cpu_gpu_threshold_k = max(
            1.0,
            abs(spec.initial_amplitude_k),
        ) * THRESHOLDS["cpu_gpu_max_diff_relative"]
        checks.append(
            _check(
                "cpu_gpu_max_difference",
                cpu_gpu_max_diff_k <= cpu_gpu_threshold_k,
                cpu_gpu_max_diff_k,
                cpu_gpu_threshold_k,
                (
                    "Maximum aligned UnitaryLab CPU/GPU field difference. "
                    "The threshold is 1e-5 times max(1 K, initial amplitude)."
                ),
                target,
            )
        )
    if finite_difference_ratio is not None:
        checks.append(
            _check(
                "finite_difference_stability",
                finite_difference_ratio
                <= THRESHOLDS["finite_difference_r"] + 1e-15,
                finite_difference_ratio,
                THRESHOLDS["finite_difference_r"],
                "Explicit finite difference requires r <= 0.5.",
                target,
            )
        )

    return {
        "passed": all(item["passed"] for item in checks),
        "thresholds": THRESHOLDS,
        "metrics": metrics,
        "checks": checks,
    }
