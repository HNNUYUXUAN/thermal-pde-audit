# Platform and Runtime

## Verified environment

| Component | Verified value |
|---|---|
| Platform | Biren competition container |
| Device | Biren106M |
| Python | 3.10.12 |
| PyTorch | 2.9.0+cu128 |
| `torch_br` | 1.10.0.20900+br1xx |
| UnitaryLab | 1.0.0 |
| UnitaryLab Algorithms | 1.1.0 |
| SUPA devices | `torch.supa.device_count() = 1` |
| SUPA compiler | `brcc` from Biren SUPA SDK |

The full environment probe is saved at
`results/run_logs/environment_probe.log`.

## Runtime capabilities

| Capability | Entry point | Evidence |
|---|---|---|
| Analytic heat solution | `classical_solver.solve_analytic` | Unit tests and result bundles |
| Explicit finite difference | `classical_solver.solve_classical` | Stability and accuracy checks |
| UnitaryLab CPU | `HeatEquationAlgorithm` | CPU logs, circuit SVGs, fields |
| UnitaryLab GPU | Device-routed `HeatEquationAlgorithm` | GPU logs, route metadata, fields |
| CPU/GPU comparison | CLI `--compare-cpu-gpu` | Maximum field difference |
| Exact profile selection | CLI `recommend` / `--validated-profile` | 14 saved profile rows |
| Error decomposition | CLI `--error-decomposition` | JSON metrics and PNG |
| `torch.supa` audit | CLI `--supa-audit` | `supa:0` metrics and NumPy comparison |
| Custom `.su` audit | CLI `--custom-supa-audit` | Compiled kernel result and audit |
| Natural-language run | CLI `plan-text` / `run-text` | Parsed plan and full artifacts |
| Evidence validation | CLI `validate-result` | Structured pass/fail checks |

## Execution profiles

Two primary profiles are included:

- **Fast demonstration:** `Fo=0.001`, 32 points, `Nt=2`; the current Skill-entry
  full workflow completed in 35 seconds.
- **Standard validation:** `Fo=0.06`, 32 points, `Nt=32`, full CPU/GPU and
  error-decomposition evidence.

GPU and SUPA work is executed serially to keep each result attributable to one
experiment and one device route. The current end-to-end evidence is saved in
`results/skill_entry_gpu_validation/`.

## Local development

CPU-side parsing, schema validation, analytic solutions, finite differences,
profile validation, saved-evidence validation, and all 55 tests run on a
standard Python workstation. GPU demonstrations use the preconfigured Biren
container.
