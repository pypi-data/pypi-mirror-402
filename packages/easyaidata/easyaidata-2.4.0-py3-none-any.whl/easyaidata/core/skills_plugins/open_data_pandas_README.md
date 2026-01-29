### open_data_pandas

**分类**: 工具
**功能**: 使用Pandas引擎打开数据文件

**参数**:
- `file_path` (str, required): 文件路径，支持 .xlsx, .xls, .csv 等格式

**返回值**: (DataFrame, 列信息列表, 行数)

**示例**:
```python
# 打开Excel文件
df, columns, row_count = open_data_pandas("data.xlsx")

# 打开CSV文件
df, columns, row_count = open_data_pandas("data.csv")
```

**注意事项**:
- 文件必须存在且可读
- 支持的文件格式: .xlsx, .xls, .csv, .txt
- 返回的DataFrame可以直接用于其他技能

---
