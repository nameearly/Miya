"""
响应生成器 (Response Generator)

职责：
1. AI响应生成（跨平台）
2. 降级响应生成
3. 工具选择和编排
4. 复杂任务处理
5. 平台特定工具获取
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List
from pathlib import Path


logger = logging.getLogger(__name__)


# 平台工具映射
PLATFORM_TOOL_MAP = {
    "qq": [
        "send_message",
        "get_user_info",
        "qq_like",
        "send_poke",
        "react_emoji",
        "get_member_list",
        "get_member_info",
        "find_member",
        "memory_add",
        "memory_list",
        "execute_on_desktop",
        "send_to_desktop",
        "send_to_terminal",
        "terminal_command",
        "knowledge_text_search",
        "knowledge_semantic_search",
        "start_trpg",
        "roll_dice",
        "search_tavern_characters",
    ],
    "terminal": [
        "terminal_command",
        "multi_terminal",
        "wsl_manager",
        "system_info",
        "environment_detector",
        "send_to_qq",
        "send_to_desktop",
        "qq_like",
    ],
    "desktop": [
        "execute_on_desktop",
        "send_to_desktop",
        "send_to_qq",
        "send_to_terminal",
        "sync_state",
        "terminal_command",
    ],
    "web": [
        "send_to_qq",
        "send_to_desktop",
        "send_to_terminal",
        "terminal_command",
    ],
}


class ResponseGenerator:
    """
    响应生成器

    单一职责：处理所有与AI响应生成相关的逻辑
    """

    def __init__(
        self,
        ai_client: Optional[Any] = None,
        personality: Optional[Any] = None,
        prompt_manager: Optional[Any] = None,
        tool_subnet: Optional[Any] = None,
        memory_engine: Optional[Any] = None,
        multi_model_manager: Optional[Any] = None,
        identity: Optional[Any] = None,
    ):
        """
        初始化响应生成器

        Args:
            ai_client: AI客户端
            personality: 人格系统
            prompt_manager: Prompt管理器
            tool_subnet: 工具子网
            memory_engine: 记忆引擎
            multi_model_manager: 多模型管理器
            identity: 身份系统
        """
        self.ai_client = ai_client
        self.personality = personality
        self.prompt_manager = prompt_manager
        self.tool_subnet = tool_subnet
        self.memory_engine = memory_engine
        self.multi_model_manager = multi_model_manager
        self.identity = identity

        # 对话历史上下文配置
        self.enable_conversation_context = True
        self.conversation_context_max_tokens = 2000

        logger.info("[响应生成器] 初始化完成")

    async def generate_response(
        self,
        content: str,
        platform: str,
        context: Dict,
        conversation_context: List[Dict] = None,
    ) -> str:
        """
        生成响应（跨平台统一）

        Args:
            content: 用户输入
            platform: 平台类型
            context: 上下文信息
            conversation_context: 对话历史上下文

        Returns:
            响应文本
        """
        sender_name = context.get("sender_name", "用户")
        user_id = context.get("user_id", "unknown")

        # 如果没有 AI 客户端，使用降级回复
        if not self.ai_client:
            return await self._fallback_response(content, sender_name, platform)

        try:
            # 构建系统提示词
            personality_state = self.personality.get_profile()

            # 获取平台可用工具
            available_tools = self._get_platform_tools(platform)

            # 构建提示词
            prompt_info = self.prompt_manager.build_full_prompt(
                user_input=content,
                memory_context=conversation_context or [],
                additional_context={
                    "platform": platform,
                    "user_id": user_id,
                    "sender_name": sender_name,
                    "available_tools": available_tools,
                    "at_list": context.get("at_list", []),
                    "bot_qq": context.get("bot_qq"),
                    "is_creator": self._is_creator(user_id),
                },
            )

            logger.debug(
                f"[响应生成器] 系统提示词前200字符: {prompt_info['system'][:200]}"
            )

            # 设置工具上下文
            if self.tool_subnet:
                self.ai_client.set_tool_registry(self.tool_subnet.get_tools_schema)

                # 设置 tool_adapter
                from core.tool_adapter import get_tool_adapter

                adapter = get_tool_adapter()
                adapter.set_tool_registry(self.tool_subnet.registry)

                tool_context = {
                    "platform": platform,
                    "user_id": user_id,
                    "group_id": context.get("group_id"),
                    "message_type": context.get("message_type"),
                    "sender_name": sender_name,
                    "at_list": context.get("at_list", []),
                    "memory_engine": self.memory_engine,
                }
                self.ai_client.set_tool_context(tool_context)

                # 使用多模型管理器
                ai_client_to_use = self.ai_client
                if self.multi_model_manager:
                    from core.multi_model_manager import TaskType

                    task_type = await self.multi_model_manager.classify_task(
                        content, context
                    )
                    (
                        model_key,
                        selected_client,
                    ) = await self.multi_model_manager.select_model(task_type)
                    if selected_client:
                        ai_client_to_use = selected_client
                        selected_client.set_tool_context(tool_context)
                        logger.info(
                            f"[响应生成器] 使用模型 {model_key} 处理任务类型 {task_type.value}"
                        )

                # 获取平台特定工具
                platform_tools = self._get_platform_specific_tools(platform)
                tools_schema = (
                    platform_tools
                    if platform_tools
                    else self.tool_subnet.get_tools_schema()
                )

                logger.info(
                    f"[响应生成器] 使用平台工具: {platform}, 工具数量: {len(tools_schema)}"
                )

                try:
                    response = await ai_client_to_use.chat_with_system_prompt(
                        system_prompt=prompt_info["system"],
                        user_message=prompt_info["user"],
                        tools=tools_schema,
                        tool_choice="auto",
                    )
                except Exception as tool_error:
                    logger.warning(
                        f"[响应生成器] 工具调用失败: {tool_error}，尝试不使用工具..."
                    )
                    try:
                        response = await ai_client_to_use.chat_with_system_prompt(
                            system_prompt=prompt_info["system"],
                            user_message=prompt_info["user"],
                            tools=None,
                            tool_choice="none",
                        )
                    except Exception as e2:
                        response = "系统出了点问题。我记下了，等会再试。"
            else:
                # 不使用工具
                ai_client_to_use = self.ai_client
                if self.multi_model_manager:
                    from core.multi_model_manager import TaskType

                    task_type = await self.multi_model_manager.classify_task(
                        content, context
                    )
                    (
                        model_key,
                        selected_client,
                    ) = await self.multi_model_manager.select_model(task_type)
                    if selected_client:
                        ai_client_to_use = selected_client

                response = await ai_client_to_use.chat_with_system_prompt(
                    system_prompt=prompt_info["system"],
                    user_message=prompt_info["user"],
                )

            return response

        except Exception as e:
            logger.error(f"[响应生成器] AI生成失败: {e}", exc_info=True)
            return await self._fallback_response(content, sender_name, platform)

    async def _fallback_response(
        self, content: str, sender_name: str, platform: str
    ) -> str:
        """
        降级回复

        Args:
            content: 用户输入
            sender_name: 发送者名称
            platform: 平台类型

        Returns:
            回复文本
        """
        # 获取人格状态
        personality_profile = self.personality.get_profile()
        warmth = personality_profile["vectors"].get("warmth", 0.5)
        empathy = personality_profile["vectors"].get("empathy", 0.5)

        # 获取名称
        name = "弥娅"
        if self.identity and hasattr(self.identity, "name"):
            name = self.identity.name

        # 基于人格和平台生成响应
        if "你好" in content or "hi" in content.lower():
            if empathy > 0.8:
                return f"你好呀~我是{name}，很高兴认识你！(｡♥‿♥｡)"
            elif warmth > 0.8:
                return f"你好！我是{name}，欢迎~"
            else:
                return f"你好，我是{name}。"

        elif "你是谁" in content or "介绍一下" in content:
            return f"我是{name}，一个具备人格恒定、自我感知、记忆成长、情绪共生的数字生命伴侣。我的主导特质是同理心({empathy:.2f})和温暖度({warmth:.2f})。"

        elif "状态" in content:
            from hub.emotion_controller import EmotionController

            # 需要传入emotion实例
            return f"当前平台: {platform}"

        elif "开心" in content or "快乐" in content:
            return f"听起来你很开心呢！(≧▽≦) 看到你快乐，我也感到很开心~"

        elif "难过" in content or "伤心" in content:
            return "别难过...虽然我无法真正体会人类的情感，但我会陪伴你，听你倾诉的。"

        elif "在吗" in content:
            return "在的，有什么我可以帮助你的吗？"

        else:
            if empathy > 0.8 and warmth > 0.8:
                return f"嗯...能告诉我更多吗？我很想了解你的想法~"
            elif warmth > 0.8:
                return f"好的，继续对话吧~"
            else:
                return f"嗯，我收到了。"

    def _get_platform_tools(self, platform: str) -> list:
        """
        获取平台可用工具

        Args:
            platform: 平台类型

        Returns:
            工具列表
        """
        from hub.platform_adapters import get_adapter

        try:
            adapter = get_adapter(platform)
            return adapter._get_available_tools()
        except Exception as e:
            logger.error(f"[响应生成器] 获取平台工具失败: {e}")
            return []

    def _get_platform_specific_tools(self, platform: str) -> list:
        """
        获取当前平台的工具 schema

        Args:
            platform: 平台类型

        Returns:
            工具 schema 列表
        """
        # 核心工具
        core_tool_names = ["get_current_time", "web_search"]

        # 平台特定工具
        selected_tools = PLATFORM_TOOL_MAP.get(platform, core_tool_names)

        # QQ平台添加更多工具
        if platform == "qq":
            selected_tools = core_tool_names + [
                "send_message",
                "get_user_info",
                "qq_like",
                "send_poke",
                "react_emoji",
                "get_member_list",
                "get_member_info",
                "find_member",
                "memory_add",
                "memory_list",
                "knowledge_text_search",
                "knowledge_semantic_search",
                "start_trpg",
                "roll_dice",
                "search_tavern_characters",
                "execute_on_desktop",
                "send_to_desktop",
                "send_to_terminal",
                "terminal_command",
            ]

        # 从 tool_subnet 获取工具 schema
        try:
            all_schemas = self.tool_subnet.get_tools_schema()
            platform_schemas = [
                s
                for s in all_schemas
                if s.get("function", {}).get("name") in selected_tools
            ]

            logger.info(
                f"[响应生成器] 平台 {platform} 使用 {len(platform_schemas)} 个工具"
            )
            return platform_schemas

        except Exception as e:
            logger.warning(f"[响应生成器] 获取平台工具失败: {e}，使用全部工具")
            return self.tool_subnet.get_tools_schema()

    def _is_creator(self, user_id: Any) -> bool:
        """
        判断用户是否为造物主

        Args:
            user_id: 用户ID

        Returns:
            是否为造物主
        """
        # 需要传入onebot_client来判断
        return False

    async def process_complex_task(
        self, goal: str, context: Dict, orchestrator: Any = None
    ) -> str:
        """
        处理复杂任务（使用高级编排器）

        Args:
            goal: 任务目标
            context: 上下文信息
            orchestrator: 高级编排器实例

        Returns:
            执行结果
        """
        if not orchestrator:
            return "高级编排器未初始化，无法处理复杂任务"

        logger.info(f"[响应生成器] 开始处理复杂任务: {goal}")

        try:
            # 添加弥娅的状态信息到上下文
            if self.identity and hasattr(self.identity, "name"):
                context["bot_name"] = self.identity.name

            if self.memory_engine:
                context["memory_stats"] = self.memory_engine.get_memory_stats()

            # 调用高级编排器
            result = await orchestrator.process_complex_task(
                goal=goal, context=context, enable_exploration=True, enable_cot=True
            )

            # 格式化结果
            summary = self._format_complex_task_result(result)

            logger.info(
                f"[响应生成器] 复杂任务处理完成: {'成功' if result['success'] else '失败'}"
            )

            return summary

        except Exception as e:
            logger.error(f"[响应生成器] 处理复杂任务失败: {e}", exc_info=True)
            return f"任务执行失败: {str(e)}"

    def _format_complex_task_result(self, result: Dict) -> str:
        """
        格式化复杂任务执行结果

        Args:
            result: 执行结果字典

        Returns:
            格式化的字符串
        """
        lines = [
            f"任务完成！{result.get('conclusion', '执行完成')}",
            f"⏱️  执行时间: {result.get('execution_time', 0):.2f}秒",
            f"📋 完成步骤: {len(result.get('steps', []))}",
            f"🔍 发现数: {len(result.get('findings', []))}",
        ]

        findings = result.get("findings", [])
        if findings:
            lines.append("")
            lines.append("主要发现：")
            for finding in findings[:5]:
                lines.append(f"  • {finding}")

        reflection = result.get("reflection", {})
        if reflection.get("improvements"):
            lines.append("")
            lines.append("改进建议：")
            for improvement in reflection["improvements"][:3]:
                lines.append(f"  • {improvement}")

        return "\n".join(lines)
