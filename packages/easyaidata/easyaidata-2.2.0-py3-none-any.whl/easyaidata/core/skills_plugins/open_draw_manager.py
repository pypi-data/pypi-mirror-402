#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 绘图管理器技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd
import tkinter as tk
import threading


def _skill_open_draw_manager(df: pd.DataFrame, x_values_col: str = None, x_label_col: str = None, 
                          y_values_col: str = None, y_label_col: str = None, 
                          group_col: str = None, plot_type: str = "柱状图") -> pd.DataFrame:
    """
    打开绘图管理器 - 在绘图管理器窗口中显示数据

    Args:
        df: 要显示的数据框
        x_values_col: X数值列（可选）
        x_label_col: X标签列（可选）
        y_values_col: Y数值列（可选）
        y_label_col: Y标签列（可选）
        group_col: 分组列（可选）
        plot_type: 图表类型（柱状图、折线图、散点图、饼图等）

    Returns:
        原始数据框（不修改数据）
    """
    try:
        from core.draw import DRAW_plot_df
        
        plot_scheme = {
            'plot_type': plot_type,
            'x_values_col': x_values_col,
            'x_label_col': x_label_col,
            'y_values_col': y_values_col,
            'y_label_col': y_label_col,
            'group_col': group_col
        }
        
        print(f"[DEBUG] 调用 DRAW_plot_df，参数: {plot_scheme}")
        
        # 在主线程中创建窗口
        dialog_ref = [None]
        error_ref = [None]
        event = threading.Event()
        
        def create_dialog():
            try:
                dialog = DRAW_plot_df(df, plot_scheme)
                dialog_ref[0] = dialog
                print(f"[DEBUG] DRAW_plot_df 返回: {dialog}")
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
            
            if dialog_ref[0]:
                # 保存窗口引用，防止被垃圾回收
                _skill_open_draw_manager._window = dialog_ref[0]
        else:
            # 如果没有主窗口，直接创建
            dialog = DRAW_plot_df(df, plot_scheme)
            _skill_open_draw_manager._window = dialog
        
        return df
    except Exception as e:
        import traceback
        print(f"[ERROR] open_draw_manager 错误: {str(e)}")
        traceback.print_exc()
        raise


# 静态变量用于保存窗口引用
_skill_open_draw_manager._window = None


class OpenDrawManagerPlugin:
    """打开绘图管理器技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="open_draw_manager",
            category=SkillCategory.VISUALIZE,
            description="打开绘图管理器 - 在绘图管理器窗口中显示数据",
            function=_skill_open_draw_manager,
            parameters=[
                SkillParameter("x_values_col", "column", "X数值列", False, None),
                SkillParameter("x_label_col", "column", "X标签列", False, None),
                SkillParameter("y_values_col", "column", "Y数值列", False, None),
                SkillParameter("y_label_col", "column", "Y标签列", False, None),
                SkillParameter("group_col", "column", "分组列", False, None),
                SkillParameter("plot_type", "str", "图表类型", False, "柱状图", 
                    ["柱状图", "折线图", "散点图", "饼图", "帕累托图", "横向柱状图", "分组柱状图"])
            ],
            examples=["创建柱状图", "创建折线图", "创建饼图", "按部门分组显示"]
        ))


# 自动注册技能
OpenDrawManagerPlugin.register()
