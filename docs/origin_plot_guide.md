# Origin 绘图指南

`results/origin_data/` 包含 10 张 UTF-8-BOM CSV 表，共 189 行，可直接导入
Origin、Excel、Python 或其他科学绘图工具。当前导出以
`results/skill_entry_gpu_validation/` 为主要结果来源。

## 推荐图表

| 图表 | 文件 | X | Y / 分组 |
|---|---|---|---|
| 温度分布 | `temperature_profile.csv` | `x_m` | 解析、经典、CPU 量子、GPU 量子 |
| 绝对误差 | `temperature_profile.csv` | `x_m` | 各绝对误差列 |
| 误差分层 | `error_decomposition.csv` | `layer` | `relative_l2_error` |
| 耗时对比 | `runtime_comparison.csv` | `component` | `runtime_s` |
| Fourier 扫描 | `fourier_scan_plot.csv` | `fourier_number` | 确认步数与相对 L2 |
| 网格扫描 | `grid_scan_plot.csv` | `spatial_points` | 确认步数与相对 L2 |
| 精确档案 | `working_region_confirmed.csv` | Fourier 数 / 网格 | 确认的 Trotter 配置 |

## 数据溯源

`manifest.json` 记录：

- 来源结果文件与审计文件；
- 来源文件和导出文件的 SHA-256；
- 行数与列名；
- SI 单位与边界行标记；
- 精确量子档案参数。

配套工作簿位于：

```text
outputs/019fad77-9506-7a03-8bd6-4488117242f5/
└── thermal_pde_origin_data.xlsx
```

复现图表或核对绘图数据时，以 CSV 清单为溯源依据。
