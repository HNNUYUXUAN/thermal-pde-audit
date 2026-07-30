from __future__ import annotations

import numpy as np
import pytest

from thermal_pde_audit.classical_solver import (
    FiniteDifferenceStabilityError,
    solve_analytic,
    solve_classical,
)
from thermal_pde_audit.physics_audit import error_metrics
from thermal_pde_audit.schema import ThermalExperimentSpec


def make_spec(time_steps: int = 200) -> ThermalExperimentSpec:
    return ThermalExperimentSpec.from_dict(
        {
            "task": "heat_equation_1d",
            "length_m": 0.01,
            "thermal_diffusivity_m2_s": 1.2e-5,
            "initial_amplitude_k": 100,
            "duration_s": 0.5,
            "spatial_points": 32,
            "time_steps": time_steps,
            "boundary": "dirichlet_zero",
            "initial_condition": "sine_mode_1",
            "device": "cpu",
            "seed": 42,
        }
    )


def test_analytic_solution_has_zero_boundaries_and_decay() -> None:
    result = solve_analytic(make_spec())
    field = np.asarray(result["state_or_field_k"])
    assert field[0] == pytest.approx(0.0, abs=1e-12)
    assert field[-1] == pytest.approx(0.0, abs=1e-12)
    assert field.max() < 100.0


def test_stable_explicit_solver_matches_analytic() -> None:
    spec = make_spec()
    analytic = solve_analytic(spec)
    classical = solve_classical(spec)
    metrics = error_metrics(
        classical["state_or_field_k"],
        analytic["state_or_field_k"],
    )
    assert classical["grid"]["stability_ratio"] <= 0.5
    assert metrics["relative_l2_error"] < 0.01


def test_unstable_request_is_not_silently_modified() -> None:
    with pytest.raises(FiniteDifferenceStabilityError) as error:
        solve_classical(make_spec(time_steps=100))
    payload = error.value.to_dict()["error"]
    assert payload["stability_ratio"] > 0.5
    assert payload["recommended_min_time_steps"] > 100
    assert payload["input_modified"] is False
