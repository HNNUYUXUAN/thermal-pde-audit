---
name: thermal-pde-audit
description: 将结构化或中英文自然语言的一维热传导任务转化为带物理审计的可复现实验，联合解析解、显式有限差分、UnitaryLab Schrödingerization CPU/壁仞 GPU 量子线路仿真、torch.supa 与项目自研 SUPA 归约、误差分层和证据报告。适用于热传导 PDE 仿真、CPU/GPU 对照、量子方程求解演示、结果复核与竞赛实验复现。
---

# 热鉴 · Thermal PDE Audit

把一维热传导需求转化为可执行、可核验、可复现的量子仿真实验，并返回计算
结果、物理审计、图表、日志和复现命令。

## 先选择工作方式

1. 处理自然语言需求时，使用 `--text` 规划或执行实验。
2. 处理结构化实验时，使用 `--input` 读取 JSON 参数。
3. 进行现场展示时，运行预置的 CPU/GPU/SUPA 完整演示。
4. 复核已有成果时，验证保存的结果包，无需重新占用 GPU。

首次运行前执行环境诊断：

```bash
python skills/thermal-pde-audit/scripts/doctor.py
```

根据任务按需阅读：

- 每次新输入都阅读 [references/protocol.md](references/protocol.md)；
- 解释物理与量子方法时阅读 [references/method.md](references/method.md)；
- 准备项目环境时阅读 [references/setup.md](references/setup.md)；
- 执行壁仞 GPU 任务前阅读 [references/runtime.md](references/runtime.md)；
- 复核结果与指标时阅读 [references/evidence.md](references/evidence.md)。

## 规划自然语言实验

运行：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "长度10毫米，热扩散率1e-6平方米每秒，初始温升100K，计算0.1秒，使用32个空间点"
```

将输入映射到受控实验协议，统一转换为 SI 单位，并返回规范化参数和执行计划。
遇到关键物理量缺失或冲突时，返回聚焦的澄清问题。

## 执行完整自然语言实验

运行：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用32个空间点；使用GPU做CPU/GPU对照、双SUPA审计、误差分层并生成报告" \
  --output results/my_thermal_run \
  --full-audit
```

执行以下完整链路：

1. 解析自然语言并记录原始需求；
2. 归一化物理参数和单位；
3. 生成解析解与显式有限差分基线；
4. 根据 `Fo + spatial_points` 选择实测精确量子参数档案；
5. 执行 UnitaryLab CPU/壁仞 GPU Schrödingerization 量子线路仿真；
6. 生成半离散参考、同参数恢复与 Trotter 误差分层；
7. 使用 `torch.supa` 和项目自研 `.su` 核计算误差指标；
8. 完成物理与数值审计；
9. 保存报告、日志、图表、线路和复现命令。

确认 `result.json` 记录：

- 原始任务与规范化 SI 参数；
- 量子参数档案及其证据来源；
- 请求设备、实际设备和底层路由记录；
- 已执行的审计阶段和关键指标；
- 基于 `input.json` 的受控复现命令。

## 执行结构化实验

先检查推荐的精确量子档案：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --input examples/standard_heat.json
```

再执行完整实验：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --input examples/standard_heat.json \
  --output results/my_standard_run \
  --device gpu \
  --full-audit
```

## 运行现场演示

运行快速完整链：

```bash
bash skills/thermal-pde-audit/scripts/run-demo.sh
```

运行自然语言完整链：

```bash
bash skills/thermal-pde-audit/scripts/run-text-demo.sh
```

演示同时覆盖解析解、经典有限差分、UnitaryLab CPU/GPU、误差分层、
`torch.supa`、项目 `.su` 核、物理审计、报告和图表。

## 验证项目与证据

运行跨平台验证入口：

```bash
python skills/thermal-pde-audit/scripts/validate.py
```

在 Linux 或竞赛容器中也可运行：

```bash
bash skills/thermal-pde-audit/scripts/validate.sh
```

开发验证：

```bash
ruff check src tests scripts
mypy src scripts tests
pytest -q
```

复核保存的完整结果：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-result \
  --result-dir results/skill_entry_gpu_validation \
  --require-gpu --require-supa --require-custom-supa \
  --require-error-decomposition --require-natural-language
```

## 输出实验成果

确保完整运行至少生成：

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

报告结果时依次给出：

1. 物理输入与 SI 单位；
2. 数值参数与量子参数档案；
3. 解析解与经典有限差分基线；
4. CPU/GPU 量子仿真结果；
5. 半离散、恢复与 Trotter 误差分层；
6. `torch.supa` 与项目 `.su` 核一致性；
7. 物理审计结论；
8. 生成文件与复现命令。

至少返回一个数值验证指标，以及 `result.json`、`audit.json` 和 `report.md`
的保存路径。执行用户要求的演示或验证，不停留在命令规划阶段。

## 使用已验证的科学协议

在以下协议内执行实验：

- 一维线性热方程；
- 正热扩散率；
- 零源项和零 Dirichlet 边界；
- 一阶正弦初始温度；
- 4–256 个内部网格点；
- CPU 或壁仞 GPU 量子线路仿真。

对协议外需求，先说明最接近的可验证实验映射，再请求用户确认。

将量子层表述为 UnitaryLab 量子线路模拟器上的 Schrödingerization 热方程
仿真。将热方程 Schrödingerization 实现归属于 UnitaryLab Algorithms；
将自然语言编排、参数治理、设备路由、经典基线、双 SUPA、物理审计、证据
验证和报告系统归属于本项目。
