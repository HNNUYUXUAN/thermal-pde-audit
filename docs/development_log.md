# 作品建设里程碑

## 里程碑一 · 建立受控热传导实验协议

- 使用 SI 单位定义类型化一维热方程 Schema。
- 实现确定性的中英文物理参数解析。
- 完成解析解与显式有限差分参考求解器。
- 建立边界、温度范围、衰减、稳定性和误差物理检查。

## 里程碑二 · 接入 UnitaryLab 量子执行

- 接入 UnitaryLab Algorithms 热方程算法。
- 完成无量纲化与温度尺度恢复。
- 实现面向壁仞环境的 CPU/GPU 设备路由与逐次记录。
- 保存线路、求解图与算法日志。

## 里程碑三 · 建立参数治理和误差解释

- 扫描 Fourier 数、网格规模和 Trotter 时间分片。
- 将 14 组实测精确档案写入 `validated_profiles.json`。
- 加入半离散参考和同参数 Schrödingerization 恢复参考。
- 为完整实验生成误差分层图。

## 里程碑四 · 完成双 SUPA 审计

- 使用 `torch.supa` 计算最大误差、RMSE 和相对 L2。
- 实现 `scripts/supa_error_reduction.su`。
- 在 Biren106M 上完成项目自研核的编译和执行。
- 使用 NumPy 对设备结果与端到端指标进行独立复核。

## 里程碑五 · 形成 Agent/Skill 工作流

- 支持自然语言规划与受控直接执行。
- 记录输入来源与执行计划来源。
- 保存 7 组差异化 Agent/Skill 交互案例。
- 实现交互结构和引用文件的机器校验。

## 里程碑六 · 完成可复现开源交付

- 建立 55 项 CPU 侧测试、Ruff、Mypy 与 GitHub Actions。
- 提供结果包、参数档案和交互证据验证器。
- 导出 12 张 Origin-ready CSV 表、222 行绘图数据和已复核 Excel 工作簿。
- 将可复用 Skill 组织为 `skills/thermal-pde-audit/` 标准文件夹。
- 围绕源码、成功证据、复现入口、科学基础和致谢完成公开仓库整理。

## 里程碑七 · 完成公开 Skill 端到端实跑

- 通过公开 `algorithm.py` 入口在壁仞竞赛容器执行文件夹式 Skill。
- 在同一运行中完成 UnitaryLab CPU/GPU、`torch.supa`、项目 `.su` 核、
  误差分层和自然语言输入溯源。
- 校验全部要求的成果文件，并将结果保存到
  `results/skill_entry_gpu_validation/`。
- 在收集结果前使用 SHA-256 核对远端执行源码与公开仓库文件。
