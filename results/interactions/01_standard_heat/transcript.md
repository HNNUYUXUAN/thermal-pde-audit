# 交互 01：标准尺度量子热方程统一验证

## 用户输入

> 请用标准尺度参数完成一维热传导 CPU/GPU 量子仿真，并给出解析、经典、
> 误差分层和 SUPA 审计结果。

## 任务解析

- 任务：`heat_equation_1d`
- Fourier 数：`0.06`
- 内部点数：`32`
- 设备：`gpu`
- 执行：CPU/GPU 对照、精确档案、SUPA、误差分层

## 参数协议与决策

命中精确实测档案 `Nt=32, na=8, R=16, point=1`。物理输入统一转换为 SI，
量子层使用无量纲长度和时间。

## 调用命令

```bash
bash scripts/run_quantum_layer_validation.sh
```

## 真实结果

- UnitaryLab CPU/GPU：成功
- GPU 相对 L2：`1.1743041e-03`
- GPU 最大绝对误差：`0.07013839 K`
- CPU/GPU 最大差：`2.9876828e-04 K`
- 半离散参考相对解析解：`4.4720588e-04`
- SUPA 一致性：通过
- 物理审计：通过

## 生成文件

- `results/quantum_layer_validation/result.json`
- `results/quantum_layer_validation/audit.json`
- `results/quantum_layer_validation/report.md`
- `results/quantum_layer_validation/temperature_comparison.png`
- `results/quantum_layer_validation/error_decomposition.png`
- `results/run_logs/quantum_layer_validation_v2_error_decomposition.log`

## 复核说明

本结果对应已记录的标准物理协议和精确量子档案，复现时使用同一环境与参数。

## 最终回答

标准尺度 CPU/GPU 量子热方程仿真、独立参考、误差分层和 SUPA 审计全部完成，
结果具备完整字段、图像、线路和日志证据。
