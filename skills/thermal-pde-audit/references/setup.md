# 安装与发现

## 完整仓库模式

使用完整仓库运行演示、验证保存证据、执行测试和壁仞 GPU 实验：

```bash
cd thermal-pde-audit
python -m pip install -e ".[dev]"
python skills/thermal-pde-audit/scripts/doctor.py
```

Skill 入口为：

```text
skills/thermal-pde-audit/SKILL.md
```

## 已安装 Skill 模式

将 Skill 文件夹复制到 Agent 的 Skills 目录后，保留项目仓库并指向它：

```bash
export THERMAL_PDE_AUDIT_ROOT=/path/to/thermal-pde-audit
python -m pip install -e "$THERMAL_PDE_AUDIT_ROOT"
```

PowerShell：

```powershell
$env:THERMAL_PDE_AUDIT_ROOT = "D:\path\to\thermal-pde-audit"
python -m pip install -e $env:THERMAL_PDE_AUDIT_ROOT
```

`scripts/algorithm.py` 与 `scripts/doctor.py` 依次查找
`THERMAL_PDE_AUDIT_ROOT`、父目录中的项目仓库和已安装的
`thermal_pde_audit` 包。

## 运行能力层级

| 层级 | 环境 | 可用工作流 |
|---|---|---|
| 核心能力 | Python 3.10+、NumPy、SciPy、Matplotlib | 解析、规划、解析解与经典检查 |
| 量子 CPU | 核心能力 + UnitaryLab + UnitaryLab Algorithms | CPU 量子线路仿真 |
| 壁仞 GPU | 竞赛运行时 + `torch.supa` + SUPA SDK | GPU、CPU/GPU 对照、双 SUPA |

以仓库 `pyproject.toml` 为依赖来源，保持 Skill 文件夹与项目环境一致。
