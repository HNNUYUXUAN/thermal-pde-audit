# Origin Plot Guide

`results/origin_data/` contains ten UTF-8-BOM CSV tables with 189 rows. The
tables can be imported directly into Origin, Excel, Python, or other scientific
plotting tools. The current export uses
`results/skill_entry_gpu_validation/` as its primary result source.

## Recommended figures

| Figure | File | X | Y / grouping |
|---|---|---|---|
| Temperature profile | `temperature_profile.csv` | `x_m` | analytic, classical, CPU quantum, GPU quantum |
| Absolute error | `temperature_profile.csv` | `x_m` | absolute-error columns |
| Error decomposition | `error_decomposition.csv` | `layer` | `relative_l2_error` |
| Runtime comparison | `runtime_comparison.csv` | `component` | `runtime_s` |
| Fourier scan | `fourier_scan_plot.csv` | `fourier_number` | confirmed steps and relative L2 |
| Grid scan | `grid_scan_plot.csv` | `spatial_points` | confirmed steps and relative L2 |
| Validated profiles | `working_region_confirmed.csv` | Fourier number / grid | confirmed Trotter configuration |

## Data provenance

`manifest.json` records:

- source result and audit files;
- source and exported SHA-256 values;
- row counts and column lists;
- SI units and boundary-row markers;
- exact quantum-profile parameters.

The companion workbook is:

```text
outputs/019fad77-9506-7a03-8bd6-4488117242f5/
└── thermal_pde_origin_data.xlsx
```

Use the CSV manifest when reproducing a figure or checking a plotted dataset.
