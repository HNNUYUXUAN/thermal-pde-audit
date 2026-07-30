# Architecture

## Overview

Thermal PDE Audit separates experiment intent, numerical computation, quantum
execution, device verification, and reporting into independently testable
layers.

```text
Natural language / JSON
        │
        ▼
Parser + schema validation
        │
        ▼
ThermalExperimentSpec
        │
        ├── Analytic solution
        ├── Explicit finite difference
        └── Quantum profile selection
                    │
                    ▼
           UnitaryLab CPU / GPU
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   Error decomposition   SUPA reductions
          │                   │
          └─────────┬─────────┘
                    ▼
         Physics audit + artifacts
```

## Modules

| Module | Role |
|---|---|
| `schema.py` | Defines and validates the controlled experiment protocol |
| `parser.py` | Maps Chinese or English requests to SI parameters and execution plans |
| `classical_solver.py` | Computes analytic and explicit finite-difference baselines |
| `quantum_policy.py` | Selects exact empirically validated quantum profiles |
| `quantum_solver.py` | Runs the UnitaryLab heat-equation algorithm |
| `unitarylab_compat.py` | Routes and records CPU/GPU device calls |
| `error_decomposition.py` | Builds semi-discrete and same-parameter reference layers |
| `supa_audit.py` | Computes tensor metrics on `supa:0` |
| `custom_supa_audit.py` | Calls the project-owned `.su` reduction kernel |
| `physics_audit.py` | Evaluates field and error checks |
| `reporting.py` | Writes JSON, Markdown, logs, and figures |
| `evidence_validation.py` | Verifies saved result bundles |
| `interaction_validation.py` | Verifies Agent/Skill interaction records |

## Experiment contract

The controlled problem is a one-dimensional linear heat equation:

```text
∂T/∂t = α ∂²T/∂x²
T(0,t) = T(L,t) = 0
T(x,0) = A sin(πx/L)
```

This contract gives every execution path the same physical scale, grid,
boundary treatment, and reference solution. Results can therefore be compared
by maximum absolute error, RMSE, relative L2 error, boundary values, range, and
decay behavior.

## Device route

The requested device is recorded at the CLI, solver, and lower-level
Schrödingerization call. The compatibility layer:

1. inspects the installed lower-level signature;
2. routes the requested `cpu` or `gpu` device under a process-wide lock;
3. records the effective call parameters;
4. restores the original callable after execution;
5. closes algorithm log handlers and generated Matplotlib figures.

The resulting metadata is saved in `result.json` and checked by
`validate-result`.

## Artifact contract

Every complete run emits:

| Artifact | Purpose |
|---|---|
| `input.json` | Normalized SI experiment |
| `result.json` | Computed fields, metrics, device route, and provenance |
| `audit.json` | Physics and numerical checks |
| `report.md` | Reader-oriented summary and reproduction command |
| `run.log` | Ordered execution stages |
| `temperature_comparison.png` | Analytic, classical, and quantum field comparison |
| `error_decomposition.png` | Semi-discrete, recovery, and Trotter error layers |

UnitaryLab circuit and solution SVGs are stored below `unitarylab_cpu/` and
`unitarylab_gpu/`.
