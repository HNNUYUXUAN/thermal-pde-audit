# Origin 绘图数据与依据

本目录把当前已验证运行产生的结果 JSON/CSV 映射为 Origin 可直接导入的单表数据。原始结果不改写，清洗结果采用 UTF-8 with BOM、逗号分隔、第一行单层字段名、数值列保持数值类型；字段单位写在字段名或数据字典中，不把单位混入单元格。

## 清洗规则

1. 保留同级原始导出清单 `manifest.json`，所有衍生表在 `origin_ready/` 单独生成。
2. 温度曲线补齐可绘图的 `position_m`、analytic/classical/CPU/GPU 四条曲线；量子结果仅含内部节点，边界按受控零 Dirichlet 协议补为 0 K。
3. 误差分解、运行时、工作区扫描和审计检查保持一行一个观测；通过状态另设 `passed_1_0` 或 `status` 字段，避免依赖颜色表达语义。
4. 所有源文件 SHA-256 记录在 `SOURCE_MANIFEST.sha256`，每个数据集的字段与单位记录在 `DATA_DICTIONARY.csv`。
5. 图注统一使用“Biren GPU/SUPA 仿真与 CPU 参考路线”，准确体现 UnitaryLab 量子线路模拟器的执行边界，并保留运行环境说明。

## 图表—数据—源码映射

| 图号 | 图意 | Origin 数据 | 直接来源 | 推荐图型 | X | Y |
|---|---|---|---|---|---|---|
| F01 | Temperature profile comparison | origin_ready/01_temperature_profile.csv | ../skill_entry_gpu_validation/result.json | line | position_m | analytic_temperature_k; classical_temperature_k; quantum_gpu_temperature_k; quantum_cpu_temperature_k |
| F02 | Error decomposition | origin_ready/02_error_decomposition.csv | ../skill_entry_gpu_validation/result.json | clustered column | comparison | max_abs_error_k; rmse_k |
| F03 | Runtime comparison | origin_ready/03_runtime_comparison.csv | ../skill_entry_gpu_validation/result.json | column | backend | runtime_s |
| F04 | Fourier working region | origin_ready/04_working_region_fourier.csv | ../benchmarks/working_region_fo/working_region.json | line+marker | fourier_number_x | confirmed_nt_y |
| F05 | Grid working region | origin_ready/05_working_region_grid.csv | ../benchmarks/working_region_grid/working_region.json | line+marker | spatial_points_x | confirmed_nt_y |
| F06 | Material comparison | origin_ready/09_material_comparison.csv | ../benchmarks/material_comparison.json | column+line | case_label | thermal_diffusivity_m2_s; final_peak_temperature_k |
| F07 | CPU/GPU pointwise difference | origin_ready/10_cpu_gpu_field_difference.csv | ../skill_entry_gpu_validation/result.json | line | position_m | absolute_difference_k |
| F08 | SUPA consistency | origin_ready/11_supa_consistency.csv | ../skill_entry_gpu_validation/result.json | dot/bar | metric | value |

## 可复核的关键数字

- 经典有限差分相对 L2 误差：0.0000064790377963601114.
- GPU 量子仿真相对 L2 误差：0.00010028122145663477；最大绝对误差：0.009826979494448551 K。
- CPU/GPU 最大场差：0.00011324882507324219 K。
- torch.supa 误差归约运行时间：0.8918766849674284 s；项目 .su 内核子进程时间：0.023889731615781784 s。

详见 `DATA_DICTIONARY.csv`、`thermal_pde_origin_complete.xlsx` 及其 `Index` 工作表。
