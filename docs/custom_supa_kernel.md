# Project-owned SUPA Reduction Kernel

## Purpose

`scripts/supa_error_reduction.su` computes three quantities directly on the
Biren SUPA device:

```text
max_abs_error = max |u_quantum - u_reference|
sum_sq_error  = Σ (u_quantum - u_reference)²
sum_sq_ref    = Σ u_reference²
```

The host converts the reductions into RMSE and relative L2 error and compares
them with NumPy references.

## Implementation

- one 256-thread block;
- shared-memory tree reduction;
- float32 input and accumulation;
- aligned one-dimensional fields with 1–256 values;
- JSON output for deterministic integration with the Python audit layer.

Build the kernel in the Biren environment:

```bash
bash scripts/build_custom_supa_kernel.sh
```

The build produces:

```text
build/custom_supa/supa_error_reduction.out
```

Run it as part of the full workflow:

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli run \
  --input examples/minimal_heat.json \
  --output results/fast_quantum_validation \
  --device gpu \
  --compare-cpu-gpu \
  --validated-profile \
  --supa-audit \
  --custom-supa-audit \
  --error-decomposition
```

## Verification

The audit performs two independent comparisons:

1. kernel metrics versus a float32 NumPy reduction;
2. end-to-end kernel metrics versus the original float64 host data.

The fast and natural-language GPU result bundles both include successful
custom-kernel evidence. Build and execution logs are stored in
`results/run_logs/`.
