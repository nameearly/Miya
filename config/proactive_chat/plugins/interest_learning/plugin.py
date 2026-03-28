# 兴趣学习插件
# Interest Learning Plugin

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..base_plugin import BasePlugin


class Plugin(BasePlugin):
    def __init__(self, name: str = "interest_learning", config: Dict = None):
        super().__init__(name, config)

        # 兴趣分类配置
        self.categories = self.config.get("categories", {})

        # 学习参数
        self.learning_params = self.config.get("learning_params", {})
        self.decay_days = self.learning_params.get("decay_days", 30)
        self.max_interests = self.learning_params.get("max_interests", 20)

        # 用户兴趣存储
        self.user_interests = {}

    async def collect_context(self, user_id: int, context: Dict = None) -> Dict:
        # 分析用户消息中的兴趣关键词
        user_message = context.get("message", "") if context else ""

        detected_interests = []
        for category_name, category_config in self.categories.items():
            keywords = category_config.get("keywords", [])
            for keyword in keywords:
                if keyword in user_message:
                    detected_interests.append(
                        {
                            "category": category_name,
                            "keyword": keyword,
                            "weight": category_config.get("weight", 0.5),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        # 更新用户兴趣
        if user_id not in self.user_interests:
            self.user_interests[user_id] = []

        for interest in detected_interests:
            self.user_interests[user_id].append(interest)

        # 清理过期兴趣
        self._cleanup_old_interests(user_id)

        # 获取用户主要兴趣
        main_interests = self._get_main_interests(user_id)

        return {
            "detected_interests": detected_interests,
            "main_interests": main_interests,
            "has_interests": len(main_interests) > 0,
        }

    def _cleanup_old_interests(self, user_id: int):
        """清理过期兴趣"""
        if user_id not in self.user_interests:
            return

        cutoff_time = datetime.now() - timedelta(days=self.decay_days)
        self.user_interests[user_id] = [
            interest
            for interest in self.user_interests[user_id]
            if datetime.fromisoformat(interest["timestamp"]) > cutoff_time
        ]

    def _get_main_interests(self, user_id: int) -> List[Dict]:
        """获取用户主要兴趣"""
        if user_id not in self.user_interests:
            return []

        # 按权重和频率排序
        interests = self.user_interests[user_id]

        # 统计每个类别的权重
        category_weights = {}
        for interest in interests:
            category = interest["category"]
            weight = interest["weight"]
            if category not in category_weights:
                category_weights[category] = 0
            category_weights[category] += weight

        # 排序并返回前N个
        sorted_categories = sorted(
            category_weights.items(), key=lambda x: x[1], reverse=True
        )[: self.max_interests]

        return [
            {
                "category": category,
                "weight": weight,
                "name": self.categories.get(category, {}).get("name", category),
            }
            for category, weight in sorted_categories
        ]

    async def generate(self, context_data: Dict) -> str:
        interest_context = context_data.get(self.name, {})

        if not interest_context.get("has_interests", False):
            return ""

        main_interests = interest_context.get("main_interests", [])
        if not main_interests:
            return ""

        # 基于主要兴趣生成话题
        primary_interest = main_interests[0]
        category = primary_interest["category"]

        # 获取该类别的主题
        category_config = self.categories.get(category, {})
        topics = category_config.get("topics", [])

        if topics:
            import random

            topic = random.choice(topics)
            return f"关于{topic}，最近怎么样。"

        return ""
