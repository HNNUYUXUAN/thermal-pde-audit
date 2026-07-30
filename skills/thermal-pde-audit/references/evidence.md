# 证据契约

## 必备成果

| 文件 | 内容 |
|---|---|
| `input.json` | 规范化实验参数 |
| `result.json` | 温度场、设备路由、指标、来源和成果路径 |
| `audit.json` | 物理与数值检查 |
| `report.md` | 面向读者的解释与复现命令 |
| `run.log` | 按顺序记录执行阶段 |
| `temperature_comparison.png` | 解析、经典与量子温度场 |

执行误差分层时生成 `error_decomposition.png`。UnitaryLab CPU/GPU 子目录
保存算法日志、求解 SVG 和线路 SVG。

## 核心校验

对每个完整结果检查：

- 成果文件存在且 JSON 可解析；
- 结果和审计状态成功；
- 量子温度场长度正确且数值有限；
- 边界、温度范围和衰减符合物理约束；
- 使用有证据的精确量子参数档案；
- 请求设备与实际 GPU 路由一致；
- CPU/GPU 温度场一致；
- `torch.supa` 与 NumPy 指标一致；
- 项目 `.su` 核与 NumPy 指标一致；
- 误差分层完整；
- 复现命令只读取受控输入文件。

## 关键指标

报告：

```text
classical_vs_analytic.relative_l2_error
quantum_vs_analytic.relative_l2_error
quantum_vs_analytic.max_abs_error
quantum_cpu_gpu_max_abs_diff_k
```

对 SUPA 报告状态、设备、相对 L2 和一致性；对项目自研核额外报告源码路径和
启动线程数。

## 保存样例

- `results/skill_entry_gpu_validation/`：通过公开 Skill 入口生成的最新端到端结果；
- `results/fast_quantum_validation/`：快速完整链结果；
- `results/natural_language_gpu_validation/`：自然语言 GPU 闭环结果；
- `results/quantum_layer_validation/`：标准尺度量子层结果。

这些结果包包含完整成功的 CPU/GPU 仿真，可在不重新运行 GPU 的情况下复核。
