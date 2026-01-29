#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 分组透视技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_groupby_and_pivot(df: pd.DataFrame, methon: list, engine: str = "pandas") -> pd.DataFrame:
    """
    分组透视 - 创建数据透视表（支持pandas和polars）

    Args:
        df: 输入数据框
        methon: 透视参数列表
        engine: 引擎类型 (pandas, polars)

    Returns:
        透视后的数据框
    """
    if engine == "polars":
        from core.open_and_close_pl import df2pl, pl2df
        from core.funtions_pl import TOOLS_create_pivot_tool
        df_pl = df2pl(df)
        result_pl = TOOLS_create_pivot_tool(df_pl, methon)
        return pl2df(result_pl)
    else:
        from core.funtions import TOOLS_create_pivot_tool
        return TOOLS_create_pivot_tool(df, methon)


class GroupbyAndPivotPlugin:
    """分组透视技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="groupby_and_pivot",
            category=SkillCategory.ANALYSIS,
            description="分组透视 - 创建数据透视表（支持pandas和polars）",
            function=_skill_groupby_and_pivot,
            parameters=[
                SkillParameter("methon", "list", "透视参数列表", True),
                SkillParameter("engine", "str", "引擎类型", False, "pandas", ["pandas", "polars"])
            ],
            examples=["按部门和产品透视销售数据", "创建多维数据透视表"]
        ))


# 自动注册技能
GroupbyAndPivotPlugin.register()
