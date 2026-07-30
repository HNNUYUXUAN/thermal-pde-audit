"""Cross-check validated quantum profiles against saved empirical scans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .quantum_policy import PROFILE_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _check(
    name: str,
    passed: bool,
    value: Any,
    expected: Any,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "value": value,
        "expected": expected,
    }


def _profile_key(row: dict[str, Any]) -> tuple[float, int]:
    return float(row["fourier_number"]), int(row["spatial_points"])


def validate_quantum_profile_evidence(
    policy_path: Path = PROFILE_PATH,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Validate exact profiles, scan settings, and confirmed passing streaks."""

    policy_path = Path(policy_path)
    project_root = Path(project_root).resolve()
    checks: list[dict[str, Any]] = []
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "task": "validate_quantum_profile_evidence",
            "policy": str(policy_path),
            "passed": False,
            "checks": [
                _check(
                    "policy_json",
                    False,
                    f"{type(exc).__name__}: {exc}",
                    "valid UTF-8 JSON",
                )
            ],
        }

    profiles = policy.get("profiles", [])
    policy_keys = [_profile_key(row) for row in profiles]
    checks.append(
        _check(
            "unique_policy_profiles",
            len(policy_keys) == len(set(policy_keys)),
            {"profiles": len(policy_keys), "unique": len(set(policy_keys))},
            {"profiles_equal_unique": True},
        )
    )

    evidence_paths = [
        Path(item)
        for item in policy.get("evidence", [])
        if str(item).endswith(".json")
    ]
    checks.append(
        _check(
            "json_evidence_declared",
            bool(evidence_paths),
            [path.as_posix() for path in evidence_paths],
            "at least one JSON working-region report",
        )
    )
    evidence_cases: dict[tuple[float, int], list[dict[str, Any]]] = {}
    evidence_errors: list[dict[str, Any]] = []
    fixed = policy.get("fixed_quantum_parameters", {})
    scope = policy.get("scope", {})

    for relative in evidence_paths:
        resolved = (project_root / relative).resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError:
            evidence_errors.append(
                {
                    "path": relative.as_posix(),
                    "error": "path escapes project root",
                }
            )
            continue
        try:
            report = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            evidence_errors.append(
                {
                    "path": relative.as_posix(),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        expected_settings = {
            "ancilla_qubits": fixed.get("ancilla_qubits"),
            "auxiliary_range": fixed.get("auxiliary_range"),
            "recovery_point": fixed.get("recovery_point"),
            "strict_relative_l2_threshold": scope.get(
                "strict_relative_l2_threshold"
            ),
        }
        observed_settings = {
            name: report.get(name) for name in expected_settings
        }
        if report.get("status") != "completed":
            evidence_errors.append(
                {
                    "path": relative.as_posix(),
                    "error": f"unexpected report status: {report.get('status')}",
                }
            )
        if observed_settings != expected_settings:
            evidence_errors.append(
                {
                    "path": relative.as_posix(),
                    "error": "scan settings differ from policy",
                    "observed": observed_settings,
                    "expected": expected_settings,
                }
            )
        for case in report.get("cases", []):
            if case.get("confirmed_quantum_steps") is None:
                continue
            key = _profile_key(case)
            evidence_cases.setdefault(key, []).append(
                {
                    "path": relative.as_posix(),
                    "case": case,
                }
            )

    checks.append(
        _check(
            "evidence_files_and_settings",
            not evidence_errors,
            evidence_errors,
            [],
        )
    )

    row_errors: list[dict[str, Any]] = []
    for profile in profiles:
        key = _profile_key(profile)
        matches = evidence_cases.get(key, [])
        if not matches:
            row_errors.append(
                {
                    "profile": {
                        "fourier_number": key[0],
                        "spatial_points": key[1],
                    },
                    "error": "no matching confirmed evidence case",
                }
            )
            continue
        for match in matches:
            case = match["case"]
            confirmed = int(case["confirmed_quantum_steps"])
            streak = [int(value) for value in case.get("confirmed_streak", [])]
            passing_steps = {
                int(run["requested_nt"])
                for run in case.get("runs", [])
                if run.get("strict_accuracy_passed") is True
                and run.get("physics_audit_passed") is True
            }
            expected_streak = [
                int(value) for value in profile["confirmed_streak"]
            ]
            if (
                confirmed != int(profile["quantum_steps"])
                or streak != expected_streak
                or confirmed != expected_streak[-1]
                or not set(expected_streak).issubset(passing_steps)
            ):
                row_errors.append(
                    {
                        "profile": {
                            "fourier_number": key[0],
                            "spatial_points": key[1],
                        },
                        "evidence": match["path"],
                        "error": "confirmed steps or passing streak mismatch",
                        "policy_quantum_steps": profile["quantum_steps"],
                        "policy_streak": expected_streak,
                        "evidence_quantum_steps": confirmed,
                        "evidence_streak": streak,
                        "passing_steps": sorted(passing_steps),
                    }
                )

    evidence_keys = set(evidence_cases)
    checks.extend(
        [
            _check(
                "profile_rows_match_confirmed_evidence",
                not row_errors,
                row_errors,
                [],
            ),
            _check(
                "policy_and_evidence_key_sets",
                set(policy_keys) == evidence_keys,
                {
                    "policy_only": sorted(set(policy_keys) - evidence_keys),
                    "evidence_only": sorted(evidence_keys - set(policy_keys)),
                },
                {"policy_only": [], "evidence_only": []},
            ),
        ]
    )
    return {
        "task": "validate_quantum_profile_evidence",
        "policy": str(policy_path),
        "passed": all(check["passed"] for check in checks),
        "profile_count": len(profiles),
        "evidence_case_count": len(evidence_cases),
        "checks": checks,
    }
