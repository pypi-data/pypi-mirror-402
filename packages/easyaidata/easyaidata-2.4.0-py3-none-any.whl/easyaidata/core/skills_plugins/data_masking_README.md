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
