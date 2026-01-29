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
