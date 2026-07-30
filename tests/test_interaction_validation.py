from __future__ import annotations

from pathlib import Path

from thermal_pde_audit.interaction_validation import (
    validate_interaction_records,
)


ROOT = Path(__file__).resolve().parents[1]


def test_saved_interactions_are_distinct_and_traceable() -> None:
    validation = validate_interaction_records(
        ROOT / "results" / "interactions",
        project_root=ROOT,
    )

    assert validation["passed"] is True
    assert validation["record_count"] >= 5


def test_missing_interaction_sections_are_rejected(tmp_path: Path) -> None:
    interactions = tmp_path / "results" / "interactions"
    transcript_dir = interactions / "01_incomplete"
    transcript_dir.mkdir(parents=True)
    (transcript_dir / "transcript.md").write_text(
        "# 不完整交互\n\n## 用户输入\n\n测试\n",
        encoding="utf-8",
    )

    validation = validate_interaction_records(
        interactions,
        project_root=tmp_path,
        minimum_count=1,
    )
    record_check = next(
        check
        for check in validation["checks"]
        if check["name"] == "interaction_record_structure_and_evidence"
    )

    assert validation["passed"] is False
    assert record_check["passed"] is False
