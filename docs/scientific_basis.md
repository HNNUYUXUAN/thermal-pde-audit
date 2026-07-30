# Scientific Basis

## Heat-equation reference problem

The controlled experiment solves:

```text
∂T/∂t = α ∂²T/∂x²,      0 < x < L
T(0,t) = T(L,t) = 0
T(x,0) = A sin(πx/L)
```

The analytic solution is:

```text
T(x,t) = A exp[-α(π/L)²t] sin(πx/L)
```

This solution supplies a direct physical reference for every grid point.

## Classical discretization

The explicit centered finite-difference update is:

```text
Tᵢⁿ⁺¹ = Tᵢⁿ + r(Tᵢ₋₁ⁿ - 2Tᵢⁿ + Tᵢ₊₁ⁿ)
r = αΔt/Δx²
```

The solver checks the standard stability condition `r ≤ 1/2` before
execution. This produces an independent numerical baseline with transparent
time and space discretization.

## Nondimensionalization

The physical experiment is mapped to:

```text
x* = x/L
t* = αt/L²
```

so the normalized equation has unit length and unit diffusivity. Temperature
is rescaled by the initial amplitude after quantum execution. The dimensionless
duration is the Fourier number:

```text
Fo = αt/L²
```

## Schrödingerization layer

The quantum-simulation path uses the heat-equation implementation from
UnitaryLab Algorithms. The project supplies:

- the physical-to-dimensionless mapping;
- the exact measured parameter profile;
- CPU/GPU device routing and route evidence;
- field extraction and SI rescaling;
- independent reference solvers and numerical audits.

For interpretation, each complete run compares:

1. continuous analytic solution;
2. exact evolution of the central-difference semi-discrete system;
3. same-parameter Schrödingerization recovery;
4. Trotter circuit result.

This decomposition makes spatial discretization, auxiliary recovery, and
Trotter differences visible in the same result bundle.

## Physics audit

The audit checks:

- finite field values;
- zero Dirichlet boundary completion;
- temperature range and maximum principle;
- expected modal decay;
- classical stability;
- analytic, classical, and quantum error metrics;
- CPU/GPU field consistency;
- SUPA and NumPy metric consistency.

## References

1. S. Jin and N. Liu, “Analog quantum simulation of partial differential
   equations,” *Physical Review Letters* 130, 080401 (2023).
   <https://doi.org/10.1103/PhysRevLett.130.080401>
2. S. Jin, N. Liu, and Y. Yu, “Quantum simulation of partial differential
   equations via Schrödingerisation,” arXiv:2212.13969.
   <https://arxiv.org/abs/2212.13969>
3. S. Jin, N. Liu, and Y. Yu, “Quantum simulation of partial differential
   equations: Applications and detailed analysis,” arXiv:2303.13088.
   <https://arxiv.org/abs/2303.13088>
4. [UnitaryLab Algorithms](https://github.com/unitarylab/unitarylab_algorithms)
   provides the installed heat-equation Schrödingerization implementation used
   by this project.
