"""Exact-match access to empirically validated quantum parameter profiles."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

from .schema import ThermalExperimentSpec


PROFILE_PATH = Path(__file__).with_name("validated_profiles.json")


class QuantumProfileError(ValueError):
    """Structured failure for absent or incompatible validated profiles."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        requested: dict[str, Any],
        allowed: Any,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.requested = requested
        self.allowed = allowed

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "failed",
            "error": {
                "code": self.code,
                "type": type(self).__name__,
                "message": str(self),
                "requested": self.requested,
                "allowed": self.allowed,
                "recoverable": True,
                "suggestions": [
                    "Use an exact validated Fo/spatial-points pair.",
                    (
                        "Run scripts/map_quantum_working_region.py and review "
                        "the evidence before adding a new profile."
                    ),
                    (
                        "Use explicit manual quantum parameters only when a "
                        "new audited experiment is intended."
                    ),
                ],
            },
        }


def _load_policy(path: Path = PROFILE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def recommend_quantum_profile(
    spec: ThermalExperimentSpec,
    *,
    validate_environment: bool = False,
    policy_path: Path = PROFILE_PATH,
) -> dict[str, Any]:
    """Return an exact validated profile without interpolation or extrapolation."""

    policy = _load_policy(policy_path)
    requested = {
        "fourier_number": spec.fourier_number,
        "spatial_points": spec.spatial_points,
    }
    match = next(
        (
            row
            for row in policy["profiles"]
            if row["spatial_points"] == spec.spatial_points
            and abs(row["fourier_number"] - spec.fourier_number) <= 1e-12
        ),
        None,
    )
    if match is None:
        allowed = [
            {
                "fourier_number": row["fourier_number"],
                "spatial_points": row["spatial_points"],
            }
            for row in policy["profiles"]
        ]
        raise QuantumProfileError(
            "UNVERIFIED_QUANTUM_CONFIGURATION",
            (
                "No exact empirical quantum profile exists for the requested "
                "Fourier number and spatial grid; interpolation is disabled."
            ),
            requested=requested,
            allowed=allowed,
        )

    observed_versions: dict[str, str] = {}
    if validate_environment:
        for package, expected in policy["environment"].items():
            try:
                observed = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                observed = "not_installed"
            observed_versions[package] = observed
            if observed != expected:
                raise QuantumProfileError(
                    "QUANTUM_PROFILE_ENVIRONMENT_MISMATCH",
                    (
                        f"Validated profile requires {package}=={expected}; "
                        f"observed {observed}."
                    ),
                    requested={
                        **requested,
                        "observed_versions": observed_versions,
                    },
                    allowed=policy["environment"],
                )

    fixed = policy["fixed_quantum_parameters"]
    return {
        "status": "validated_profile",
        "selection_mode": "exact_empirical_match",
        "requested": requested,
        "parameters": {
            "quantum_steps": match["quantum_steps"],
            "ancilla_qubits": fixed["ancilla_qubits"],
            "auxiliary_range": fixed["auxiliary_range"],
            "recovery_point": fixed["recovery_point"],
        },
        "confirmed_streak": match["confirmed_streak"],
        "validation_scope": policy["scope"],
        "required_environment": policy["environment"],
        "observed_versions": observed_versions,
        "evidence": policy["evidence"],
        "warnings": [
            (
                "This is an exact empirical profile for the controlled "
                "sine/Dirichlet problem, not an interpolated convergence rule."
            )
        ],
    }
