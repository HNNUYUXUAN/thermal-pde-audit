# 一维热传导量子仿真物理审计报告

## 用户任务

模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用32个空间点和50个时间步；使用GPU做完整验证，进行CPU/GPU对照、SUPA与自定义SUPA审计、误差分层并生成报告

## 自然语言任务解析

- 解析器：`deterministic_whitelist_v1`
- 默认值及来源：`{'boundary': {'value': 'dirichlet_zero', 'source': 'thermal-pde-audit first-round deterministic default'}, 'initial_condition': {'value': 'sine_mode_1', 'source': 'thermal-pde-audit first-round deterministic default'}, 'seed': {'value': 42, 'source': 'thermal-pde-audit first-round deterministic default'}}`
- 安全边界：Natural language was mapped to whitelisted fields only; no shell or Python code was generated or executed.
- 受控参数：`{'task': 'heat_equation_1d', 'length_m': 0.01, 'thermal_diffusivity_m2_s': 1e-06, 'initial_amplitude_k': 100.0, 'duration_s': 0.1, 'spatial_points': 32, 'time_steps': 50, 'boundary': 'dirichlet_zero', 'initial_condition': 'sine_mode_1', 'device': 'gpu', 'seed': 42}`
- 白名单执行计划：`{'compare_cpu_gpu': True, 'validated_profile': True, 'supa_audit': True, 'custom_supa_audit': True, 'error_decomposition': True, 'report_level': 'full', 'sources': {'compare_cpu_gpu': 'natural_language:cpu_gpu_comparison', 'validated_profile': 'safe_default:exact_empirical_profile', 'supa_audit': 'natural_language:full_validation', 'custom_supa_audit': 'natural_language:full_validation', 'error_decomposition': 'natural_language:full_validation', 'report_level': 'natural_language:full_validation'}}`

## 参数与单位

| 参数 | SI 值 |
|---|---:|
| `task` | heat_equation_1d |
| `length_m` | 0.01 |
| `thermal_diffusivity_m2_s` | 1e-06 |
| `initial_amplitude_k` | 100 |
| `duration_s` | 0.1 |
| `spatial_points` | 32 |
| `time_steps` | 50 |
| `boundary` | dirichlet_zero |
| `initial_condition` | sine_mode_1 |
| `device` | gpu |
| `seed` | 42 |

## 已验证量子参数档案

- 选择方式：`exact_empirical_match`
- 参数：`{'quantum_steps': 2, 'ancilla_qubits': 8, 'auxiliary_range': 16.0, 'recovery_point': 1}`
- 连续通过点：`[1, 2]`
- 证据：`['results/benchmarks/working_region_fo/working_region.json', 'results/benchmarks/working_region_grid/working_region.json', 'results/benchmarks/working_region_gapfill/working_region.json', 'results/run_logs/quantum_working_region_fo_retry.log', 'results/run_logs/quantum_working_region_grid.log', 'results/run_logs/quantum_profile_gapfill.log']`

## 实际量子仿真算法与执行设备

- 状态：`success`
- 后端：`unitarylab_gpu`
- 实际类：`unitarylab_algorithms.schrodingerization.equation_heat.algorithm.HeatEquationAlgorithm`
- 运行时间：`26.941588` s
- 设备信息：`{'requested_device': 'gpu', 'torch': '2.9.0+cu128', 'torch_br': '1.10.0.20900+br1xx', 'unitarylab': '1.0.0', 'unitarylab_algorithms': '1.1.0', 'supa_device_count': 1}`
- 原始返回键：`['circuit', 'grid', 'message', 'plot', 'status', 'u', 'x']`
- 底层设备路由：`[{'device': 'gpu', 'requested_device': 'gpu', 'device_was_injected': True, 'device_matches_requested': True, 'Nt': 2, 'na': 8, 'R': 16, 'order': 2, 'point': 1}]`

量子环节使用 Schrödingerization 的 Trotter 线路把非幺正热扩散演化嵌入幺正演化并在指定 UnitaryLab 后端执行。物理参数先无量纲化，返回场再缩放到米和开尔文。

## 解析解与经典基线

- 解析解：一阶正弦模态的闭式衰减解。
- 经典基线状态：`success`
- 有限差分网格诊断：`{'stable': True, 'stability_ratio': 0.02178, 'threshold': 0.5, 'dx_m': 0.00030303030303030303, 'dt_s': 0.002, 'requested_time_steps': 50, 'recommended_min_time_steps': 3}`

## Schrödingerization 误差分层

- 状态：`success`
- 方法：`independent_semi_discrete_reference_with_same_parameter_unitarylab_recovery`
- 同参数非 Trotter 恢复：`success`

| 对照层 | 最大绝对误差 | RMSE | 相对 L2 |
|---|---:|---:|---:|
| 半离散精确演化 vs 连续解析解 | `0.00073702511` | `0.00052983599` | `7.451793e-06` |
| 同参数 schro_classical vs 半离散 | `0.0042761114` | `0.0030740305` | `4.3233886e-05` |
| Trotter vs 同参数 schro_classical | `0.0062878932` | `0.0045933675` | `6.4604991e-05` |
| Trotter vs 半离散 | `0.010564005` | `0.0076590909` | `0.00010771925` |
| Trotter vs 连续解析解 | `0.0098269795` | `0.0071301765` | `0.00010028122` |
- 解释边界：The semi-discrete reference isolates spatial discretization from the continuous analytic solution.
- 解释边界：The same-parameter recovery reference runs schro_classical without Trotter time splitting.
- 解释边界：Trotter-versus-recovery is a diagnostic gap, not an additive error theorem; cancellation can make a downstream field closer to the analytic solution.
- 解释边界：All conclusions are limited to this controlled 1D heat equation and the exact recorded parameter profile.

## 误差与物理审计

- 总体通过：`True`

| 检查 | 目标 | 通过 | 值 | 阈值 |
|---|---|---:|---|---|
| `finite_nonempty_field` | `classical` | True | `{'size': 34, 'all_finite': True}` | `{'min_size': 1, 'all_finite': True}` |
| `boundary_residual` | `classical` | True | `0.0` | `1e-08` |
| `maximum_principle_range` | `classical` | True | `{'min_k': 0.0, 'max_k': 98.90638115602745}` | `{'min_k': -0.001, 'max_k': 100.001}` |
| `positive_diffusivity_decay` | `classical` | True | `98.90638115602745` | `100.000001` |
| `max_abs_error` | `classical` | True | `0.0006408140299640763` | `15.0` |
| `rmse` | `classical` | True | `0.00044691683276772284` | `15.0` |
| `relative_l2_error` | `classical` | True | `6.4790377963601114e-06` | `0.2` |
| `finite_difference_stability` | `classical` | True | `0.02178` | `0.5` |
| `finite_nonempty_field` | `quantum` | True | `{'size': 32, 'all_finite': True}` | `{'min_size': 1, 'all_finite': True}` |
| `boundary_residual` | `quantum` | True | `0.0` | `1e-08` |
| `maximum_principle_range` | `quantum` | True | `{'min_k': 9.412875771522522, 'max_k': 98.89591336250305}` | `{'min_k': -0.001, 'max_k': 100.001}` |
| `positive_diffusivity_decay` | `quantum` | True | `98.89591336250305` | `100.000001` |
| `max_abs_error` | `quantum` | True | `0.009826979494448551` | `15.0` |
| `rmse` | `quantum` | True | `0.007130176547467133` | `15.0` |
| `relative_l2_error` | `quantum` | True | `0.00010028122145663477` | `0.2` |
| `cpu_gpu_max_difference` | `quantum` | True | `0.00011324882507324219` | `0.001` |
| `schrodingerization_error_decomposition` | `error_decomposition` | True | `{'status': 'success', 'recovery_status': 'success'}` | `{'status': 'success', 'recovery_status': 'success'}` |
| `supa_error_metric_consistency` | `supa_audit` | True | `{'passed': True, 'reduction_vs_roundtrip_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 0.0, 'rmse': 9.985290545799774e-11, 'relative_l2_error': 9.69388710470899e-12}, 'threshold': 1e-08}, 'end_to_end_vs_source_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 3.1933819855112233e-07, 'rmse': 3.3595457730670186e-07, 'relative_l2_error': 4.735703305387305e-09}, 'threshold': 1e-05}, 'host_device_roundtrip_max_abs_k': {'actual': 3.5762786865234375e-06, 'reference': 3.085959548343453e-06}}` | `{'status': 'success', 'reduction_vs_roundtrip_cpu': '1e-8', 'end_to_end_vs_source_cpu': '1e-5'}` |
| `custom_supa_error_metric_consistency` | `custom_supa_audit` | True | `{'passed': True, 'kernel_vs_float32_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 0.0, 'rmse': 9.985734461537277e-11, 'relative_l2_error': 2.417946946180541e-12}, 'threshold': 1e-06}, 'end_to_end_vs_source_float64_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 3.1933819855112233e-07, 'rmse': 3.359545728675445e-07, 'relative_l2_error': 4.728427365228776e-09}, 'threshold': 1e-05}}` | `{'status': 'success', 'kernel_vs_float32_cpu': '1e-6', 'end_to_end_vs_source_float64_cpu': '1e-5'}` |

## SUPA 误差归约

- 状态：`success`
- 后端：`torch_supa_tensor_reduction`
- 设备：`supa:0`
- 数据类型：`float64`
- SUPA 指标：`{'max_abs_error': 0.00982666015625, 'rmse': 0.007130512502044439, 'relative_l2_error': 0.00010028595715994015}`
- CPU/SUPA 一致性：`{'passed': True, 'reduction_vs_roundtrip_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 0.0, 'rmse': 9.985290545799774e-11, 'relative_l2_error': 9.69388710470899e-12}, 'threshold': 1e-08}, 'end_to_end_vs_source_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 3.1933819855112233e-07, 'rmse': 3.3595457730670186e-07, 'relative_l2_error': 4.735703305387305e-09}, 'threshold': 1e-05}, 'host_device_roundtrip_max_abs_k': {'actual': 3.5762786865234375e-06, 'reference': 3.085959548343453e-06}}`
- 分段耗时：`{'host_to_device_and_sync': 0.0005776160396635532, 'device_compute_and_sync': 0.890979636926204, 'device_to_host': 0.00012938817963004112, 'total': 0.8918812638148665}`
- 运行说明：This stage uses torch.supa tensor reduction for the error metrics; the project-owned .su kernel is reported separately.
- 运行说明：The reported runtime includes tensor transfer, device initialization, and reduction for the 32-value field.
- 运行说明：The nominal float64 host/device round trip changed field values by at most 3.57628e-06 K; reduction accuracy is therefore checked separately from transfer quantization.

## 自定义 SUPA 误差归约核

- 状态：`success`
- 源码：`scripts/supa_error_reduction.su`
- 设备：`supa:0`
- 数据类型：`float32`
- 核指标：`{'max_abs_error': 0.00982666015625, 'rmse': 0.00713051250204, 'relative_l2_error': 0.000100285949884}`
- CPU/自定义核一致性：`{'passed': True, 'kernel_vs_float32_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 0.0, 'rmse': 9.985734461537277e-11, 'relative_l2_error': 2.417946946180541e-12}, 'threshold': 1e-06}, 'end_to_end_vs_source_float64_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 3.1933819855112233e-07, 'rmse': 3.359545728675445e-07, 'relative_l2_error': 4.728427365228776e-09}, 'threshold': 1e-05}}`
- 进程耗时：`{'subprocess_total': 0.01988664921373129}`
- 配置：The custom kernel is optimized for fields of up to 256 values using one 256-thread SUPA block and shared-memory tree reduction.
- 实现说明：The kernel accumulates in float32. Independent float32 and source-float64 checks use separate tolerances.

## 性能

- 量子主后端总调用：`26.941588` s
- CPU 参考总调用：`2.4099365` s
- 运行时间完整计入后端初始化、编译、执行与数据传输，便于复现实验进行同口径对照。

## 结论

本次结果通过所列阈值。

## 实验配置与适用范围

- 当前实验协议：一维、零源、Dirichlet 零边界和一阶正弦初态。
- UnitaryLab 返回的是内部网格点；边界值由受控协议施加。
- 项目适配层在进程锁保护下完成设备参数透传、记录并恢复原函数。
- 报告聚焦热方程结果、误差分解、后端路由和物理一致性。
- 运行说明：The adapter routed and recorded the requested device under a process-wide lock, then restored the upstream function; compatibility injection count: 1.
- 运行说明：UnitaryLab supplies the interior nodes, and the controlled experiment protocol supplies the zero Dirichlet boundaries.
- 运行说明：The workflow nondimensionalizes the physical problem before the UnitaryLab call and restores metres and kelvin afterward.

## 复现命令

```bash
python3 -m thermal_pde_audit.cli run --input results/natural_language_gpu_validation/input.json --output results/natural_language_gpu_validation --device gpu --quantum-steps 2 --ancilla-qubits 8 --auxiliary-range 16.0 --recovery-point 1 --compare-cpu-gpu --validated-profile --supa-audit --custom-supa-audit --error-decomposition
```
