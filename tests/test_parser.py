from __future__ import annotations

import pytest

from thermal_pde_audit.parser import (
    parse_natural_language,
    plan_natural_language,
)
from thermal_pde_audit.schema import ThermalSpecValidationError


def test_parse_chinese_si_conversion_and_gpu() -> None:
    parsed = parse_natural_language(
        "模拟长度10毫米、热扩散率1.2e-5平方米每秒、初始温升100K的"
        "一维热传导，计算0.5秒，使用GPU并生成验证报告"
    )
    assert parsed.spec.length_m == pytest.approx(0.01)
    assert parsed.spec.thermal_diffusivity_m2_s == pytest.approx(1.2e-5)
    assert parsed.spec.duration_s == pytest.approx(0.5)
    assert parsed.spec.device == "gpu"
    assert parsed.spec.time_steps == 200
    assert "time_steps" in parsed.defaults_applied
    assert parsed.execution_plan.validated_profile is True
    assert parsed.execution_plan.compare_cpu_gpu is False


def test_parse_full_validation_builds_whitelisted_execution_plan() -> None:
    parsed = parse_natural_language(
        "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的"
        "一维热传导，计算0.1秒，使用GPU做完整验证，进行CPU/GPU对照、"
        "SUPA与自定义SUPA审计、误差分层"
    )

    assert parsed.spec.device == "gpu"
    assert parsed.execution_plan.to_dict() == {
        "compare_cpu_gpu": True,
        "validated_profile": True,
        "supa_audit": True,
        "custom_supa_audit": True,
        "error_decomposition": True,
        "report_level": "full",
        "sources": {
            "compare_cpu_gpu": "natural_language:cpu_gpu_comparison",
            "validated_profile": "safe_default:exact_empirical_profile",
            "supa_audit": "natural_language:full_validation",
            "custom_supa_audit": "natural_language:full_validation",
            "error_decomposition": "natural_language:full_validation",
            "report_level": "natural_language:full_validation",
        },
    }


def test_parse_rejects_unsupported_periodic_boundary() -> None:
    with pytest.raises(ThermalSpecValidationError) as error:
        parse_natural_language(
            "长度1米，热扩散率1e-4平方米每秒，初始温升10K，"
            "计算1秒，使用周期边界"
        )
    assert any(issue.code == "UNSUPPORTED_BOUNDARY" for issue in error.value.issues)


def test_parse_requires_core_parameters() -> None:
    with pytest.raises(ThermalSpecValidationError) as error:
        parse_natural_language("请模拟一维热传导")
    fields = {issue.field for issue in error.value.issues}
    assert {
        "length_m",
        "thermal_diffusivity_m2_s",
        "initial_amplitude_k",
        "duration_s",
    }.issubset(fields)


def test_plan_text_returns_questions_without_executing() -> None:
    plan = plan_natural_language(
        "长度10毫米，热扩散率1e-6平方米每秒，请模拟一维热传导"
    )

    assert plan["status"] == "needs_clarification"
    assert {issue["field"] for issue in plan["issues"]} == {
        "initial_amplitude_k",
        "duration_s",
    }
    assert len(plan["questions"]) == 2
    assert "No solver" in plan["security_boundary"]
