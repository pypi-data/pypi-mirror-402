#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 打开表格查看器技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd
import tkinter as tk
import threading


def _skill_open_table_viewer(df: pd.DataFrame) -> pd.DataFrame:
    """
    打开表格查看器 - 在独立的表格查看器窗口中显示数据

    Args:
        df: 要显示的数据框

    Returns:
        原始数据框（不修改数据）
    """
    try:
        from core.viewer import PROGRAM_DataFrameViewer
        
        # 在主线程中创建窗口
        dialog_ref = [None]
        error_ref = [None]
        event = threading.Event()
        
        def create_dialog():
            try:
                dialog = PROGRAM_DataFrameViewer(df)
                dialog_ref[0] = dialog
            except Exception as e:
                import traceback
                error_ref[0] = e
                traceback.print_exc()
            finally:
                event.set()
        
        # 获取主窗口并使用 after 在主线程中执行
        if tk._default_root:
            tk._default_root.after(0, create_dialog)
            # 等待窗口创建完成
            event.wait(timeout=10)  # 最多等待10秒
            
            if error_ref[0]:
                raise error_ref[0]
        else:
            # 如果没有主窗口，直接创建
            dialog = PROGRAM_DataFrameViewer(df)
            _skill_open_table_viewer._window = dialog
        
        return df
    except Exception as e:
        import traceback
        print(f"[ERROR] open_table_viewer 错误: {str(e)}")
        traceback.print_exc()
        raise


class OpenTableViewerPlugin:
    """打开表格查看器技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="open_table_viewer",
            category=SkillCategory.VISUALIZE,
            description="打开表格查看器 - 在独立的表格查看器窗口中显示数据",
            function=_skill_open_table_viewer,
            parameters=[],
            examples=["在表格查看器中查看数据", "打开详细的表格视图"]
        ))


# 自动注册技能
OpenTableViewerPlugin.register()
