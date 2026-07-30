"""Machine-check the saved Agent/Skill interaction transcripts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SECTION_ALIASES = {
    "user_input": ("用户输入",),
    "task_parse": ("任务解析",),
    "parameter_protocol": ("参数协议", "参数协议与决策"),
    "command": ("调用命令",),
    "evidence": ("真实日志", "真实结果"),
    "generated_files": ("生成文件",),
    "warning": ("复核说明", "警告"),
    "final_answer": ("最终回答",),
}
REPOSITORY_PATH = re.compile(
    r"(?:results|examples|scripts|docs|src)/"
    r"[A-Za-z0-9_.*/-]+"
)


def _sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip()] = text[match.end() : end].strip()
    return sections


def _section_value(
    sections: dict[str, str],
    aliases: tuple[str, ...],
) -> str:
    for alias in aliases:
        if alias in sections:
            return sections[alias]
    return ""


def _referenced_paths(text: str) -> list[str]:
    return sorted(
        {
            match.group(0).rstrip(".,:;")
            for match in REPOSITORY_PATH.finditer(text)
            if "*" not in match.group(0)
        }
    )


def validate_interaction_records(
    interactions_dir: Path,
    *,
    project_root: Path | None = None,
    minimum_count: int = 5,
) -> dict[str, Any]:
    """Validate distinct transcripts and the evidence paths they cite."""

    interactions_dir = Path(interactions_dir)
    root = (
        Path(project_root)
        if project_root is not None
        else interactions_dir.resolve().parents[1]
    )
    transcripts = sorted(interactions_dir.glob("*/transcript.md"))
    records: list[dict[str, Any]] = []
    user_inputs: list[str] = []
    commands: list[str] = []
    for transcript in transcripts:
        try:
            text = transcript.read_text(encoding="utf-8")
        except OSError as exc:
            records.append(
                {
                    "path": str(transcript),
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        sections = _sections(text)
        missing_sections = [
            key
            for key, aliases in SECTION_ALIASES.items()
            if not _section_value(sections, aliases)
        ]
        user_input = _section_value(sections, SECTION_ALIASES["user_input"])
        command = _section_value(sections, SECTION_ALIASES["command"])
        user_inputs.append(re.sub(r"\s+", " ", user_input).strip())
        commands.append(re.sub(r"\s+", " ", command).strip())
        evidence_text = "\n".join(
            [
                _section_value(sections, SECTION_ALIASES["evidence"]),
                _section_value(sections, SECTION_ALIASES["generated_files"]),
            ]
        )
        paths = _referenced_paths(evidence_text)
        missing_paths = [
            path
            for path in paths
            if not (root / Path(path.rstrip("/"))).exists()
        ]
        command_is_controlled = (
            "```" in command
            and (
                "scripts/" in command
                or "python3 -m thermal_pde_audit.cli" in command
            )
        )
        records.append(
            {
                "path": str(transcript.resolve().relative_to(root.resolve())),
                "passed": (
                    not missing_sections
                    and command_is_controlled
                    and bool(paths)
                    and not missing_paths
                ),
                "missing_sections": missing_sections,
                "command_is_controlled": command_is_controlled,
                "referenced_paths": paths,
                "missing_paths": missing_paths,
            }
        )

    unique_inputs = len(set(user_inputs)) == len(user_inputs)
    unique_commands = len(set(commands)) == len(commands)
    checks = [
        {
            "name": "minimum_interaction_count",
            "passed": len(transcripts) >= minimum_count,
            "value": len(transcripts),
            "expected": f">={minimum_count}",
        },
        {
            "name": "interaction_record_structure_and_evidence",
            "passed": bool(records) and all(record["passed"] for record in records),
            "value": records,
            "expected": "all records have required sections and existing evidence",
        },
        {
            "name": "distinct_user_inputs",
            "passed": unique_inputs,
            "value": len(set(user_inputs)),
            "expected": len(user_inputs),
        },
        {
            "name": "distinct_commands",
            "passed": unique_commands,
            "value": len(set(commands)),
            "expected": len(commands),
        },
    ]
    return {
        "task": "validate_interaction_records",
        "interactions_dir": str(interactions_dir),
        "passed": all(check["passed"] for check in checks),
        "record_count": len(transcripts),
        "checks": checks,
    }
