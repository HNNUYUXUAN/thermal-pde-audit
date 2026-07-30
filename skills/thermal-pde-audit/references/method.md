# Method

## Physical model

The controlled experiment solves:

```text
∂u/∂t = α ∂²u/∂x²
u(0,t) = u(L,t) = 0
u(x,0) = A sin(πx/L)
```

with positive diffusivity `α`, domain length `L`, duration `t`, and initial
amplitude `A`.

The continuous reference is:

```text
u(x,t) = A exp[-α(π/L)²t] sin(πx/L)
```

## Comparison pipeline

1. Normalize the request to SI units.
2. Evaluate the continuous analytic solution.
3. Run the explicit finite-difference baseline and verify its stability ratio.
4. Select an exact measured quantum profile from `Fo` and the spatial grid.
5. Run the UnitaryLab Schrödingerization circuit on CPU or Biren GPU.
6. Compare the recovered field with the semi-discrete and continuous
   references.
7. Recompute error metrics with NumPy, `torch.supa`, and the project `.su`
   reduction kernel when requested.
8. Save the experiment, routes, metrics, audit checks, figures, and
   reproduction command.

## Error layers

Keep these comparisons distinct:

- semi-discrete versus continuous analytic;
- same-parameter Schrödingerization recovery versus semi-discrete;
- Trotter result versus same-parameter recovery;
- Trotter result versus continuous analytic;
- CPU versus GPU;
- SUPA reductions versus NumPy.

This separation identifies discretization, recovery, Trotter, device, and
reduction effects without conflating them.

## Attribution

UnitaryLab Algorithms supplies the heat-equation Schrödingerization
implementation. This project supplies the experiment protocol, natural
language mapping, validated profile selection, device-route adaptation,
classical and analytic baselines, SUPA reductions, audits, evidence validation,
and reporting.
