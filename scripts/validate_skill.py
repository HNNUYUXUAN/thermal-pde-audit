#!/usr/bin/env python3
"""Validate the public Thermal PDE Audit Skill package."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "thermal-pde-audit"
REQUIRED_FILES = {
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
    Path("scripts/run-demo.sh"),
    Path("scripts/run-text-demo.sh"),
    Path("scripts/validate.sh"),
    Path("scripts/algorithm.py"),
    Path("scripts/doctor.py"),
    Path("scripts/validate.py"),
    Path("references/protocol.md"),
    Path("references/runtime.md"),
    Path("references/evidence.md"),
    Path("references/setup.md"),
    Path("references/method.md"),
}


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must begin with YAML frontmatter.")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("SKILL.md frontmatter is not closed.") from error
    values: dict[str, str] = {}
    for line in lines[1:closing]:
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Invalid frontmatter line: {line!r}")
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    missing = sorted(
        path.as_posix()
        for path in REQUIRED_FILES
        if not (SKILL_DIR / path).is_file()
    )
    if missing:
        raise SystemExit(f"Missing Skill files: {missing}")

    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(skill_text)
    if set(metadata) != {"name", "description"}:
        raise SystemExit(
            "SKILL.md frontmatter must contain only name and description."
        )
    if metadata["name"] != "thermal-pde-audit":
        raise SystemExit("Skill name must be thermal-pde-audit.")
    if not metadata["description"]:
        raise SystemExit("Skill description must not be empty.")

    interface = (SKILL_DIR / "agents" / "openai.yaml").read_text(
        encoding="utf-8"
    )
    required_interface_lines = {
        'display_name: "Thermal PDE Audit"',
        'short_description: "Physics-validated quantum heat simulation workflow"',
        '$thermal-pde-audit',
    }
    absent = sorted(
        value for value in required_interface_lines if value not in interface
    )
    if absent:
        raise SystemExit(f"Skill interface metadata is incomplete: {absent}")

    public_paths = [SKILL_DIR / relative for relative in REQUIRED_FILES]
    public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in public_paths
        if path.suffix in {".md", ".yaml", ".sh"}
    ).lower()
    if "todo" in public_text:
        raise SystemExit("Skill package still contains TODO placeholders.")

    print("skill=thermal-pde-audit")
    print(f"required_files={len(REQUIRED_FILES)}")
    print("status=valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
