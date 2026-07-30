"""Independent semi-discrete and Schrödingerization error diagnostics."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from .classical_solver import analytic_field_at
from .physics_audit import error_metrics
from .schema import ThermalExperimentSpec


def _real_array(values: Any) -> tuple[np.ndarray, float]:
    """Return real values and the largest discarded imaginary component."""

    array = np.asarray(values)
    imaginary_max = (
        float(np.max(np.abs(np.imag(array)))) if np.iscomplexobj(array) else 0.0
    )
    return np.asarray(np.real(array), dtype=float), imaginary_max


def build_semidiscrete_reference(
    spec: ThermalExperimentSpec,
) -> dict[str, Any]:
    """Build the project-owned central-difference matrix and exact evolution."""

    point_count = spec.spatial_points
    dx_dimensionless = 1.0 / (point_count + 1)
    x_dimensionless = (
        np.arange(1, point_count + 1, dtype=float) * dx_dimensionless
    )
    operator = np.zeros((point_count, point_count), dtype=float)
    np.fill_diagonal(operator, -2.0 / dx_dimensionless**2)
    off_diagonal = np.full(point_count - 1, 1.0 / dx_dimensionless**2)
    operator[np.arange(point_count - 1), np.arange(1, point_count)] = (
        off_diagonal
    )
    operator[np.arange(1, point_count), np.arange(point_count - 1)] = (
        off_diagonal
    )
    initial_dimensionless = np.sin(np.pi * x_dimensionless)
    eigenvalues, eigenvectors = np.linalg.eigh(operator)
    semi_discrete_dimensionless = eigenvectors @ (
        np.exp(eigenvalues * spec.fourier_number)
        * (eigenvectors.T @ initial_dimensionless)
    )
    spatial_grid_m = x_dimensionless * spec.length_m
    semi_discrete_k = (
        semi_discrete_dimensionless * spec.initial_amplitude_k
    )
    analytic_k = analytic_field_at(spec, spatial_grid_m)
    return {
        "method": "project_owned_dense_eigendecomposition",
        "spatial_grid_m": spatial_grid_m.tolist(),
        "state_or_field_k": semi_discrete_k.tolist(),
        "matrix_dense_dimensionless": operator.tolist(),
        "initial_dimensionless": initial_dimensionless.tolist(),
        "duration_dimensionless": spec.fourier_number,
        "dx_dimensionless": dx_dimensionless,
        "boundary": "dirichlet_zero",
        "scheme": "second_order_central_difference",
        "eigenvalue_min": float(np.min(eigenvalues)),
        "eigenvalue_max": float(np.max(eigenvalues)),
        "metrics_vs_continuous_analytic": error_metrics(
            semi_discrete_k.tolist(),
            analytic_k.tolist(),
        ),
    }


def _run_same_parameter_recovery(
    spec: ThermalExperimentSpec,
    semi_discrete: dict[str, Any],
    *,
    ancilla_qubits: int,
    auxiliary_range: float,
    recovery_point: int,
) -> dict[str, Any]:
    """Run UnitaryLab's non-Trotter recovery on the independent matrix."""

    try:
        from scipy.sparse import csr_matrix
        from unitarylab.library.equation.schrodingerization import (
            schro_classical,
        )

        matrix = csr_matrix(
            np.asarray(
                semi_discrete["matrix_dense_dimensionless"],
                dtype=float,
            )
        )
        initial = np.asarray(
            semi_discrete["initial_dimensionless"],
            dtype=float,
        )
        started = time.perf_counter()
        raw = schro_classical(
            matrix,
            initial,
            T=spec.fourier_number,
            na=ancilla_qubits,
            R=auxiliary_range,
            order=2,
            point=recovery_point,
            b=np.zeros(spec.spatial_points, dtype=float),
            device="cpu",
        )
        runtime_s = time.perf_counter() - started
        values, imaginary_max = _real_array(raw)
        if values.size != spec.spatial_points:
            raise ValueError(
                "schro_classical returned "
                f"{values.size} values; expected {spec.spatial_points}."
            )
        values_k = values * spec.initial_amplitude_k
        semi_k = semi_discrete["state_or_field_k"]
        return {
            "status": "success",
            "backend": "unitarylab_schro_classical_cpu",
            "parameters": {
                "ancilla_qubits": ancilla_qubits,
                "auxiliary_range": auxiliary_range,
                "recovery_point": recovery_point,
                "order": 2,
                "duration_dimensionless": spec.fourier_number,
            },
            "state_or_field_k": values_k.tolist(),
            "runtime_s": runtime_s,
            "max_discarded_imaginary": imaginary_max,
            "metrics_vs_semi_discrete": error_metrics(
                values_k.tolist(),
                semi_k,
            ),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "backend": "unitarylab_schro_classical_cpu",
            "parameters": {
                "ancilla_qubits": ancilla_qubits,
                "auxiliary_range": auxiliary_range,
                "recovery_point": recovery_point,
                "order": 2,
                "duration_dimensionless": spec.fourier_number,
            },
            "state_or_field_k": [],
            "runtime_s": 0.0,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }


def decompose_quantum_error(
    spec: ThermalExperimentSpec,
    quantum: dict[str, Any],
    *,
    ancilla_qubits: int,
    auxiliary_range: float,
    recovery_point: int,
    include_recovery: bool,
) -> dict[str, Any]:
    """Compare continuous, semi-discrete, recovery, and Trotter fields."""

    semi_discrete = build_semidiscrete_reference(spec)
    quantum_field = np.asarray(quantum.get("state_or_field", []), dtype=float)
    quantum_grid = np.asarray(quantum.get("spatial_grid_m", []), dtype=float)
    expected_grid = np.asarray(
        semi_discrete["spatial_grid_m"],
        dtype=float,
    )
    if (
        quantum.get("status") != "success"
        or quantum_field.size != spec.spatial_points
        or quantum_grid.size != spec.spatial_points
    ):
        return {
            "status": "failed",
            "error": {
                "type": "InvalidQuantumField",
                "message": (
                    "Error decomposition requires a successful quantum field "
                    "and grid matching spatial_points."
                ),
            },
            "semi_discrete_reference": semi_discrete,
        }
    if not np.allclose(quantum_grid, expected_grid, rtol=0.0, atol=1e-12):
        return {
            "status": "failed",
            "error": {
                "type": "QuantumGridMismatch",
                "message": (
                    "The UnitaryLab interior grid does not match the "
                    "independent central-difference reference grid."
                ),
            },
            "semi_discrete_reference": semi_discrete,
        }

    analytic_k = analytic_field_at(spec, quantum_grid).tolist()
    semi_k = semi_discrete["state_or_field_k"]
    recovery = (
        _run_same_parameter_recovery(
            spec,
            semi_discrete,
            ancilla_qubits=ancilla_qubits,
            auxiliary_range=auxiliary_range,
            recovery_point=recovery_point,
        )
        if include_recovery
        else {
            "status": "not_requested",
            "backend": "unitarylab_schro_classical_cpu",
        }
    )
    metrics: dict[str, Any] = {
        "semi_discrete_vs_continuous_analytic": semi_discrete[
            "metrics_vs_continuous_analytic"
        ],
        "trotter_vs_semi_discrete": error_metrics(
            quantum_field.tolist(),
            semi_k,
        ),
        "trotter_vs_continuous_analytic": error_metrics(
            quantum_field.tolist(),
            analytic_k,
        ),
    }
    if recovery.get("status") == "success":
        recovery_field = np.asarray(
            recovery["state_or_field_k"],
            dtype=float,
        )
        metrics["same_parameter_recovery_vs_semi_discrete"] = recovery[
            "metrics_vs_semi_discrete"
        ]
        metrics["trotter_vs_same_parameter_recovery"] = error_metrics(
            quantum_field.tolist(),
            recovery_field,
        )

    status = (
        "success"
        if recovery.get("status") in {"success", "not_requested"}
        else "failed"
    )
    return {
        "status": status,
        "method": (
            "independent_semi_discrete_reference_with_same_parameter_"
            "unitarylab_recovery"
        ),
        "semi_discrete_reference": semi_discrete,
        "recovery_reference": recovery,
        "trotter_result": {
            "backend": quantum.get("backend"),
            "algorithm": quantum.get("algorithm"),
            "state_or_field_k": quantum_field.tolist(),
            "runtime_s": quantum.get("runtime_s"),
        },
        "metrics": metrics,
        "interpretation": [
            (
                "The semi-discrete reference isolates spatial discretization "
                "from the continuous analytic solution."
            ),
            (
                "The same-parameter recovery reference runs schro_classical "
                "without Trotter time splitting."
            ),
            (
                "Trotter-versus-recovery is a diagnostic gap, not an additive "
                "error theorem; cancellation can make a downstream field "
                "closer to the analytic solution."
            ),
            (
                "All conclusions are limited to this controlled 1D heat "
                "equation and the exact recorded parameter profile."
            ),
        ],
    }
