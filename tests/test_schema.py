from __future__ import annotations

import pytest

from thermal_pde_audit.schema import (
    ThermalExperimentSpec,
    ThermalSpecValidationError,
)


def valid_raw() -> dict[str, object]:
    return {
        "task": "heat_equation_1d",
        "length_m": 0.01,
        "thermal_diffusivity_m2_s": 1.2e-5,
        "initial_amplitude_k": 100,
        "duration_s": 0.5,
        "spatial_points": 32,
        "time_steps": 200,
        "boundary": "dirichlet_zero",
        "initial_condition": "sine_mode_1",
        "device": "cpu",
        "seed": 42,
    }


def test_valid_spec_and_fourier_number() -> None:
    spec = ThermalExperimentSpec.from_dict(valid_raw())
    assert spec.fourier_number == pytest.approx(0.06)
    assert spec.spatial_points == 32


def test_negative_diffusivity_is_structured_rejection() -> None:
    raw = valid_raw()
    raw["thermal_diffusivity_m2_s"] = -1e-5
    with pytest.raises(ThermalSpecValidationError) as error:
        ThermalExperimentSpec.from_dict(raw)
    payload = error.value.to_dict()
    assert payload["status"] == "rejected"
    assert any(
        issue["field"] == "thermal_diffusivity_m2_s"
        for issue in payload["error"]["issues"]
    )


def test_unsupported_boundary_is_rejected() -> None:
    raw = valid_raw()
    raw["boundary"] = "periodic"
    with pytest.raises(ThermalSpecValidationError) as error:
        ThermalExperimentSpec.from_dict(raw)
    assert error.value.issues[0].code == "UNSUPPORTED_BOUNDARY"


def test_spatial_points_must_be_power_of_two() -> None:
    raw = valid_raw()
    raw["spatial_points"] = 30
    with pytest.raises(ThermalSpecValidationError) as error:
        ThermalExperimentSpec.from_dict(raw)
    assert any(issue.code == "NOT_POWER_OF_TWO" for issue in error.value.issues)
