### pandas_operations

**分类**: 转换
**功能**: 执行各种Pandas数据操作（筛选、排序、合并、聚合、转换等）

**参数**:
- `operation` (str, required): 操作类型，可选值:
  - 数据操作: "filter", "sort", "merge", "concat"
  - 聚合分析: "groupby", "pivot", "melt"
  - 数据处理: "sample", "drop_duplicates", "fillna", "dropna", "replace"
  - 列操作: "rename", "astype"
  - 数值计算: "round", "abs", "clip", "rank", "shift", "diff", "cumsum"
  - 时间序列: "rolling", "resample"
  - 字符串处理: "str_extract", "str_replace", "str_split"
- `params` (dict, required): 操作参数，根据operation不同而不同

**返回值**: DataFrame

**示例**:
```python
# 筛选数据
result = execute_skill("pandas_operations", df, operation="filter", params={"condition": "销售额 > 150"})

# 排序数据
result = execute_skill("pandas_operations", df, operation="sort", params={"columns": ["销售额"], "ascending": False})

# 分组聚合
result = execute_skill("pandas_operations", df, operation="groupby", params={"by": ["产品"], "agg": {"销售额": "sum"}})

# 填充缺失值
result = execute_skill("pandas_operations", df, operation="fillna", params={"value": 0})

# 删除重复值
result = execute_skill("pandas_operations", df, operation="drop_duplicates", params={"keep": "first"})

# 类型转换
result = execute_skill("pandas_operations", df, operation="astype", params={"columns": {"销售额": "float64"}})

# 四舍五入
result = execute_skill("pandas_operations", df, operation="round", params={"decimals": 2, "columns": ["销售额"]})

# 数据透视
result = execute_skill("pandas_operations", df, operation="pivot", params={"index": "产品", "columns": "月份", "values": "销售额"})

# 滚动窗口
result = execute_skill("pandas_operations", df, operation="rolling", params={"column": "销售额", "window": 3, "agg": "mean"})

# 字符串替换
result = execute_skill("pandas_operations", df, operation="str_replace", params={"column": "描述", "pat": "旧文本", "repl": "新文本"})
```

**注意事项**:
- 所有操作都会返回一个新的DataFrame，不会修改原始数据
- 对于复杂的筛选条件，使用query()方法支持的语法
- 筛选条件必须是字符串类型，例如: `"销售额 > 150"` 或 `"产品 == 'A'"`
- 筛选条件支持逻辑运算符: `and`, `or`, `not`
- 筛选条件支持比较运算符: `>`, `<`, `>=`, `<=`, `==`, `!=`
- 筛选条件支持字符串包含: `"产品.str.contains('A')"`
- 合并操作时，确保两个DataFrame有共同的列
- 时间重采样操作需要先将时间列转换为datetime类型
- 字符串操作仅对字符串类型的列有效

---
