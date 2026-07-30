"""JSON-adjacent Markdown and figure generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_temperature_figure(
    result: dict[str, Any],
    output_path: Path,
) -> None:
    """Plot analytic, classical, and available quantum final fields."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 5))
    analytic = result["analytic"]
    axis.plot(
        analytic["spatial_grid_m"],
        analytic["state_or_field_k"],
        label="Analytic",
        linewidth=2.2,
    )
    classical = result.get("classical", {})
    if classical.get("status") == "success":
        axis.plot(
            classical["spatial_grid_m"],
            classical["state_or_field_k"],
            "--",
            label="Explicit finite difference",
        )
    quantum = result.get("quantum", {})
    if quantum.get("status") == "success":
        axis.plot(
            quantum["spatial_grid_m"],
            quantum["state_or_field"],
            "o-",
            markersize=3,
            label=quantum["backend"],
        )
    axis.set_xlabel("Position x (m)")
    axis.set_ylabel("Temperature rise u (K)")
    axis.set_title("1D heat equation final field")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def write_error_decomposition_figure(
    result: dict[str, Any],
    output_path: Path,
) -> None:
    """Plot same-run relative L2 diagnostics on a logarithmic scale."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    decomposition = result.get("error_decomposition", {})
    if decomposition.get("status") != "success":
        raise ValueError("A successful error decomposition is required.")
    metrics = decomposition["metrics"]
    labels_and_keys = [
        ("Semi vs analytic", "semi_discrete_vs_continuous_analytic"),
        ("Recovery vs semi", "same_parameter_recovery_vs_semi_discrete"),
        ("Trotter vs recovery", "trotter_vs_same_parameter_recovery"),
        ("Trotter vs semi", "trotter_vs_semi_discrete"),
        ("Trotter vs analytic", "trotter_vs_continuous_analytic"),
    ]
    labels = [
        label for label, key in labels_and_keys if key in metrics
    ]
    values = [
        metrics[key]["relative_l2_error"]
        for _, key in labels_and_keys
        if key in metrics
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9, 5))
    bars = axis.bar(labels, values, color="#2878b5")
    axis.set_yscale("log")
    axis.set_ylabel("Relative L2 error (log scale)")
    axis.set_title("Same-run Schrödingerization error diagnostics")
    axis.grid(axis="y", alpha=0.25)
    axis.tick_params(axis="x", rotation=18)
    for bar, value in zip(bars, values):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.3e}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value)


def write_report(
    spec: dict[str, Any],
    result: dict[str, Any],
    audit: dict[str, Any],
    output_path: Path,
    *,
    user_task: str,
    reproduce_command: str,
) -> None:
    """Write a truthful Markdown report from the same-run artifacts."""

    quantum = result.get("quantum", {})
    classical = result.get("classical", {})
    supa_audit = result.get("supa_audit", {})
    custom_supa_audit = result.get("custom_supa_audit", {})
    error_decomposition = result.get("error_decomposition", {})
    profile_selection = result.get("quantum_profile_selection", {})
    lines = [
        "# 一维热传导量子仿真物理审计报告",
        "",
        "## 用户任务",
        "",
        user_task,
    ]
    input_provenance = result.get("input_provenance", {})
    if input_provenance.get("mode") == "natural_language":
        lines.extend(
            [
                "",
                "## 自然语言任务解析",
                "",
                f"- 解析器：`{input_provenance.get('parser')}`",
                (
                    "- 默认值及来源："
                    f"`{input_provenance.get('defaults_applied', {})}`"
                ),
                (
                    "- 安全边界："
                    f"{input_provenance.get('security_boundary', '')}"
                ),
                (
                    "- 受控参数："
                    f"`{input_provenance.get('spec', {})}`"
                ),
                (
                    "- 白名单执行计划："
                    f"`{input_provenance.get('execution_plan', {})}`"
                ),
            ]
        )
    lines.extend(
        [
            "",
            "## 参数与单位",
            "",
            "| 参数 | SI 值 |",
            "|---|---:|",
        ]
    )
    for name, value in spec.items():
        lines.append(f"| `{name}` | {_fmt(value)} |")

    if profile_selection:
        lines.extend(
            [
                "",
                "## 已验证量子参数档案",
                "",
                f"- 选择方式：`{profile_selection.get('selection_mode')}`",
                f"- 参数：`{profile_selection.get('parameters', {})}`",
                f"- 连续通过点：`{profile_selection.get('confirmed_streak')}`",
                f"- 证据：`{profile_selection.get('evidence', [])}`",
            ]
        )

    lines.extend(
        [
            "",
            "## 真实量子算法与设备",
            "",
            f"- 状态：`{quantum.get('status', 'not_run')}`",
            f"- 后端：`{quantum.get('backend', 'not_run')}`",
            f"- 实际类：`{quantum.get('algorithm', 'not_run')}`",
            f"- 运行时间：`{_fmt(quantum.get('runtime_s'))}` s",
            f"- 设备信息：`{quantum.get('device_info', {})}`",
            f"- 原始返回键：`{quantum.get('raw_result_keys', [])}`",
            f"- 底层设备路由：`{quantum.get('device_route_calls', [])}`",
            "",
            "量子环节使用 Schrödingerization 的 Trotter 线路把非幺正热扩散演化嵌入幺正演化并在指定 UnitaryLab 后端执行。物理参数先无量纲化，返回场再缩放到米和开尔文。",
            "",
            "## 解析解与经典基线",
            "",
            "- 解析解：一阶正弦模态的闭式衰减解。",
            f"- 经典基线状态：`{classical.get('status', 'not_run')}`",
            f"- 有限差分网格诊断：`{classical.get('grid', classical.get('error', {}))}`",
        ]
    )
    if error_decomposition.get("status") != "not_requested":
        lines.extend(
            [
                "",
                "## Schrödingerization 误差分层",
                "",
                f"- 状态：`{error_decomposition.get('status')}`",
                (
                    "- 方法："
                    f"`{error_decomposition.get('method', 'unavailable')}`"
                ),
                (
                    "- 同参数非 Trotter 恢复："
                    f"`{error_decomposition.get('recovery_reference', {}).get('status')}`"
                ),
                "",
                "| 对照层 | 最大绝对误差 | RMSE | 相对 L2 |",
                "|---|---:|---:|---:|",
            ]
        )
        for key, label in (
            (
                "semi_discrete_vs_continuous_analytic",
                "半离散精确演化 vs 连续解析解",
            ),
            (
                "same_parameter_recovery_vs_semi_discrete",
                "同参数 schro_classical vs 半离散",
            ),
            (
                "trotter_vs_same_parameter_recovery",
                "Trotter vs 同参数 schro_classical",
            ),
            (
                "trotter_vs_semi_discrete",
                "Trotter vs 半离散",
            ),
            (
                "trotter_vs_continuous_analytic",
                "Trotter vs 连续解析解",
            ),
        ):
            metric = error_decomposition.get("metrics", {}).get(key)
            if metric:
                lines.append(
                    f"| {label} | `{_fmt(metric['max_abs_error'])}` | "
                    f"`{_fmt(metric['rmse'])}` | "
                    f"`{_fmt(metric['relative_l2_error'])}` |"
                )
        for note in error_decomposition.get("interpretation", []):
            lines.append(f"- 解释边界：{note}")
        if error_decomposition.get("error"):
            lines.append(
                f"- 分层错误：`{error_decomposition['error']}`"
            )
    lines.extend(
        [
            "",
            "## 误差与物理审计",
            "",
            f"- 总体通过：`{audit.get('passed', False)}`",
            "",
            "| 检查 | 目标 | 通过 | 值 | 阈值 |",
            "|---|---|---:|---|---|",
        ]
    )
    for item in audit.get("checks", []):
        lines.append(
            f"| `{item['name']}` | `{item.get('target')}` | "
            f"{item['passed']} | `{item['value']}` | `{item['threshold']}` |"
        )

    if supa_audit:
        lines.extend(
            [
                "",
                "## SUPA 误差归约",
                "",
                f"- 状态：`{supa_audit.get('status')}`",
                f"- 后端：`{supa_audit.get('backend')}`",
                f"- 设备：`{supa_audit.get('device')}`",
                f"- 数据类型：`{supa_audit.get('dtype')}`",
                f"- SUPA 指标：`{supa_audit.get('metrics', {})}`",
                (
                    "- CPU/SUPA 一致性："
                    f"`{supa_audit.get('consistency', {})}`"
                ),
                f"- 分段耗时：`{supa_audit.get('runtime_s', {})}`",
            ]
        )
        for warning in supa_audit.get("warnings", []):
            lines.append(f"- 运行说明：{warning}")

    if custom_supa_audit:
        lines.extend(
            [
                "",
                "## 自定义 SUPA 误差归约核",
                "",
                f"- 状态：`{custom_supa_audit.get('status')}`",
                f"- 源码：`{custom_supa_audit.get('kernel_source')}`",
                f"- 设备：`{custom_supa_audit.get('device')}`",
                f"- 数据类型：`{custom_supa_audit.get('dtype')}`",
                f"- 核指标：`{custom_supa_audit.get('metrics', {})}`",
                (
                    "- CPU/自定义核一致性："
                    f"`{custom_supa_audit.get('consistency', {})}`"
                ),
                f"- 进程耗时：`{custom_supa_audit.get('runtime_s', {})}`",
            ]
        )
        for warning in custom_supa_audit.get("warnings", []):
            lines.append(f"- 实现说明：{warning}")

    lines.extend(
        [
            "",
            "## 性能",
            "",
            f"- 量子主后端总调用：`{_fmt(quantum.get('runtime_s'))}` s",
            f"- CPU 参考总调用：`{_fmt(result.get('quantum_cpu_reference', {}).get('runtime_s'))}` s",
            "- 运行时间完整计入后端初始化、编译、执行与数据传输，便于复现实验进行同口径对照。",
            "",
            "## 结论",
            "",
            (
                "本次结果通过所列阈值。"
                if audit.get("passed")
                else "本次结果未通过全部阈值，应查看失败检查与运行日志。"
            ),
            "",
            "## 实验配置与适用范围",
            "",
            "- 当前实验协议：一维、零源、Dirichlet 零边界和一阶正弦初态。",
            "- UnitaryLab 返回的是内部网格点；边界值由受控协议施加。",
            "- 项目适配层在进程锁保护下完成设备参数透传、记录并恢复原函数。",
            "- 报告聚焦热方程结果、误差分解、后端路由和物理一致性。",
        ]
    )
    for warning in quantum.get("warnings", []):
        lines.append(f"- 运行说明：{warning}")
    if quantum.get("error"):
        lines.append(f"- 量子错误：`{quantum['error']}`")
    lines.extend(
        [
            "",
            "## 复现命令",
            "",
            "```bash",
            reproduce_command,
            "```",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
