from __future__ import annotations

import csv
import json
from pathlib import Path

from thermal_pde_audit.origin_export import export_origin_data


ROOT = Path(__file__).resolve().parents[1]


def test_origin_export_produces_flat_numeric_tables(
    tmp_path: Path,
) -> None:
    output = tmp_path / "origin"
    manifest = export_origin_data(
        ROOT / "results" / "skill_entry_gpu_validation",
        output,
        working_region_paths=[
            ROOT
            / "results"
            / "benchmarks"
            / "working_region_fo"
            / "working_region.json",
            ROOT
            / "results"
            / "benchmarks"
            / "working_region_grid"
            / "working_region.json",
            ROOT
            / "results"
            / "benchmarks"
            / "working_region_gapfill"
            / "working_region.json",
        ],
        command_log=ROOT / "results" / "skill_entry_gpu_validation" / "run.log",
    )

    assert manifest["status"] == "success"
    assert {table["path"] for table in manifest["tables"]} == {
        "temperature_profile.csv",
        "error_decomposition.csv",
        "runtime_comparison.csv",
        "audit_checks.csv",
        "working_region_confirmed.csv",
        "working_region_runs.csv",
        "working_region_unique.csv",
        "fourier_scan_plot.csv",
        "grid_scan_plot.csv",
        "metadata.csv",
    }
    with (output / "temperature_profile.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        temperature_rows = list(csv.DictReader(stream))
    assert len(temperature_rows) == 34
    assert temperature_rows[0]["is_protocol_boundary"] == "1"
    assert float(temperature_rows[0]["quantum_gpu_k"]) == 0.0
    assert temperature_rows[-1]["is_protocol_boundary"] == "1"
    with (output / "runtime_comparison.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        runtime_rows = list(csv.DictReader(stream))
    assert runtime_rows[1]["notes"] == "small-field GPU reference run"
    assert float(runtime_rows[-1]["runtime_s"]) == 35.0
    with (output / "metadata.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        metadata_rows = list(csv.DictReader(stream))
    assert all("\\" not in row["source_file"] for row in metadata_rows)
    with (output / "working_region_confirmed.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        confirmed_rows = list(csv.DictReader(stream))
    assert len(confirmed_rows) == 15
    assert sum(int(row["resolved_1_0"]) for row in confirmed_rows) == 15
    assert (
        sum(int(row["duplicate_fo_n_key_1_0"]) for row in confirmed_rows)
        == 2
    )
    with (output / "working_region_unique.csv").open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        unique_rows = list(csv.DictReader(stream))
    assert len(unique_rows) == 14
    saved_manifest = json.loads(
        (output / "manifest.json").read_text(encoding="utf-8")
    )
    assert len(saved_manifest["source_files"]) == 6
