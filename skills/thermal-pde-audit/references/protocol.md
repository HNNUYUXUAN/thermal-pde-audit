# 输入协议

## 结构化参数

```json
{
  "task": "heat_equation_1d",
  "length_m": 0.01,
  "thermal_diffusivity_m2_s": 1e-6,
  "initial_amplitude_k": 100.0,
  "duration_s": 0.1,
  "spatial_points": 32,
  "time_steps": 50,
  "boundary": "dirichlet_zero",
  "initial_condition": "sine_mode_1",
  "device": "gpu",
  "seed": 42
}
```

要求以下物理量为正的 SI 数值：

- `length_m`
- `thermal_diffusivity_m2_s`
- `initial_amplitude_k`
- `duration_s`

使用以下配置：

- `task = heat_equation_1d`
- `boundary = dirichlet_zero`
- `initial_condition = sine_mode_1`
- `device = cpu | gpu`
- `spatial_points` 为 4–256 范围内的 2 的幂
- `time_steps` 为 1–100000 范围内的整数

## 自然语言单位

识别：

- 米、毫米、厘米；
- 秒、毫秒；
- 开尔文或摄氏温差；
- 平方米、平方毫米或平方厘米每秒。

执行前将所有参数转换为 SI 单位，并记录原始文本与转换来源。

## 派生参数

计算：

```text
Fo = thermal_diffusivity_m2_s * duration_s / length_m²
dx = length_m / (spatial_points + 1)
r  = thermal_diffusivity_m2_s * dt / dx²
```

使用 `Fo + spatial_points` 查询精确量子参数档案。
