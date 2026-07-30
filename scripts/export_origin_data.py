#!/usr/bin/env python3
"""Export remote result evidence into Origin-friendly CSV files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from thermal_pde_audit.origin_export import export_origin_data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result-dir",
        type=Path,
        default=Path("results/skill_entry_gpu_validation"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/origin_data"),
    )
    parser.add_argument(
        "--command-log",
        type=Path,
        default=Path("results/skill_entry_gpu_validation/run.log"),
    )
    args = parser.parse_args()
    manifest = export_origin_data(
        args.result_dir,
        args.output_dir,
        working_region_paths=[
            Path("results/benchmarks/working_region_fo/working_region.json"),
            Path("results/benchmarks/working_region_grid/working_region.json"),
            Path(
                "results/benchmarks/working_region_gapfill/"
                "working_region.json"
            ),
        ],
        command_log=args.command_log,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
