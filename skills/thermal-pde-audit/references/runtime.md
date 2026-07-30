# Biren Runtime

## Verified environment

```text
Python                    3.10.12
torch                     2.9.0+cu128
torch_br                  1.10.0.20900+br1xx
unitarylab                1.0.0
unitarylab_algorithms     1.1.0
device                    Biren106M
torch.supa.device_count   1
```

## Environment setup

```bash
source /usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh >/dev/null
export PYTHONPATH=/workspace/thermal-pde-audit/src
```

## Device evidence

Check these `result.json` fields after a GPU run:

```text
quantum.backend
quantum.device_info
quantum.device_route_calls
quantum.device_route_compatibility
quantum.algorithm_log_handler_cleanup
quantum.algorithm_figure_cleanup
```

A complete GPU route records:

- `backend = unitarylab_gpu`;
- `requested_device = gpu`;
- a lower-level routed call with `device = gpu`;
- `all_devices_match_requested = true`;
- `restored = true`.

## SUPA kernel

Build:

```bash
bash scripts/build_custom_supa_kernel.sh
```

The workflow calls:

```text
build/custom_supa/supa_error_reduction.out
```

and saves kernel metadata, metrics, runtime, and NumPy comparisons in
`custom_supa_audit`.
