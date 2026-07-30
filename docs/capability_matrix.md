# 平台与运行能力

## 已验证环境

| 组件 | 实测值 |
|---|---|
| 平台 | 壁仞竞赛容器 |
| 设备 | Biren106M |
| Python | 3.10.12 |
| PyTorch | 2.9.0+cu128 |
| `torch_br` | 1.10.0.20900+br1xx |
| UnitaryLab | 1.0.0 |
| UnitaryLab Algorithms | 1.1.0 |
| SUPA 设备 | `torch.supa.device_count() = 1` |
| SUPA 编译器 | 壁仞 SUPA SDK 提供的 `brcc` |

完整环境探测记录位于 `results/run_logs/environment_probe.log`。

## 能力矩阵

| 能力 | 入口 | 证据 |
|---|---|---|
| 热方程解析解 | `classical_solver.solve_analytic` | 自动化测试与结果包 |
| 显式有限差分 | `classical_solver.solve_classical` | 稳定性和精度检查 |
| UnitaryLab CPU | `HeatEquationAlgorithm` | CPU 日志、线路 SVG、温度场 |
| UnitaryLab GPU | 设备路由后的 `HeatEquationAlgorithm` | GPU 日志、路由元数据、温度场 |
| CPU/GPU 对照 | CLI `--compare-cpu-gpu` | 最大场差 |
| 精确档案选择 | CLI `recommend` / `--validated-profile` | 14 组保存档案 |
| 误差分层 | CLI `--error-decomposition` | JSON 指标与 PNG |
| `torch.supa` 审计 | CLI `--supa-audit` | `supa:0` 指标与 NumPy 对照 |
| 自研 `.su` 核审计 | CLI `--custom-supa-audit` | 编译核结果与审计 |
| 自然语言执行 | CLI `plan-text` / `run-text` | 解析计划与完整成果 |
| 证据验证 | CLI `validate-result` | 结构化校验结果 |

## 代表性实验档案

- **快速演示档案：** `Fo=0.001`、32 个内部点、`Nt=2`，最新 Skill 入口完整
  工作流实测 36.143 秒完成。
- **标准验证档案：** `Fo=0.06`、32 个内部点、`Nt=32`，保存完整 CPU/GPU、
  SUPA 和误差分层证据。

GPU 与 SUPA 阶段采用串行执行，使每份结果都能对应到唯一实验和明确设备路由。
最新端到端证据位于 `results/skill_entry_gpu_validation/`。

## 本地与云端协同

标准 Python 工作站可运行自然语言解析、Schema 校验、解析解、有限差分、
档案验证、保存证据验证和全部 55 项测试。预配置壁仞竞赛容器用于执行
UnitaryLab GPU、CPU/GPU 对照和双 SUPA 工作流。
