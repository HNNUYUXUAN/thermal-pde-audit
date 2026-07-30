# 热鉴 · Thermal PDE Audit

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CPU Validation](https://img.shields.io/badge/tests-55%20passed-brightgreen.svg)](.github/workflows/cpu-validation.yml)

**让自然语言描述的热传导问题，成为可在壁仞 GPU 上执行、可用经典方法核验、可由完整证据复现的量子仿真实验。**

`thermal-pde-audit` 面向“量子应用与跨界探索”中的工程仿真与方程求解场景，将
中英文自然语言或结构化参数转换为受控的一维热传导实验，在同一条 Agent/Skill
工作流中完成解析解、经典有限差分、UnitaryLab Schrödingerization CPU/壁仞
GPU 量子线路仿真、双 SUPA 归约、误差分层、物理审计与可复现报告生成。

项目交付的不只是一个求解脚本，而是一套从**问题理解、量子执行到结果验收**
的完整实验产品：每次运行都记录输入、参数、设备路由、数值指标、审计结论、
图表、日志和复现命令，使结果能够被演示、比较和独立复核。

## 作品价值

| 作品能力 | 面向用户的价值 |
|---|---|
| 自然语言实验编排 | 用中文描述长度、热扩散率、温升、时长、网格和设备要求，即可形成规范化实验 |
| 多基线联合验证 | 同轮生成解析解、经典有限差分和量子仿真结果，避免把“成功运行”误当作“结果正确” |
| 壁仞 GPU 真实执行 | 在 Biren106M 竞赛环境完成 UnitaryLab CPU/GPU 同参数复验并记录实际设备路由 |
| 双 SUPA 数值审计 | 同时使用 `torch.supa` 与项目自研 `.su` 归约核计算误差指标，并与 NumPy 独立对照 |
| 量子参数治理 | 基于 14 组实测精确档案自动选择 Trotter 参数，让可复现实验优先使用已验证配置 |
| 误差分层解释 | 区分空间离散、Schrödingerization 恢复、Trotter 演化和设备差异 |
| 证据化交付 | 自动输出 JSON、Markdown、日志、温度图、误差图和量子线路 SVG |
| 开源 Skill 交付 | 采用标准文件夹结构，包含说明、脚本、参考资料和 UI 元数据，可被 Agent 直接读取 |

## 一条完整的量子 PDE 实验链

```text
自然语言 / JSON 实验需求
            ↓
白名单参数协议与 SI 单位归一化
            ↓
解析解 + 显式有限差分基线
            ↓
Fo + 网格规模精确参数档案
            ↓
UnitaryLab CPU / Biren GPU 量子线路仿真
            ↓
半离散参考 + 同参数恢复 + Trotter 误差分层
            ↓
torch.supa + 项目自研 .su 归约核
            ↓
物理审计、报告、图表、日志与复现命令
```

系统将自然语言交互层、物理协议层、经典基线、量子执行、设备审计和证据输出
拆分为可独立测试的模块。完整架构见
[docs/architecture.md](docs/architecture.md)。

## 快速开始

安装开发与验证依赖：

```bash
python3 -m pip install -e ".[dev]"
```

检查当前环境和可用能力：

```bash
python skills/thermal-pde-audit/scripts/doctor.py
```

把自然语言任务转换为规范化实验计划：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "长度10毫米，热扩散率1e-6平方米每秒，初始温升100K，计算0.1秒，使用32个空间点"
```

在竞赛容器中执行 GPU、CPU/GPU 对照、双 SUPA、误差分层和报告生成：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用32个空间点；使用GPU做CPU/GPU对照、双SUPA审计、误差分层并生成报告" \
  --output results/my_thermal_run \
  --full-audit
```

运行预置的完整演示：

```bash
bash skills/thermal-pde-audit/scripts/run-demo.sh
bash skills/thermal-pde-audit/scripts/run-text-demo.sh
```

## 已验证成果

最新公开 Skill 入口已在 Biren106M 竞赛容器完成端到端实跑，覆盖自然语言解析、
解析解、有限差分、UnitaryLab CPU/GPU、`torch.supa`、项目 `.su` 核、
误差分层、物理审计和证据导出。

| 指标 | 实测结果 |
|---|---:|
| 完整工作流状态 | `success` |
| 完整工作流用时 | 约 `35 s` |
| 经典有限差分相对 L2 | `6.47904e-06` |
| GPU 量子仿真相对 L2 | `1.0028122e-04` |
| GPU 最大绝对误差 | `0.00982698 K` |
| CPU/GPU 最大场差 | `1.1324883e-04 K` |
| `torch.supa` 一致性 | 通过 |
| 项目自研 `.su` 核一致性 | 通过 |
| 物理与数值审计 | 全部通过 |

项目同时保存标准尺度 `Fo=0.06`、32 个内部点、32 个 Trotter 时间分片的统一
复验结果，并提供：

- 14 组可由证据反查的精确量子参数档案；
- 7 组覆盖标准运行、材料对比、CPU/GPU 对照、参数治理、双 SUPA 和自然语言
  闭环的 Agent/Skill 交互记录；
- 55 项自动化测试及 GitHub Actions；
- 10 张 Origin 友好 CSV 表、189 行绘图数据和一份已复核 Excel 工作簿。

结果说明见 [docs/results.md](docs/results.md)，原始证据位于：

- `results/skill_entry_gpu_validation/`
- `results/fast_quantum_validation/`
- `results/natural_language_gpu_validation/`
- `results/quantum_layer_validation/`
- `results/origin_data/`

## 每次运行的交付物

```text
input.json
result.json
audit.json
report.md
run.log
temperature_comparison.png
error_decomposition.png
unitarylab_cpu/*.svg
unitarylab_gpu/*.svg
```

这些文件分别回答“输入是什么、实际运行了什么、结果是否通过、如何解释、
如何复现”，构成可机器校验也可供评审阅读的证据闭环。

## Skill 文件夹

```text
skills/thermal-pde-audit/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── algorithm.py
│   ├── doctor.py
│   ├── validate.py
│   └── *.sh
└── references/
    ├── protocol.md
    ├── method.md
    ├── setup.md
    ├── runtime.md
    └── evidence.md
```

示例提示词：

```text
使用 $thermal-pde-audit，把长度 10 mm、热扩散率 1e-6 m²/s、
初始温升 100 K、时长 0.1 s 的一维热传导任务转换为
壁仞 GPU 量子仿真与物理审计报告。
```

## 验证与复现

运行跨平台验证入口：

```bash
python skills/thermal-pde-audit/scripts/validate.py
```

复核已保存的 GPU、双 SUPA、误差分层和自然语言证据：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-result \
  --result-dir results/skill_entry_gpu_validation \
  --require-gpu --require-supa --require-custom-supa \
  --require-error-decomposition --require-natural-language
```

复核精确参数档案与交互证据：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-profiles
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-interactions
```

## 适用范围

当前开源版本聚焦一维线性热方程，采用零源项、零 Dirichlet 边界和一阶正弦
初态，覆盖 4–256 个内部网格点。明确的物理协议让解析解、经典离散、量子恢复
和设备归约能够在同一尺度、同一网格和同一指标体系下比较。

量子计算环节采用 UnitaryLab Algorithms 的热方程 Schrödingerization
实现，并在 UnitaryLab 量子线路模拟器上执行。项目完成自然语言实验编排、
精确参数档案、CPU/GPU 路由适配、经典与解析基线、双 SUPA 归约、物理审计、
证据验证和报告系统。

## 参考与致谢

项目使用和参考 UnitaryLab、UnitaryLab Algorithms、壁仞 SUPA SDK、
PyTorch、NumPy、SciPy 与 Matplotlib。科学依据、论文和软件来源见
[docs/scientific_basis.md](docs/scientific_basis.md) 与
[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)。

## 开源许可

本项目采用 [MIT License](LICENSE)。
