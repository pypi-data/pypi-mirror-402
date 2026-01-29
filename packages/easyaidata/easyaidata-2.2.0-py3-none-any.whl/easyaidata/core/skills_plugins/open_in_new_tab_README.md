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
