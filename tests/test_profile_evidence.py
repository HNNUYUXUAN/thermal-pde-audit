import json
from pathlib import Path

from thermal_pde_audit.profile_evidence import (
    validate_quantum_profile_evidence,
)


ROOT = Path(__file__).resolve().parents[1]


def test_current_quantum_profiles_match_saved_scan_evidence() -> None:
    result = validate_quantum_profile_evidence()

    assert result["passed"] is True
    assert result["profile_count"] == 14
    assert result["evidence_case_count"] == 14


def test_profile_without_matching_evidence_is_rejected(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "results"
    evidence_dir.mkdir()
    evidence_path = evidence_dir / "working_region.json"
    evidence_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "ancilla_qubits": 8,
                "auxiliary_range": 16.0,
                "recovery_point": 1,
                "strict_relative_l2_threshold": 0.02,
                "cases": [],
            }
        ),
        encoding="utf-8",
    )
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "scope": {"strict_relative_l2_threshold": 0.02},
                "fixed_quantum_parameters": {
                    "ancilla_qubits": 8,
                    "auxiliary_range": 16.0,
                    "recovery_point": 1,
                },
                "evidence": ["results/working_region.json"],
                "profiles": [
                    {
                        "fourier_number": 0.03,
                        "spatial_points": 32,
                        "quantum_steps": 16,
                        "confirmed_streak": [8, 16],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = validate_quantum_profile_evidence(
        policy_path,
        project_root=tmp_path,
    )

    assert result["passed"] is False
    row_check = next(
        check
        for check in result["checks"]
        if check["name"] == "profile_rows_match_confirmed_evidence"
    )
    assert row_check["passed"] is False
