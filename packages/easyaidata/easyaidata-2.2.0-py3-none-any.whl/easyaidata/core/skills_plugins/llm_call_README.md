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
