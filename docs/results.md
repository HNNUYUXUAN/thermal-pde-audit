# 已验证结果

## 公开 Skill 入口端到端验证

公开 Skill 已通过
`skills/thermal-pde-audit/scripts/algorithm.py --full-audit` 在壁仞竞赛容器
完成端到端执行。自然语言需求先被转换为受控实验协议，随后在同一工作流中完成
CPU/GPU 量子仿真、双 SUPA 归约、物理检查、误差分层和证据导出。

| 指标 | 结果 |
|---|---:|
| 工作流状态 | `success` |
| 精确量子档案 | `Nt=2, na=8, R=16, point=1` |
| 完整工作流用时 | `36.143 s` |
| 经典有限差分相对 L2 | `6.47904e-06` |
| GPU 量子仿真相对 L2 | `1.0028122e-04` |
| GPU 最大绝对误差 | `0.00982698 K` |
| CPU/GPU 最大场差 | `1.1324883e-04 K` |
| CPU 量子调用 | `2.48456 s` |
| GPU 量子调用 | `27.97223 s` |
| `torch.supa` 一致性 | 通过 |
| 项目 `.su` 核一致性 | 通过 |
| 物理与数值审计 | 通过 |

证据目录：

- `results/skill_entry_gpu_validation/`

## 快速完整链演示

推荐现场演示采用 10 mm 长度、`1e-6 m²/s` 热扩散率、100 K 初始温升、
0.1 s 时长和 32 个内部点。

| 指标 | 结果 |
|---|---:|
| 精确量子档案 | `Nt=2, na=8, R=16, point=1` |
| 完整命令用时 | `36.143 s` |
| 经典有限差分相对 L2 | `6.47904e-06` |
| GPU 量子仿真相对 L2 | `1.0028122e-04` |
| GPU 最大绝对误差 | `0.00982698 K` |
| CPU/GPU 最大场差 | `1.1324883e-04 K` |
| `torch.supa` 一致性 | 通过 |
| 项目 `.su` 核一致性 | 通过 |
| 物理审计 | 通过 |

证据：

- `results/fast_quantum_validation/`
- `results/run_logs/final_minimal_gpu_validation_v1.log`
- `results/run_logs/final_minimal_gpu_validation_check_v3.log`

## 自然语言 GPU 闭环

保存的自然语言结果包记录原始中文任务、解析后的 SI 参数、所选量子档案、
请求设备、实际设备调用和复现命令。

| 指标 | 结果 |
|---|---:|
| 工作流状态 | `success` |
| 后端 | `unitarylab_gpu` |
| GPU 量子仿真相对 L2 | `1.0028122e-04` |
| CPU/GPU 最大场差 | `1.1324883e-04 K` |
| `torch.supa` | 通过 |
| 项目 `.su` 核 | 通过 |
| 误差分层 | 通过 |
| 保存证据校验 | 通过 |

证据：

- `results/natural_language_gpu_validation/`
- `results/run_logs/natural_language_gpu_validation_v2_plan.log`
- `results/run_logs/natural_language_gpu_validation_v2_plan_check.log`

## 标准尺度验证

标准档案采用 `Fo=0.06`、32 个内部点和 32 个 Trotter 时间分片。

| 指标 | 结果 |
|---|---:|
| GPU 量子仿真相对 L2 | `1.1743041e-03` |
| GPU 最大绝对误差 | `0.07013839 K` |
| CPU/GPU 最大场差 | `2.9876828e-04 K` |
| 半离散参考相对 L2 | `4.4720588e-04` |
| SUPA 端到端最大指标差 | `1.36464e-06` |
| 物理审计 | 通过 |

证据：

- `results/quantum_layer_validation/`
- `results/run_logs/quantum_layer_validation_v2_error_decomposition.log`

## 精确量子参数档案

档案表包含 14 组实测精确配置：

- 32 点网格上的 11 个 Fourier 数；
- `Fo=0.06` 下的 4 种网格规模；
- 合并去重后共 14 组精确配置。

运行：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-profiles
```

将每条策略档案与保存的扫描证据逐一匹配。

## Origin 友好数据

12 张 Origin-ready CSV、222 行绘图数据和一份已复核工作簿提供温度、绝对误差、
误差分层、运行时间、扫描、材料对比、CPU/GPU 场差、SUPA 一致性和自然语言计划数据。详见
[origin_plot_guide.md](origin_plot_guide.md)。
