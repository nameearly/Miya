# 情绪感知插件
# Emotion Perception Plugin

import logging
import asyncio
from typing import Dict, List, Optional, Any
from ..base_plugin import BasePlugin

class Plugin(BasePlugin):
    def __init__(self, name: str = "emotion_perception", config: Dict = None):
        super().__init__(name, config)
        
        # 情绪关键词配置
        self.emotion_keywords = self.config.get("emotion_keywords", {})
        
        # 情绪响应策略
        self.response_strategies = self.config.get("response_strategies", {})
        
        # 灵敏度
        self.sensitivity = self.config.get("sensitivity", "medium")
    
    async def collect_context(self, user_id: int, context: Dict = None) -> Dict:
        # 分析用户消息中的情绪关键词
        user_message = context.get("message", "") if context else ""
        
        detected_emotions = []
        for emotion_type, config in self.emotion_keywords.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword in user_message:
                    detected_emotions.append({
                        "type": emotion_type,
                        "keyword": keyword,
                        "weight": config.get("weight", 1.0),
                        "strategy": config.get("response_strategy", "")
                    })
        
        return {
            "detected_emotions": detected_emotions,
            "primary_emotion": detected_emotions[0]["type"] if detected_emotions else None,
            "confidence": len(detected_emotions) > 0
        }
    
    async def generate(self, context_data: Dict) -> str:
        emotion_context = context_data.get(self.name, {})
        
        if not emotion_context.get("confidence", False):
            return ""
        
        primary_emotion = emotion_context.get("primary_emotion")
        if not primary_emotion:
            return ""
        
        # 获取情绪响应策略
        strategy = self.emotion_keywords.get(primary_emotion, {}).get("response_strategy", "")
        if not strategy:
            return ""
        
        # 获取策略配置
        strategy_config = self.response_strategies.get(strategy, {})
        templates = strategy_config.get("templates", [])
        
        if templates:
            import random
            return random.choice(templates)
        
        return ""
