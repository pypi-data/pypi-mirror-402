#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ROR计算技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_ror_calculation(df: pd.DataFrame, target_column: str, event_column: str, extra_event_column: str = "", 
                          code_column: str = "", result_mode: str = "a>=3&ROR_CI_95_low>1",
                          display_mode: str = "详细表", count_mode: str = "nunique",
                          engine: str = "pandas") -> pd.DataFrame:
    """
    ROR计算 - 计算报告比值比（支持pandas和polars）

    Args:
        df: 输入数据框
        target_column: 目标列名
        event_column: 事件列名
        extra_event_column: 额外事件列名
        code_column: 编码列名
        result_mode: 结果模式
        display_mode: 显示模式 (详细表, 简化表)
        count_mode: 计数模式 (nunique, count)
        engine: 引擎类型 (pandas, polars)

    Returns:
        ROR计算结果数据框
    """
    if engine == "polars":
        from core.open_and_close_pl import df2pl, pl2df
        from core.ror_and_tread_pl import TOOLS_ROR_from_df
        df_pl = df2pl(df)
        result_pl = TOOLS_ROR_from_df(df_pl, target_column, event_column, extra_event_column, code_column, result_mode, display_mode, count_mode)
        return pl2df(result_pl)
    else:
        from core.ror_and_tread_pd import TOOLS_ROR_from_df
        return TOOLS_ROR_from_df(df, target_column, event_column, extra_event_column, code_column, result_mode, display_mode, count_mode)


class RorCalculationPlugin:
    """ROR计算技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="ror_calculation",
            category=SkillCategory.ANALYSIS,
            description="ROR计算 - 计算报告比值比（支持pandas和polars）",
            function=_skill_ror_calculation,
            parameters=[
                SkillParameter("target_column", "str", "目标列名", True),
                SkillParameter("event_column", "str", "事件列名", True),
                SkillParameter("extra_event_column", "str", "额外事件列名", False, ""),
                SkillParameter("code_column", "str", "编码列名", False, ""),
                SkillParameter("result_mode", "str", "结果模式", False, "a>=3&ROR_CI_95_low>1"),
                SkillParameter("display_mode", "str", "显示模式", False, "详细表", ["详细表", "简化表"]),
                SkillParameter("count_mode", "str", "计数模式", False, "nunique", ["nunique", "count"]),
                SkillParameter("engine", "str", "引擎类型", False, "pandas", ["pandas", "polars"])
            ],
            examples=["计算药品不良反应ROR", "计算事件发生率"]
        ))


# 自动注册技能
RorCalculationPlugin.register()
