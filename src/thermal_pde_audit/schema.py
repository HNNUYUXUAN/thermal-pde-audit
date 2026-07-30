"""Controlled experiment schema and structured validation errors."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    """One machine-readable input validation issue."""

    field: str
    code: str
    message: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ThermalSpecValidationError(ValueError):
    """Raised when an experiment specification violates the whitelist."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "rejected",
            "error": {
                "code": "INVALID_EXPERIMENT_SPEC",
                "message": "Experiment specification validation failed.",
                "issues": [issue.to_dict() for issue in self.issues],
            },
        }


@dataclass(frozen=True)
class ThermalExperimentSpec:
    """Whitelisted one-dimensional heat-equation experiment."""

    task: str
    length_m: float
    thermal_diffusivity_m2_s: float
    initial_amplitude_k: float
    duration_s: float
    spatial_points: int = 32
    time_steps: int = 200
    boundary: str = "dirichlet_zero"
    initial_condition: str = "sine_mode_1"
    device: str = "cpu"
    seed: int = 42

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ThermalExperimentSpec":
        if not isinstance(raw, dict):
            raise ThermalSpecValidationError(
                [
                    ValidationIssue(
                        field="$",
                        code="TYPE_ERROR",
                        message="The experiment input must be a JSON object.",
                        value=type(raw).__name__,
                    )
                ]
            )

        allowed = set(cls.__dataclass_fields__)
        issues: list[ValidationIssue] = []
        for name in sorted(set(raw) - allowed):
            issues.append(
                ValidationIssue(
                    field=name,
                    code="UNKNOWN_FIELD",
                    message=f"Field '{name}' is not part of the controlled protocol.",
                    value=raw[name],
                )
            )

        required = (
            "length_m",
            "thermal_diffusivity_m2_s",
            "initial_amplitude_k",
            "duration_s",
        )
        for name in required:
            if name not in raw:
                issues.append(
                    ValidationIssue(
                        field=name,
                        code="MISSING_FIELD",
                        message=f"Required field '{name}' is missing.",
                    )
                )
        if issues:
            raise ThermalSpecValidationError(issues)

        values = {
            "task": raw.get("task", "heat_equation_1d"),
            "length_m": raw["length_m"],
            "thermal_diffusivity_m2_s": raw["thermal_diffusivity_m2_s"],
            "initial_amplitude_k": raw["initial_amplitude_k"],
            "duration_s": raw["duration_s"],
            "spatial_points": raw.get("spatial_points", 32),
            "time_steps": raw.get("time_steps", 200),
            "boundary": raw.get("boundary", "dirichlet_zero"),
            "initial_condition": raw.get("initial_condition", "sine_mode_1"),
            "device": str(raw.get("device", "cpu")).lower(),
            "seed": raw.get("seed", 42),
        }

        for name in (
            "length_m",
            "thermal_diffusivity_m2_s",
            "initial_amplitude_k",
            "duration_s",
        ):
            try:
                values[name] = float(values[name])
            except (TypeError, ValueError):
                issues.append(
                    ValidationIssue(
                        field=name,
                        code="TYPE_ERROR",
                        message=f"Field '{name}' must be numeric.",
                        value=values[name],
                    )
                )

        for name in ("spatial_points", "time_steps", "seed"):
            value = values[name]
            if isinstance(value, bool):
                issues.append(
                    ValidationIssue(
                        field=name,
                        code="TYPE_ERROR",
                        message=f"Field '{name}' must be an integer.",
                        value=value,
                    )
                )
                continue
            try:
                converted = int(value)
                if float(value) != converted:
                    raise ValueError
                values[name] = converted
            except (TypeError, ValueError):
                issues.append(
                    ValidationIssue(
                        field=name,
                        code="TYPE_ERROR",
                        message=f"Field '{name}' must be an integer.",
                        value=value,
                    )
                )

        if issues:
            raise ThermalSpecValidationError(issues)

        positive_bounds = {
            "length_m": (1e-6, 100.0),
            "thermal_diffusivity_m2_s": (1e-12, 1.0),
            "initial_amplitude_k": (1e-9, 1e6),
            "duration_s": (1e-9, 1e6),
        }
        for name, (lower, upper) in positive_bounds.items():
            value = values[name]
            if not lower <= value <= upper:
                issues.append(
                    ValidationIssue(
                        field=name,
                        code="OUT_OF_RANGE",
                        message=(
                            f"Field '{name}' must be within [{lower:g}, {upper:g}]."
                        ),
                        value=value,
                    )
                )

        if values["task"] != "heat_equation_1d":
            issues.append(
                ValidationIssue(
                    field="task",
                    code="UNSUPPORTED_TASK",
                    message="Only 'heat_equation_1d' is supported.",
                    value=values["task"],
                )
            )
        if values["boundary"] != "dirichlet_zero":
            issues.append(
                ValidationIssue(
                    field="boundary",
                    code="UNSUPPORTED_BOUNDARY",
                    message="Only zero Dirichlet boundaries are supported.",
                    value=values["boundary"],
                )
            )
        if values["initial_condition"] != "sine_mode_1":
            issues.append(
                ValidationIssue(
                    field="initial_condition",
                    code="UNSUPPORTED_INITIAL_CONDITION",
                    message="Only the first sine mode is supported.",
                    value=values["initial_condition"],
                )
            )
        if values["device"] not in {"cpu", "gpu"}:
            issues.append(
                ValidationIssue(
                    field="device",
                    code="UNSUPPORTED_DEVICE",
                    message="Device must be 'cpu' or 'gpu'.",
                    value=values["device"],
                )
            )

        spatial_points = values["spatial_points"]
        if not 4 <= spatial_points <= 256:
            issues.append(
                ValidationIssue(
                    field="spatial_points",
                    code="OUT_OF_RANGE",
                    message="spatial_points must be within [4, 256].",
                    value=spatial_points,
                )
            )
        elif spatial_points & (spatial_points - 1):
            issues.append(
                ValidationIssue(
                    field="spatial_points",
                    code="NOT_POWER_OF_TWO",
                    message="spatial_points must be a power of two for UnitaryLab.",
                    value=spatial_points,
                )
            )

        if not 1 <= values["time_steps"] <= 100_000:
            issues.append(
                ValidationIssue(
                    field="time_steps",
                    code="OUT_OF_RANGE",
                    message="time_steps must be within [1, 100000].",
                    value=values["time_steps"],
                )
            )
        if not 0 <= values["seed"] <= 2**32 - 1:
            issues.append(
                ValidationIssue(
                    field="seed",
                    code="OUT_OF_RANGE",
                    message="seed must be within the unsigned 32-bit range.",
                    value=values["seed"],
                )
            )

        if not issues:
            fourier_number = (
                values["thermal_diffusivity_m2_s"]
                * values["duration_s"]
                / values["length_m"] ** 2
            )
            if fourier_number > 5.0:
                issues.append(
                    ValidationIssue(
                        field="duration_s",
                        code="FOURIER_NUMBER_OUT_OF_SCOPE",
                        message=(
                            "alpha * duration / length^2 must not exceed 5 "
                            "in the first-round capability boundary."
                        ),
                        value=fourier_number,
                    )
                )

        if issues:
            raise ThermalSpecValidationError(issues)
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def fourier_number(self) -> float:
        return (
            self.thermal_diffusivity_m2_s
            * self.duration_s
            / self.length_m**2
        )
