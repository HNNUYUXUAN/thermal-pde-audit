#!/usr/bin/env python3
"""Framework-free CPU validation for the fixed competition environment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from thermal_pde_audit.classical_solver import (
    FiniteDifferenceStabilityError,
    solve_analytic,
    solve_classical,
)
from thermal_pde_audit.evidence_validation import validate_result_bundle
from thermal_pde_audit.interaction_validation import (
    validate_interaction_records,
)
from thermal_pde_audit.parser import (
    parse_natural_language,
    plan_natural_language,
)
from thermal_pde_audit.physics_audit import audit_field
from thermal_pde_audit.profile_evidence import (
    validate_quantum_profile_evidence,
)
from thermal_pde_audit.schema import (
    ThermalExperimentSpec,
    ThermalSpecValidationError,
)
from thermal_pde_audit.quantum_policy import (
    QuantumProfileError,
    recommend_quantum_profile,
)


def standard_raw() -> dict[str, object]:
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


def main() -> int:
    checks: list[dict[str, object]] = []
    parsed = parse_natural_language(
        "模拟长度10毫米、热扩散率1.2e-5平方米每秒、初始温升100K的"
        "一维热传导，计算0.5秒，使用GPU并生成验证报告"
    )
    checks.append(
        {
            "name": "natural_language_si_and_device",
            "passed": (
                abs(parsed.spec.length_m - 0.01) < 1e-15
                and parsed.spec.device == "gpu"
            ),
        }
    )
    clarification = plan_natural_language(
        "长度10毫米，热扩散率1e-6平方米每秒，请模拟一维热传导"
    )
    checks.append(
        {
            "name": "natural_language_clarification_without_execution",
            "passed": (
                clarification["status"] == "needs_clarification"
                and len(clarification["questions"]) == 2
                and "No solver" in clarification["security_boundary"]
            ),
        }
    )

    spec = ThermalExperimentSpec.from_dict(standard_raw())
    profile = recommend_quantum_profile(spec)
    checks.append(
        {
            "name": "standard_exact_quantum_profile",
            "passed": (
                profile["parameters"]["quantum_steps"] == 32
                and profile["selection_mode"] == "exact_empirical_match"
            ),
        }
    )

    profile_evidence = validate_quantum_profile_evidence()
    checks.append(
        {
            "name": "quantum_profile_evidence_consistency",
            "passed": profile_evidence["passed"],
        }
    )

    unverified_raw = standard_raw()
    length_m = unverified_raw["length_m"]
    diffusivity_m2_s = unverified_raw["thermal_diffusivity_m2_s"]
    assert isinstance(length_m, (int, float))
    assert isinstance(diffusivity_m2_s, (int, float))
    unverified_raw["duration_s"] = (
        0.035
        * float(length_m) ** 2
        / float(diffusivity_m2_s)
    )
    try:
        recommend_quantum_profile(
            ThermalExperimentSpec.from_dict(unverified_raw)
        )
        rejected_unverified = False
    except QuantumProfileError as exc:
        rejected_unverified = (
            exc.code == "UNVERIFIED_QUANTUM_CONFIGURATION"
        )
    checks.append(
        {
            "name": "unverified_quantum_profile_rejected",
            "passed": rejected_unverified,
        }
    )

    fast_bundle = validate_result_bundle(
        Path("results/fast_quantum_validation"),
        require_gpu=True,
        require_supa=True,
        require_custom_supa=True,
        require_error_decomposition=True,
    )
    checks.append(
        {
            "name": "saved_fast_gpu_supa_bundle",
            "passed": fast_bundle["passed"],
        }
    )

    natural_language_bundle = validate_result_bundle(
        Path("results/natural_language_gpu_validation"),
        require_gpu=True,
        require_supa=True,
        require_custom_supa=True,
        require_error_decomposition=True,
        require_natural_language=True,
    )
    checks.append(
        {
            "name": "saved_natural_language_gpu_closed_loop",
            "passed": natural_language_bundle["passed"],
        }
    )

    current_skill_bundle = validate_result_bundle(
        Path("results/skill_entry_gpu_validation"),
        require_gpu=True,
        require_supa=True,
        require_custom_supa=True,
        require_error_decomposition=True,
        require_natural_language=True,
    )
    checks.append(
        {
            "name": "current_skill_entry_gpu_closed_loop",
            "passed": current_skill_bundle["passed"],
        }
    )

    origin_dir = Path("results/origin_data")
    try:
        origin_manifest = json.loads(
            (origin_dir / "manifest.json").read_text(encoding="utf-8")
        )
        origin_hashes_match = all(
            (
                (origin_dir / table["path"]).is_file()
                and hashlib.sha256(
                    (origin_dir / table["path"]).read_bytes()
                ).hexdigest()
                == table["sha256"]
            )
            for table in origin_manifest["tables"]
        )
        origin_data_passed = (
            origin_manifest["status"] == "success"
            and len(origin_manifest["tables"]) == 10
            and sum(
                int(table["data_rows"])
                for table in origin_manifest["tables"]
            )
            == 189
            and origin_hashes_match
        )
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        origin_data_passed = False
    checks.append(
        {
            "name": "origin_plot_data_manifest_and_hashes",
            "passed": origin_data_passed,
        }
    )

    interaction_records = validate_interaction_records(
        Path("results/interactions")
    )
    checks.append(
        {
            "name": "saved_interaction_records",
            "passed": interaction_records["passed"],
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
    checks.append({"name": "classical_physics_audit", "passed": audit["passed"]})

    unstable = standard_raw()
    unstable["time_steps"] = 100
    try:
        solve_classical(ThermalExperimentSpec.from_dict(unstable))
        rejected_unstable = False
    except FiniteDifferenceStabilityError as exc:
        rejected_unstable = (
            exc.stability_ratio > 0.5
            and exc.recommended_min_time_steps > 100
        )
    checks.append(
        {
            "name": "unstable_finite_difference_rejected",
            "passed": rejected_unstable,
        }
    )

    invalid = standard_raw()
    invalid["thermal_diffusivity_m2_s"] = -1e-5
    try:
        ThermalExperimentSpec.from_dict(invalid)
        rejected_invalid = False
    except ThermalSpecValidationError:
        rejected_invalid = True
    checks.append(
        {
            "name": "negative_diffusivity_rejected",
            "passed": rejected_invalid,
        }
    )
    report = {
        "task": "framework_free_cpu_validation",
        "checks": checks,
        "passed": all(bool(check["passed"]) for check in checks),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
