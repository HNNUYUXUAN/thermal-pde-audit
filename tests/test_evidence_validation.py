import json
import shutil
from pathlib import Path

from thermal_pde_audit.evidence_validation import validate_result_bundle


ROOT = Path(__file__).resolve().parents[1]


def test_fast_result_bundle_has_all_device_evidence() -> None:
    result = validate_result_bundle(
        ROOT / "results" / "fast_quantum_validation",
        require_gpu=True,
        require_supa=True,
        require_custom_supa=True,
        require_error_decomposition=True,
    )

    assert result["passed"] is True


def test_missing_error_decomposition_is_rejected_when_required(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "results" / "fast_quantum_validation", bundle)
    result_path = bundle / "result.json"
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    saved["error_decomposition"] = {"status": "not_requested"}
    result_path.write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    validation = validate_result_bundle(
        bundle,
        require_error_decomposition=True,
    )
    decomposition_check = next(
        check
        for check in validation["checks"]
        if check["name"]
        == "schrodingerization_error_decomposition_evidence"
    )

    assert validation["passed"] is False
    assert decomposition_check["passed"] is False


def test_natural_language_provenance_must_match_saved_input(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "results" / "fast_quantum_validation", bundle)
    result_path = bundle / "result.json"
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    saved["input_provenance"] = {
        "mode": "natural_language",
        "parser": "deterministic_whitelist_v1",
        "status": "parsed",
        "source_text": "受控自然语言测试",
        "spec": saved["input"],
        "defaults_applied": {},
        "execution_plan": {
            "compare_cpu_gpu": True,
            "validated_profile": True,
            "supa_audit": True,
            "custom_supa_audit": True,
            "error_decomposition": True,
            "report_level": "full",
            "sources": {
                "compare_cpu_gpu": "test:controlled",
                "validated_profile": (
                    "safe_default:exact_empirical_profile"
                ),
                "supa_audit": "test:controlled",
                "custom_supa_audit": "test:controlled",
                "error_decomposition": "test:controlled",
                "report_level": "test:controlled",
            },
        },
        "security_boundary": (
            "Natural language was mapped to whitelisted fields only; "
            "no shell or Python code was generated or executed."
        ),
    }
    result_path.write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    validation = validate_result_bundle(
        bundle,
        require_natural_language=True,
    )

    assert validation["passed"] is True

    report_path = bundle / "report.md"
    original_report = report_path.read_text(encoding="utf-8")
    report_path.write_text(
        f"{original_report}\n{saved['input_provenance']['source_text']}\n",
        encoding="utf-8",
    )
    unsafe_reproduction = validate_result_bundle(
        bundle,
        require_natural_language=True,
    )
    unsafe_check = next(
        check
        for check in unsafe_reproduction["checks"]
        if check["name"] == "natural_language_closed_loop_evidence"
    )
    assert unsafe_reproduction["passed"] is False
    assert unsafe_check["value"][
        "source_text_absent_from_reproduction"
    ] is False
    report_path.write_text(original_report, encoding="utf-8")

    saved["input_provenance"]["spec"]["duration_s"] = 99
    result_path.write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rejected = validate_result_bundle(
        bundle,
        require_natural_language=True,
    )
    provenance_check = next(
        check
        for check in rejected["checks"]
        if check["name"] == "natural_language_closed_loop_evidence"
    )

    assert rejected["passed"] is False
    assert provenance_check["passed"] is False


def test_missing_result_bundle_is_structurally_rejected(
    tmp_path: Path,
) -> None:
    result = validate_result_bundle(tmp_path)

    assert result["passed"] is False
    assert result["checks"][0]["name"] == "required_artifacts"


def test_gpu_route_conflict_is_rejected_even_with_gpu_backend(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "results" / "fast_quantum_validation", bundle)
    result_path = bundle / "result.json"
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    saved["quantum"]["device_route_calls"][0]["device"] = "cpu"
    saved["quantum"]["device_route_calls"][0][
        "device_matches_requested"
    ] = False
    saved["quantum"]["device_route_compatibility"]["conflict_count"] = 1
    saved["quantum"]["device_route_compatibility"][
        "all_devices_match_requested"
    ] = False
    result_path.write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    validation = validate_result_bundle(bundle, require_gpu=True)
    route_check = next(
        check
        for check in validation["checks"]
        if check["name"] == "gpu_route_evidence"
    )

    assert validation["passed"] is False
    assert route_check["passed"] is False
