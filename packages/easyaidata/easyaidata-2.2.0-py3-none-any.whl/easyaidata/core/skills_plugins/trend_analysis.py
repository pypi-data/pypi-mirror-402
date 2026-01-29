#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 趋势分析技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd
import tkinter as tk
import threading


def _skill_trend_analysis(df: pd.DataFrame, date_column: str, event_column: str, windows: int = 12,
                         method: str = "nunique", freq: str = "M", control_limit: str = "标准差",
                         engine: str = "pandas") -> pd.DataFrame:
    """
    趋势分析 - 分析数据趋势变化（支持pandas和polars），直接弹出趋势图绘制窗口

    Args:
        df: 输入数据框
        date_column: 日期列名
        event_column: 事件列名
        windows: 窗口大小
        method: 统计方法 (nunique, count, sum)
        freq: 频率 (D, W, M, Q, Y)
        control_limit: 控制限 (标准差, 1.5IQR)
        engine: 引擎类型 (pandas, polars)

    Returns:
        原始数据框（不修改数据）
    """
    try:
        from core.ror_and_tread_pd import TOOLS_trend_analysis_with_3_sd, TOOLS_trend_analysis_with_1_5IQR
        from core.open_and_close_pl import df2pl, pl2df
        from core.ror_and_tread_pl import TOOLS_trend_analysis_with_3_sd as TOOLS_trend_analysis_with_3_sd_pl
        from core.ror_and_tread_pl import TOOLS_trend_analysis_with_1_5IQR as TOOLS_trend_analysis_with_1_5IQR_pl
        
        def create_trend_plot():
            try:
                if engine == "polars":
                    df_pl = df2pl(df)
                    if control_limit == "标准差":
                        result_pl = TOOLS_trend_analysis_with_3_sd_pl(df_pl, date_column, event_column, windows, method, "draw", freq)
                    else:
                        result_pl = TOOLS_trend_analysis_with_1_5IQR_pl(df_pl, date_column, event_column, windows, method, "draw", freq)
                else:
                    if control_limit == "标准差":
                        TOOLS_trend_analysis_with_3_sd(df, date_column, event_column, windows, method, "draw", freq)
                    else:
                        TOOLS_trend_analysis_with_1_5IQR(df, date_column, event_column, windows, method, "draw", freq)
            except Exception as e:
                import traceback
                print(f"[ERROR] 趋势分析绘图错误: {str(e)}")
                traceback.print_exc()
        
        if tk._default_root:
            tk._default_root.after(0, create_trend_plot)
        else:
            create_trend_plot()
        
        return df
    except Exception as e:
        import traceback
        print(f"[ERROR] trend_analysis 错误: {str(e)}")
        traceback.print_exc()
        raise


class TrendAnalysisPlugin:
    """趋势分析技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="trend_analysis",
            category=SkillCategory.ANALYSIS,
            description="趋势分析 - 分析数据趋势变化（支持pandas和polars）",
            function=_skill_trend_analysis,
            parameters=[
                SkillParameter("date_column", "str", "日期列名", True),
                SkillParameter("event_column", "str", "事件列名", True),
                SkillParameter("windows", "int", "窗口大小", False, 12),
                SkillParameter("method", "str", "统计方法", False, "nunique", ["nunique", "count", "sum"]),
                SkillParameter("freq", "str", "频率", False, "M", ["D", "W", "M", "Q", "Y"]),
                SkillParameter("control_limit", "str", "控制限", False, "标准差", ["标准差", "1.5IQR"]),
                SkillParameter("engine", "str", "引擎类型", False, "pandas", ["pandas", "polars"])
            ],
            examples=["分析月度趋势", "分析年度趋势", "检测异常波动"]
        ))


# 自动注册技能
TrendAnalysisPlugin.register()
