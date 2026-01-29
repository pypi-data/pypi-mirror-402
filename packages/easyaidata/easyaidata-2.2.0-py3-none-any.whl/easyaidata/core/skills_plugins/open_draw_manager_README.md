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
