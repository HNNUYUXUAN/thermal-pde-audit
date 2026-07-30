"""Analytic and explicit finite-difference baselines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .schema import ThermalExperimentSpec


@dataclass(frozen=True)
class FiniteDifferenceStabilityError(ValueError):
    """Diagnostic for an unstable explicit finite-difference request."""

    stability_ratio: float
    requested_time_steps: int
    recommended_min_time_steps: int
    dx_m: float
    dt_s: float

    def __str__(self) -> str:
        return (
            f"Explicit finite difference is unstable: r={self.stability_ratio:.6g} "
            f"> 0.5; use at least {self.recommended_min_time_steps} time steps."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "rejected",
            "error": {
                "code": "FINITE_DIFFERENCE_UNSTABLE",
                "message": str(self),
                "stability_ratio": self.stability_ratio,
                "threshold": 0.5,
                "requested_time_steps": self.requested_time_steps,
                "recommended_min_time_steps": self.recommended_min_time_steps,
                "dx_m": self.dx_m,
                "dt_s": self.dt_s,
                "input_modified": False,
            },
        }


def analytic_field_at(
    spec: ThermalExperimentSpec,
    x_m: np.ndarray,
    time_s: float | None = None,
) -> np.ndarray:
    """Evaluate the first-sine-mode analytic solution at arbitrary points."""

    t = spec.duration_s if time_s is None else float(time_s)
    decay = np.exp(
        -spec.thermal_diffusivity_m2_s
        * (np.pi / spec.length_m) ** 2
        * t
    )
    return (
        spec.initial_amplitude_k
        * decay
        * np.sin(np.pi * np.asarray(x_m, dtype=float) / spec.length_m)
    )


def solve_analytic(spec: ThermalExperimentSpec) -> dict[str, Any]:
    """Return the exact final field including the two boundary points."""

    x = np.linspace(0.0, spec.length_m, spec.spatial_points + 2)
    initial = analytic_field_at(spec, x, time_s=0.0)
    final = analytic_field_at(spec, x)
    return {
        "backend": "analytic",
        "status": "success",
        "spatial_grid_m": x.tolist(),
        "initial_field_k": initial.tolist(),
        "state_or_field_k": final.tolist(),
        "time_s": spec.duration_s,
        "parameters": {
            "length_m": spec.length_m,
            "thermal_diffusivity_m2_s": spec.thermal_diffusivity_m2_s,
            "initial_amplitude_k": spec.initial_amplitude_k,
            "mode": 1,
            "boundary": spec.boundary,
        },
    }


def stability_diagnostic(spec: ThermalExperimentSpec) -> dict[str, Any]:
    """Compute the explicit scheme's r ratio without running the solver."""

    dx = spec.length_m / (spec.spatial_points + 1)
    dt = spec.duration_s / spec.time_steps
    ratio = spec.thermal_diffusivity_m2_s * dt / dx**2
    min_steps = int(
        np.ceil(
            spec.thermal_diffusivity_m2_s
            * spec.duration_s
            / (0.5 * dx**2)
        )
    )
    return {
        "stable": bool(ratio <= 0.5 + 1e-15),
        "stability_ratio": float(ratio),
        "threshold": 0.5,
        "dx_m": float(dx),
        "dt_s": float(dt),
        "requested_time_steps": spec.time_steps,
        "recommended_min_time_steps": max(1, min_steps),
    }


def solve_classical(spec: ThermalExperimentSpec) -> dict[str, Any]:
    """Solve with an explicit centered finite-difference method."""

    diagnostic = stability_diagnostic(spec)
    if not diagnostic["stable"]:
        raise FiniteDifferenceStabilityError(
            stability_ratio=diagnostic["stability_ratio"],
            requested_time_steps=spec.time_steps,
            recommended_min_time_steps=diagnostic["recommended_min_time_steps"],
            dx_m=diagnostic["dx_m"],
            dt_s=diagnostic["dt_s"],
        )

    x = np.linspace(0.0, spec.length_m, spec.spatial_points + 2)
    u = analytic_field_at(spec, x, time_s=0.0)
    ratio = diagnostic["stability_ratio"]
    for _ in range(spec.time_steps):
        next_u = u.copy()
        next_u[1:-1] = (
            u[1:-1] + ratio * (u[2:] - 2.0 * u[1:-1] + u[:-2])
        )
        next_u[0] = 0.0
        next_u[-1] = 0.0
        u = next_u

    return {
        "backend": "explicit_finite_difference",
        "status": "success",
        "spatial_grid_m": x.tolist(),
        "state_or_field_k": u.tolist(),
        "time_s": spec.duration_s,
        "grid": diagnostic,
    }
