from pathlib import Path
from types import SimpleNamespace

import numpy as np

from thermal_pde_audit.custom_supa_audit import (
    audit_error_metrics_with_custom_supa,
)


def test_custom_supa_rejects_oversized_field_before_process() -> None:
    values = np.zeros(257)

    result = audit_error_metrics_with_custom_supa(
        values,
        values,
        Path("missing"),
    )

    assert result["status"] == "failed"
    assert result["error"]["type"] == "ValueError"


def test_custom_supa_rejects_non_1d_field_before_process() -> None:
    values = np.zeros((2, 2))

    result = audit_error_metrics_with_custom_supa(
        values,
        values,
        Path("missing"),
    )

    assert result["status"] == "failed"
    assert result["error"]["type"] == "ValueError"


def test_custom_supa_checks_kernel_metrics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    executable = tmp_path / "custom.out"
    executable.write_bytes(b"placeholder")
    monkeypatch.setattr(
        "thermal_pde_audit.custom_supa_audit.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=(
                '{"max_abs_error": 1.0, "rmse": 0.707106769, '
                '"relative_l2_error": 0.44721359, '
                '"squared_error_sum": 1.0, '
                '"squared_reference_sum": 5.0}'
            ),
            stderr="",
        ),
    )

    result = audit_error_metrics_with_custom_supa(
        [1.0, 1.0],
        [2.0, 1.0],
        executable,
    )

    assert result["status"] == "success"
    assert result["consistency"]["passed"] is True
