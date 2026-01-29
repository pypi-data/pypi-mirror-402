#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 打开数据文件技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd
from typing import Tuple


def _skill_open_data_pandas(file_path: str) -> Tuple[pd.DataFrame, list, int]:
    """
    打开数据文件 - 使用Pandas引擎打开数据文件

    Args:
        file_path: 文件路径

    Returns:
        (DataFrame, 列信息列表, 行数)
    """
    from core.open_and_close import open_data_pandas
    return open_data_pandas(file_path)


class OpenDataPandasPlugin:
    """打开数据文件技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="open_data_pandas",
            category=SkillCategory.UTILITY,
            description="打开数据文件 - 使用Pandas引擎打开数据文件",
            function=_skill_open_data_pandas,
            parameters=[
                SkillParameter("file_path", "str", "文件路径", True)
            ],
            examples=["打开Excel文件", "打开CSV文件"]
        ))


# 自动注册技能
OpenDataPandasPlugin.register()
