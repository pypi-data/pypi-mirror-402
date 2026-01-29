### save_data_file

**分类**: 工具
**功能**: 保存数据到文件

**参数**:
- `file_path` (str, required): 文件路径，支持 .xlsx, .csv 等格式
- `file_format` (str, required): 文件格式，可选值: "xlsx", "csv"

**返回值**: None

**示例**:
```python
# 保存为Excel
save_data_file(df, "output.xlsx", "xlsx")

# 保存为CSV
save_data_file(df, "output.csv", "csv")
```

**注意事项**:
- 文件路径必须有效
- 如果文件已存在，会被覆盖
- file_format必须与file_path的扩展名匹配

---
