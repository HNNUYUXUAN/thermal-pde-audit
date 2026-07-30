# Development Log

## Milestone 1 · Controlled thermal experiment protocol

- Defined a typed one-dimensional heat-equation schema in SI units.
- Added deterministic Chinese and English parameter parsing.
- Implemented analytic and explicit finite-difference reference solvers.
- Added physics checks for boundaries, range, decay, stability, and error.

## Milestone 2 · UnitaryLab quantum execution

- Connected the installed UnitaryLab Algorithms heat-equation class.
- Added nondimensionalization and temperature rescaling.
- Implemented recorded CPU/GPU device routing for the Biren environment.
- Preserved circuit, solution, and algorithm-log artifacts.

## Milestone 3 · Parameter governance and numerical interpretation

- Scanned Fourier number, grid size, and Trotter steps.
- Consolidated 14 exact measured profiles in `validated_profiles.json`.
- Added semi-discrete and same-parameter recovery references.
- Generated an error-decomposition figure for each complete experiment.

## Milestone 4 · SUPA integration

- Added `torch.supa` tensor reductions for maximum error, RMSE, and relative L2.
- Implemented `scripts/supa_error_reduction.su`.
- Compiled and executed the project-owned kernel on Biren106M.
- Added independent NumPy comparisons for device and end-to-end metrics.

## Milestone 5 · Agent/Skill workflow

- Added natural-language planning and direct controlled execution.
- Recorded input provenance and execution-plan provenance.
- Added seven distinct Agent/Skill interaction examples.
- Implemented machine validation for interaction structure and referenced files.

## Milestone 6 · Reproducible open-source release

- Added 55 CPU-side tests, Ruff, Mypy, and GitHub Actions validation.
- Added saved-evidence and profile validators.
- Exported ten Origin-friendly CSV tables and a checked Excel workbook.
- Organized the reusable Skill as `skills/thermal-pde-audit/`.
- Curated the public repository around source, successful evidence,
  reproducibility, scientific foundations, and acknowledgments.

## Milestone 7 · Public Skill end-to-end validation

- Executed the folder-based Skill through its public `algorithm.py` entry point
  in the Biren competition container.
- Completed UnitaryLab CPU/GPU comparison, `torch.supa`, the project `.su`
  kernel, error decomposition, and natural-language provenance in one run.
- Validated all required artifacts and recorded the current result in
  `results/skill_entry_gpu_validation/`.
- Matched the remotely executed source files to the published repository tree
  by SHA-256 before collecting the result bundle.
