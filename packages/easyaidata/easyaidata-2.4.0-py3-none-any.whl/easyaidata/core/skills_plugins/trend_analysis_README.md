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
