# Evidence Contract

## Required artifacts

| File | Contents |
|---|---|
| `input.json` | Normalized experiment specification |
| `result.json` | Fields, routes, metrics, provenance, artifacts |
| `audit.json` | Physics and numerical checks |
| `report.md` | Reader-facing interpretation and reproduction command |
| `run.log` | Ordered execution stages |
| `temperature_comparison.png` | Analytic, classical, and quantum profiles |

`error_decomposition.png` is included for decomposition runs. UnitaryLab CPU
and GPU directories contain algorithm logs, solution SVGs, and circuit SVGs.

## Core checks

Every complete result verifies:

- artifact presence and JSON parsing;
- successful result and audit status;
- quantum field length and finiteness;
- physical boundary and range behavior;
- validated parameter profile;
- requested and routed GPU device;
- CPU/GPU field consistency;
- `torch.supa` and NumPy metric consistency;
- custom `.su` and NumPy metric consistency;
- error-decomposition layers;
- controlled reproduction command.

## Key metrics

Report:

```text
classical_vs_analytic.relative_l2_error
quantum_vs_analytic.relative_l2_error
quantum_vs_analytic.max_abs_error
quantum_cpu_gpu_max_abs_diff_k
```

For SUPA, report status, device, relative L2, and consistency. For the custom
kernel, also report the source path and launched thread count.

## Saved examples

- `results/skill_entry_gpu_validation/` — current end-to-end run through the
  public Skill entry point;
- `results/fast_quantum_validation/`
- `results/natural_language_gpu_validation/`
- `results/quantum_layer_validation/`

These bundles contain complete successful CPU/GPU simulations and can be
validated without rerunning the GPU.
