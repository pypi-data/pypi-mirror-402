# 技能插件系统使用指南

## 概述

技能插件系统允许你通过创建独立的 Python 文件来扩展数据分析智能体的功能，无需修改核心代码。

## 目录结构

```
core/
├── skills.py              # 核心技能模块
├── skill_loader.py        # 技能加载器
└── skills_plugins/        # 技能插件目录
    ├── filter_rows.py     # 行过滤插件
    ├── convert_column_type.py  # 列类型转换插件
    ├── calculate_statistics.py   # 统计分析插件
    └── your_skill.py     # 你的自定义技能
```

## 如何创建新技能

### 方法 1: 使用模板生成器

```python
from core.skill_loader import create_skill_plugin_template

# 创建技能模板
file_path = create_skill_plugin_template("My Custom Skill")
print(f"模板已创建: {file_path}")
```

### 方法 2: 手动创建技能文件

在 `core/skills_plugins/` 目录下创建一个新的 Python 文件，例如 `my_skill.py`：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 我的自定义技能

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_my_custom_skill(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    我的自定义技能实现

    Args:
        df: 输入数据框
        **kwargs: 技能参数

    Returns:
        处理后的数据框
    """
    # 在这里实现你的技能逻辑
    return df


class MyCustomSkillPlugin:
    """我的自定义技能插件"""

    author = "Your Name"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="my_custom_skill",
            category=SkillCategory.UTILITY,
            description="我的自定义技能 - 技能描述",
            function=_skill_my_custom_skill,
            parameters=[
                SkillParameter("param_name", "str", "参数描述", True)
            ],
            examples=[
                "示例1",
                "示例2"
            ]
        ))


# 自动注册技能
MyCustomSkillPlugin.register()
```

## 技能分类

技能支持以下分类：

- `FILTER` - 筛选
- `TRANSFORM` - 转换
- `AGGREGATE` - 聚合
- `CLEAN` - 清洗
- `ANALYSIS` - 分析
- `VISUALIZE` - 可视化
- `UTILITY` - 工具

## 参数类型

支持以下参数类型：

- `str` - 字符串
- `int` - 整数
- `float` - 浮点数
- `bool` - 布尔值
- `list` - 列表
- `dict` - 字典
- `column` - 列名（自动验证列是否存在）

## 自动加载

技能插件会在以下时机自动加载：

1. 当 `core.skills` 模块被导入时
2. 当调用 `load_plugin_skills()` 函数时

## 动态加载

你也可以在运行时动态加载技能：

```python
from core.skill_loader import get_skill_loader

# 获取技能加载器
loader = get_skill_loader()

# 发现技能文件
skill_files = loader.discover_skills()

# 加载单个技能
loader.load_skill_from_file(skill_files[0])

# 加载所有技能
results = loader.load_all_skills()

# 重新加载技能
loader.reload_skill(skill_files[0])

# 获取技能信息
info = loader.get_skill_info()
print(info)
```

## 已有技能示例

### 1. filter_rows - 行过滤

```python
# 过滤出年龄大于30的行
df_filtered = execute_skill("filter_rows", df, column="年龄", operator=">", value=30)

# 过滤出城市为北京的行
df_filtered = execute_skill("filter_rows", df, column="城市", operator=="", value="北京")

# 过滤出姓名包含'张'的行
df_filtered = execute_skill("filter_rows", df, column="姓名", operator="contains", value="张")
```

### 2. convert_column_type - 列类型转换

```python
# 将年龄列转换为整数类型
df_converted = execute_skill("convert_column_type", df, column="年龄", target_type="int")

# 将日期列转换为日期时间类型
df_converted = execute_skill("convert_column_type", df, column="日期", target_type="datetime")
```

### 3. calculate_statistics - 统计分析

```python
# 计算所有数值列的统计信息
stats = execute_skill("calculate_statistics", df)

# 计算指定列的统计信息
stats = execute_skill("calculate_statistics", df, columns=["年龄", "收入"])
```

## 最佳实践

1. **命名规范**: 技能文件名使用小写字母和下划线，如 `my_skill.py`
2. **函数命名**: 技能实现函数使用 `_skill_` 前缀，如 `_skill_my_skill`
3. **插件类**: 创建一个插件类，包含 `author` 和 `version` 属性
4. **错误处理**: 在技能实现中添加适当的错误处理
5. **文档注释**: 为函数和类添加详细的文档字符串
6. **参数验证**: 使用 `SkillParameter` 的 `options` 参数限制可选值

## 调试技巧

1. 查看已加载的技能：

```python
from core.skills import get_all_skills

skills = get_all_skills()
for name, skill in skills.items():
    print(f"{name}: {skill.description}")
```

2. 查看技能参数：

```python
from core.skills import get_skill

skill = get_skill("my_custom_skill")
params = skill.get_parameter_info()
print(params)
```

3. 测试技能：

```python
from core.skills import execute_skill

result = execute_skill("my_custom_skill", df, param1="value1")
if result.success:
    print("成功:", result.message)
    print("数据:", result.data)
else:
    print("失败:", result.message)
    print("建议:", result.suggestions)
```

## 故障排除

### 技能未加载

1. 检查文件是否在 `core/skills_plugins/` 目录下
2. 检查文件名是否以 `_` 开头（会被忽略）
3. 检查文件是否有语法错误
4. 查看日志输出

### 技能执行失败

1. 检查参数是否正确
2. 检查列名是否存在
3. 查看 `result.suggestions` 获取修复建议
4. 查看 `result.error_type` 了解错误类型

## 扩展阅读

- 查看 `core/skills.py` 了解技能基类
- 查看 `core/skill_loader.py` 了解加载机制
- 查看现有插件实现学习最佳实践
