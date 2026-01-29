### data_cleaning

**分类**: 清洗
**功能**: 执行数据清洗操作（支持pandas和polars）

**参数**:
- `method` (str, required): 清洗方法，可选值:
  - "remove_duplicates": 删除重复行
  - "dropna": 删除缺失值
  - "fillna": 填充缺失值
  - "strip_whitespace": 去除字符串两端的空格
  - "standardize_case": 标准化大小写
  - "remove_outliers": 删除异常值
  - "normalize": 数据标准化
  - "delete_columns": 删除指定列
  - "keep_columns": 保留指定列
  - "sort_data": 排序数据
  - "rename_column": 重命名列
  - "convert_format": 转换格式
- `params` (dict, required): 清洗参数，根据method不同而不同:
  - remove_duplicates: {"subset": [列名列表], "keep": "first/last/false"}
  - dropna: {"subset": [列名列表], "how": "any/all"}
  - fillna: {"columns": [列名列表], "method": "手工填写/前向填充/后向填充/均值填充/众数填充/50%分位数填充/最大值填充/最小值填充", "fill_value": 填充值}
  - strip_whitespace: {"columns": [列名列表]}
  - standardize_case: {"columns": [列名列表], "case": "upper/lower/title"}
  - remove_outliers: {"columns": [列名列表], "method": "iqr/zscore", "threshold": 数值}
  - normalize: {"columns": [列名列表], "method": "minmax/standard"}
  - delete_columns: {"columns": [列名列表]}
  - keep_columns: {"columns": [列名列表]}
  - sort_data: {"columns": [列名列表], "ascending": True/False}
  - rename_column: {"old_name": "旧列名", "new_name": "新列名"}
  - convert_format: {"columns": [列名列表], "target_format": "str/float/int/round2/percent_round2/percent_integer/日期/年份/月份/季度"}
- `engine` (str, optional): 引擎类型，默认"pandas"，可选值: "pandas", "polars"

**返回值**: DataFrame

**示例**:
```python
# 删除重复行
result = data_cleaning(df, "remove_duplicates", {"subset": ["姓名"], "keep": "first"})

# 删除缺失值
result = data_cleaning(df, "dropna", {"subset": ["年龄", "收入"], "how": "any"})

# 填充缺失值
result = data_cleaning(df, "fillna", {"columns": ["年龄"], "method": "均值填充"})

# 去除空格
result = data_cleaning(df, "strip_whitespace", {"columns": ["姓名", "城市"]})

# 标准化大小写
result = data_cleaning(df, "standardize_case", {"columns": ["城市"], "case": "upper"})

# 删除异常值
result = data_cleaning(df, "remove_outliers", {"columns": ["收入"], "method": "iqr", "threshold": 1.5})

# 数据标准化
result = data_cleaning(df, "normalize", {"columns": ["收入"], "method": "minmax"})

# 删除指定列
result = data_cleaning(df, "delete_columns", {"columns": ["临时列"]})

# 保留指定列
result = data_cleaning(df, "keep_columns", {"columns": ["姓名", "年龄", "收入"]})

# 排序数据
result = data_cleaning(df, "sort_data", {"columns": ["收入"], "ascending": False})

# 重命名列
result = data_cleaning(df, "rename_column", {"old_name": "旧列名", "new_name": "新列名"})

# 转换格式
result = data_cleaning(df, "convert_format", {"columns": ["日期"], "target_format": "日期"})

# 使用polars引擎
result = data_cleaning(df, "remove_duplicates", {"subset": ["姓名"], "keep": "first"}, engine="polars")
```

**注意事项**:
- params必须是一个字典
- 不同的method需要不同的params结构
- engine参数影响性能，大数据集建议使用polars

---
