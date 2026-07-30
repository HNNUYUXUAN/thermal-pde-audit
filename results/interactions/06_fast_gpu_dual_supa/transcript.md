# 交互 06：短时 GPU 与双 SUPA 完整演示

## 用户输入

> 用现场演示配置运行一维热传导，调用量子 GPU，并同时完成 torch.supa、
> 项目自研 SUPA 核、误差分层和报告。

## 任务解析

- 长度：`0.01 m`
- 热扩散率：`1e-6 m²/s`
- 初始温升：`100 K`
- 时长：`0.1 s`
- 内部点数：`32`
- 设备：`gpu`

## 参数协议与决策

命中快速档案 `Nt=2, na=8, R=16, point=1`，执行解析、经典、CPU/GPU
量子、半离散参考、双 SUPA、物理审计和图表生成。

## 调用命令

```bash
bash scripts/run_demo.sh
```

## 真实结果

- 完整耗时：`36.143 s`
- GPU 相对 L2：`1.0028122e-04`
- GPU 最大绝对误差：`0.00982698 K`
- CPU/GPU 最大差：`1.1324883e-04 K`
- `torch.supa`：通过
- 自研 `.su` 核：通过
- 物理审计：通过

## 生成文件

- `results/fast_quantum_validation/input.json`
- `results/fast_quantum_validation/result.json`
- `results/fast_quantum_validation/audit.json`
- `results/fast_quantum_validation/report.md`
- `results/fast_quantum_validation/temperature_comparison.png`
- `results/fast_quantum_validation/error_decomposition.png`
- `results/run_logs/final_minimal_gpu_validation_v1.log`
- `results/run_logs/final_minimal_gpu_validation_check_v3.log`

## 复核说明

该配置为快速现场演示档案，完整保留了各计算层和设备归约证据。

## 最终回答

快速 GPU、CPU 对照、双 SUPA、误差分层和报告链全部完成，可直接用于现场展示。
