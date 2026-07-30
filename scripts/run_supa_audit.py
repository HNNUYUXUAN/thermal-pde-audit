#!/usr/bin/env python3
"""Recompute a saved quantum field's error metrics on Biren SUPA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from thermal_pde_audit.classical_solver import analytic_field_at
from thermal_pde_audit.schema import ThermalExperimentSpec
from thermal_pde_audit.supa_audit import audit_error_metrics_on_supa


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    saved = json.loads(args.result.read_text(encoding="utf-8"))
    quantum = saved.get("quantum", {})
    if quantum.get("status") != "success":
        raise SystemExit("Saved result does not contain a successful quantum field.")
    spec = ThermalExperimentSpec.from_dict(saved["input"])
    reference = analytic_field_at(
        spec,
        quantum["spatial_grid_m"],
    )
    result = audit_error_metrics_on_supa(
        quantum["state_or_field"],
        reference,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
