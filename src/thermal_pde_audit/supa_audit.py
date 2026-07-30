"""Biren SUPA tensor reductions for independent error-metric verification."""

from __future__ import annotations

import importlib.metadata
import time
from typing import Any

import numpy as np

from .physics_audit import error_metrics


SUPA_REDUCTION_TOLERANCE = 1e-8
SUPA_END_TO_END_TOLERANCE = 1e-5


def _metric_consistency(
    supa_metrics: dict[str, float],
    cpu_metrics: dict[str, float],
    *,
    tolerance: float = SUPA_REDUCTION_TOLERANCE,
) -> dict[str, Any]:
    differences = {
        name: abs(float(supa_metrics[name]) - float(cpu_metrics[name]))
        for name in cpu_metrics
    }
    return {
        "passed": all(value <= tolerance for value in differences.values()),
        "absolute_differences": differences,
        "threshold": tolerance,
    }


def audit_error_metrics_on_supa(
    actual: list[float] | np.ndarray,
    reference: list[float] | np.ndarray,
) -> dict[str, Any]:
    """Compute three error metrics on ``supa:0`` and compare with NumPy."""

    actual_array = np.asarray(actual, dtype=np.float64)
    reference_array = np.asarray(reference, dtype=np.float64)
    base: dict[str, Any] = {
        "backend": "torch_supa_tensor_reduction",
        "device": "supa:0",
        "dtype": "float64",
        "status": "failed",
        "operation": (
            "temperature delta, maximum absolute error, RMSE, and relative L2"
        ),
        "metrics": {},
        "cpu_reference_metrics": {},
        "cpu_roundtrip_metrics": {},
        "consistency": {},
        "runtime_s": {},
        "device_info": {},
        "warnings": [
            (
                "This stage uses torch.supa tensor reduction for the error "
                "metrics; the project-owned .su kernel is reported separately."
            ),
            (
                "The reported runtime includes tensor transfer, device "
                "initialization, and reduction for the 32-value field."
            ),
        ],
    }
    if (
        actual_array.shape != reference_array.shape
        or actual_array.size == 0
        or not np.all(np.isfinite(actual_array))
        or not np.all(np.isfinite(reference_array))
    ):
        base["error"] = {
            "type": "ValueError",
            "message": (
                "SUPA audit requires aligned, non-empty, finite input arrays."
            ),
            "actual_shape": list(actual_array.shape),
            "reference_shape": list(reference_array.shape),
        }
        return base

    try:
        import torch
        import torch_br  # noqa: F401

        device_count = int(torch.supa.device_count())
        base["device_info"] = {
            "torch": torch.__version__,
            "torch_br": importlib.metadata.version("torch_br"),
            "supa_device_count": device_count,
        }
        if device_count < 1:
            raise RuntimeError("No SUPA device is visible.")

        total_started = time.perf_counter()
        transfer_started = time.perf_counter()
        actual_supa = torch.tensor(
            actual_array,
            dtype=torch.float64,
            device="supa:0",
        )
        reference_supa = torch.tensor(
            reference_array,
            dtype=torch.float64,
            device="supa:0",
        )
        torch.supa.synchronize()
        actual_roundtrip = actual_supa.cpu().numpy()
        reference_roundtrip = reference_supa.cpu().numpy()
        transfer_s = time.perf_counter() - transfer_started

        compute_started = time.perf_counter()
        delta = actual_supa - reference_supa
        max_abs = torch.max(torch.abs(delta))
        rmse = torch.sqrt(torch.mean(delta * delta))
        relative_l2 = (
            torch.linalg.vector_norm(delta)
            / torch.linalg.vector_norm(reference_supa)
        )
        torch.supa.synchronize()
        compute_s = time.perf_counter() - compute_started

        retrieval_started = time.perf_counter()
        supa_metrics = {
            "max_abs_error": float(max_abs.cpu().item()),
            "rmse": float(rmse.cpu().item()),
            "relative_l2_error": float(relative_l2.cpu().item()),
        }
        retrieval_s = time.perf_counter() - retrieval_started
        source_cpu_metrics = error_metrics(actual_array, reference_array)
        roundtrip_cpu_metrics = error_metrics(
            actual_roundtrip,
            reference_roundtrip,
        )
        reduction_consistency = _metric_consistency(
            supa_metrics,
            roundtrip_cpu_metrics,
            tolerance=SUPA_REDUCTION_TOLERANCE,
        )
        end_to_end_consistency = _metric_consistency(
            supa_metrics,
            source_cpu_metrics,
            tolerance=SUPA_END_TO_END_TOLERANCE,
        )
        consistency = {
            "passed": (
                reduction_consistency["passed"]
                and end_to_end_consistency["passed"]
            ),
            "reduction_vs_roundtrip_cpu": reduction_consistency,
            "end_to_end_vs_source_cpu": end_to_end_consistency,
            "host_device_roundtrip_max_abs_k": {
                "actual": float(
                    np.max(np.abs(actual_roundtrip - actual_array))
                ),
                "reference": float(
                    np.max(np.abs(reference_roundtrip - reference_array))
                ),
            },
        }
        roundtrip_max = max(
            consistency["host_device_roundtrip_max_abs_k"].values()
        )
        if roundtrip_max > 0:
            base["warnings"].append(
                "The nominal float64 host/device round trip changed field "
                f"values by at most {roundtrip_max:.6g} K; reduction accuracy "
                "is therefore checked separately from transfer quantization."
            )
        base.update(
            {
                "status": "success" if consistency["passed"] else "failed",
                "metrics": supa_metrics,
                "cpu_reference_metrics": source_cpu_metrics,
                "cpu_roundtrip_metrics": roundtrip_cpu_metrics,
                "consistency": consistency,
                "runtime_s": {
                    "host_to_device_and_sync": transfer_s,
                    "device_compute_and_sync": compute_s,
                    "device_to_host": retrieval_s,
                    "total": time.perf_counter() - total_started,
                },
            }
        )
        if not consistency["passed"]:
            base["error"] = {
                "type": "SupaMetricMismatch",
                "message": (
                    "SUPA reductions or end-to-end metrics exceeded their "
                    "separate tolerances."
                ),
            }
    except Exception as exc:
        base["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
    return base
