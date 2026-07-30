import json
from pathlib import Path

import pytest

from thermal_pde_audit.quantum_policy import (
    QuantumProfileError,
    recommend_quantum_profile,
)
from thermal_pde_audit.schema import ThermalExperimentSpec


def _spec(*, fourier_number: float, spatial_points: int) -> ThermalExperimentSpec:
    length = 0.01
    diffusivity = 1.2e-5
    return ThermalExperimentSpec.from_dict(
        {
            "task": "heat_equation_1d",
            "length_m": length,
            "thermal_diffusivity_m2_s": diffusivity,
            "initial_amplitude_k": 100.0,
            "duration_s": fourier_number * length**2 / diffusivity,
            "spatial_points": spatial_points,
            "time_steps": 1000,
            "boundary": "dirichlet_zero",
            "initial_condition": "sine_mode_1",
            "device": "gpu",
            "seed": 42,
        }
    )


def test_standard_case_gets_exact_validated_profile() -> None:
    result = recommend_quantum_profile(
        _spec(fourier_number=0.06, spatial_points=32)
    )

    assert result["selection_mode"] == "exact_empirical_match"
    assert result["parameters"] == {
        "quantum_steps": 32,
        "ancilla_qubits": 8,
        "auxiliary_range": 16.0,
        "recovery_point": 1,
    }
    assert result["confirmed_streak"] == [16, 32]


def test_profile_does_not_interpolate_unverified_case() -> None:
    with pytest.raises(QuantumProfileError) as caught:
        recommend_quantum_profile(
            _spec(fourier_number=0.035, spatial_points=32)
        )

    assert caught.value.code == "UNVERIFIED_QUANTUM_CONFIGURATION"


def test_profile_rejects_an_unvalidated_installed_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "thermal_pde_audit.quantum_policy.importlib.metadata.version",
        lambda package: "unexpected-version",
    )

    with pytest.raises(QuantumProfileError) as caught:
        recommend_quantum_profile(
            _spec(fourier_number=0.06, spatial_points=32),
            validate_environment=True,
        )

    assert caught.value.code == "QUANTUM_PROFILE_ENVIRONMENT_MISMATCH"


def test_profile_can_be_loaded_from_an_explicit_evidence_file(
    tmp_path: Path,
) -> None:
    policy = {
        "scope": {},
        "environment": {},
        "fixed_quantum_parameters": {
            "ancilla_qubits": 5,
            "auxiliary_range": 4.0,
            "recovery_point": 1,
        },
        "evidence": ["test"],
        "profiles": [
            {
                "fourier_number": 0.06,
                "spatial_points": 32,
                "quantum_steps": 16,
                "confirmed_streak": [8, 16],
            }
        ],
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")

    result = recommend_quantum_profile(
        _spec(fourier_number=0.06, spatial_points=32),
        policy_path=path,
    )

    assert result["parameters"]["quantum_steps"] == 16
