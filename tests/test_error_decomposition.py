from __future__ import annotations

import numpy as np

from thermal_pde_audit.error_decomposition import (
    build_semidiscrete_reference,
    decompose_quantum_error,
)
from thermal_pde_audit.schema import ThermalExperimentSpec


def _spec() -> ThermalExperimentSpec:
    return ThermalExperimentSpec.from_dict(
        {
            "task": "heat_equation_1d",
            "length_m": 0.01,
            "thermal_diffusivity_m2_s": 1.2e-5,
            "initial_amplitude_k": 100.0,
            "duration_s": 0.5,
            "spatial_points": 32,
            "time_steps": 200,
            "boundary": "dirichlet_zero",
            "initial_condition": "sine_mode_1",
            "device": "cpu",
            "seed": 42,
        }
    )


def test_semidiscrete_reference_reproduces_known_spatial_error() -> None:
    reference = build_semidiscrete_reference(_spec())

    relative_l2 = reference["metrics_vs_continuous_analytic"][
        "relative_l2_error"
    ]
    assert reference["method"] == "project_owned_dense_eigendecomposition"
    assert len(reference["state_or_field_k"]) == 32
    assert np.isclose(relative_l2, 4.472058828e-4, rtol=1e-8)


def test_decomposition_without_recovery_separates_spatial_and_total_error() -> None:
    spec = _spec()
    reference = build_semidiscrete_reference(spec)
    quantum = {
        "status": "success",
        "backend": "unitarylab_cpu",
        "algorithm": "test",
        "state_or_field": reference["state_or_field_k"],
        "spatial_grid_m": reference["spatial_grid_m"],
        "runtime_s": 0.1,
    }

    decomposition = decompose_quantum_error(
        spec,
        quantum,
        ancilla_qubits=8,
        auxiliary_range=16.0,
        recovery_point=1,
        include_recovery=False,
    )

    assert decomposition["status"] == "success"
    assert decomposition["recovery_reference"]["status"] == "not_requested"
    assert (
        decomposition["metrics"]["trotter_vs_semi_discrete"][
            "relative_l2_error"
        ]
        == 0.0
    )


def test_decomposition_rejects_mismatched_quantum_grid() -> None:
    spec = _spec()
    reference = build_semidiscrete_reference(spec)
    shifted_grid = np.asarray(reference["spatial_grid_m"]) + 1e-6
    quantum = {
        "status": "success",
        "state_or_field": reference["state_or_field_k"],
        "spatial_grid_m": shifted_grid.tolist(),
    }

    decomposition = decompose_quantum_error(
        spec,
        quantum,
        ancilla_qubits=8,
        auxiliary_range=16.0,
        recovery_point=1,
        include_recovery=False,
    )

    assert decomposition["status"] == "failed"
    assert decomposition["error"]["type"] == "QuantumGridMismatch"
