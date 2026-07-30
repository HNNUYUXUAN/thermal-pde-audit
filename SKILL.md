---
name: thermal-pde-audit
description: 将结构化或中英文自然语言的一维热传导任务转化为带物理审计的可复现实验，联合解析解、显式有限差分、UnitaryLab Schrödingerization CPU/壁仞 GPU 量子线路仿真、torch.supa 与项目自研 SUPA 归约、误差分层和证据报告。适用于热传导 PDE 仿真、CPU/GPU 对照、量子方程求解演示、结果复核与竞赛实验复现。
---

# 热鉴 · Thermal PDE Audit

**把自然语言描述的热传导问题，转化为可在壁仞 GPU 上执行、可用经典方法核验、可由完整证据复现的量子仿真实验。**

热鉴面向“量子应用与跨界探索”中的工程仿真与方程求解场景。输入一段中文、
英文或结构化的一维热传导需求，Skill 即可完成参数理解、物理建模、经典基线、
UnitaryLab Schrödingerization CPU/壁仞 GPU 量子线路仿真、双 SUPA 归约、
误差分层、物理审计与可复现报告生成。

这是一套从**问题理解、量子执行到结果验收**的完整实验工作流。每次运行都
记录输入、量子参数、实际设备路由、数值指标、审计结论、图表、日志和复现
命令，使实验既适合现场演示，也能够被评审和研究者独立复核。

## 核心价值

| 能力 | 作品实现 |
|---|---|
| 自然语言驱动实验 | 确定性解析中英文长度、热扩散率、温升、时长、网格与设备要求 |
| 多基线联合验证 | 同轮生成解析解、显式有限差分与量子仿真结果 |
| 壁仞 GPU 真实执行 | 在 Biren106M 竞赛环境完成 UnitaryLab CPU/GPU 同参数复验 |
| 双 SUPA 审计 | `torch.supa` 张量归约 + 项目自研 `.su` 并行归约核 |
| 精确量子参数治理 | 依据 14 组实测档案自动选择 Trotter 参数 |
| 分层误差解释 | 区分空间离散、Schrödingerization 恢复、Trotter 与设备差异 |
| 证据化成果交付 | 自动生成 JSON、Markdown、日志、对比图、误差图与线路 SVG |
| 标准 Skill 结构 | 包含 `SKILL.md`、执行脚本、参考资料和 Agent UI 元数据 |

## 完整工作流

```text
自然语言 / JSON 实验需求
            ↓
白名单参数协议与 SI 单位归一化
            ↓
解析解 + 显式有限差分基线
            ↓
Fo + 网格规模精确量子参数档案
            ↓
UnitaryLab CPU / Biren GPU 量子线路仿真
            ↓
半离散参考 + 同参数恢复 + Trotter 误差分层
            ↓
torch.supa + 项目自研 .su 归约核
            ↓
物理审计、报告、图表、日志与复现命令
```

## 立即体验

检查环境：

```bash
python skills/thermal-pde-audit/scripts/doctor.py
```

把自然语言转化为规范化实验计划：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "长度10毫米，热扩散率1e-6平方米每秒，初始温升100K，计算0.1秒，使用32个空间点"
```

执行 GPU、CPU/GPU 对照、双 SUPA、误差分层与报告生成：

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用32个空间点；使用GPU做CPU/GPU对照、双SUPA审计、误差分层并生成报告" \
  --output results/my_thermal_run \
  --full-audit
```

运行预置现场演示：

```bash
bash skills/thermal-pde-audit/scripts/run-demo.sh
bash skills/thermal-pde-audit/scripts/run-text-demo.sh
```

## 已验证成果

最新公开 Skill 入口已在 Biren106M 竞赛容器完成端到端实跑：

| 指标 | 实测结果 |
|---|---:|
| 完整工作流状态 | `success` |
| 完整工作流用时 | `36.143 s` |
| 经典有限差分相对 L2 | `6.47904e-06` |
| GPU 量子仿真相对 L2 | `1.0028122e-04` |
| GPU 最大绝对误差 | `0.00982698 K` |
| CPU/GPU 最大场差 | `1.1324883e-04 K` |
| `torch.supa` 一致性 | 通过 |
| 项目自研 `.su` 核一致性 | 通过 |
| 物理与数值审计 | 全部通过 |

当前开源成果同时包含：

- 14 组可由保存证据反查的精确量子参数档案；
- 7 组差异化 Agent/Skill 交互记录；
- 55 项自动化测试与 GitHub Actions；
- 12 张 Origin-ready CSV 表、222 行绘图数据和已复核 Excel 工作簿；
- 快速演示、自然语言闭环和标准尺度量子层三类完整结果包。

## 执行 Skill

可复用 Skill 位于
[`skills/thermal-pde-audit/`](skills/thermal-pde-audit/)。每次处理新需求：

1. 阅读 [输入协议](skills/thermal-pde-audit/references/protocol.md)；
2. 按任务运行自然语言或结构化实验入口；
3. 在壁仞 GPU 运行前阅读
   [运行环境](skills/thermal-pde-audit/references/runtime.md)；
4. 使用 [证据契约](skills/thermal-pde-audit/references/evidence.md)
   验证成果；
5. 按物理输入、量子参数、经典基线、CPU/GPU、误差分层、SUPA、
   审计结论和复现命令的顺序报告结果。

完整自然语言实验将依次执行：

1. 解析任务并记录原始需求；
2. 转换为 SI 单位和受控实验协议；
3. 计算解析解与显式有限差分基线；
4. 选择 `Fo + spatial_points` 对应的精确量子档案；
5. 执行 UnitaryLab CPU/壁仞 GPU Schrödingerization 仿真；
6. 构造半离散参考、同参数恢复和 Trotter 误差分层；
7. 使用 `torch.supa` 和项目 `.su` 核重复计算误差；
8. 完成物理与数值审计；
9. 输出成果包和受控复现命令。

## 成果文件

每次完整运行生成：

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
如何复现”，构成面向 Agent、研究者和评审的统一证据闭环。

## 验证保存结果

运行跨平台验证：

```bash
python skills/thermal-pde-audit/scripts/validate.py
```

复核已保存的 GPU、双 SUPA、误差分层和自然语言成果：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-result \
  --result-dir results/skill_entry_gpu_validation \
  --require-gpu --require-supa --require-custom-supa \
  --require-error-decomposition --require-natural-language
```

## 适用范围与实现归属

当前开源版本聚焦一维线性热方程，采用零源项、零 Dirichlet 边界和一阶正弦
初态，覆盖 4–256 个内部网格点。明确的科学协议使解析解、经典离散、量子恢复
和设备归约能够在同一尺度、同一网格与同一指标体系下比较。

量子计算环节采用 UnitaryLab Algorithms 的热方程 Schrödingerization
实现，并在 UnitaryLab 量子线路模拟器上执行。本项目完成自然语言实验编排、
量子参数治理、CPU/GPU 路由适配、解析与经典基线、双 SUPA 归约、物理审计、
证据验证和报告系统。

运行分工为：Biren GPU/SUPA 承担量子线路、状态向量张量计算与误差归约，
CPU 承担流程控制和后处理。

项目源码、结果证据、科学依据与复现入口均已随本目录开源发布。
