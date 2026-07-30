# 壁仞运行环境

## 已验证环境

```text
Python                    3.10.12
torch                     2.9.0+cu128
torch_br                  1.10.0.20900+br1xx
unitarylab                1.0.0
unitarylab_algorithms     1.1.0
device                    Biren106M
torch.supa.device_count   1
```

## 环境准备

```bash
source /usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh >/dev/null
export PYTHONPATH=/workspace/thermal-pde-audit/src
```

## 设备证据

GPU 运行后检查 `result.json`：

```text
quantum.backend
quantum.device_info
quantum.device_route_calls
quantum.device_route_compatibility
quantum.algorithm_log_handler_cleanup
quantum.algorithm_figure_cleanup
```

完整 GPU 路由应记录：

- `backend = unitarylab_gpu`；
- `requested_device = gpu`；
- 底层调用使用 `device = gpu`；
- `all_devices_match_requested = true`；
- `restored = true`。

## SUPA 核

构建：

```bash
bash scripts/build_custom_supa_kernel.sh
```

工作流调用：

```text
build/custom_supa/supa_error_reduction.out
```

并在 `custom_supa_audit` 中保存核元数据、指标、运行时间和 NumPy 对照。
