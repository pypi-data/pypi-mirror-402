#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 数据清洗技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_data_cleaning(df: pd.DataFrame, method: str, params: dict, engine: str = "pandas") -> pd.DataFrame:
    """
    数据清洗 - 执行数据清洗操作（支持pandas和polars）

    Args:
        df: 输入数据框
        method: 清洗方法，可选值:
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
        params: 清洗参数，根据method不同而不同:
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
        engine: 引擎类型，默认"pandas"，可选值: "pandas", "polars"

    Returns:
        清洗后的数据框
    """
    if engine == "polars":
        from core.open_and_close_pl import df2pl, pl2df
        from core.clean_pl import DataCleaner as DataCleanerPL
        df_pl = df2pl(df)
        cleaner = DataCleanerPL(df_pl)
        result_pl = cleaner.clean(method, params)
        return pl2df(result_pl)
    else:
        from core.clean import DataCleaner
        cleaner = DataCleaner(df)
        return cleaner.clean(method, params)


class DataCleaningPlugin:
    """数据清洗技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="data_cleaning",
            category=SkillCategory.CLEAN,
            description="数据清洗 - 执行数据清洗操作（支持pandas和polars）",
            function=_skill_data_cleaning,
            parameters=[
                SkillParameter("method", "str", "清洗方法", True),
                SkillParameter("params", "dict", "清洗参数", True),
                SkillParameter("engine", "str", "引擎类型", False, "pandas", ["pandas", "polars"])
            ],
            examples=["删除重复行", "删除缺失值", "填充缺失值", "去除空格", "标准化大小写", "删除异常值", "数据标准化"]
        ))


# 自动注册技能
DataCleaningPlugin.register()
