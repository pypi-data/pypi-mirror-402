#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 保存数据文件技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_save_data_file(df: pd.DataFrame, file_path: str, file_format: str) -> None:
    """
    保存数据文件 - 保存数据到文件

    Args:
        df: 要保存的数据框
        file_path: 文件路径
        file_format: 文件格式 (xlsx, csv等）
    """
    from core.open_and_close import save_data_file
    save_data_file(df, file_path, file_format)


class SaveDataFilePlugin:
    """保存数据文件技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="save_data_file",
            category=SkillCategory.UTILITY,
            description="保存数据文件 - 保存数据到文件",
            function=_skill_save_data_file,
            parameters=[
                SkillParameter("file_path", "str", "文件路径", True),
                SkillParameter("file_format", "str", "文件格式", True)
            ],
            examples=["保存为Excel", "保存为CSV"]
        ))


# 自动注册技能
SaveDataFilePlugin.register()
