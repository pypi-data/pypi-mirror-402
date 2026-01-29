#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Pandas操作技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd
import numpy as np
from typing import Union, List, Optional


def _skill_pandas_operations(df: pd.DataFrame, operation: str, params: dict) -> pd.DataFrame:
    """
    Pandas操作 - 执行各种Pandas数据操作

    Args:
        df: 输入数据框
        operation: 操作类型，可选值:
          - "filter": 数据筛选
          - "sort": 数据排序
          - "merge": 数据合并
          - "concat": 数据拼接
          - "groupby": 分组聚合
          - "apply": 应用函数
          - "map": 映射转换
          - "pivot": 数据透视
          - "melt": 数据重塑
          - "sample": 数据采样
          - "drop_duplicates": 删除重复
          - "fillna": 填充缺失值
          - "dropna": 删除缺失值
          - "replace": 替换值
          - "rename": 重命名列
          - "astype": 类型转换
          - "round": 数值四舍五入
          - "abs": 绝对值
          - "clip": 裁剪值
          - "rank": 排名
          - "shift": 数据偏移
          - "diff": 差分计算
          - "cumsum": 累计求和
          - "rolling": 滚动窗口
          - "resample": 时间重采样
          - "str_extract": 字符串提取
          - "str_replace": 字符串替换
          - "str_split": 字符串分割
        params: 操作参数，根据operation不同而不同:
          - filter: {"condition": "筛选条件表达式", "columns": [列名列表]}
          - sort: {"columns": [列名列表], "ascending": True/False}
          - merge: {"right_df": DataFrame, "on": [列名列表], "how": "inner/left/right/outer"}
          - concat: {"dfs": [DataFrame列表], "axis": 0/1, "ignore_index": True/False}
          - groupby: {"by": [列名列表], "agg": {列名: 聚合函数}}
          - apply: {"func": 函数, "axis": 0/1}
          - map: {"column": 列名, "mapping": {映射字典}}
          - pivot: {"index": 列名, "columns": 列名, "values": 列名}
          - melt: {"id_vars": [列名列表], "value_vars": [列名列表]}
          - sample: {"n": 样本数量, "frac": 采样比例, "random_state": 随机种子}
          - drop_duplicates: {"subset": [列名列表], "keep": "first/last/false"}
          - fillna: {"value": 填充值, "method": "ffill/bfill", "columns": [列名列表]}
          - dropna: {"subset": [列名列表], "how": "any/all"}
          - replace: {"to_replace": 旧值, "value": 新值, "columns": [列名列表]}
          - rename: {"columns": {旧列名: 新列名}}
          - astype: {"columns": {列名: 类型}}
          - round: {"decimals": 小数位数, "columns": [列名列表]}
          - abs: {"columns": [列名列表]}
          - clip: {"lower": 下限, "upper": 上限, "columns": [列名列表]}
          - rank: {"column": 列名, "method": "average/min/max/first/dense", "ascending": True/False}
          - shift: {"periods": 偏移量, "columns": [列名列表]}
          - diff: {"periods": 差分期数, "columns": [列名列表]}
          - cumsum: {"columns": [列名列表]}
          - rolling: {"column": 列名, "window": 窗口大小, "agg": 聚合函数}
          - resample: {"column": 时间列, "rule": 重采样规则, "agg": 聚合函数}
          - str_extract: {"column": 列名, "pattern": 正则表达式}
          - str_replace: {"column": 列名, "pat": 模式, "repl": 替换值}
          - str_split: {"column": 列名, "pat": 分隔符, "expand": True/False}

    Returns:
        操作后的数据框
    """
    result_df = df.copy()
    
    if operation == "filter":
        condition = params.get("condition", "")
        columns = params.get("columns", [])
        
        if condition and isinstance(condition, str) and condition.strip():
            try:
                result_df = result_df.query(condition)
            except Exception as e:
                error_msg = str(e)
                if "True" in error_msg and "boolean label" in error_msg:
                    raise ValueError(f"筛选条件错误: 请使用字符串表达式，例如 '销售额 > 150' 或 '产品 == \"A\"'")
                raise ValueError(f"筛选条件错误: {error_msg}")
        elif condition and not isinstance(condition, str):
            raise ValueError(f"筛选条件错误: condition参数必须是字符串类型，当前类型为 {type(condition).__name__}")
        
        if columns:
            result_df = result_df[columns]
    
    elif operation == "sort":
        columns = params.get("columns", [])
        ascending = params.get("ascending", True)
        
        if columns:
            result_df = result_df.sort_values(by=columns, ascending=ascending)
    
    elif operation == "merge":
        right_df = params.get("right_df")
        on = params.get("on")
        left_on = params.get("left_on")
        right_on = params.get("right_on")
        how = params.get("how", "inner")
        
        if right_df is not None and isinstance(right_df, pd.DataFrame):
            # 根据提供的参数选择合适的合并方式
            merge_kwargs = {"how": how}
            if on is not None:
                merge_kwargs["on"] = on
            elif left_on is not None and right_on is not None:
                merge_kwargs["left_on"] = left_on
                merge_kwargs["right_on"] = right_on
            else:
                raise ValueError("merge操作需要提供on参数，或者同时提供left_on和right_on参数")
            
            result_df = pd.merge(result_df, right_df, **merge_kwargs)
        else:
            raise ValueError("merge操作需要提供right_df参数")
    
    elif operation == "concat":
        dfs = params.get("dfs", [])
        axis = params.get("axis", 0)
        ignore_index = params.get("ignore_index", True)
        
        if dfs:
            all_dfs = [result_df] + dfs
            result_df = pd.concat(all_dfs, axis=axis, ignore_index=ignore_index)
    
    elif operation == "groupby":
        by = params.get("by", [])
        agg = params.get("agg", {})
        
        if by and agg:
            result_df = result_df.groupby(by, as_index=False).agg(agg)
    
    elif operation == "apply":
        func = params.get("func")
        axis = params.get("axis", 0)
        
        if func:
            result_df = result_df.apply(func, axis=axis)
    
    elif operation == "map":
        column = params.get("column")
        mapping = params.get("mapping", {})
        
        if column and mapping:
            result_df[column] = result_df[column].map(mapping)
    
    elif operation == "pivot":
        index = params.get("index")
        columns = params.get("columns")
        values = params.get("values")
        
        if index and columns and values:
            result_df = result_df.pivot_table(index=index, columns=columns, values=values, aggfunc='first').reset_index()
    
    elif operation == "melt":
        id_vars = params.get("id_vars", [])
        value_vars = params.get("value_vars", [])
        
        result_df = result_df.melt(id_vars=id_vars, value_vars=value_vars)
    
    elif operation == "sample":
        n = params.get("n")
        frac = params.get("frac")
        random_state = params.get("random_state")
        
        if n is not None:
            result_df = result_df.sample(n=n, random_state=random_state)
        elif frac is not None:
            result_df = result_df.sample(frac=frac, random_state=random_state)
    
    elif operation == "drop_duplicates":
        subset = params.get("subset")
        keep = params.get("keep", "first")
        
        result_df = result_df.drop_duplicates(subset=subset, keep=keep)
    
    elif operation == "fillna":
        value = params.get("value")
        method = params.get("method")
        columns = params.get("columns", [])
        
        if columns:
            if value is not None:
                result_df[columns] = result_df[columns].fillna(value)
            elif method:
                result_df[columns] = result_df[columns].fillna(method=method)
        else:
            if value is not None:
                result_df = result_df.fillna(value)
            elif method:
                result_df = result_df.fillna(method=method)
    
    elif operation == "dropna":
        subset = params.get("subset")
        how = params.get("how", "any")
        
        result_df = result_df.dropna(subset=subset, how=how)
    
    elif operation == "replace":
        to_replace = params.get("to_replace")
        value = params.get("value")
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].replace(to_replace, value)
        else:
            result_df = result_df.replace(to_replace, value)
    
    elif operation == "rename":
        columns_map = params.get("columns", {})
        
        if columns_map:
            result_df = result_df.rename(columns=columns_map)
    
    elif operation == "astype":
        columns_map = params.get("columns", {})
        
        if columns_map:
            for col, dtype in columns_map.items():
                result_df[col] = result_df[col].astype(dtype)
    
    elif operation == "round":
        decimals = params.get("decimals", 2)
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].round(decimals)
        else:
            result_df = result_df.round(decimals)
    
    elif operation == "abs":
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].abs()
        else:
            result_df = result_df.abs()
    
    elif operation == "clip":
        lower = params.get("lower")
        upper = params.get("upper")
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].clip(lower=lower, upper=upper)
        else:
            result_df = result_df.clip(lower=lower, upper=upper)
    
    elif operation == "rank":
        column = params.get("column")
        method = params.get("method", "average")
        ascending = params.get("ascending", True)
        
        if column:
            result_df[f"{column}_rank"] = result_df[column].rank(method=method, ascending=ascending)
    
    elif operation == "shift":
        periods = params.get("periods", 1)
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].shift(periods=periods)
        else:
            result_df = result_df.shift(periods=periods)
    
    elif operation == "diff":
        periods = params.get("periods", 1)
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].diff(periods=periods)
        else:
            result_df = result_df.diff(periods=periods)
    
    elif operation == "cumsum":
        columns = params.get("columns", [])
        
        if columns:
            result_df[columns] = result_df[columns].cumsum()
        else:
            result_df = result_df.cumsum()
    
    elif operation == "rolling":
        column = params.get("column")
        window = params.get("window")
        agg = params.get("agg", "mean")
        
        if column and window:
            if agg == "mean":
                result_df[f"{column}_rolling_{window}_{agg}"] = result_df[column].rolling(window=window).mean()
            elif agg == "sum":
                result_df[f"{column}_rolling_{window}_{agg}"] = result_df[column].rolling(window=window).sum()
            elif agg == "std":
                result_df[f"{column}_rolling_{window}_{agg}"] = result_df[column].rolling(window=window).std()
            elif agg == "max":
                result_df[f"{column}_rolling_{window}_{agg}"] = result_df[column].rolling(window=window).max()
            elif agg == "min":
                result_df[f"{column}_rolling_{window}_{agg}"] = result_df[column].rolling(window=window).min()
    
    elif operation == "resample":
        column = params.get("column")
        rule = params.get("rule")
        agg = params.get("agg", "mean")
        
        if column and rule:
            result_df[column] = pd.to_datetime(result_df[column])
            result_df = result_df.set_index(column)
            
            if agg == "mean":
                result_df = result_df.resample(rule).mean()
            elif agg == "sum":
                result_df = result_df.resample(rule).sum()
            elif agg == "count":
                result_df = result_df.resample(rule).count()
            elif agg == "first":
                result_df = result_df.resample(rule).first()
            elif agg == "last":
                result_df = result_df.resample(rule).last()
            
            result_df = result_df.reset_index()
    
    elif operation == "str_extract":
        column = params.get("column")
        pattern = params.get("pattern")
        
        if column and pattern:
            result_df[f"{column}_extract"] = result_df[column].str.extract(pattern)
    
    elif operation == "str_replace":
        column = params.get("column")
        pat = params.get("pat")
        repl = params.get("repl", "")
        
        if column and pat:
            result_df[column] = result_df[column].str.replace(pat, repl)
    
    elif operation == "str_split":
        column = params.get("column")
        pat = params.get("pat", ",")
        expand = params.get("expand", False)
        
        if column:
            result_df[column] = result_df[column].str.split(pat, expand=expand)
    
    else:
        raise ValueError(f"未知的操作类型: {operation}")
    
    return result_df


class PandasOperationsPlugin:
    """Pandas操作技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="pandas_operations",
            category=SkillCategory.TRANSFORM,
            description="Pandas操作 - 执行各种Pandas数据操作（筛选、排序、合并、聚合、转换等）",
            function=_skill_pandas_operations,
            parameters=[
                SkillParameter("operation", "str", "操作类型", True, "", [
                    "filter", "sort", "merge", "concat", "groupby", "apply", "map", "pivot", "melt",
                    "sample", "drop_duplicates", "fillna", "dropna", "replace", "rename", "astype",
                    "round", "abs", "clip", "rank", "shift", "diff", "cumsum", "rolling", "resample",
                    "str_extract", "str_replace", "str_split"
                ]),
                SkillParameter("params", "dict", "操作参数", True)
            ],
            examples=[
                "筛选数据",
                "排序数据",
                "合并数据表",
                "分组聚合",
                "填充缺失值",
                "删除重复值",
                "替换值",
                "类型转换",
                "数据透视",
                "字符串处理"
            ]
        ))


# 自动注册技能
PandasOperationsPlugin.register()
