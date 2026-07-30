# Setup and Discovery

## Full repository mode

Use this mode for demonstrations, saved evidence, tests, and Biren GPU runs.

```bash
cd thermal-pde-audit
python -m pip install -e ".[dev]"
python skills/thermal-pde-audit/scripts/doctor.py
```

The Skill is discovered from:

```text
skills/thermal-pde-audit/SKILL.md
```

## Installed Skill mode

When the Skill folder is copied into an Agent Skill directory, keep a project
checkout available and point the Skill to it:

```bash
export THERMAL_PDE_AUDIT_ROOT=/path/to/thermal-pde-audit
python -m pip install -e "$THERMAL_PDE_AUDIT_ROOT"
```

PowerShell:

```powershell
$env:THERMAL_PDE_AUDIT_ROOT = "D:\path\to\thermal-pde-audit"
python -m pip install -e $env:THERMAL_PDE_AUDIT_ROOT
```

`scripts/algorithm.py` and `scripts/doctor.py` first use
`THERMAL_PDE_AUDIT_ROOT`, then search their parent directories, and finally
use an installed `thermal_pde_audit` package.

## Runtime levels

| Level | Requirements | Available workflows |
|---|---|---|
| Core | Python 3.10+, NumPy, SciPy, Matplotlib | Parsing, planning, classical checks |
| Quantum CPU | Core + UnitaryLab + UnitaryLab Algorithms | CPU quantum simulation |
| Biren GPU | Competition runtime + `torch.supa` + SUPA SDK | GPU, CPU/GPU, dual SUPA |

Use the repository `pyproject.toml` as the dependency source. Do not duplicate
or independently pin project dependencies inside the Skill folder.
