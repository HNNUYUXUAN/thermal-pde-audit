# 一维热传导量子仿真物理审计报告

## 用户任务

使用实测参数档案完成标准热方程量子GPU与SUPA审计闭环

## 参数与单位

| 参数 | SI 值 |
|---|---:|
| `task` | heat_equation_1d |
| `length_m` | 0.01 |
| `thermal_diffusivity_m2_s` | 1.2e-05 |
| `initial_amplitude_k` | 100 |
| `duration_s` | 0.5 |
| `spatial_points` | 32 |
| `time_steps` | 200 |
| `boundary` | dirichlet_zero |
| `initial_condition` | sine_mode_1 |
| `device` | gpu |
| `seed` | 42 |

## 已验证量子参数档案

- 选择方式：`exact_empirical_match`
- 参数：`{'quantum_steps': 32, 'ancilla_qubits': 8, 'auxiliary_range': 16.0, 'recovery_point': 1}`
- 连续通过点：`[16, 32]`
- 证据：`['results/benchmarks/working_region_fo/working_region.json', 'results/benchmarks/working_region_grid/working_region.json', 'results/benchmarks/working_region_gapfill/working_region.json', 'results/run_logs/quantum_working_region_fo_retry.log', 'results/run_logs/quantum_working_region_grid.log', 'results/run_logs/quantum_profile_gapfill.log']`

## 实际量子仿真算法与执行设备

- 状态：`success`
- 后端：`unitarylab_gpu`
- 实际类：`unitarylab_algorithms.schrodingerization.equation_heat.algorithm.HeatEquationAlgorithm`
- 运行时间：`403.02887` s
- 设备信息：`{'requested_device': 'gpu', 'torch': '2.9.0+cu128', 'torch_br': '1.10.0.20900+br1xx', 'unitarylab': '1.0.0', 'unitarylab_algorithms': '1.1.0', 'supa_device_count': 1}`
- 原始返回键：`['circuit', 'grid', 'message', 'plot', 'status', 'u', 'x']`
- 底层设备路由：`[{'device': 'gpu', 'requested_device': 'gpu', 'device_was_injected': True, 'device_matches_requested': True, 'Nt': 32, 'na': 8, 'R': 16, 'order': 2, 'point': 1}]`

量子环节使用 Schrödingerization 的 Trotter 线路把非幺正热扩散演化嵌入幺正演化并在指定 UnitaryLab 后端执行。物理参数先无量纲化，返回场再缩放到米和开尔文。

## 解析解与经典基线

- 解析解：一阶正弦模态的闭式衰减解。
- 经典基线状态：`success`
- 有限差分网格诊断：`{'stable': True, 'stability_ratio': 0.32670000000000005, 'threshold': 0.5, 'dx_m': 0.00030303030303030303, 'dt_s': 0.0025, 'requested_time_steps': 200, 'recommended_min_time_steps': 131}`

## Schrödingerization 误差分层

- 状态：`success`
- 方法：`independent_semi_discrete_reference_with_same_parameter_unitarylab_recovery`
- 同参数非 Trotter 恢复：`success`

| 对照层 | 最大绝对误差 | RMSE | 相对 L2 |
|---|---:|---:|---:|
| 半离散精确演化 vs 连续解析解 | `0.024707934` | `0.017762153` | `0.00044720588` |
| 同参数 schro_classical vs 半离散 | `0.14664139` | `0.10541824` | `0.0026529769` |
| Trotter vs 同参数 schro_classical | `0.24148771` | `0.16915397` | `0.0042456997` |
| Trotter vs 半离散 | `0.094846323` | `0.064149438` | `0.0016143979` |
| Trotter vs 连续解析解 | `0.070138389` | `0.046641087` | `0.0011743041` |
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
| `maximum_principle_range` | `classical` | True | `{'min_k': 0.0, 'max_k': 55.225822132680996}` | `{'min_k': -0.001, 'max_k': 100.001}` |
| `positive_diffusivity_decay` | `classical` | True | `55.225822132680996` | `100.000001` |
| `max_abs_error` | `classical` | True | `0.02375127061227289` | `15.0` |
| `rmse` | `classical` | True | `0.01656462271437014` | `15.0` |
| `relative_l2_error` | `classical` | True | `0.0004298905701749726` | `0.2` |
| `finite_difference_stability` | `classical` | True | `0.32670000000000005` | `0.5` |
| `finite_nonempty_field` | `quantum` | True | `{'size': 32, 'all_finite': True}` | `{'min_size': 1, 'all_finite': True}` |
| `boundary_residual` | `quantum` | True | `0.0` | `1e-08` |
| `maximum_principle_range` | `quantum` | True | `{'min_k': 5.271061509847641, 'max_k': 55.17943501472473}` | `{'min_k': -0.001, 'max_k': 100.001}` |
| `positive_diffusivity_decay` | `quantum` | True | `55.17943501472473` | `100.000001` |
| `max_abs_error` | `quantum` | True | `0.07013838856853738` | `15.0` |
| `rmse` | `quantum` | True | `0.04664108739847566` | `15.0` |
| `relative_l2_error` | `quantum` | True | `0.0011743040749737114` | `0.2` |
| `cpu_gpu_max_difference` | `quantum` | True | `0.0002987682819366455` | `0.001` |
| `schrodingerization_error_decomposition` | `error_decomposition` | True | `{'status': 'success', 'recovery_status': 'success'}` | `{'status': 'success', 'recovery_status': 'success'}` |
| `supa_error_metric_consistency` | `supa_audit` | True | `{'passed': True, 'reduction_vs_roundtrip_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 0.0, 'rmse': 2.461190869162966e-09, 'relative_l2_error': 1.0017510996065959e-10}, 'threshold': 1e-08}, 'end_to_end_vs_source_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 1.364642756129797e-06, 'rmse': 1.5436058615342363e-07, 'relative_l2_error': 4.051818600254997e-09}, 'threshold': 1e-05}, 'host_device_roundtrip_max_abs_k': {'actual': 1.430511474609375e-06, 'reference': 1.6515486365165089e-06}}` | `{'status': 'success', 'reduction_vs_roundtrip_cpu': '1e-8', 'end_to_end_vs_source_cpu': '1e-5'}` |

## SUPA 误差归约

- 状态：`success`
- 后端：`torch_supa_tensor_reduction`
- 设备：`supa:0`
- 数据类型：`float64`
- SUPA 指标：`{'max_abs_error': 0.07013702392578125, 'rmse': 0.04664124175906181, 'relative_l2_error': 0.0011743081267923117}`
- CPU/SUPA 一致性：`{'passed': True, 'reduction_vs_roundtrip_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 0.0, 'rmse': 2.461190869162966e-09, 'relative_l2_error': 1.0017510996065959e-10}, 'threshold': 1e-08}, 'end_to_end_vs_source_cpu': {'passed': True, 'absolute_differences': {'max_abs_error': 1.364642756129797e-06, 'rmse': 1.5436058615342363e-07, 'relative_l2_error': 4.051818600254997e-09}, 'threshold': 1e-05}, 'host_device_roundtrip_max_abs_k': {'actual': 1.430511474609375e-06, 'reference': 1.6515486365165089e-06}}`
- 分段耗时：`{'host_to_device_and_sync': 0.0005806079134345055, 'device_compute_and_sync': 0.8872820967808366, 'device_to_host': 0.00012529687955975533, 'total': 0.8882013438269496}`
- 运行说明：This stage uses torch.supa tensor reduction for the error metrics; the project-owned .su kernel is reported separately.
- 运行说明：The reported runtime includes tensor transfer, device initialization, and reduction for the 32-value field.
- 运行说明：The nominal float64 host/device round trip changed field values by at most 1.65155e-06 K; reduction accuracy is therefore checked separately from transfer quantization.

## 性能

- 量子主后端总调用：`403.02887` s
- CPU 参考总调用：`20.667282` s
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
python3 -m thermal_pde_audit.cli run --input examples/standard_heat.json --output results/quantum_layer_validation --device gpu --quantum-steps 32 --ancilla-qubits 8 --auxiliary-range 16.0 --recovery-point 1 --compare-cpu-gpu --validated-profile --supa-audit --error-decomposition
```
