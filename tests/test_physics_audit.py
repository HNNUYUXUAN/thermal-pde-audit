from __future__ import annotations

from thermal_pde_audit.classical_solver import solve_analytic, solve_classical
from thermal_pde_audit.physics_audit import audit_field
from thermal_pde_audit.schema import ThermalExperimentSpec


def test_classical_field_passes_physics_audit() -> None:
    spec = ThermalExperimentSpec.from_dict(
        {
            "length_m": 1.0,
            "thermal_diffusivity_m2_s": 0.01,
            "initial_amplitude_k": 1.0,
            "duration_s": 0.1,
            "spatial_points": 16,
            "time_steps": 10,
            "device": "cpu",
        }
    )
    analytic = solve_analytic(spec)
    classical = solve_classical(spec)
    audit = audit_field(
        spec,
        classical["state_or_field_k"],
        analytic["state_or_field_k"],
        target="classical",
        includes_boundaries=True,
        finite_difference_ratio=classical["grid"]["stability_ratio"],
    )
    assert audit["passed"]
    names = {item["name"] for item in audit["checks"]}
    assert {
        "boundary_residual",
        "maximum_principle_range",
        "positive_diffusivity_decay",
        "finite_nonempty_field",
        "max_abs_error",
        "rmse",
        "relative_l2_error",
        "finite_difference_stability",
    }.issubset(names)
