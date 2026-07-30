# 交互 03：UnitaryLab CPU/GPU 一致性对照

## 用户输入

> 使用同一组热方程和量子参数分别运行 CPU 与壁仞 GPU，并比较最终温度场。

## 任务解析

- 输入：`examples/minimal_heat.json`
- 设备：CPU 与 GPU
- 比较：逐点温度差、最大差、解析误差和路由记录

## 参数协议与决策

两端使用同一精确档案 `Nt=2, na=8, R=16, point=1`，串行执行并分别保存
UnitaryLab 日志、线路图和解图。

## 调用命令

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli run \
  --input examples/minimal_heat.json \
  --output results/fast_quantum_validation \
  --device gpu --compare-cpu-gpu --validated-profile
```

## 真实结果

- CPU/GPU 状态：成功
- CPU/GPU 最大温度差：`1.1324883e-04 K`
- GPU 路由记录：`device=gpu`
- 路由恢复与资源清理：通过

## 生成文件

- `results/fast_quantum_validation/result.json`
- `results/fast_quantum_validation/unitarylab_cpu/algorithm.log`
- `results/fast_quantum_validation/unitarylab_gpu/algorithm.log`

## 复核说明

CPU/GPU 对照使用相同离散和量子参数，指标用于验证两端执行一致性。

## 最终回答

CPU 与壁仞 GPU 均完成真实量子线路仿真，逐点温度场高度一致，设备路由和
生成产物可从结果 JSON 与两端日志复核。
