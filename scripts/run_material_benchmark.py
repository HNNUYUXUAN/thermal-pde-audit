#!/usr/bin/env python3
"""Run the two-diffusivity example and save a compact benchmark."""

from __future__ import annotations

import json
import time
from pathlib import Path

from thermal_pde_audit.benchmark import run_experiment
from thermal_pde_audit.schema import ThermalExperimentSpec


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    source = json.loads(
        (ROOT / "examples" / "compare_materials.json").read_text(
            encoding="utf-8"
        )
    )
    summaries = []
    for item in source["cases"]:
        raw = {
            "task": "heat_equation_1d",
            **source["shared"],
            "thermal_diffusivity_m2_s": item[
                "thermal_diffusivity_m2_s"
            ],
        }
        spec = ThermalExperimentSpec.from_dict(raw)
        output_dir = ROOT / "results" / "benchmarks" / item["label"]
        started = time.perf_counter()
        result = run_experiment(
            spec,
            output_dir,
            user_task=(
                f"Compare material case {item['label']} with diffusivity "
                f"{item['thermal_diffusivity_m2_s']} m^2/s"
            ),
            compare_cpu_gpu=False,
            quantum_steps=1,
            ancilla_qubits=5,
            reproduce_command="bash scripts/run_benchmark.sh",
        )
        summaries.append(
            {
                "label": item["label"],
                "thermal_diffusivity_m2_s": spec.thermal_diffusivity_m2_s,
                "status": result["status"],
                "wall_runtime_s": time.perf_counter() - started,
                "quantum_runtime_s": result["quantum"]["runtime_s"],
                "final_peak_k": max(result["quantum"]["state_or_field"])
                if result["quantum"]["state_or_field"]
                else None,
            }
        )
    report = {
        "task": source["task"],
        "cases": summaries,
        "summary": (
            "This benchmark reports measured runtimes and thermal-response "
            "metrics for two diffusivity settings under the same protocol."
        ),
    }
    path = ROOT / "results" / "benchmarks" / "material_comparison.json"
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "success" for item in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
