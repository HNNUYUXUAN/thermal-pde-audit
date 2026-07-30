#!/usr/bin/env python3
"""Run a minimal 1D heat Trotter case on CPU and Biren GPU."""

from __future__ import annotations

import importlib.metadata
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch_br  # noqa: F401 - registers torch.supa
from unitarylab_algorithms.schrodingerization.equation_heat.algorithm import (
    HeatEquationAlgorithm,
)

from probe_heat_params import build_params


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = PROJECT_ROOT / "results" / "heat_minimal_result.json"


def run_cpu(params: dict[str, Any]) -> tuple[dict[str, Any], float]:
    output_dir = PROJECT_ROOT / "results" / "remote_heat_cpu"
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    result = HeatEquationAlgorithm().run(
        params=params,
        algo_dir=str(output_dir),
        backend="torch",
        device="cpu",
    )
    return result, time.perf_counter() - started


def run_gpu_with_device_shim(
    params: dict[str, Any],
) -> tuple[dict[str, Any], float, list[dict[str, Any]]]:
    """Route the 1D algorithm's omitted device argument to schro_trotter."""

    from unitarylab.library.equation import schrodingerization as schro_module

    original = schro_module.schro_trotter
    routed_calls: list[dict[str, Any]] = []

    def routed(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("device", "gpu")
        routed_calls.append(
            {
                "device": kwargs["device"],
                "Nt": kwargs.get("Nt"),
                "na": kwargs.get("na"),
                "R": kwargs.get("R"),
                "order": kwargs.get("order"),
                "point": kwargs.get("point"),
            }
        )
        return original(*args, **kwargs)

    output_dir = PROJECT_ROOT / "results" / "remote_heat_gpu"
    output_dir.mkdir(parents=True, exist_ok=True)
    schro_module.schro_trotter = routed
    try:
        started = time.perf_counter()
        result = HeatEquationAlgorithm().run(
            params=params,
            algo_dir=str(output_dir),
            backend="torch",
            device="gpu",
        )
        runtime = time.perf_counter() - started
    finally:
        schro_module.schro_trotter = original
    return result, runtime, routed_calls


def main() -> int:
    params = build_params()
    cpu, cpu_runtime = run_cpu(params)
    gpu, gpu_runtime, routed_calls = run_gpu_with_device_shim(params)

    cpu_u = np.asarray(cpu.get("u", []), dtype=float)
    gpu_u = np.asarray(gpu.get("u", []), dtype=float)
    same_shape = cpu_u.shape == gpu_u.shape and cpu_u.size > 0
    max_abs_diff = (
        float(np.max(np.abs(cpu_u - gpu_u))) if same_shape else None
    )

    report = {
        "task": "minimal_heat_equation_1d_trotter",
        "algorithm": (
            "unitarylab_algorithms.schrodingerization."
            "equation_heat.algorithm.HeatEquationAlgorithm"
        ),
        "compatibility_shim": (
            "Temporarily forwards the omitted 1D algorithm device argument "
            "to unitarylab.library.equation.schrodingerization.schro_trotter."
        ),
        "versions": {
            "torch": torch.__version__,
            "torch_br": importlib.metadata.version("torch_br"),
            "unitarylab": importlib.metadata.version("unitarylab"),
            "unitarylab_algorithms": importlib.metadata.version(
                "unitarylab_algorithms"
            ),
        },
        "supa_device_count": torch.supa.device_count(),
        "cpu": cpu,
        "gpu": gpu,
        "cpu_runtime_s": cpu_runtime,
        "gpu_runtime_s": gpu_runtime,
        "gpu_routed_calls": routed_calls,
        "raw_result_keys": {
            "cpu": sorted(cpu),
            "gpu": sorted(gpu),
        },
        "cpu_gpu_max_abs_diff": max_abs_diff,
        "ok": bool(
            cpu.get("status") == "ok"
            and gpu.get("status") == "ok"
            and routed_calls
            and all(call["device"] == "gpu" for call in routed_calls)
            and max_abs_diff is not None
            and max_abs_diff <= 1e-5
        ),
    }
    RESULT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
