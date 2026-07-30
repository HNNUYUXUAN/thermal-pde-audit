# 交互 04：热扩散率输入质量校验

## 用户输入

> 运行 `examples/invalid_negative_alpha.json`，并说明输入校验结果。

## 任务解析

结构化输入包含热方程任务、长度、温升、时长、网格和热扩散率。

## 参数协议与决策

协议要求热扩散率为正 SI 数值。系统在求解器启动前完成字段校验并返回结构化
问题说明。

## 调用命令

```bash
PYTHONPATH=src python3 -m thermal_pde_audit.cli run \
  --input examples/invalid_negative_alpha.json \
  --output results/input_quality_check
```

## 真实结果

输入质量检查准确定位 `thermal_diffusivity_m2_s`，返回稳定的错误代码和字段
信息，未进入数值与量子执行阶段。

## 生成文件

- `examples/invalid_negative_alpha.json`
- `results/run_logs/invalid_negative_alpha.log`

## 复核说明

该交互展示协议校验能力，正常实验使用正热扩散率。

## 最终回答

输入校验按设计工作，能够在运行前定位物理参数问题并给出可操作的修正信息。
