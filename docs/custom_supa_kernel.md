# 项目自研 SUPA 误差归约核

## 功能

`scripts/supa_error_reduction.su` 直接在壁仞 SUPA 设备上计算：

```text
max_abs_error = max |u_quantum - u_reference|
sum_sq_error  = Σ (u_quantum - u_reference)²
sum_sq_ref    = Σ u_reference²
```

主机端据此得到 RMSE 和相对 L2，并与独立 NumPy 参考结果对照。

## 实现

- 单个 256 线程 block；
- shared-memory 树形归约；
- float32 输入与累加；
- 支持 1–256 个值的一维对齐温度场；
- 输出 JSON，便于 Python 审计层确定性读取。

在壁仞环境中构建：

```bash
bash scripts/build_custom_supa_kernel.sh
```

生成：

```text
build/custom_supa/supa_error_reduction.out
```

在完整工作流中运行：

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli run \
  --input examples/minimal_heat.json \
  --output results/fast_quantum_validation \
  --device gpu \
  --compare-cpu-gpu \
  --validated-profile \
  --supa-audit \
  --custom-supa-audit \
  --error-decomposition
```

## 一致性验证

审计执行两组独立对照：

1. `.su` 核指标与 NumPy float32 归约对照；
2. 端到端 `.su` 核指标与原始主机 float64 数据对照。

快速演示和自然语言 GPU 结果包均保存自研核通过证据，构建与运行日志位于
`results/run_logs/`。
