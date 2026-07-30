"""Deterministic Chinese/English parser for the controlled protocol."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from .schema import (
    ThermalExperimentSpec,
    ThermalSpecValidationError,
    ValidationIssue,
)


DEFAULTS = {
    "spatial_points": 32,
    "time_steps": 200,
    "boundary": "dirichlet_zero",
    "initial_condition": "sine_mode_1",
    "device": "cpu",
    "seed": 42,
}
NUMBER = r"([+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"


@dataclass(frozen=True)
class ExecutionPlan:
    """Whitelisted execution choices derived from the task text."""

    compare_cpu_gpu: bool
    validated_profile: bool
    supa_audit: bool
    custom_supa_audit: bool
    error_decomposition: bool
    report_level: str
    sources: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "compare_cpu_gpu": self.compare_cpu_gpu,
            "validated_profile": self.validated_profile,
            "supa_audit": self.supa_audit,
            "custom_supa_audit": self.custom_supa_audit,
            "error_decomposition": self.error_decomposition,
            "report_level": self.report_level,
            "sources": self.sources,
        }


@dataclass(frozen=True)
class ParseResult:
    """Parsed specification plus an explicit default-value trace."""

    spec: ThermalExperimentSpec
    defaults_applied: dict[str, object]
    source_text: str
    execution_plan: ExecutionPlan

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "parsed",
            "spec": self.spec.to_dict(),
            "defaults_applied": self.defaults_applied,
            "execution_plan": self.execution_plan.to_dict(),
            "source_text": self.source_text,
            "security_boundary": (
                "Natural language was mapped to whitelisted fields only; "
                "no shell or Python code was generated or executed."
            ),
        }


def _execution_plan(text: str) -> ExecutionPlan:
    full = bool(
        re.search(
            r"完整验证|完整审计|全链路|full\s+validation|full\s+audit",
            text,
            re.I,
        )
    )
    compare = bool(
        re.search(
            r"CPU\s*(?:/|和|与|及|and)\s*GPU|"
            r"(?:CPU|GPU).{0,12}(?:对照|对比|比较|consistency|comparison)",
            text,
            re.I,
        )
    )
    custom_supa = full or bool(
        re.search(r"自定义\s*SUPA|custom\s+SUPA", text, re.I)
    )
    supa = full or custom_supa or bool(re.search(r"SUPA", text, re.I))
    error_decomposition = full or bool(
        re.search(
            r"误差分层|误差分解|error\s+decomposition",
            text,
            re.I,
        )
    )
    sources = {
        "compare_cpu_gpu": (
            "natural_language:cpu_gpu_comparison"
            if compare
            else "default:false"
        ),
        "validated_profile": "safe_default:exact_empirical_profile",
        "supa_audit": (
            "natural_language:full_validation"
            if full
            else (
                "natural_language:supa_audit" if supa else "default:false"
            )
        ),
        "custom_supa_audit": (
            "natural_language:full_validation"
            if full
            else (
                "natural_language:custom_supa_audit"
                if custom_supa
                else "default:false"
            )
        ),
        "error_decomposition": (
            "natural_language:full_validation"
            if full
            else (
                "natural_language:error_decomposition"
                if error_decomposition
                else "default:false"
            )
        ),
        "report_level": (
            "natural_language:full_validation"
            if full
            else "default:standard"
        ),
    }
    return ExecutionPlan(
        compare_cpu_gpu=compare,
        validated_profile=True,
        supa_audit=supa,
        custom_supa_audit=custom_supa,
        error_decomposition=error_decomposition,
        report_level="full" if full else "standard",
        sources=sources,
    )


def plan_natural_language(text: str) -> dict[str, Any]:
    """Return a ready plan or deterministic clarification questions."""

    try:
        parsed = parse_natural_language(text)
    except ThermalSpecValidationError as exc:
        clarification_codes = {
            "MISSING_PARAMETER",
            "AMBIGUOUS_PARAMETER",
        }
        needs_clarification = bool(exc.issues) and all(
            issue.code in clarification_codes for issue in exc.issues
        )
        questions: list[str] = []
        labels = {
            "length_m": "请补充一维区域长度，并注明米、厘米或毫米。",
            "thermal_diffusivity_m2_s": (
                "请补充正的热扩散率，并注明平方米每秒等受支持单位。"
            ),
            "initial_amplitude_k": "请补充初始温升，并注明 K 或摄氏温差。",
            "duration_s": "请补充计算时长，并注明秒或毫秒。",
            "device": "请明确选择主设备，或明确要求 CPU/GPU 对照。",
            "natural_language": "请消除网格点或时间步中的冲突数值。",
        }
        for issue in exc.issues:
            question = labels.get(issue.field, issue.message)
            if question not in questions:
                questions.append(question)
        return {
            "status": (
                "needs_clarification" if needs_clarification else "rejected"
            ),
            "issues": [issue.to_dict() for issue in exc.issues],
            "questions": questions,
            "source_text": text,
            "security_boundary": (
                "No solver, shell command, or Python code was executed."
            ),
        }
    return {
        **parsed.to_dict(),
        "status": "ready",
    }


def _extract_measurement(
    text: str,
    field: str,
    label: str,
    pattern: str,
    converter: Callable[[float, str], float],
) -> float:
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    converted: list[float] = []
    for value, unit in matches:
        converted.append(converter(float(value), unit.lower()))
    distinct = {round(value, 15) for value in converted}
    if not converted:
        raise ThermalSpecValidationError(
            [
                ValidationIssue(
                    field=field,
                    code="MISSING_PARAMETER",
                    message=f"Could not find an unambiguous {label}.",
                )
            ]
        )
    if len(distinct) > 1:
        raise ThermalSpecValidationError(
            [
                ValidationIssue(
                    field=field,
                    code="AMBIGUOUS_PARAMETER",
                    message=f"Multiple conflicting values were found for {label}.",
                    value=converted,
                )
            ]
        )
    return converted[0]


def _length_to_m(value: float, unit: str) -> float:
    unit = unit.replace(" ", "")
    if unit in {"毫米", "mm"}:
        return value * 1e-3
    if unit in {"厘米", "cm"}:
        return value * 1e-2
    return value


def _duration_to_s(value: float, unit: str) -> float:
    unit = unit.replace(" ", "")
    if unit in {"毫秒", "ms"}:
        return value * 1e-3
    return value


def _diffusivity_to_si(value: float, unit: str) -> float:
    normalized = (
        unit.replace(" ", "")
        .replace("^", "")
        .replace("²", "2")
        .replace("每", "/")
    )
    if normalized in {"mm2/s", "平方毫米/秒"}:
        return value * 1e-6
    if normalized in {"cm2/s", "平方厘米/秒"}:
        return value * 1e-4
    return value


def _temperature_difference_to_k(value: float, unit: str) -> float:
    del unit
    return value


def _optional_integer(text: str, patterns: tuple[str, ...]) -> int | None:
    values: list[int] = []
    for pattern in patterns:
        values.extend(int(value) for value in re.findall(pattern, text, re.I))
    if not values:
        return None
    if len(set(values)) > 1:
        raise ThermalSpecValidationError(
            [
                ValidationIssue(
                    field="natural_language",
                    code="AMBIGUOUS_PARAMETER",
                    message="Conflicting integer grid/time-step values were found.",
                    value=values,
                )
            ]
        )
    return values[0]


def parse_natural_language(text: str) -> ParseResult:
    """Parse a constrained thermal task without an external model."""

    if not isinstance(text, str) or not text.strip():
        raise ThermalSpecValidationError(
            [
                ValidationIssue(
                    field="text",
                    code="EMPTY_TEXT",
                    message="Natural-language input must not be empty.",
                    value=text,
                )
            ]
        )
    normalized = text.strip()
    issues: list[ValidationIssue] = []
    values: dict[str, object] = {"task": "heat_equation_1d"}
    execution_plan = _execution_plan(normalized)

    extractors = (
        (
            "length_m",
            "length",
            rf"(?:长度|length)\s*[:：]?\s*{NUMBER}\s*(毫米|mm|厘米|cm|米|m)",
            _length_to_m,
        ),
        (
            "thermal_diffusivity_m2_s",
            "thermal diffusivity",
            (
                rf"(?:热扩散率|热扩散系数|thermal\s+diffusivity)"
                rf"\s*[:：]?\s*{NUMBER}\s*"
                r"(平方米每秒|平方毫米每秒|平方厘米每秒|m\s*\^?2\s*/\s*s|"
                r"m²\s*/\s*s|mm\s*\^?2\s*/\s*s|mm²\s*/\s*s|"
                r"cm\s*\^?2\s*/\s*s|cm²\s*/\s*s)"
            ),
            _diffusivity_to_si,
        ),
        (
            "initial_amplitude_k",
            "initial temperature rise",
            (
                rf"(?:初始温升|初始温度|初始振幅|initial\s+(?:temperature\s+rise|"
                rf"amplitude|temperature))\s*[:：]?\s*{NUMBER}\s*(K|开尔文|°?C|摄氏度)"
            ),
            _temperature_difference_to_k,
        ),
        (
            "duration_s",
            "duration",
            (
                rf"(?:计算|持续|时长|duration|simulate\s+for)\s*[:：]?\s*"
                rf"{NUMBER}\s*(毫秒|ms|秒|s)"
            ),
            _duration_to_s,
        ),
    )
    for field, label, pattern, converter in extractors:
        try:
            values[field] = _extract_measurement(
                normalized,
                field,
                label,
                pattern,
                converter,
            )
        except ThermalSpecValidationError as exc:
            issues.extend(exc.issues)

    spatial_points = _optional_integer(
        normalized,
        (
            r"(\d+)\s*(?:个)?(?:空间点|网格点)",
            r"(?:spatial|grid)\s+points?\s*[:=]?\s*(\d+)",
        ),
    )
    time_steps = _optional_integer(
        normalized,
        (
            r"(\d+)\s*(?:个)?时间步",
            r"time\s+steps?\s*[:=]?\s*(\d+)",
        ),
    )

    defaults_applied: dict[str, object] = {}
    for field, default in DEFAULTS.items():
        values[field] = default
        defaults_applied[field] = {
            "value": default,
            "source": "thermal-pde-audit first-round deterministic default",
        }
    if spatial_points is not None:
        values["spatial_points"] = spatial_points
        defaults_applied.pop("spatial_points", None)
    if time_steps is not None:
        values["time_steps"] = time_steps
        defaults_applied.pop("time_steps", None)

    has_gpu = bool(re.search(r"GPU|壁仞|显卡", normalized, re.I))
    has_cpu = bool(re.search(r"CPU", normalized, re.I))
    if has_gpu and has_cpu and not execution_plan.compare_cpu_gpu:
        issues.append(
            ValidationIssue(
                field="device",
                code="AMBIGUOUS_PARAMETER",
                message="Specify one primary device: CPU or GPU.",
                value=["cpu", "gpu"],
            )
        )
    elif has_gpu or execution_plan.compare_cpu_gpu:
        values["device"] = "gpu"
        defaults_applied.pop("device", None)
    elif has_cpu:
        values["device"] = "cpu"
        defaults_applied.pop("device", None)

    if re.search(r"周期|periodic|neumann|诺依曼", normalized, re.I):
        issues.append(
            ValidationIssue(
                field="boundary",
                code="UNSUPPORTED_BOUNDARY",
                message="Only zero Dirichlet boundaries are supported.",
            )
        )
    if re.search(r"高斯|gaussian|二维|2d|非线性|nonlinear", normalized, re.I):
        issues.append(
            ValidationIssue(
                field="task",
                code="OUTSIDE_CAPABILITY_BOUNDARY",
                message=(
                    "The first round supports only a 1D linear heat equation "
                    "with the first sine initial mode."
                ),
            )
        )
    if execution_plan.supa_audit and values["device"] != "gpu":
        issues.append(
            ValidationIssue(
                field="device",
                code="PLAN_DEVICE_CONFLICT",
                message="SUPA audit requires a GPU primary device.",
                value=values["device"],
            )
        )

    if issues:
        raise ThermalSpecValidationError(issues)
    return ParseResult(
        spec=ThermalExperimentSpec.from_dict(values),
        defaults_applied=defaults_applied,
        source_text=normalized,
        execution_plan=execution_plan,
    )
