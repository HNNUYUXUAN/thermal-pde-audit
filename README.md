# 热鉴 · Thermal PDE Audit

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CPU Validation](https://img.shields.io/badge/tests-55%20passed-brightgreen.svg)](.github/workflows/cpu-validation.yml)

面向一维热传导问题的物理约束量子仿真与证据审计 Skill。项目将自然语言任务
转换为结构化热方程实验，在同一条工作流中完成解析解、经典有限差分、
UnitaryLab Schrödingerization CPU/GPU 仿真、SUPA 数值归约、误差分层和
可复现报告生成。

## 项目亮点

| 能力 | 实现 |
|---|---|
| 自然语言实验编排 | 确定性解析中英文长度、热扩散率、温升、时长、网格和设备要求 |
| 三路结果对照 | 解析解、显式有限差分、UnitaryLab 量子线路仿真 |
| 壁仞 GPU 实跑 | Biren106M 上完成 CPU/GPU 同参数串行复验 |
| 双 SUPA 审计 | `torch.supa` 张量归约 + 项目自研 `.su` 并行归约核 |
| 物理正确性检查 | 有限性、边界、最大值原理、衰减、稳定性和多层误差指标 |
| 量子参数治理 | 14 组实测精确档案，自动选择对应 Trotter 参数 |
| 完整证据包 | JSON、Markdown、日志、温度图、误差分层图和线路 SVG |
| Skill 开源交付 | 标准文件夹结构，可由 Agent 直接读取和调用 |

## 工作流

```text
自然语言 / JSON 实验
        ↓
受控参数协议与单位归一化
        ↓
解析解 + 经典有限差分基线
        ↓
精确量子参数档案选择
        ↓
UnitaryLab CPU / Biren GPU
        ↓
半离散参考 + Trotter 误差分层
        ↓
torch.supa + 自研 .su 核
        ↓
物理审计、报告与可视化
```

架构与模块映射见 [docs/architecture.md](docs/architecture.md)。

## 快速开始

安装 CPU 侧依赖：

```bash
python3 -m pip install -e ".[test]"
```

运行测试与框架无关验证：

```bash
PYTHONPATH=src python3 -m pytest -q
bash scripts/run_validation.sh
```

查看能力：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli capabilities
```

解析自然语言任务：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli parse \
  --text "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用GPU并生成验证报告"
```

## 壁仞 GPU 完整演示

竞赛容器已提供 UnitaryLab、PyTorch、`torch_br`、Biren SUPA SDK 与 `brcc`。
在该环境中运行：

```bash
bash scripts/run_demo.sh
```

自然语言直接驱动同一条完整链：

```bash
bash scripts/run_text_demo.sh
```

一次运行生成：

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

## 实测结果

最新结果由公开 Skill 的 `algorithm.py --full-audit` 入口在 Biren106M
竞赛容器中生成，使用 `Fo=0.001`、32 个内部点和 2 个 Trotter 时间分片：

| 指标 | 实测值 |
|---|---:|
| 完整工作流耗时 | `35 s` |
| GPU 相对 L2 | `1.0028122e-04` |
| GPU 最大绝对误差 | `0.00982698 K` |
| CPU/GPU 最大差 | `1.1324883e-04 K` |
| CPU 量子调用 | `2.48456 s` |
| GPU 量子调用 | `27.97223 s` |
| `torch.supa` 一致性 | 通过 |
| 自研 `.su` 核一致性 | 通过 |
| 物理与数值审计 | 全部通过 |

标准尺度 `Fo=0.06` 使用 32 个 Trotter 时间分片，CPU/GPU、误差分层和 SUPA
统一复验同样通过。完整结果说明见 [docs/results.md](docs/results.md)，可复核
数据位于：

- `results/skill_entry_gpu_validation/`（最新 Skill 入口完整实跑）
- `results/fast_quantum_validation/`
- `results/natural_language_gpu_validation/`
- `results/quantum_layer_validation/`
- `results/origin_data/`

## Skill 文件夹

公开 Skill 位于：

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

它包含 Agent 执行流程、输入协议、运行入口、结果契约和壁仞环境说明。
[`skills/thermal-pde-audit/`](skills/thermal-pde-audit/) 是仓库唯一的
Skill 发布入口。

跨平台自检与验证：

```bash
python skills/thermal-pde-audit/scripts/doctor.py
python skills/thermal-pde-audit/scripts/validate.py
```

示例调用：

```text
使用 $thermal-pde-audit，把长度 10 mm、热扩散率 1e-6 m²/s、
初始温升 100 K、时长 0.1 s 的热传导任务转换为 GPU 审计报告。
```

## 仓库结构

```text
thermal-pde-audit/
├── skills/                    # 可安装的 Skill 包
├── src/thermal_pde_audit/     # 核心 Python 实现
├── scripts/                   # 演示、验证、SUPA 与绘图脚本
├── examples/                  # 结构化输入示例
├── tests/                     # 55 项 CPU 侧测试
├── results/                   # 已保存的真实运行证据
├── outputs/                   # Origin 友好工作簿
└── docs/                      # 架构、科学依据与结果说明
```

## 结果复核

验证保存的 GPU、双 SUPA、误差分层和自然语言闭环：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-result \
  --result-dir results/skill_entry_gpu_validation \
  --require-gpu --require-supa --require-custom-supa \
  --require-error-decomposition --require-natural-language
```

验证 14 组量子参数档案和 7 段 Agent/Skill 交互：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-profiles
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-interactions
```

## 技术范围

当前开源版本聚焦一维、线性、零源项、零 Dirichlet 边界和一阶正弦初态，
覆盖 4–256 个内部网格点。这个明确的物理协议使解析基线、经典离散、量子
恢复与设备归约能够在统一指标下直接比较。

项目运行的是壁仞 GPU 上的量子线路仿真。量子计算环节由 UnitaryLab
Schrödingerization 提供，项目重点实现自然语言实验编排、设备路由适配、
物理审计、量子参数治理、双 SUPA 验证和完整证据链。

## 参考与致谢

项目使用和参考了 UnitaryLab、UnitaryLab Algorithms、Biren SUPA SDK、
PyTorch、NumPy、SciPy 与 Matplotlib。完整来源和论文链接见
[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) 与
[docs/scientific_basis.md](docs/scientific_basis.md)。

## License

本项目以 [MIT License](LICENSE) 开源。
