# 交互 02：不同热扩散率材料响应对比

## 用户输入

> 比较两种热扩散率下的温度衰减曲线，并生成可复核的量子仿真对照结果。

## 任务解析

- 任务：两组 `heat_equation_1d`
- 公共网格、边界和初始温升
- 变量：`thermal_diffusivity_m2_s`
- 输出：温度场、误差、运行时间和材料对照表

## 参数协议与决策

两组实验独立执行并使用一致的空间网格和结果协议，以便直接比较扩散速度与
温度分布。

## 调用命令

```bash
PYTHONPATH=src python3 scripts/run_material_benchmark.py
```

## 真实结果

两组量子实验均完成，温度场、物理审计和汇总 JSON 已生成；较高热扩散率对应
更快的温度衰减，符合热方程解析趋势。

## 生成文件

- `results/benchmarks/higher_diffusivity/result.json`
- `results/benchmarks/lower_diffusivity/result.json`
- `results/benchmarks/material_comparison.json`

## 复核说明

材料对比共享同一受控边界和初始条件，差异直接对应本轮热扩散率设置。

## 最终回答

两种热扩散率的量子温度场与审计结果已完成并汇总，可直接用于材料响应对比图。
