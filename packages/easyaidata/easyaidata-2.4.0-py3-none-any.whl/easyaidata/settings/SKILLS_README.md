# 技能系统文档

本文档描述了系统中所有可用的技能，供大语言模型（LLM）使用。

## 技能调用规则

1. **技能名称**: 必须完全匹配，区分大小写
2. **参数顺序**: 按照参数定义的顺序传递
3. **必需参数**: 所有标记为 `required=True` 的参数必须提供
4. **可选参数**: 标记为 `required=False` 的参数可以省略，使用默认值
5. **参数类型**: 必须符合参数定义的类型（str, int, float, list, dict, column等）
6. **返回值**: 技能函数的返回值即为技能执行结果

## 技能列表

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


### data_masking

**分类**: 清洗
**功能**: 对指定列进行脱敏处理

**参数**:
- `selected_columns` (list, required): 要脱敏的列名列表
- `extra_option` (str, optional): 额外选项，默认"无"，可选值:
  - "无": 标准脱敏
  - "保留格式": 保留原始格式（如手机号格式）
  - "数字脱敏": 对数字进行特殊脱敏

**返回值**: DataFrame

**示例**:
```python
# 对手机号和身份证脱敏
result = data_masking(df, ["手机号", "身份证"])

# 保留格式脱敏
result = data_masking(df, ["手机号"], extra_option="保留格式")

# 数字脱敏
result = data_masking(df, ["收入"], extra_option="数字脱敏")
```

**注意事项**:
- selected_columns必须是一个列表
- 列名必须存在于DataFrame中
- 脱敏密钥会自动保存到用户目录

---


### groupby_and_pivot - 分组透视

**分类**: 分析  
**描述**: 创建数据透视表，支持多维度分组和聚合，支持pandas和polars两种引擎

**参数详解**:
- `methon` (list, **必需**): 透视参数列表
  - 格式: `[row_labels, col_labels, value_cols, agg_methods, text_content, all_ratio]`
  - `row_labels` (list): 行标签列表
    - 示例: `['部门']` - 按部门分组
    - 示例: `['部门', '地区']` - 按部门和地区分组
  - `col_labels` (list或dict): 列标签
    - 列表格式: `['产品']` - 透视列为产品
    - 字典格式: `{'产品': '产品名称'}` - 透视列为产品名称
    - 示例: `{'产品': '产品', '类别': '类别'}` - 多个透视列
  - `value_cols` (list): 值列列表
    - 示例: `['销售额']` - 统计销售额
    - 示例: `['销售额', '数量']` - 统计销售额和数量
  - `agg_methods` (list): 聚合方法列表
    - 示例: `['count']` - 计数
    - 示例: `['sum']` - 求和
    - 示例: `['mean']` - 求平均值
    - 示例: `['ValueCounts']` - 值计数（支持分隔符）
    - 支持的分隔符: `count_CH_semicolon`（中文分号）、`count_EN_semicolon`（英文分号）、`count_CH_comma`（中文逗号）、`count_EN_comma`（英文逗号）、`count_CH_commas`（中文顿号）、`count_ALL`（所有分隔符）
  - `text_content` (dict, 可选): 文本内容映射
    - 示例: `{'产品': '产品名称'}` - 替换产品列的显示名称
  - `all_ratio` (bool, 可选): 是否计算全部比率
    - 默认值: `False`
    - 示例: `True` - 计算全部比率
- `engine` (str, 可选): 引擎类型
  - 默认值: `"pandas"`
  - 可选值: `["pandas", "polars"]`

**使用示例**:
```python
from core.skills import execute_skill
import pandas as pd

# 准备数据
df = pd.DataFrame({
    '部门': ['销售', '技术', '销售', '技术'],
    '产品': ['A', 'A', 'B', 'B'],
    '销售额': [100, 200, 150, 250]
})

# 示例1: 按部门透视（简单计数）
result = execute_skill(
    'groupby_and_pivot',
    df,
    methon=[['部门'], ['产品'], ['销售额'], ['count'], {}, False],
    engine='pandas'
)
if result.success:
    print(result.data)

# 示例2: 按部门透视（求和）
result = execute_skill(
    'groupby_and_pivot',
    df,
    methon=[['部门'], ['产品'], ['销售额'], ['sum'], {}, False],
    engine='pandas'
)
if result.success:
    print(result.data)

# 示例3: 多维度分组（部门和产品）
result = execute_skill(
    'groupby_and_pivot',
    df,
    methon=[['部门', '产品'], {}, ['销售额'], ['sum'], {}, False],
    engine='pandas'
)
if result.success:
    print(result.data)

# 示例4: 使用值计数（支持分隔符）
result = execute_skill(
    'groupby_and_pivot',
    df,
    methon=[['部门'], ['产品'], ['销售额'], ['ValueCounts'], {}, False],
    engine='pandas'
)
if result.success:
    print(result.data)

# 示例5: 使用文本内容映射
result = execute_skill(
    'groupby_and_pivot',
    df,
    methon=[['部门'], {'产品': '产品名称'}, ['销售额'], ['sum'], {}, False],
    engine='pandas'
)
if result.success:
    print(result.data)
```

**返回结果的列名（特别要注意，因为和常规返回的字段名称不太一样）**:
```
假如入参methon为[['产品名称', '伤害'], {}, ['报告编码', '单位名称', '伤害表现'], ['count', 'nunique', 'ValueCounts'], {}, ['报告编码']]
那么结果的第一行示例为（注意字段名称）：
	产品名称: 注射泵
	伤害: 其他
	报告编码: 3
	单位名称: 2
	伤害表现: 空值(2)、药液输注不通(1)
	报告编码_构成比: 10.0

假如入参methon为[['产品名称', '伤害'], {'报告编码': '伤害'}, ['报告编码', '单位名称', '伤害表现'], ['count', 'nunique', 'ValueCounts'], {}, ['报告编码']]
那么结果的第一行示例为（注意字段名称）：
产品名称: 注射泵
伤害: 其他
报告编码_报告编码女: 2
报告编码_报告编码男: 1
单位名称: 2
伤害表现: 空值(2)、药液输注不通(1)
报告编码_构成比: 10.0
```

**对应函数**:
- pandas: `core.funtions.TOOLS_create_pivot_tool`
- polars: `core.funtions_pl.TOOLS_create_pivot_tool`

**注意事项**:
- methon参数格式必须正确，必须是包含6个元素的列表
- 值列应为数值类型（对于sum、mean等聚合）
- ValueCounts方法支持多种分隔符，适用于处理复合值
- text_content可以自定义列的显示名称
- 分组透视模式（字典）使用下划线分隔值列名和透视值，便于区分

---


### llm_call

**分类**: 工具
**功能**: 调用大语言模型API

**参数**:
- `prompt` (str, required): 提示词
- `model` (str, optional): 模型名称，默认"gpt-3.5-turbo"
- `temperature` (float, optional): 温度参数，默认0.7，范围0-2

**返回值**: str (LLM响应文本)

**示例**:
```python
# 调用GPT进行文本分析
response = llm_call("分析这段文本的情感: 今天天气真好")

# 使用不同的模型
response = llm_call("总结这段文本", model="gpt-4")

# 调整温度参数
response = llm_call("生成创意文案", temperature=1.0)
```

**注意事项**:
- prompt必须是非空字符串
- model必须是支持的模型名称
- temperature越高，输出越随机

---


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


### open_draw_manager

**分类**: 可视化
**功能**: 在绘图管理器窗口中显示数据

**参数**:
- `x_values_col` (str, optional): X数值列，默认None
- `x_label_col` (str, optional): X标签列，默认None
- `y_values_col` (str, optional): Y数值列，默认None
- `y_label_col` (str, optional): Y标签列，默认None
- `group_col` (str, optional): 分组列，默认None
- `plot_type` (str, optional): 图表类型，默认"柱状图"，可选值:
  - "柱状图"
  - "折线图"
  - "散点图"
  - "饼图"
  - "帕累托图"
  - "横向柱状图"
  - "分组柱状图"

**返回值**: DataFrame (原始数据框，不修改数据)

**示例**:
```python
# 创建柱状图
result = open_draw_manager(df, x_values_col="销售额", x_label_col="产品", plot_type="柱状图")

# 创建折线图
result = open_draw_manager(df, x_values_col="日期", y_values_col="销售额", plot_type="折线图")

# 创建饼图
result = open_draw_manager(df, x_label_col="产品", y_values_col="销售额", plot_type="饼图")

# 按部门分组显示
result = open_draw_manager(df, x_label_col="产品", y_values_col="销售额", group_col="部门", plot_type="分组柱状图")
```

**注意事项**:
- 会打开一个新的窗口
- 列名必须存在于DataFrame中
- 不同图表类型需要不同的参数组合
- 不修改原始数据

---


### open_in_new_tab

**分类**: 可视化
**功能**: 在主界面的新标签页中显示数据

**参数**:
- `methon` (dict, optional): 方法参数，默认None
- `ori` (str, optional): 原始数据标识，默认None

**返回值**: DataFrame (原始数据框，不修改数据)

**示例**:
```python
# 在新标签页中查看数据
result = open_in_new_tab(df)

# 带方法参数
result = open_in_new_tab(df, methon={"type": "pivot"})
```

**注意事项**:
- 需要在主界面上下文中执行
- 支持透视、筛选等功能
- 不修改原始数据

---


### open_table_viewer

**分类**: 可视化
**功能**: 在独立的表格查看器窗口中显示数据

**参数**: 无

**返回值**: DataFrame (原始数据框，不修改数据)

**示例**:
```python
# 在表格查看器中查看数据
result = open_table_viewer(df)
```

**注意事项**:
- 会打开一个新的窗口
- 支持分页、复制、导出等功能
- 不修改原始数据

---


### open_text_viewer

**分类**: 可视化
**功能**: 在文本查看器窗口中显示数据内容

**参数**: 无

**返回值**: DataFrame (原始数据框，不修改数据)

**示例**:
```python
# 在文本查看器中查看数据
result = open_text_viewer(df)
```

**注意事项**:
- 会打开一个新的窗口
- 以文本格式显示数据
- 支持复制、导出等功能

---


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


### ror_calculation

**分类**: 分析
**描述**: 计算报告比值比（Report Odds Ratio），用于药物不良反应分析，支持pandas和polars两种引擎

**参数详解**:
- `target_column` (str, **必需**): 目标列名
  - 示例: `"药品名称"` - 药品列
  - 示例: `"产品"` - 产品列
- `event_column` (str, **必需**): 事件列名
  - 示例: `"不良反应"` - 不良反应列
  - 示例: `"事件类型"` - 事件类型列
- `extra_event_column` (str, 可选): 额外事件列名
  - 默认值: `""`
- `code_column` (str, 可选): 编码列名
  - 默认值: `""`
- `result_mode` (str, 可选): 结果模式
  - 默认值: `"a>=3&ROR_CI_95_low>1"`
- `display_mode` (str, 可选): 显示模式
  - 默认值: `"详细表"`
  - 可选值: `["详细表", "简化表"]`
- `count_mode` (str, 可选): 计数模式
  - 默认值: `"nunique"`
  - 可选值: `["nunique", "count"]`
- `engine` (str, 可选): 引擎类型
  - 默认值: `"pandas"`
  - 可选值: `["pandas", "polars"]`

**使用示例**:
```python
from core.skills import execute_skill
import pandas as pd

# 准备数据
df = pd.DataFrame({
    '药品名称': ['A', 'A', 'B', 'B', 'C', 'C'],
    '不良反应': ['X', 'Y', 'X', 'Y', 'X', 'Y'],
    '病例ID': [1, 2, 3, 4, 5, 6]
})

# 示例1: 基本ROR计算
result = execute_skill(
    'ror_calculation',
    df,
    target_column='药品名称',
    event_column='不良反应',
    code_column='病例ID',
    engine='pandas'
)
if result.success:
    print(result.data)

# 示例2: 使用polars引擎
result = execute_skill(
    'ror_calculation',
    df,
    target_column='药品名称',
    event_column='不良反应',
    code_column='病例ID',
    result_mode='a>=3&ROR_CI_95_low>1',
    display_mode='详细表',
    count_mode='nunique',
    engine='polars'
)
if result.success:
    print(result.data)
```

**对应函数**: 
- pandas: `core.ror_and_tread_pd.TOOLS_ROR_from_df`
- polars: `core.ror_and_tread_pl.TOOLS_ROR_from_df`

**注意事项**:
- 确保目标列、事件列都存在于数据中
- ROR计算需要足够的数据量（建议至少30个事件）
- 结果包含ROR值、置信区间、P值等统计信息

---


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


### trend_analysis

**分类**: 分析
**功能**: 分析数据趋势变化（支持pandas和polars）

**参数**:
- `date_column` (str, required): 日期列名
- `event_column` (str, required): 事件列名
- `windows` (int, optional): 窗口大小，默认12
- `method` (str, optional): 统计方法，默认"nunique"，可选值: "nunique", "count", "sum"
- `freq` (str, optional): 频率，默认"M"，可选值:
  - "D": 日
  - "W": 周
  - "M": 月
  - "Q": 季度
  - "Y": 年
- `control_limit` (str, optional): 控制限，默认"标准差"，可选值: "标准差", "1.5IQR"
- `engine` (str, optional): 引擎类型，默认"pandas"，可选值: "pandas", "polars"

**返回值**: DataFrame

**示例**:
```python
# 分析月度趋势
result = trend_analysis(df, "日期", "事件", windows=12, method="nunique", freq="M", control_limit="标准差")

# 分析年度趋势
result = trend_analysis(df, "日期", "事件", windows=4, method="count", freq="Y", control_limit="1.5IQR")

# 使用polars引擎
result = trend_analysis(df, "日期", "事件", windows=12, method="nunique", freq="M", control_limit="标准差", engine="polars")
```

**注意事项**:
- date_column必须是日期类型
- event_column必须存在
- windows应该根据freq合理设置
- control_limit影响异常检测的敏感度

---



## 技能使用建议

### 1. 数据处理流程

典型的数据处理流程：
1. 使用 `open_data_pandas` 打开数据文件
2. 使用 `data_cleaning` 清洗数据
3. 使用 `pandas_operations` 进行数据转换和处理（筛选、排序、聚合等）
4. 使用 `groupby_and_pivot` 进行深度数据分析
5. 使用 `open_table_viewer` 或 `open_draw_manager` 查看结果
6. 使用 `save_data_file` 保存结果

### 2. 参数验证

在调用技能前，确保：
- 所有必需参数都已提供
- 参数类型正确
- 列名存在于DataFrame中
- 枚举值在允许的范围内

### 3. 错误处理

如果技能调用失败，检查：
- 参数是否正确
- 列名是否存在
- 数据类型是否匹配
- 文件路径是否有效

### 4. 性能优化

- 大数据集建议使用 `engine="polars"`
- 合理设置窗口大小和频率参数
- 避免重复计算

---

## 附录: 参数类型说明

- `str`: 字符串类型
- `int`: 整数类型
- `float`: 浮点数类型
- `list`: 列表类型
- `dict`: 字典类型
- `column`: 列名类型（字符串，必须是DataFrame中的列名）
- `required`: 必需参数
- `optional`: 可选参数（有默认值）
