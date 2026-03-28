# 动态消息生成器
# Dynamic Message Generator

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DynamicMessageGenerator:
    """动态消息生成器 - 插件式架构"""

    def __init__(self, config_loader=None):
        """
        初始化动态消息生成器

        Args:
            config_loader: 配置加载器实例
        """
        self.config_loader = config_loader
        self.plugins = {}
        self.plugin_load_order = [
            "time_awareness",
            "emotion_perception",
            "interest_learning",
            "context_awareness",
            "generation_strategy",
        ]

        # 状态
        self.is_initialized = False
        self.failure_count = 0
        self.max_failures = 3

        logger.info("[DynamicMessageGenerator] 初始化完成")

    async def initialize(self):
        """初始化生成器"""
        if self.is_initialized:
            logger.warning("[DynamicMessageGenerator] 已经初始化")
            return

        try:
            # 加载插件
            await self._load_plugins()

            self.is_initialized = True
            logger.info("[DynamicMessageGenerator] 初始化成功")

        except Exception as e:
            logger.error(f"[DynamicMessageGenerator] 初始化失败: {e}")
            raise

    async def _load_plugins(self):
        """加载所有插件"""
        logger.info("[DynamicMessageGenerator] 开始加载插件...")

        for plugin_name in self.plugin_load_order:
            try:
                plugin = await self._load_plugin(plugin_name)
                if plugin:
                    self.plugins[plugin_name] = plugin
                    logger.info(
                        f"[DynamicMessageGenerator] 加载插件成功: {plugin_name}"
                    )
                else:
                    logger.warning(
                        f"[DynamicMessageGenerator] 插件加载失败: {plugin_name}"
                    )

            except Exception as e:
                logger.error(
                    f"[DynamicMessageGenerator] 加载插件异常 {plugin_name}: {e}"
                )

        logger.info(
            f"[DynamicMessageGenerator] 插件加载完成，共加载 {len(self.plugins)} 个插件"
        )

    async def _load_plugin(self, plugin_name: str):
        """加载单个插件"""
        try:
            # 动态导入插件
            module_path = f"config.proactive_chat.plugins.{plugin_name}.plugin"
            module = __import__(module_path, fromlist=["Plugin"])

            # 创建插件实例
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class:
                plugin = plugin_class(config={})
                return plugin

            return None

        except ImportError as e:
            logger.warning(
                f"[DynamicMessageGenerator] 插件模块不存在: {plugin_name} - {e}"
            )
            return None
        except Exception as e:
            logger.error(f"[DynamicMessageGenerator] 加载插件失败: {plugin_name} - {e}")
            return None

    async def generate_message(
        self, user_id: int, context: Dict = None
    ) -> Optional[str]:
        """
        生成动态消息

        Args:
            user_id: 用户ID
            context: 上下文信息

        Returns:
            生成的消息，失败时返回None
        """
        try:
            # 检查是否已初始化
            if not self.is_initialized:
                await self.initialize()

            # 收集上下文信息
            context_data = await self._collect_context(user_id, context)

            # 选择生成策略
            strategy_plugin = self.plugins.get("generation_strategy")
            if strategy_plugin:
                strategy = strategy_plugin.select_strategy(context_data)
            else:
                strategy = "time_awareness"

            # 生成消息
            if strategy in self.plugins:
                plugin = self.plugins[strategy]
                message = await plugin.generate(context_data)
                if message:
                    return message

            # 如果策略插件没有生成消息，尝试其他插件
            for plugin_name, plugin in self.plugins.items():
                try:
                    message = await plugin.generate(context_data)
                    if message:
                        return message
                except Exception as e:
                    logger.error(
                        f"[DynamicMessageGenerator] 插件 {plugin_name} 生成消息失败: {e}"
                    )

            return None

        except Exception as e:
            self.failure_count += 1
            logger.error(
                f"[DynamicMessageGenerator] 生成消息失败 (第{self.failure_count}次): {e}"
            )

            # 检查是否达到最大失败次数
            if self.failure_count >= self.max_failures:
                logger.error("[DynamicMessageGenerator] 连续失败次数过多，跳过本次生成")
                self.failure_count = 0

            return None

    async def _collect_context(self, user_id: int, context: Dict = None) -> Dict:
        """收集上下文信息"""
        context_data = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "context": context or {},
        }

        # 调用各个插件收集上下文
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin_context = await plugin.collect_context(user_id, context)
                context_data[plugin_name] = plugin_context
            except Exception as e:
                logger.error(
                    f"[DynamicMessageGenerator] 插件 {plugin_name} 收集上下文失败: {e}"
                )

        return context_data

    async def reload_config(self):
        """重载配置"""
        try:
            logger.info("[DynamicMessageGenerator] 开始重载配置...")

            # 重新加载插件
            for plugin_name, plugin in self.plugins.items():
                try:
                    if hasattr(plugin, "update_config"):
                        await plugin.update_config({})
                except Exception as e:
                    logger.error(
                        f"[DynamicMessageGenerator] 重载插件配置失败 {plugin_name}: {e}"
                    )

            logger.info("[DynamicMessageGenerator] 配置重载完成")

        except Exception as e:
            logger.error(f"[DynamicMessageGenerator] 重载配置失败: {e}")

    async def shutdown(self):
        """关闭生成器"""
        try:
            logger.info("[DynamicMessageGenerator] 开始关闭...")

            # 关闭所有插件
            for plugin_name, plugin in self.plugins.items():
                try:
                    if hasattr(plugin, "shutdown"):
                        await plugin.shutdown()
                except Exception as e:
                    logger.error(
                        f"[DynamicMessageGenerator] 关闭插件失败 {plugin_name}: {e}"
                    )

            self.is_initialized = False
            logger.info("[DynamicMessageGenerator] 已关闭")

        except Exception as e:
            logger.error(f"[DynamicMessageGenerator] 关闭失败: {e}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "is_initialized": self.is_initialized,
            "plugins_loaded": len(self.plugins),
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "plugin_names": list(self.plugins.keys()),
        }
