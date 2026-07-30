---
name: thermal-pde-audit
description: Convert structured or natural-language one-dimensional heat-transfer requests into physics-audited experiments with analytic and finite-difference baselines, exact UnitaryLab parameter profiles, CPU or Biren GPU quantum simulation, torch.supa and project-owned SUPA reductions, error decomposition, reports, logs, and figures. Use for thermal PDE simulation, CPU/GPU comparison, quantum heat-equation demonstrations, saved-evidence validation, or reproducible competition experiments.
---

# Thermal PDE Audit

Turn a heat-transfer request into a reproducible experiment and return the
generated result, audit, report, log, and figures.

## Read chain

Before writing commands or interpreting results:

1. Read this file.
2. Read [references/protocol.md](references/protocol.md) for every new input.
3. Read [references/setup.md](references/setup.md) when preparing an environment.
4. Read [references/runtime.md](references/runtime.md) before a Biren GPU run.
5. Read [references/evidence.md](references/evidence.md) when validating or
   explaining results.
6. Read [references/method.md](references/method.md) when explaining the
   mathematics or the Schrödingerization pipeline.

## Choose the workflow

Use one of these paths:

1. **Natural-language task** — plan or run the request with `plan-text` or
   `run-text`.
2. **Structured experiment** — validate a JSON input and run it with `run`.
3. **Live demonstration** — execute the packaged fast CPU/GPU/SUPA workflow.
4. **Evidence review** — validate an existing result bundle without rerunning
   the GPU.

Run the environment doctor before the first execution:

```bash
python skills/thermal-pde-audit/scripts/doctor.py
```

Use `python3` instead of `python` when that is the active interpreter.

## Plan a natural-language experiment

Use the Skill entry point:

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "长度10毫米，热扩散率1e-6平方米每秒，初始温升100K，计算0.1秒"
```

Return either:

- a complete normalized SI specification and execution plan; or
- focused clarification questions for required physical values.

Map user text only to the experiment schema and supported execution flags.

## Run a natural-language experiment

Use:

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --text "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，计算0.1秒，使用32个空间点；使用GPU做CPU/GPU对照、双SUPA审计、误差分层并生成报告" \
  --output results/my_thermal_run \
  --full-audit
```

Confirm that `result.json` records:

- the original task;
- parsed SI parameters;
- selected quantum profile;
- requested and effective device;
- enabled audit stages;
- a reproduction command based on `input.json`.

## Run a structured experiment

Inspect the exact profile first:

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --input examples/standard_heat.json
```

Then run:

```bash
python skills/thermal-pde-audit/scripts/algorithm.py \
  --input examples/standard_heat.json \
  --output results/my_standard_run \
  --device gpu \
  --full-audit
```

Use an exact measured profile for checked quantum experiments.

## Run the demonstrations

Fast full-chain demonstration:

```bash
bash skills/thermal-pde-audit/scripts/run-demo.sh
```

Natural-language full-chain demonstration:

```bash
bash skills/thermal-pde-audit/scripts/run-text-demo.sh
```

The demonstration executes analytic, classical, CPU quantum, GPU quantum,
error-decomposition, `torch.supa`, custom `.su`, audit, and reporting stages.

## Validate the result

Run the cross-platform validator:

```bash
python skills/thermal-pde-audit/scripts/validate.py
```

On Linux or the competition container, this wrapper is equivalent:

```bash
bash skills/thermal-pde-audit/scripts/validate.sh
```

Report the backend, actual routed device, profile, key error metrics, audit
status, and artifact paths.

## Interpret the experiment

Present results in this order:

1. physical input and SI units;
2. selected numerical and quantum parameters;
3. analytic and classical baselines;
4. CPU/GPU quantum results;
5. error-decomposition metrics;
6. SUPA consistency;
7. physics-audit conclusion;
8. generated files and reproduction command.

Always execute a requested demonstration or validation. Do not stop after
constructing a command. Return at least one numerical validation signal and
the paths to the saved result and report.

Describe the quantum layer as a UnitaryLab quantum-circuit simulation executed
on the Biren GPU. Attribute the heat-equation Schrödingerization implementation
to UnitaryLab Algorithms and the orchestration, validation, SUPA kernel, and
evidence system to this project.

## Use the supported scientific scope

Work within the project protocol:

- one-dimensional linear heat equation;
- positive thermal diffusivity;
- zero source;
- zero Dirichlet boundaries;
- first sine-mode initial temperature;
- 4–256 interior points;
- CPU or Biren GPU execution.

For a request outside this protocol, explain the closest supported experiment
and ask whether to map the task to it.
