#!/usr/bin/env python3
"""Build a collision-safe submission ZIP from the clean Git snapshot."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}
FORBIDDEN_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _tracked_files() -> list[Path]:
    raw = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [
        Path(item.decode("utf-8"))
        for item in raw.split(b"\0")
        if item
    ]


def _audit_path(relative: Path) -> None:
    posix = relative.as_posix()
    lowered_parts = {part.lower() for part in relative.parts}
    if posix.startswith("public_quantum_skills/"):
        raise ValueError(f"Reference corpus must not be packaged: {posix}")
    if lowered_parts & FORBIDDEN_PARTS:
        raise ValueError(f"Sensitive filename is not allowed: {posix}")
    if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
        raise ValueError(f"Sensitive file suffix is not allowed: {posix}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    status = _git("status", "--porcelain", "--untracked-files=no")
    if status:
        raise SystemExit(
            "Refusing to package tracked changes. Commit the scoped stage first."
        )
    untracked = [
        line
        for line in _git(
            "ls-files",
            "--others",
            "--exclude-standard",
        ).splitlines()
        if line
    ]
    commit = _git("rev-parse", "--short=12", "HEAD")
    output = args.output or (
        ROOT / "dist" / f"thermal-pde-audit-submission-{commit}.zip"
    )
    output = output.resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing archive: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    tracked = _tracked_files()
    required = {
        Path("ACKNOWLEDGMENTS.md"),
        Path("LICENSE"),
        Path("README.md"),
        Path("docs/scientific_basis.md"),
        Path("skills/thermal-pde-audit/SKILL.md"),
        Path("skills/thermal-pde-audit/agents/openai.yaml"),
    }
    missing = sorted(path.as_posix() for path in required - set(tracked))
    if missing:
        raise SystemExit(f"Required tracked files are missing: {missing}")
    for relative in tracked:
        _audit_path(relative)
        if not (ROOT / relative).is_file():
            raise SystemExit(f"Tracked file is missing on disk: {relative}")

    with tempfile.TemporaryDirectory(prefix="thermal-pde-audit-submission-") as tmp:
        stage = Path(tmp) / "thermal-pde-audit"
        stage.mkdir()
        manifest_lines = []
        for relative in tracked:
            source = ROOT / relative
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            manifest_lines.append(f"{_sha256(target)}  {relative.as_posix()}")
        manifest = stage / "MANIFEST.sha256"
        manifest.write_text(
            "\n".join(manifest_lines) + "\n",
            encoding="utf-8",
        )

        with zipfile.ZipFile(
            output,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    relative = path.relative_to(stage)
                    member = PurePosixPath("thermal-pde-audit") / PurePosixPath(
                        relative.as_posix()
                    )
                    archive.write(path, member.as_posix())

    with zipfile.ZipFile(output) as archive:
        members = archive.namelist()
        expected_count = len(tracked) + 1
        if len(members) != expected_count:
            raise SystemExit(
                f"Archive member mismatch: {len(members)} != {expected_count}"
            )
        if "thermal-pde-audit/MANIFEST.sha256" not in members:
            raise SystemExit("Archive manifest is missing.")
    print(f"archive={output}")
    print(f"commit={commit}")
    print(f"tracked_files={len(tracked)}")
    print(f"archive_members={len(members)}")
    print(f"untracked_files_excluded={len(untracked)}")
    print(f"sha256={_sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
