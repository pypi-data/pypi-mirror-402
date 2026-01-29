#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 打开文本查看器技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_open_text_viewer(df: pd.DataFrame) -> pd.DataFrame:
    """
    打开文本查看器 - 在文本查看器窗口中显示数据内容

    Args:
        df: 要显示的数据框

    Returns:
        原始数据框（不修改数据）
    """
    # 将DataFrame转换为文本格式
    content = df.to_string(index=False)
    
    from core.viewer import PROGRAM_display_content_in_textbox
    PROGRAM_display_content_in_textbox(content, edit='n')
    
    return df


class OpenTextViewerPlugin:
    """打开文本查看器技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="open_text_viewer",
            category=SkillCategory.VISUALIZE,
            description="打开文本查看器 - 在文本查看器窗口中显示数据内容，支持复制、导出等功能",
            function=_skill_open_text_viewer,
            parameters=[],
            examples=["在文本查看器中查看数据", "以文本格式显示数据"]
        ))


# 自动注册技能
OpenTextViewerPlugin.register()
