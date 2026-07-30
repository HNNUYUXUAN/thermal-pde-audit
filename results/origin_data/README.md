# Origin 数据包索引

- 工作簿：`thermal_pde_origin_complete.xlsx`
- 单表 CSV：`origin_ready/`
- 字段说明：`DATA_DICTIONARY.csv`
- 图源映射：`ORIGIN_DATA_INDEX.md`
- 来源校验：`SOURCE_MANIFEST.sha256`
- 工作簿检查：`WORKBOOK_INSPECT.ndjson`、`WORKBOOK_ERROR_SCAN.ndjson`

工作簿采用 Index + 12 个扁平数据表，数据表第一行为列名，不依赖单元格颜色表达通过状态，便于 Origin、Excel、Python 或 R 继续处理。
