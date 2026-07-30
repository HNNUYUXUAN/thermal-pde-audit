# 交互 07：自然语言驱动 GPU 完整闭环

## 用户输入

> 模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的一维热传导，
> 计算0.1秒，使用32个空间点；使用GPU完成CPU/GPU对照、双SUPA审计、
> 误差分层并生成报告。

## 任务解析

自然语言解析器生成 SI 实验规格、GPU 执行计划、精确档案选择和完整报告级别。

## 参数协议与决策

原始文本、字段来源、默认值来源和白名单执行计划写入结果；复现命令读取生成的
`input.json`。

## 调用命令

```bash
bash scripts/run_text_demo.sh
```

## 真实结果

- 工作流状态：成功
- 后端：`unitarylab_gpu`
- GPU/CPU 量子调用：`26.94159 / 2.40994 s`
- GPU 相对 L2：`1.0028122e-04`
- CPU/GPU 最大差：`1.1324883e-04 K`
- 双 SUPA、误差分层和物理审计：通过
- 保存证据验证：通过

## 生成文件

- `results/natural_language_gpu_validation/input.json`
- `results/natural_language_gpu_validation/result.json`
- `results/natural_language_gpu_validation/audit.json`
- `results/natural_language_gpu_validation/report.md`
- `results/natural_language_gpu_validation/temperature_comparison.png`
- `results/natural_language_gpu_validation/error_decomposition.png`
- `results/run_logs/natural_language_gpu_validation_v2_plan.log`
- `results/run_logs/natural_language_gpu_validation_v2_plan_check.log`

## 复核说明

自然语言只映射到热方程实验字段和已定义执行阶段，确保运行过程可复现。

## 最终回答

自然语言已经完成从物理参数解析、量子档案选择、GPU 执行到双 SUPA 审计和
报告生成的完整闭环。
