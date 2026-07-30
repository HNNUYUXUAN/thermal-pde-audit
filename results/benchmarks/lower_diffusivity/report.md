# 一维热传导量子仿真物理审计报告

## 用户任务

Compare material case lower_diffusivity with diffusivity 5e-07 m^2/s

## 参数与单位

| 参数 | SI 值 |
|---|---:|
| `task` | heat_equation_1d |
| `length_m` | 0.01 |
| `thermal_diffusivity_m2_s` | 5e-07 |
| `initial_amplitude_k` | 100 |
| `duration_s` | 0.1 |
| `spatial_points` | 32 |
| `time_steps` | 50 |
| `boundary` | dirichlet_zero |
| `initial_condition` | sine_mode_1 |
| `device` | gpu |
| `seed` | 42 |

## 真实量子算法与设备

- 状态：`success`
- 后端：`unitarylab_gpu`
- 实际类：`unitarylab_algorithms.schrodingerization.equation_heat.algorithm.HeatEquationAlgorithm`
- 运行时间：`2.7236577` s
- 设备信息：`{'requested_device': 'gpu', 'torch': '2.9.0+cu128', 'torch_br': '1.10.0.20900+br1xx', 'unitarylab': '1.0.0', 'unitarylab_algorithms': '1.1.0', 'supa_device_count': 1}`
- 原始返回键：`['circuit', 'grid', 'message', 'plot', 'status', 'u', 'x']`
- 底层设备路由：`[{'device': 'gpu', 'Nt': 1, 'na': 5, 'R': 4, 'order': 2, 'point': 1}]`

量子环节使用 Schrödingerization 的 Trotter 线路把非幺正热扩散演化嵌入幺正演化并在指定 UnitaryLab 后端执行。物理参数先无量纲化，返回场再缩放到米和开尔文。

## 解析解与经典基线

- 解析解：一阶正弦模态的闭式衰减解。
- 经典基线状态：`success`
- 有限差分网格诊断：`{'stable': True, 'stability_ratio': 0.01089, 'threshold': 0.5, 'dx_m': 0.00030303030303030303, 'dt_s': 0.002, 'requested_time_steps': 50, 'recommended_min_time_steps': 2}`

## 误差与物理审计

- 总体通过：`True`

| 检查 | 目标 | 通过 | 值 | 阈值 |
|---|---|---:|---|---|
| `finite_nonempty_field` | `classical` | True | `{'size': 34, 'all_finite': True}` | `{'min_size': 1, 'all_finite': True}` |
| `boundary_residual` | `classical` | True | `0.0` | `1e-08` |
| `maximum_principle_range` | `classical` | True | `{'min_k': 0.0, 'max_k': 99.3953730450973}` | `{'min_k': -0.001, 'max_k': 100.001}` |
| `positive_diffusivity_decay` | `classical` | True | `99.3953730450973` | `100.000001` |
| `max_abs_error` | `classical` | True | `0.0003461648068849854` | `15.0` |
| `rmse` | `classical` | True | `0.0002414224281600979` | `15.0` |
| `relative_l2_error` | `classical` | True | `3.4827175740433458e-06` | `0.2` |
| `finite_difference_stability` | `classical` | True | `0.01089` | `0.5` |
| `finite_nonempty_field` | `quantum` | True | `{'size': 32, 'all_finite': True}` | `{'min_size': 1, 'all_finite': True}` |
| `boundary_residual` | `quantum` | True | `0.0` | `1e-08` |
| `maximum_principle_range` | `quantum` | True | `{'min_k': 9.481941163539886, 'max_k': 99.48055148124695}` | `{'min_k': -0.001, 'max_k': 100.001}` |
| `positive_diffusivity_decay` | `quantum` | True | `99.48055148124695` | `100.000001` |
| `max_abs_error` | `quantum` | True | `0.08552460095653203` | `15.0` |
| `rmse` | `quantum` | True | `0.0622550565826788` | `15.0` |
| `relative_l2_error` | `quantum` | True | `0.0008712660802486498` | `0.2` |

## 性能

- 量子主后端总调用：`2.7236577` s
- CPU 参考总调用：`None` s
- 小规模 GPU 若慢于 CPU，原因可能包括后端初始化、编译和数据迁移；本报告不据此宣称量子或 GPU 加速。

## 结论

本次结果通过所列阈值。

## 实验配置与适用范围

- 当前实验协议：一维、零源、Dirichlet 零边界和一阶正弦初态。
- UnitaryLab 返回的是内部网格点；边界值由受控协议施加。
- 项目适配层完成设备参数透传并在调用后恢复。
- 报告聚焦热方程结果、后端路由和物理一致性。
- 运行说明：The adapter routed and recorded the requested device under a process-wide lock, then restored the upstream function; compatibility injection count: 1.
- 运行说明：UnitaryLab supplies the interior nodes, and the controlled experiment protocol supplies the zero Dirichlet boundaries.
- 运行说明：The workflow nondimensionalizes the physical problem before the UnitaryLab call and restores metres and kelvin afterward.

## 复现命令

```bash
bash scripts/run_benchmark.sh
```
