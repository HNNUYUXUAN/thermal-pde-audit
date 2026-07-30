from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from thermal_pde_audit.unitarylab_compat import (
    DeviceRouteCompatibilityError,
    route_schro_trotter_device,
)
from thermal_pde_audit.quantum_solver import (
    _close_algorithm_figures,
    _close_algorithm_log_handlers,
    _device_route_is_verified,
    _prepare_raw_directory,
    solve_quantum,
)
from thermal_pde_audit.schema import ThermalExperimentSpec


def test_route_injects_records_and_restores_device() -> None:
    def original(*, Nt: int, device: str = "cpu") -> tuple[int, str]:
        return Nt, device

    module = SimpleNamespace(schro_trotter=original)
    calls: list[dict[str, object]] = []

    with route_schro_trotter_device(module, "gpu", calls) as metadata:
        assert module.schro_trotter(Nt=4) == (4, "gpu")

    assert module.schro_trotter is original
    assert calls == [
        {
            "device": "gpu",
            "requested_device": "gpu",
            "device_was_injected": True,
            "device_matches_requested": True,
            "Nt": 4,
            "na": None,
            "R": None,
            "order": None,
            "point": None,
        }
    ]
    assert metadata["injection_count"] == 1
    assert metadata["forwarded_count"] == 0
    assert metadata["conflict_count"] == 0
    assert metadata["all_devices_match_requested"] is True
    assert metadata["restored"] is True


def test_route_preserves_matching_explicit_upstream_device() -> None:
    def original(*, device: str = "cpu") -> str:
        return device

    module = SimpleNamespace(schro_trotter=original)
    calls: list[dict[str, object]] = []

    with route_schro_trotter_device(module, "gpu", calls) as metadata:
        assert module.schro_trotter(device="gpu") == "gpu"

    assert calls[0]["device"] == "gpu"
    assert calls[0]["device_matches_requested"] is True
    assert calls[0]["device_was_injected"] is False
    assert metadata["injection_count"] == 0
    assert metadata["forwarded_count"] == 1
    assert metadata["conflict_count"] == 0


def test_route_rejects_conflicting_explicit_upstream_device() -> None:
    def original(*, device: str = "cpu") -> str:
        return device

    module = SimpleNamespace(schro_trotter=original)
    calls: list[dict[str, object]] = []

    with pytest.raises(DeviceRouteCompatibilityError):
        with route_schro_trotter_device(module, "gpu", calls) as metadata:
            module.schro_trotter(device="cpu")

    assert module.schro_trotter is original
    assert calls[0]["device"] == "cpu"
    assert calls[0]["requested_device"] == "gpu"
    assert calls[0]["device_matches_requested"] is False
    assert metadata["conflict_count"] == 1
    assert metadata["all_devices_match_requested"] is False
    assert metadata["restored"] is True


def test_route_fails_closed_when_device_is_unsupported() -> None:
    def original(Nt: int) -> int:
        return Nt

    module = SimpleNamespace(schro_trotter=original)

    with pytest.raises(DeviceRouteCompatibilityError):
        with route_schro_trotter_device(module, "gpu", []):
            pass


def test_route_restores_after_algorithm_exception() -> None:
    def original(*, device: str = "cpu") -> str:
        return device

    module = SimpleNamespace(schro_trotter=original)

    with pytest.raises(RuntimeError):
        with route_schro_trotter_device(module, "gpu", []):
            raise RuntimeError("algorithm failed")

    assert module.schro_trotter is original


def test_final_route_verification_rejects_mislabeled_or_unrestored_route() -> None:
    matching_call = {
        "device": "gpu",
        "requested_device": "gpu",
        "device_matches_requested": True,
    }
    matching_compatibility = {
        "requested_device": "gpu",
        "all_devices_match_requested": True,
        "conflict_count": 0,
        "restored": True,
    }

    assert _device_route_is_verified(
        [matching_call],
        matching_compatibility,
        "gpu",
    )
    assert not _device_route_is_verified(
        [{**matching_call, "device": "cpu"}],
        matching_compatibility,
        "gpu",
    )
    assert not _device_route_is_verified(
        [matching_call],
        {**matching_compatibility, "restored": False},
        "gpu",
    )


def test_prepare_raw_directory_removes_only_selected_backend(
    tmp_path: Path,
) -> None:
    raw_dir = tmp_path / "unitarylab_gpu"
    raw_dir.mkdir()
    (raw_dir / "stale.log").write_text("old", encoding="utf-8")
    sibling = tmp_path / "keep.txt"
    sibling.write_text("keep", encoding="utf-8")

    prepared = _prepare_raw_directory(tmp_path, "gpu")

    assert prepared == raw_dir.resolve()
    assert list(prepared.iterdir()) == []
    assert sibling.read_text(encoding="utf-8") == "keep"


def test_invalid_solver_parameters_do_not_clear_existing_artifacts(
    tmp_path: Path,
) -> None:
    raw_dir = tmp_path / "unitarylab_cpu"
    raw_dir.mkdir()
    marker = raw_dir / "prior.log"
    marker.write_text("prior evidence", encoding="utf-8")
    spec = ThermalExperimentSpec.from_dict(
        {
            "task": "heat_equation_1d",
            "length_m": 0.01,
            "thermal_diffusivity_m2_s": 1.2e-5,
            "initial_amplitude_k": 100.0,
            "duration_s": 0.5,
            "spatial_points": 32,
            "time_steps": 300,
            "boundary": "dirichlet_zero",
            "initial_condition": "sine_mode_1",
            "device": "cpu",
            "seed": 42,
        }
    )

    result = solve_quantum(spec, tmp_path, device="cpu", quantum_steps=0)

    assert result["status"] == "failed"
    assert result["error"]["type"] == "ValueError"
    assert marker.read_text(encoding="utf-8") == "prior evidence"


def test_solver_preserves_original_import_failure_without_scope_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = ThermalExperimentSpec.from_dict(
        {
            "task": "heat_equation_1d",
            "length_m": 0.01,
            "thermal_diffusivity_m2_s": 1.2e-5,
            "initial_amplitude_k": 100.0,
            "duration_s": 0.5,
            "spatial_points": 32,
            "time_steps": 300,
            "boundary": "dirichlet_zero",
            "initial_condition": "sine_mode_1",
            "device": "cpu",
            "seed": 42,
        }
    )
    monkeypatch.setattr(
        "thermal_pde_audit.quantum_solver._device_info",
        lambda device: {"requested_device": device, "supa_device_count": 1},
    )
    monkeypatch.setattr(
        "thermal_pde_audit.quantum_solver.importlib.import_module",
        Mock(side_effect=RuntimeError("controlled import failure")),
    )

    result = solve_quantum(spec, tmp_path, device="cpu")

    assert result["status"] == "failed"
    assert result["error"] == {
        "type": "RuntimeError",
        "message": "controlled import failure",
    }


def test_upstream_log_handlers_are_closed_and_detached() -> None:
    handler = Mock()
    logger = SimpleNamespace(handlers=[handler])
    algorithm = SimpleNamespace(logger=logger)

    result = _close_algorithm_log_handlers(algorithm)

    handler.flush.assert_called_once_with()
    handler.close.assert_called_once_with()
    assert logger.handlers == []
    assert result == {"observed": 1, "closed": 1, "errors": []}


def test_upstream_figures_are_closed_after_saving() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.figure()
    result = _close_algorithm_figures()

    assert result["observed"] >= 1
    assert result["closed"] == result["observed"]
    assert plt.get_fignums() == []
