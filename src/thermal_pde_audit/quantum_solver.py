"""UnitaryLab 1D heat-equation adapter with explicit device evidence."""

from __future__ import annotations

import copy
import importlib
import importlib.metadata
import json
import math
import shutil
import time
from pathlib import Path
from typing import Any

from .schema import ThermalExperimentSpec
from .unitarylab_compat import route_schro_trotter_device


ALGORITHM_PATH = (
    "unitarylab_algorithms.schrodingerization."
    "equation_heat.algorithm.HeatEquationAlgorithm"
)


def _device_route_is_verified(
    routed_calls: list[dict[str, Any]],
    compatibility: dict[str, Any],
    requested_device: str,
) -> bool:
    """Return true only for a restored route with no device conflicts."""

    return (
        bool(routed_calls)
        and compatibility.get("requested_device") == requested_device
        and compatibility.get("all_devices_match_requested") is True
        and compatibility.get("conflict_count") == 0
        and compatibility.get("restored") is True
        and all(
            call.get("device") == requested_device
            and call.get("requested_device") == requested_device
            and call.get("device_matches_requested") is True
            for call in routed_calls
        )
    )


def _prepare_raw_directory(output_dir: Path, requested_device: str) -> Path:
    """Create an empty, bounded directory for one upstream backend run."""

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / f"unitarylab_{requested_device}"
    if candidate.is_symlink():
        raise ValueError(
            f"Refusing to replace a symlinked artifact directory: {candidate}"
        )
    raw_dir = candidate.resolve()
    if (
        raw_dir.parent != output_dir
        or raw_dir.name not in {"unitarylab_cpu", "unitarylab_gpu"}
    ):
        raise ValueError(f"Unsafe UnitaryLab artifact directory: {raw_dir}")
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir()
    return raw_dir


def _close_algorithm_log_handlers(algorithm: Any) -> dict[str, Any]:
    """Flush, close, and detach handlers created by the upstream algorithm."""

    logger = getattr(algorithm, "logger", None)
    handlers = list(getattr(logger, "handlers", []))
    errors: list[str] = []
    for handler in handlers:
        try:
            handler.flush()
            handler.close()
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    if logger is not None:
        logger.handlers.clear()
    return {
        "observed": len(handlers),
        "closed": len(handlers) - len(errors),
        "errors": errors,
    }


def _close_algorithm_figures() -> dict[str, int]:
    """Close figures retained by upstream plotting helpers after saving."""

    try:
        import matplotlib.pyplot as plt

        observed = len(plt.get_fignums())
        plt.close("all")
        return {"observed": observed, "closed": observed}
    except Exception:
        return {"observed": 0, "closed": 0}


def _set_named_value(items: list[dict[str, Any]], name: str, value: str) -> None:
    for item in items:
        if item.get("name") == name:
            item["value"] = value
            return
    raise KeyError(f"UnitaryLab setup field not found: {name}")


def _build_params(
    spec: ThermalExperimentSpec,
    quantum_steps: int,
    ancilla_qubits: int,
    auxiliary_range: float,
    recovery_point: int,
) -> dict[str, Any]:
    algorithm_module = importlib.import_module(
        "unitarylab_algorithms.schrodingerization.equation_heat.algorithm"
    )
    module_file = getattr(algorithm_module, "__file__", None)
    if not module_file:
        raise ImportError(
            "Installed heat algorithm module does not expose a file path."
        )
    setup_path = Path(module_file).resolve().with_name("setup.json")
    data = copy.deepcopy(json.loads(setup_path.read_text(encoding="utf-8")))
    config = data["params"][0]
    spatial_qubits = int(math.log2(spec.spatial_points))

    # Nondimensionalization: x*=x/L and t*=alpha*t/L^2.
    _set_named_value(config["equation"]["par_fix"], "a", "1")
    _set_named_value(config["equation"]["par_fix"], "L", "1")
    _set_named_value(
        config["equation"]["par_fix"],
        "T",
        f"{spec.fourier_number:.15g}",
    )
    _set_named_value(config["equation"]["par_func"], "f(x)", "0*x")
    _set_named_value(
        config["discrete_format"][0]["par_fix"],
        "nx",
        str(spatial_qubits),
    )
    _set_named_value(
        config["initial_condition"][0]["par_func"],
        "u0(x)",
        "sin(pi*x/L)",
    )
    data["params"][1] = {
        "help": "thermal-pde-audit controlled Trotter configuration",
        "latex": "",
        "name": "Controlled Trotter method",
        "par_fix": [
            {"name": "na", "value": str(ancilla_qubits)},
            {"name": "R", "value": f"{auxiliary_range:.17g}"},
            {"name": "p", "value": str(recovery_point)},
            {
                "name": "dt",
                "value": f"{spec.fourier_number / quantum_steps:.15g}",
            },
        ],
        "par_func": [],
        "type": "solutionMethod_trotter",
    }
    data["request_id"] = "thermal-pde-audit"
    return data


def _device_info(device: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "requested_device": device,
        "torch": None,
        "torch_br": None,
        "unitarylab": None,
        "unitarylab_algorithms": None,
        "supa_device_count": None,
    }
    try:
        import torch
        import torch_br  # noqa: F401

        info["torch"] = torch.__version__
        info["torch_br"] = importlib.metadata.version("torch_br")
        info["supa_device_count"] = torch.supa.device_count()
    except Exception as exc:
        info["device_probe_error"] = f"{type(exc).__name__}: {exc}"
    for package in ("unitarylab", "unitarylab_algorithms"):
        try:
            info[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            info[package] = "unknown"
    return info


def solve_quantum(
    spec: ThermalExperimentSpec,
    output_dir: Path,
    *,
    device: str | None = None,
    quantum_steps: int = 1,
    ancilla_qubits: int = 5,
    auxiliary_range: float = 4.0,
    recovery_point: int = 1,
) -> dict[str, Any]:
    """Run the installed HeatEquationAlgorithm and return a stable protocol."""

    requested_device = (device or spec.device).lower()
    output_dir = Path(output_dir)
    base: dict[str, Any] = {
        "backend": f"unitarylab_{requested_device}",
        "algorithm": ALGORITHM_PATH,
        "status": "failed",
        "parameters": {
            "device": requested_device,
            "quantum_steps": quantum_steps,
            "ancilla_qubits": ancilla_qubits,
            "auxiliary_range": auxiliary_range,
            "recovery_point": recovery_point,
            "nondimensionalization": {
                "x_star": "x / length_m",
                "t_star": "thermal_diffusivity_m2_s * t / length_m^2",
                "normalized_length": 1.0,
                "normalized_diffusivity": 1.0,
                "normalized_duration": spec.fourier_number,
                "temperature_scale_k": spec.initial_amplitude_k,
            },
        },
        "state_or_field": [],
        "spatial_grid_m": [],
        "runtime_s": 0.0,
        "device_info": _device_info(requested_device),
        "raw_result_keys": [],
        "artifacts": [],
        "warnings": [],
    }
    if requested_device not in {"cpu", "gpu"}:
        base["error"] = {
            "type": "ValueError",
            "message": f"Unsupported UnitaryLab device: {requested_device}",
        }
        return base
    if quantum_steps < 1 or ancilla_qubits < 1 or auxiliary_range <= 0:
        base["error"] = {
            "type": "ValueError",
            "message": (
                "quantum_steps, ancilla_qubits, and auxiliary_range must be "
                "positive."
            ),
        }
        return base
    if (
        requested_device == "gpu"
        and base["device_info"].get("supa_device_count", 0) < 1
    ):
        base["error"] = {
            "type": "RuntimeError",
            "message": "No SUPA device is visible; GPU execution was not attempted.",
        }
        return base
    try:
        raw_dir = _prepare_raw_directory(output_dir, requested_device)
    except (OSError, ValueError) as exc:
        base["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return base

    routed_calls: list[dict[str, Any]] = []
    route_compatibility: dict[str, Any] = {}
    log_handler_cleanup: dict[str, Any] = {}
    figure_cleanup: dict[str, Any] = {}
    try:
        module = importlib.import_module(
            "unitarylab_algorithms.schrodingerization.equation_heat.algorithm"
        )
        algorithm_class = module.HeatEquationAlgorithm
        from unitarylab.library.equation import schrodingerization as schro_module

        params = _build_params(
            spec,
            quantum_steps,
            ancilla_qubits,
            auxiliary_range,
            recovery_point,
        )
        with route_schro_trotter_device(
            schro_module,
            requested_device,
            routed_calls,
        ) as route_compatibility:
            algorithm = algorithm_class()
            started = time.perf_counter()
            try:
                raw = algorithm.run(
                    params=params,
                    algo_dir=str(raw_dir),
                    backend="torch",
                    device=requested_device,
                )
                runtime = time.perf_counter() - started
            finally:
                log_handler_cleanup = _close_algorithm_log_handlers(algorithm)
                figure_cleanup = _close_algorithm_figures()

        raw_x = [float(value) for value in raw.get("x", [])]
        raw_u = [float(value) for value in raw.get("u", [])]
        artifacts: list[str] = []
        plot = raw.get("plot", {})
        if isinstance(plot, dict) and plot.get("filename"):
            artifacts.append(str(plot["filename"]))
        for item in raw.get("circuit", []):
            if isinstance(item, dict) and item.get("filename"):
                artifacts.append(str(item["filename"]))
            elif isinstance(item, str):
                artifacts.append(item)

        base.update(
            {
                "status": (
                    "success"
                    if raw.get("status") in {"ok", "success", "partial_success"}
                    and raw_x
                    and len(raw_x) == len(raw_u)
                    and _device_route_is_verified(
                        routed_calls,
                        route_compatibility,
                        requested_device,
                    )
                    else "failed"
                ),
                "state_or_field": [
                    value * spec.initial_amplitude_k for value in raw_u
                ],
                "spatial_grid_m": [
                    value * spec.length_m for value in raw_x
                ],
                "runtime_s": runtime,
                "raw_result_keys": sorted(raw),
                "artifacts": artifacts,
                "raw_status": raw.get("status"),
                "raw_message": raw.get("message"),
                "raw_grid": raw.get("grid"),
                "device_route_calls": routed_calls,
                "device_route_compatibility": route_compatibility,
                "algorithm_log_handler_cleanup": log_handler_cleanup,
                "algorithm_figure_cleanup": figure_cleanup,
            }
        )
        base["parameters"]["unitarylab_params"] = {
            "spatial_qubits": int(math.log2(spec.spatial_points)),
            "ancilla_qubits": ancilla_qubits,
            "R": auxiliary_range,
            "recovery_point": recovery_point,
            "Nt": quantum_steps,
            "dt_dimensionless": spec.fourier_number / quantum_steps,
        }
        route_warning = (
            "The adapter routed and recorded the requested device under a "
            "process-wide lock, then restored the upstream function; "
            "compatibility injection count: "
            f"{route_compatibility['injection_count']}."
            if route_compatibility["injection_count"]
            else (
                "The 1D heat class forwarded the requested lower-level device; "
                "the adapter recorded the call under a process-wide lock and "
                "restored the upstream function."
            )
        )
        base["warnings"] = [
            route_warning,
            (
                "UnitaryLab supplies the interior nodes, and the controlled "
                "experiment protocol supplies the zero Dirichlet boundaries."
            ),
            (
                "The workflow nondimensionalizes the physical problem before "
                "the UnitaryLab call and restores metres and kelvin afterward."
            ),
        ]
        if log_handler_cleanup["errors"]:
            base["warnings"].append(
                "One or more upstream algorithm log handlers could not be "
                f"closed cleanly: {log_handler_cleanup['errors']}"
            )
        if base["status"] != "success":
            base["error"] = {
                "type": "InvalidUnitaryLabResult",
                "message": (
                    "UnitaryLab did not return a successful, non-empty field "
                    "with a recorded lower-level device route."
                ),
            }
    except Exception as exc:
        if routed_calls:
            base["device_route_calls"] = routed_calls
        if route_compatibility:
            base["device_route_compatibility"] = route_compatibility
        if log_handler_cleanup:
            base["algorithm_log_handler_cleanup"] = log_handler_cleanup
        if figure_cleanup:
            base["algorithm_figure_cleanup"] = figure_cleanup
        base["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
    return base
