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
