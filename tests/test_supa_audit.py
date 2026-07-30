import numpy as np

from thermal_pde_audit.supa_audit import (
    _metric_consistency,
    audit_error_metrics_on_supa,
)


def test_metric_consistency_reports_each_difference() -> None:
    cpu = {
        "max_abs_error": 1.0,
        "rmse": 0.5,
        "relative_l2_error": 0.25,
    }
    supa = {
        "max_abs_error": 1.0 + 1e-12,
        "rmse": 0.5,
        "relative_l2_error": 0.25,
    }

    result = _metric_consistency(supa, cpu)

    assert result["passed"] is True
    assert set(result["absolute_differences"]) == set(cpu)


def test_supa_audit_rejects_shape_mismatch_before_device_import() -> None:
    result = audit_error_metrics_on_supa(
        np.asarray([1.0, 2.0]),
        np.asarray([1.0]),
    )

    assert result["status"] == "failed"
    assert result["error"]["type"] == "ValueError"
