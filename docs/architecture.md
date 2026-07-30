# 系统架构

## 总体设计

热鉴将实验意图、数值计算、量子执行、设备核验与成果报告拆分为可独立测试的
模块，使一条自然语言需求能够沿清晰、可追踪的路径转化为实验结果。

```text
自然语言 / JSON
        │
        ▼
参数解析 + Schema 校验
        │
        ▼
ThermalExperimentSpec
        │
        ├── 解析解
        ├── 显式有限差分
        └── 精确量子参数档案
                    │
                    ▼
           UnitaryLab CPU / GPU
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       误差分层          SUPA 设备归约
          │                   │
          └─────────┬─────────┘
                    ▼
             物理审计 + 成果包
```

## 模块职责

| 模块 | 职责 |
|---|---|
| `schema.py` | 定义并校验受控实验协议 |
| `parser.py` | 将中英文需求映射为 SI 参数与执行计划 |
| `classical_solver.py` | 计算解析解和显式有限差分基线 |
| `quantum_policy.py` | 选择有实测证据的精确量子参数档案 |
| `quantum_solver.py` | 执行 UnitaryLab 热方程算法 |
| `unitarylab_compat.py` | 路由并记录 CPU/GPU 设备调用 |
| `error_decomposition.py` | 构造半离散与同参数恢复参考 |
| `supa_audit.py` | 在 `supa:0` 上计算张量误差指标 |
| `custom_supa_audit.py` | 调用项目自研 `.su` 归约核 |
| `physics_audit.py` | 执行物理约束与数值误差检查 |
| `reporting.py` | 生成 JSON、Markdown、日志与图表 |
| `evidence_validation.py` | 校验保存的结果证据包 |
| `interaction_validation.py` | 校验 Agent/Skill 交互记录 |

## 实验协议

当前受控问题为一维线性热方程：

```text
∂T/∂t = α ∂²T/∂x²
T(0,t) = T(L,t) = 0
T(x,0) = A sin(πx/L)
```

所有执行路径共享相同的物理尺度、空间网格、边界处理和解析参考，因此可以使用
最大绝对误差、RMSE、相对 L2、边界值、温度范围和衰减行为进行统一比较。

## 设备路由

在 CLI、求解器与底层 Schrödingerization 调用三个层级记录请求设备。兼容层：

1. 检查已安装底层函数签名；
2. 在进程级锁内路由 `cpu` 或 `gpu`；
3. 记录实际调用参数与设备；
4. 执行结束后恢复原始函数；
5. 关闭算法日志句柄和生成的 Matplotlib 图。

路由元数据写入 `result.json`，并由 `validate-result` 自动核验。

## 成果契约

每次完整运行生成：

| 文件 | 用途 |
|---|---|
| `input.json` | 规范化 SI 实验参数 |
| `result.json` | 温度场、指标、设备路由与输入溯源 |
| `audit.json` | 物理与数值检查结果 |
| `report.md` | 面向读者的结果说明与复现命令 |
| `run.log` | 按顺序记录执行阶段 |
| `temperature_comparison.png` | 解析、经典与量子温度场对比 |
| `error_decomposition.png` | 半离散、恢复与 Trotter 误差分层 |

UnitaryLab 线路与求解 SVG 分别保存在 `unitarylab_cpu/` 和
`unitarylab_gpu/`。
