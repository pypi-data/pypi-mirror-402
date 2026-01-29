#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 数据脱敏技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd
import os
import json
from datetime import datetime


def _skill_data_masking(df: pd.DataFrame, selected_columns: list, extra_option: str = "无") -> pd.DataFrame:
    """
    数据脱敏 - 对指定列进行脱敏处理

    Args:
        df: 输入数据框
        selected_columns: 要脱敏的列名列表
        extra_option: 额外选项 (无, 保留格式, 数字脱敏)

    Returns:
        脱敏后的数据框
    """
    from core.clean import TOOLS_data_masking
    result_df, mapping_keys = TOOLS_data_masking(df, selected_columns, extra_option)
    
    # 保存密钥
    user_home = os.path.expanduser("~")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    key_file_name = f"脱敏恢复密匙{timestamp}.json"
    key_file_path = os.path.join(user_home, key_file_name)
    with open(key_file_path, "w", encoding="utf-8") as f:
        json.dump(mapping_keys, f, ensure_ascii=False, indent=4)
    print(f"[提示] 脱敏密钥已保存到：{key_file_path}")
    
    return result_df


class DataMaskingPlugin:
    """数据脱敏技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="data_masking",
            category=SkillCategory.CLEAN,
            description="数据脱敏 - 对指定列进行脱敏处理",
            function=_skill_data_masking,
            parameters=[
                SkillParameter("selected_columns", "list", "要脱敏的列名列表", True),
                SkillParameter("extra_option", "str", "额外选项", False, "无", ["无", "保留格式", "数字脱敏"])
            ],
            examples=["对手机号列脱敏", "对身份证列脱敏", "对姓名列脱敏"]
        ))


# 自动注册技能
DataMaskingPlugin.register()
