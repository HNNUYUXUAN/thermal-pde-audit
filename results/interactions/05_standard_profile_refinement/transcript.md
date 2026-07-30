# 交互 05：量子参数档案验证

## 用户输入

> 核对标准热方程的量子参数档案，确认每一组策略都能追溯到实测扫描结果。

## 任务解析

- 策略：`src/thermal_pde_audit/validated_profiles.json`
- 证据：Fourier 扫描、网格扫描和补充扫描
- 核对：键集合、固定参数、确认步数和连续通过点

## 参数协议与决策

使用 `Fo + spatial_points` 作为档案主键，将 14 组策略逐行映射到三份实测
工作区间 JSON。

## 调用命令

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-profiles
```

## 真实结果

- 策略档案：14 组
- 实测证据：14 组
- 重复键：0
- 策略与证据差集：0
- 固定量子参数和确认步数：全部匹配

## 生成文件

- `src/thermal_pde_audit/validated_profiles.json`
- `results/benchmarks/working_region_fo/working_region.json`
- `results/benchmarks/working_region_grid/working_region.json`
- `results/benchmarks/working_region_gapfill/working_region.json`

## 复核说明

档案选择采用精确键匹配，使每次量子运行都能回溯到对应实测配置。

## 最终回答

14 组量子参数档案与三份实测扫描证据逐项一致，可直接用于受控实验自动选参。
