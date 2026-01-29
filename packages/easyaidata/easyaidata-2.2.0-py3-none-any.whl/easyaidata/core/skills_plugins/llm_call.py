#!/usr/bin/env python
# -*- coding: utf-8 -*-
# LLM调用技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill, SkillResult

def _skill_llm_call(df, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> SkillResult:
    """
    LLM调用 - 调用大语言模型API

    Args:
        df: 输入数据框（该技能未使用此参数）
        prompt: 提示词
        model: 模型名称
        temperature: 温度参数

    Returns:
        SkillResult包含LLM响应文本
    """
    from core.llm2 import LLM_Functions
    llm = LLM_Functions()
    response = llm.call_api(prompt, model, temperature)
    
    return SkillResult(
        success=True,
        data=response,
        message=f"LLM调用成功，使用模型: {model}"
    )


class LlmCallPlugin:
    """LLM调用技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="llm_call",
            category=SkillCategory.UTILITY,
            description="LLM调用 - 调用大语言模型API",
            function=_skill_llm_call,
            parameters=[
                SkillParameter("prompt", "str", "提示词", True),
                SkillParameter("model", "str", "模型名称", False, "gpt-3.5-turbo"),
                SkillParameter("temperature", "float", "温度参数", False, 0.7)
            ],
            examples=["调用GPT进行文本分析", "使用LLM生成摘要"]
        ))


# 自动注册技能
LlmCallPlugin.register()
