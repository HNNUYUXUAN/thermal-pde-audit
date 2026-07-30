# Results

## Current Skill-entry GPU validation

The current public Skill was executed end to end in the Biren competition
container through `skills/thermal-pde-audit/scripts/algorithm.py --full-audit`.
The natural-language request was converted to the controlled experiment
protocol, then the CPU/GPU quantum paths, both SUPA reductions, physical
checks, error decomposition, and evidence export completed in one workflow.

| Item | Result |
|---|---:|
| Workflow status | success |
| Validated profile | `Nt=2, na=8, R=16, point=1` |
| Full workflow runtime | `35 s` |
| Classical relative L2 | `6.47904e-06` |
| GPU relative L2 | `1.0028122e-04` |
| GPU maximum absolute error | `0.00982698 K` |
| CPU/GPU maximum difference | `1.1324883e-04 K` |
| CPU quantum call | `2.48456 s` |
| GPU quantum call | `27.97223 s` |
| `torch.supa` consistency | passed |
| Project `.su` consistency | passed |
| Physics and numerical audit | passed |

Evidence:

- `results/skill_entry_gpu_validation/`

## Fast full-chain demonstration

The recommended live demonstration uses a 10 mm domain, thermal diffusivity
`1e-6 m²/s`, initial temperature rise `100 K`, duration `0.1 s`, and 32
interior points.

| Item | Result |
|---|---:|
| Validated profile | `Nt=2, na=8, R=16, point=1` |
| Full command runtime | `36.143 s` |
| Classical relative L2 | `6.47904e-06` |
| GPU relative L2 | `1.0028122e-04` |
| GPU maximum absolute error | `0.00982698 K` |
| CPU/GPU maximum difference | `1.1324883e-04 K` |
| CPU quantum call | `2.43503 s` |
| GPU quantum call | `26.85717 s` |
| `torch.supa` consistency | passed |
| Project `.su` consistency | passed |
| Physics audit | passed |

Evidence:

- `results/fast_quantum_validation/`
- `results/run_logs/final_minimal_gpu_validation_v1.log`
- `results/run_logs/final_minimal_gpu_validation_check_v3.log`

## Natural-language GPU workflow

The saved natural-language regression bundle records the original Chinese
task text, parsed SI parameters, selected profile, requested device, actual
device call, and reproduction command.

| Item | Result |
|---|---:|
| Workflow status | success |
| Backend | `unitarylab_gpu` |
| GPU relative L2 | `1.0028122e-04` |
| CPU/GPU maximum difference | `1.1324883e-04 K` |
| `torch.supa` | passed |
| Project `.su` kernel | passed |
| Error decomposition | passed |
| Saved-evidence validation | passed |

Evidence:

- `results/natural_language_gpu_validation/`
- `results/run_logs/natural_language_gpu_validation_v2_plan.log`
- `results/run_logs/natural_language_gpu_validation_v2_plan_check.log`

## Standard-scale validation

The standard profile uses `Fo=0.06`, 32 interior points, and 32 Trotter time
slices.

| Item | Result |
|---|---:|
| GPU relative L2 | `1.1743041e-03` |
| GPU maximum absolute error | `0.07013839 K` |
| CPU/GPU maximum difference | `2.9876828e-04 K` |
| Semi-discrete relative L2 | `4.4720588e-04` |
| SUPA end-to-end maximum metric difference | `1.36464e-06` |
| Physics audit | passed |

Evidence:

- `results/quantum_layer_validation/`
- `results/run_logs/quantum_layer_validation_v2_error_decomposition.log`

## Parameter profiles

The profile table contains 14 exact measured configurations spanning:

- 11 Fourier-number points for a 32-point grid;
- 4 grid sizes at `Fo=0.06`;
- a gap-fill profile completing the combined set.

Run:

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli validate-profiles
```

to match every policy row to its saved scan evidence.

## Origin-ready data

Ten CSV tables and one checked workbook provide plot-ready temperature,
absolute error, error decomposition, runtime, scan, and profile data derived
from the current Skill-entry result. See
[origin_plot_guide.md](origin_plot_guide.md).
