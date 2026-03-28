# 生成策略插件
# Generation Strategy Plugin

import logging
import asyncio
from typing import Dict, List, Optional, Any
from ..base_plugin import BasePlugin

class Plugin(BasePlugin):
    def __init__(self, name: str = "generation_strategy", config: Dict = None):
        super().__init__(name, config)
        
        # 策略配置
        self.strategies = self.config.get("strategies", {})
        
        # 选择参数
        self.selection_params = self.config.get("selection_params", {})
        self.min_confidence = self.selection_params.get("min_confidence", 0.6)
        
        # 策略权重
        self.strategy_weights = {}
        for strategy_name, strategy_config in self.strategies.items():
            if strategy_config.get("enabled", True):
                self.strategy_weights[strategy_name] = strategy_config.get("weight", 0.5)
    
    async def collect_context(self, user_id: int, context: Dict = None) -> Dict:
        # 收集策略相关的上下文信息
        return {
            "available_strategies": list(self.strategies.keys()),
            "strategy_weights": self.strategy_weights,
            "min_confidence": self.min_confidence
        }
    
    async def generate(self, context_data: Dict) -> str:
        # 这个插件不直接生成消息，而是选择策略
        # 实际的消息生成由其他插件完成
        return ""
    
    def select_strategy(self, context_data: Dict) -> str:
        """选择生成策略"""
        # 分析各个插件的上下文信息
        strategy_scores = {}
        
        # 时间感知策略
        time_context = context_data.get("time_awareness", {})
        if time_context:
            time_slot = time_context.get("time_slot", "")
            if time_slot:
                strategy_scores["time_based"] = self.strategy_weights.get("time_based", 0.3)
        
        # 上下文感知策略
        context_plugin = context_data.get("context_awareness", {})
        if context_plugin and context_plugin.get("has_pending", False):
            strategy_scores["context_based"] = self.strategy_weights.get("context_based", 0.4)
        
        # 情绪感知策略
        emotion_context = context_data.get("emotion_perception", {})
        if emotion_context and emotion_context.get("confidence", False):
            strategy_scores["emotion_based"] = self.strategy_weights.get("emotion_based", 0.1)
        
        # 兴趣学习策略
        interest_context = context_data.get("interest_learning", {})
        if interest_context and interest_context.get("has_interests", False):
            strategy_scores["interest_based"] = self.strategy_weights.get("interest_based", 0.2)
        
        # 选择得分最高的策略
        if strategy_scores:
            selected_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
            return selected_strategy
        
        # 默认策略
        return "time_based"
