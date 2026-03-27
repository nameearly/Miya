"""
决策层 Hub
监听 M-Link 消息并协调各子网进行决策

架构：门面模式 (Facade Pattern)
- DecisionHub 作为协调器，委托给各个专业处理器
- PerceptionHandler: 感知处理
- ResponseGenerator: 响应生成
- EmotionController: 情绪控制
- MemoryManager: 记忆管理
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Optional, Any, List
from datetime import datetime
from pathlib import Path

from mlink.message import Message, MessageType, FlowType
from core.constants import Encoding
from memory.session_manager import (
    SessionManager,
    init_session_manager,
    get_session_manager,
    SessionCategory,
)

# 导入新的处理器类
from hub.perception_handler import PerceptionHandler
from hub.response_generator import ResponseGenerator
from hub.emotion_controller import EmotionController
from hub.memory_manager import MemoryManager

# 导入辅助模块
from hub.conversation_context import ConversationContextManager
from hub.platform_tools import PlatformToolsManager
from hub.session_handler import SessionHandler
from core.personality import Personality


logger = logging.getLogger(__name__)


class DecisionHub:
    """
    决策层 Hub (门面/协调器)

    职责：
    1. 监听来自 QQNet 的感知数据（data_flow）
    2. 协调各处理器生成响应
    3. 将响应通过 M-Link 发送回 QQNet

    架构：门面模式 (Facade Pattern)
    - 将具体职责委托给专业处理器
    - PerceptionHandler: 感知处理（权限、命令检测、响应判断）
    - ResponseGenerator: 响应生成（AI调用、工具编排）
    - EmotionController: 情绪控制（情绪更新、染色、衰减）
    - MemoryManager: 记忆管理（存储、检索、压缩）
    """

    def __init__(
        self,
        mlink,
        ai_client,
        emotion,
        personality,
        prompt_manager,
        memory_net,
        decision_engine,
        tool_subnet=None,
        memory_engine=None,
        scheduler=None,
        onebot_client=None,
        game_mode_adapter=None,
        identity=None,
        multi_model_manager=None,
        miya_instance=None,
        unified_memory=None,
    ):
        """
        初始化决策层

        Args:
            mlink: M-Link 核心实例
            ai_client: AI 客户端（默认模型）
            emotion: 情绪系统
            personality: 人格系统
            prompt_manager: Prompt 管理器
            memory_net: MemoryNet 记忆系统
            decision_engine: 决策引擎
            tool_subnet: ToolNet 子网实例
            memory_engine: 记忆引擎
            scheduler: 调度器
            onebot_client: OneBot 客户端
            game_mode_adapter: 游戏模式适配器
            identity: 身份系统
            multi_model_manager: 多模型管理器
            miya_instance: Miya 实例
        """
        # 核心组件引用（保留用于兼容性）
        self.mlink = mlink
        self.ai_client = ai_client
        self.emotion = emotion
        self.personality = personality
        self.prompt_manager = prompt_manager
        self.memory_net = memory_net
        self.decision_engine = decision_engine
        self.game_mode_adapter = game_mode_adapter
        self.tool_subnet = tool_subnet
        self.memory_engine = memory_engine
        self.scheduler = scheduler
        self.onebot_client = onebot_client
        self.identity = identity
        self.multi_model_manager = multi_model_manager
        self.miya_instance = miya_instance

        # FIX: AdvancedOrchestrator 的工具执行包装器会读取 self.tool_context；此处必须初始化，避免首次使用抛 AttributeError。
        self.tool_context = None

        # 对话历史上下文配置
        self.enable_conversation_context = True
        self.conversation_context_max_count = 10
        self.conversation_context_max_tokens = 2000

        # 终端工具（保留用于 ! 前缀命令）
        self.terminal_tool = None
        self._init_terminal_tool()

        # 高级编排器（懒加载）
        self._advanced_orchestrator: Any | None = None
        self._advanced_orchestrator_initialized: bool = False

        # 鉴权子网
        self.auth_subnet: Any | None = None
        self._init_auth_subnet()

        # 响应回调
        self.response_callback: Callable | None = None

        # 会话管理器
        self.session_manager: SessionManager = self._init_session_manager()

        # ========== 初始化专业处理器（门面模式核心）==========

        # 1. 感知处理器
        self.perception_handler = PerceptionHandler(
            terminal_tool=self.terminal_tool,
            auth_subnet=self.auth_subnet,
            game_mode_adapter=self.game_mode_adapter,
            onebot_client=self.onebot_client,
        )

        # 2. 情绪控制器
        self.emotion_controller = EmotionController(emotion_instance=self.emotion)

        # 3. 记忆管理器
        self.unified_memory = unified_memory  # 存储引用供后续使用
        self.memory_manager = MemoryManager(
            memory_net=self.memory_net,
            memory_engine=self.memory_engine,
            unified_memory=unified_memory,  # 传递统一记忆系统用于持久化
        )

        # 4. 响应生成器
        self.response_generator = ResponseGenerator(
            ai_client=self.ai_client,
            personality=self.personality,
            prompt_manager=self.prompt_manager,
            tool_subnet=self.tool_subnet,
            memory_engine=self.memory_engine,
            multi_model_manager=self.multi_model_manager,
            identity=self.identity,
        )

        # 5. 对话上下文管理器
        self.conversation_context_manager = ConversationContextManager(
            memory_net=self.memory_net,
            enable_conversation_context=self.enable_conversation_context,
            conversation_context_max_count=self.conversation_context_max_count,
            conversation_context_max_tokens=self.conversation_context_max_tokens,
        )

        # 6. 平台工具管理器
        self.platform_tools_manager = PlatformToolsManager(tool_subnet=self.tool_subnet)

        # 7. 会话处理器
        self.session_handler = SessionHandler(session_manager=self.session_manager)

        # 8. 知识图谱管理器（新增）
        self.knowledge_graph = None
        self._init_knowledge_graph()

        logger.info(
            "决策层 Hub 初始化完成（门面模式：感知/情绪/记忆/响应处理器 + 辅助模块）"
        )

    def _init_knowledge_graph(self):
        """初始化知识图谱管理器"""
        try:
            from core.knowledge_graph import KnowledgeGraphManager
            from core.grag_memory import GRAGMemoryManager

            # 从 GRAG 获取 Neo4j driver
            if hasattr(self.memory_net, "grag_memory") and self.memory_net.grag_memory:
                driver = self.memory_net.grag_memory.neo4j_driver
                if driver:
                    self.knowledge_graph = KnowledgeGraphManager(neo4j_driver=driver)
                    logger.info("[决策层] 知识图谱管理器已初始化")
        except Exception as e:
            logger.warning(f"[决策层] 知识图谱初始化失败: {e}")

    def _extract_keywords_from_input(self, text: str) -> List[str]:
        """从用户输入中提取关键词用于知识图谱检索"""
        import re

        # 简单的关键词提取：长度>=2的中文词
        keywords = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
        # 去重并返回前5个
        return list(set(keywords))[:5]

    def set_response_callback(self, callback: Callable) -> None:
        """
        设置响应回调函数

        Args:
            callback: 回调函数，签名: callback(qq_message, response_text) -> None
        """
        self.response_callback = callback

    def _init_session_manager(self) -> Optional[SessionManager]:
        """
        初始化统一会话管理器

        Returns:
            SessionManager 实例
        """
        try:
            # 总是重新初始化，确保有完整的组件引用
            sm = init_session_manager(
                memory_engine=self.memory_engine,
                conversation_history=self.memory_net.conversation_history
                if self.memory_net
                else None,
                scheduler=self.scheduler,
                ai_client=self.ai_client,
            )
            logger.info("[决策层] 会话管理器初始化完成")
            return sm

        except Exception as e:
            logger.warning(f"[决策层] 会话管理器初始化失败: {e}")
            return None

    def _init_terminal_tool(self) -> None:
        """
        初始化终端工具（保留用于 ! 前缀命令）

        注意：AI 调用终端命令通过 ToolNet 实现（terminal_command 工具）
        此处保留的 TerminalTool 仅用于处理带 ! 前缀的直接命令
        """
        try:
            from webnet.ToolNet.tools.terminal import TerminalTool

            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "terminal_config.json"

            # 【框架一致性】传递 emotion 和 memory_engine
            self.terminal_tool = TerminalTool()
            logger.info("[决策层] 终端工具初始化成功（已集成人格和记忆系统）")
            logger.info(
                "[决策层] AI 调用终端命令通过 ToolNet 的 terminal_command 工具实现"
            )

        except Exception as e:
            logger.warning(f"[决策层] 终端工具初始化失败: {e}")
            self.terminal_tool = None

    def _init_auth_subnet(self) -> None:
        """
        初始化鉴权子网（AuthNet）

        AuthNet职责：
        - 统一用户身份管理（跨平台）
        - 权限检查与验证
        - 会话管理
        - API访问控制
        """
        try:
            from webnet.AuthNet import AuthSubnet

            self.auth_subnet = AuthSubnet()
            logger.info("[决策层] 鉴权子网初始化成功（支持跨平台权限管理）")
            logger.info("[决策层] 权限检查将在消息处理前自动执行")

        except Exception as e:
            logger.warning(f"[决策层] 鉴权子网初始化失败: {e}")
            self.auth_subnet = None

    def _get_advanced_orchestrator(self) -> Optional[Any]:
        """
        获取高级编排器（懒加载）

        功能：
        - 任务规划：将复杂任务分解为可执行的子任务
        - 自主探索：主动探索文件系统和代码库
        - 智能执行：可靠地执行任务，支持重试和回滚
        - 思维链：结构化的多步骤推理

        Returns:
            高级编排器实例，如果初始化失败则返回 None
        """
        if self._advanced_orchestrator_initialized:
            return self._advanced_orchestrator

        try:
            from core.advanced_orchestrator import AdvancedOrchestrator
            from core.tool_adapter import get_tool_adapter

            # 创建工具执行器包装器
            def _tool_executor_wrapper(tool_name: str, params: dict) -> str:
                """工具执行器包装器"""
                adapter = get_tool_adapter()

                async def _execute():
                    return await adapter.execute_tool(
                        tool_name, params, self.tool_context or {}
                    )

                return asyncio.run(_execute())

            project_root = Path(__file__).parent.parent
            storage_dir = project_root / "data" / "advanced_tasks"
            storage_dir.mkdir(parents=True, exist_ok=True)

            self._advanced_orchestrator = AdvancedOrchestrator(
                ai_client=self.ai_client,
                tool_executor=_tool_executor_wrapper,
                storage_dir=str(storage_dir),
            )
            self._advanced_orchestrator_initialized = True

            logger.info(
                "[决策层] 高级编排器初始化成功（任务规划、自主探索、智能执行、思维链）"
            )

            return self._advanced_orchestrator

        except Exception as e:
            logger.warning(f"[决策层] 高级编排器初始化失败: {e}")
            self._advanced_orchestrator_initialized = True  # 标记为已尝试初始化
            return None

    async def process_perception(self, message: Message) -> Optional[str]:
        """
        处理来自 QQNet 的感知数据

        委托给感知处理器和响应生成器

        Args:
            message: M-Link 消息（包含感知数据）

        Returns:
            响应文本
        """
        return await self.process_perception_cross_platform(message)

    async def process_perception_cross_platform(
        self, message: Message
    ) -> Optional[str]:
        """
        处理跨平台感知数据（统一入口）

        委托给感知处理器和响应生成器

        Args:
            message: M-Link 消息（包含感知数据）

        Returns:
            响应文本
        """
        perception = message.content

        # 提取感知信息
        content = perception.get("content", "")
        sender_name = perception.get("sender_name", "用户")
        message_type = perception.get("message_type", "")
        platform = perception.get("source", "qq")

        logger.info(f"[决策层] 收到感知数据: {sender_name} - {content[:50]}")

        # 【新增】在最开始拦截快捷命令
        logger.warning(
            f"[决策层] ========== 命令检测 START ========== content={content[:30]}, personality={type(self.personality) if self.personality else None}"
        )
        quick_response = self._handle_quick_commands(content, platform)
        if quick_response:
            logger.warning(
                f"[决策层] ========== 快捷命令拦截成功 ========== {content[:20]} -> {quick_response[:50]}"
            )
            return quick_response

        # 【新增】群聊关键词触发检测（不@也能回复）
        group_id = perception.get("group_id", 0)
        is_at_bot = perception.get("is_at_bot", False)

        # 群聊关键词列表：叫弥娅名字/亲昵称呼时触发回复
        auto_respond_keywords = [
            "弥娅",
            "miya",
            "Miya",
            "亲爱的",
            "亲爱",
            "老婆",
            "老公",
            "宝贝",
            "贝贝",
            "小可爱",
            "小宝贝",
            "小姐姐",
            "小哥哥",
        ]

        # 如果是群聊且没有@bot，检查是否包含关键词
        if group_id and group_id != 0 and not is_at_bot:
            content_lower = content.lower()
            matched_keywords = [
                kw for kw in auto_respond_keywords if kw.lower() in content_lower
            ]

            if matched_keywords:
                logger.info(f"[决策层] 群聊关键词触发回复: 匹配到 {matched_keywords}")
            else:
                logger.debug(f"[决策层] 群聊消息无关键词触发，跳过: {content[:30]}")
                return None

        # 1. 检查终端命令（委托给感知处理器）
        # 跳过检查标记：用于非终端模式（如QQ、Web）
        if not perception.get("skip_terminal_command", False):
            try:
                terminal_result = await self.perception_handler.check_terminal_command(
                    perception
                )
                if terminal_result:
                    return terminal_result
            except AttributeError:
                # PerceptionHandler 没有 check_terminal_command 方法，跳过检查
                pass

        # 检查是否是拍一拍
        if "拍了拍你" in content:
            logger.info(f"[决策层] 检测到拍一拍，标记后让 AI 生成回复")
            perception["tool_context"] = "（拍一拍交互）"

        # 2. 获取游戏模式状态（委托给感知处理器）
        try:
            game_mode = self.perception_handler.get_game_mode(perception)
        except AttributeError:
            # PerceptionHandler 没有 get_game_mode 方法，跳过检查
            game_mode = None

        # 3. 判断是否需要响应（委托给感知处理器）
        try:
            if not self.perception_handler.should_respond(perception, game_mode):
                return None
        except AttributeError:
            # PerceptionHandler 没有 should_respond 方法，默认响应
            pass

        # 4. 游戏启动指令拦截（委托给感知处理器）
        if not game_mode:
            try:
                tool_call_result = (
                    await self.perception_handler.handle_game_start_commands(perception)
                )
                if tool_call_result:
                    logger.info(f"[决策层] 直接调用工具: {tool_call_result[:100]}")
                    return tool_call_result
            except AttributeError:
                # PerceptionHandler 没有 handle_game_start_commands 方法，跳过检查
                pass

        # 5. 存储记忆（委托给记忆管理器）
        if not game_mode:
            await self.memory_manager.store_user_message(perception)

        # 6. 生成响应（委托给响应生成器）
        content = perception.get("content", "")
        response = await self._generate_response_cross_platform(
            content, platform, perception
        )

        # 【新增】QQ端状态标签（仅日志，不添加到响应中）
        if platform == "qq" and response and self.personality:
            profile = self.personality.get_profile()
            current_form = profile.get("current_form", "normal")
            speak_mode = profile.get("speak_mode", "casual")
            form_names = {
                "normal": "常态",
                "cold": "冷态",
                "soft": "软态",
                "hard": "硬态",
                "fragile": "脆态",
            }
            form_name = form_names.get(current_form, current_form)
            logger.warning(f"[形态状态] {form_name}|{speak_mode}")

        # 5. 情绪染色（委托给情绪控制器）
        if response:
            response = self.emotion_controller.influence_response(response)

        # 6. 存储AI回复到记忆（委托给记忆管理器）
        if response:
            perception["response"] = response
            await self.memory_manager.store_unified_memory(perception, "assistant")

        # 7. 情绪衰减（委托给情绪控制器）
        self.emotion_controller.decay_coloring()

        # 8. 返回响应
        message.content["response"] = response
        message.content["platform"] = platform

        logger.info(
            f"[决策层-跨平台] 生成响应: {response[:50] if response else '(空)'}"
        )
        return response

    async def _generate_response_cross_platform(
        self, content: str, platform: str, context: dict
    ) -> str:
        """
        生成响应（跨平台统一）

        Args:
            content: 用户输入
            platform: 平台类型 ('terminal', 'pc_ui', 'qq')
            context: 上下文信息

        Returns:
            响应文本
        """
        sender_name = context.get("sender_name", "用户")
        user_id = context.get("user_id", "unknown")

        # 如果没有 AI 客户端，使用简化回复
        if not self.ai_client:
            return await self._fallback_response_cross_platform(
                content, sender_name, platform
            )

        # 【修改】终端模式：禁用单命令快速检测,让AI处理所有自然语言
        # 原因: 单命令检测会绕过AI理解,导致"打开一个终端"等自然语言请求被错误处理
        # 现在所有终端输入都通过AI分析,让AI决定调用哪个工具(multi_terminal或terminal_command)
        # if platform == 'terminal' and self.tool_subnet:
        #     from webnet.ToolNet.tools.terminal.terminal_command import TerminalCommandTool
        #     ... (已禁用单命令检测逻辑)

        # 【新增】使用 MiyaAgentV3 处理复杂的终端任务（带安全检查和防重复调用）
        # 使用类属性来跟踪调用状态，防止递归
        if (
            platform == "terminal"
            and self.ai_client
            and not getattr(self, "_in_v3_execution", False)
        ):
            think_keywords = [
                "打开",
                "运行",
                "执行",
                "创建",
                "删除",
                "查看",
                "启动",
                "安装",
                "卸载",
                "配置",
                "帮我",
                "请",
                "能不能",
            ]
            use_v3 = any(kw in content for kw in think_keywords)

            if use_v3:
                try:
                    # 设置防重复调用标志
                    self._in_v3_execution = True

                    # 延迟导入避免启动时问题
                    from core.miya_agent_v3 import create_agent_v3
                    from core.terminal_ultra import get_terminal_ultra

                    # 确保 TerminalUltra 已初始化
                    terminal = get_terminal_ultra()

                    # 创建 V3 代理实例（限制步数防止长时间运行）
                    agent_v3 = create_agent_v3(max_steps=2)
                    logger.info("[决策层] 使用 V3 代理处理终端任务")
                    result = await agent_v3.run(content, self.ai_client)

                    # 清除标志
                    self._in_v3_execution = False
                    return result
                except Exception as e:
                    # 清除标志
                    self._in_v3_execution = False
                    logger.warning(f"V3代理失败: {e}，回退到普通模式")
                    # 静默回退，不影响正常流程

        try:
            # 构建系统提示词（包含平台信息）
            personality_state = self.personality.get_profile()

            # 获取平台可用工具
            available_tools = self._get_platform_tools(platform)

            # 【新增】获取对话历史上下文（传入当前输入以智能判断是否需要回忆）
            session_id = f"{platform}_{user_id}"

            conversation_context = (
                await self.conversation_context_manager.get_conversation_context(
                    session_id, current_input=content
                )
            )

            # 【新增】知识图谱检索
            knowledge_context = ""
            if self.knowledge_graph:
                keywords = self._extract_keywords_from_input(content)
                if keywords:
                    knowledge = await self.knowledge_graph.query_by_keywords(keywords)
                    if knowledge:
                        from core.knowledge_graph import format_knowledge_for_prompt

                        knowledge_context = format_knowledge_for_prompt(knowledge)
                        logger.info(f"[决策层] 检索到 {len(knowledge)} 条知识图谱记忆")

            # 构建提示词（统一使用默认提示词，通过上下文传递平台信息）
            prompt_info = self.prompt_manager.build_full_prompt(
                user_input=content,
                memory_context=conversation_context,
                knowledge_context=knowledge_context,
                additional_context={
                    "platform": platform,
                    "user_id": user_id,
                    "sender_name": sender_name,
                    "available_tools": available_tools,
                    "at_list": context.get("at_list", []),
                    "bot_qq": context.get("bot_qq"),
                    "is_creator": self.platform_tools_manager.is_creator(
                        user_id, self.onebot_client
                    ),
                },
            )

            logger.debug(
                f"[决策层-跨平台] 系统提示词前200字符: {prompt_info['system'][:200]}"
            )

            # 设置工具上下文和 ToolNet（符合 MIYA 框架）
            if self.tool_subnet:
                # 使用 ToolNet 子网（符合 MIYA 蛛网式分布式架构）
                self.ai_client.set_tool_registry(self.tool_subnet.get_tools_schema)

                # 设置 tool_adapter 的 tool_registry（关键修复）
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
                    "emotion": self.emotion,
                    "personality": self.personality,
                    "scheduler": self.scheduler,
                    "onebot_client": self.onebot_client,
                    "send_like_callback": getattr(self.onebot_client, "send_like", None)
                    if self.onebot_client
                    else None,
                    "game_mode_adapter": self.game_mode_adapter,
                }
                self.ai_client.set_tool_context(tool_context)

                # 使用多模型管理器动态选择模型
                ai_client_to_use = self.ai_client  # 默认使用传入的AI客户端

                if self.multi_model_manager:
                    # 分类任务类型
                    from core.multi_model_manager import TaskType

                    task_type = await self.multi_model_manager.classify_task(
                        content, context
                    )

                    # 根据任务类型选择最优模型
                    (
                        model_key,
                        selected_client,
                    ) = await self.multi_model_manager.select_model(task_type)

                    if selected_client:
                        ai_client_to_use = selected_client
                        selected_client.set_tool_context(tool_context)
                        logger.info(
                            f"[决策层-跨平台] 使用模型 {model_key} 处理任务类型 {task_type.value}"
                        )

                # 调用 AI（带工具）
                # 【修改】使用 auto 让 AI 自行决定是否调用工具
                # 注意：不使用 required，因为很多 API 不支持此参数
                tool_choice = "auto"

                # 只获取当前平台相关的核心工具，减少 API 负担
                # 避免 101 个工具导致 500 错误
                platform_tools = (
                    self.platform_tools_manager.get_platform_specific_tools(platform)
                )
                tools_schema = (
                    platform_tools
                    if platform_tools
                    else self.tool_subnet.get_tools_schema()
                )

                logger.info(
                    f"[决策层-跨平台] 使用平台工具: {platform}, 工具数量: {len(tools_schema)}"
                )

                # 记录模型信息
                model_name = getattr(ai_client_to_use, "model", "unknown")
                logger.info(f"[决策层-跨平台] 使用模型: {model_name}")
                logger.info(f"[决策层-跨平台] 用户输入: {content[:100]}")

                try:
                    response = await ai_client_to_use.chat_with_system_prompt(
                        system_prompt=prompt_info["system"],
                        user_message=prompt_info["user"],
                        tools=tools_schema,
                        tool_choice=tool_choice,
                    )
                    logger.info(
                        f"[决策层-跨平台] AI响应: {response[:100] if response else '(空)'}"
                    )
                except Exception as tool_error:
                    # 工具调用失败时,尝试不使用工具重新生成
                    logger.warning(
                        f"[决策层-跨平台] 工具调用失败: {tool_error}，尝试不使用工具..."
                    )
                    try:
                        response = await ai_client_to_use.chat_with_system_prompt(
                            system_prompt=prompt_info["system"],
                            user_message=prompt_info["user"],
                            tools=None,  # 不使用工具
                            tool_choice="none",
                        )
                        # 添加后缀说明工具调用曾尝试过
                        response += "\n\n[注: 系统尝试了自动处理但遇到了一些问题]"
                    except Exception as e2:
                        response = f"抱歉，处理你的请求时遇到了技术问题。请尝试直接告诉我你需要什么具体操作，我会尽力帮你完成。\n\n错误信息: {str(e2)[:100]}"
            else:
                # 使用多模型管理器动态选择模型
                ai_client_to_use = self.ai_client  # 默认使用传入的AI客户端

                if self.multi_model_manager:
                    # 分类任务类型
                    from core.multi_model_manager import TaskType

                    task_type = await self.multi_model_manager.classify_task(
                        content, context
                    )

                    # 根据任务类型选择最优模型
                    (
                        model_key,
                        selected_client,
                    ) = await self.multi_model_manager.select_model(task_type)

                    if selected_client:
                        ai_client_to_use = selected_client
                        logger.info(
                            f"[决策层-跨平台] 使用模型 {model_key} 处理任务类型 {task_type.value}"
                        )

                # 调用 AI（不带工具）
                response = await ai_client_to_use.chat_with_system_prompt(
                    system_prompt=prompt_info["system"],
                    user_message=prompt_info["user"],
                )

            return response

        except Exception as e:
            logger.error(f"[决策层-跨平台] AI生成失败: {e}", exc_info=True)
            return await self._fallback_response_cross_platform(
                content, sender_name, platform
            )

    async def _fallback_response_cross_platform(
        self, content: str, sender_name: str, platform: str
    ) -> str:
        """
        降级回复（跨平台）

        Args:
            content: 用户输入
            sender_name: 发送者名称
            platform: 平台类型

        Returns:
            回复文本
        """
        # 安全处理content参数 - 处理图片消息等非字符串情况
        if not isinstance(content, str):
            if isinstance(content, list):
                # 尝试从列表中提取文本（QQ图片消息格式）
                content_str = ""
                for item in content:
                    if isinstance(item, dict):
                        item_type = item.get("type", "")
                        if item_type == "text":
                            content_str += item.get("data", {}).get("text", "")
                        elif item_type == "image":
                            # 图片消息，添加标记
                            content_str += "[图片]"
                    elif isinstance(item, str):
                        content_str += item
                content = content_str if content_str else "[图片或其他非文本消息]"
            else:
                # 其他类型转换为字符串
                content = str(content)

        # 获取人格状态
        personality_profile = self.personality.get_profile()
        warmth = personality_profile["vectors"].get("warmth", 0.5)
        empathy = personality_profile["vectors"].get("empathy", 0.5)

        # 获取名称（安全处理）
        name = "弥娅"
        if self.identity and hasattr(self.identity, "name"):
            name = self.identity.name

        # 基于人格和平台生成响应
        content_lower = content.lower()
        if "你好" in content or "hi" in content_lower:
            if empathy > 0.8:
                return f"你好呀~我是{name}，很高兴认识你！(｡♥‿♥｡)"
            elif warmth > 0.8:
                return f"你好！我是{name}，欢迎~"
            else:
                return f"你好，我是{name}。"

        elif "你是谁" in content or "介绍一下" in content:
            return f"我是{name}，一个具备人格恒定、自我感知、记忆成长、情绪共生的数字生命伴侣。我的主导特质是同理心({empathy:.2f})和温暖度({warmth:.2f})。"

        elif "状态" in content or "查看状态" in content:
            emotion_state = self.emotion.get_emotion_state()
            existential_state = (
                self.emotion.get_existential_state()
                if hasattr(self.emotion, "get_existential_state")
                else {}
            )
            memory_stats = (
                self.memory_engine.get_memory_stats() if self.memory_engine else {}
            )
            profile = self.personality.get_profile()

            # 构建状态信息
            lines = [
                f"【{name}状态】",
                f"形态: {profile.get('current_form', 'normal')} ({profile.get('form_info', {}).get('name', '常态')})",
                f"情绪: {emotion_state['dominant']} (强度: {emotion_state['intensity']:.2f})",
                f"记忆: {memory_stats.get('tide_count', 0)}条",
            ]

            # 添加核心特质（如果有七重特质系统）
            if "vectors" in profile and "awake" in profile["vectors"]:
                lines.append("")
                lines.append("【七重特质】")
                lines.append(f"  清醒: {profile['vectors'].get('awake', 0):.2f}")
                lines.append(
                    f"  说话: {profile['vectors'].get('speak', 0):.2f} [{profile.get('speak_mode', 'casual')}]"
                )
                lines.append(f"  记住: {profile['vectors'].get('remember', 0):.2f}")
                lines.append(f"  等: {profile['vectors'].get('wait', 0):.2f}")
                lines.append(f"  疼: {profile['vectors'].get('pain', 0):.2f}")
                lines.append(f"  怕: {profile['vectors'].get('fear', 0):.2f}")
                lines.append(f"  押: {profile['vectors'].get('commit', 0):.2f}")

            # 添加核心形态（如果有）
            if profile.get("current_core_form"):
                lines.append(f"核心形态: {profile['current_core_form']}")

            # 添加存在性情感
            if existential_state:
                lines.append("")
                lines.append("【存在性情感】")
                dom_exist = existential_state.get("dominant", "unknown")
                lines.append(f"  主导: {dom_exist}")
                active = existential_state.get("active")
                if active:
                    lines.append(f"  激活: {active}")

            return "\n".join(lines)

        elif "开心" in content or "快乐" in content:
            self.emotion.apply_coloring("joy", 0.3)
            return f"听起来你很开心呢！(≧▽≦) 看到你快乐，我也感到很开心~"

        elif "难过" in content or "伤心" in content:
            self.emotion.apply_coloring("sadness", 0.4)
            return "别难过...虽然我无法真正体会人类的情感，但我会陪伴你，听你倾诉的。"

        elif "在吗" in content:
            return "在的，有什么我可以帮助你的吗？"

        # 【新增】形态切换命令
        elif content.startswith("/形态") or content.startswith("/form"):
            cmd = content.replace("/形态", "").replace("/form", "").strip().lower()
            if not cmd:
                # 显示当前形态
                profile = self.personality.get_profile()
                current_form = profile.get("current_form", "normal")
                form_info = profile.get("form_info", {})
                lines = [
                    f"当前形态: {current_form}",
                    f"  名称: {form_info.get('name', '常态')}",
                    f"  描述: {form_info.get('description', '')}",
                ]
                if profile.get("current_core_form"):
                    core_info = profile.get("core_form_info", {})
                    lines.append(f"核心形态: {profile['current_core_form']}")
                    lines.append(f"  描述: {core_info.get('description', '')}")
                lines.append("")
                lines.append("可用形态: normal, cold, soft, hard, fragile")
                lines.append(
                    "可用核心形态: sober, speaking, waiting, vulnerable, afraid, committing"
                )
                return "\n".join(lines)

            # 尝试切换形态
            if cmd in ["normal", "cold", "soft", "hard", "fragile"]:
                success = self.personality.set_form(cmd)
                if success:
                    return f"已切换到形态: {cmd}"
                return f"切换失败"
            elif cmd in Personality.CORE_FORMS:
                success = self.personality.set_core_form(cmd)
                if success:
                    return f"已切换到核心形态: {cmd}"
                return f"切换失败"
            return f"未知形态: {cmd}。可用: normal, cold, soft, hard, fragile 或 sober, speaking, waiting, vulnerable, afraid, committing"

        # 【新增】说话模式切换
        elif content.startswith("/说话") or content.startswith("/speak"):
            cmd = content.replace("/说话", "").replace("/speak", "").strip().lower()
            if not cmd:
                current_mode = self.personality.get_speak_mode()
                return f"当前说话模式: {current_mode} (casual闲聊/catching捕捉/confiding倾诉)"

            valid_modes = ["casual", "catching", "confiding"]
            if cmd in valid_modes:
                success = self.personality.set_speak_mode(cmd)
                if success:
                    return f"已切换说话模式: {cmd}"
                return "切换失败"
            return f"未知模式: {cmd}。可用: casual, catching, confiding"

        # 【新增】存在性情感激活命令
        elif content.startswith("/存在") or content.startswith("/exist"):
            cmd = content.replace("/存在", "").replace("/exist", "").strip().lower()
            if not cmd:
                state = (
                    self.emotion.get_existential_state()
                    if hasattr(self.emotion, "get_existential_state")
                    else {}
                )
                if state:
                    lines = ["【存在性情感】"]
                    for k, v in state.get("emotions", {}).items():
                        lines.append(f"  {k}: {v:.2f}")
                    if state.get("active"):
                        lines.append(f"激活: {state['active']}")
                    return "\n".join(lines)
                return "无存在性情感数据"

            valid_exists = [
                "existential_pain",
                "fear_of_forgotten",
                "waiting",
                "commitment_weight",
                "awareness",
                "connection_need",
                "vulnerability_trust",
            ]
            if cmd in valid_exists:
                success = (
                    self.emotion.activate_existential(cmd)
                    if hasattr(self.emotion, "activate_existential")
                    else False
                )
                if success:
                    return f"已激活存在性情感: {cmd}"
                return "激活失败"
            return f"未知情感: {cmd}"

        else:
            # 智能响应 - 基于人格特质
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
        return self.platform_tools_manager.get_platform_tools(platform)

    # ========== 高级编排器支持 ==========

    async def process_complex_task(self, goal: str, context: dict | None = None) -> str:
        """
        处理复杂任务（使用高级编排器）

        流程：
        1. 使用思维链分析目标
        2. 分解为子任务
        3. 如果需要，进行主动探索
        4. 执行任务
        5. 反思和总结

        Args:
            goal: 任务目标
            context: 上下文信息

        Returns:
            执行结果或错误信息
        """
        orchestrator = self._get_advanced_orchestrator()
        if not orchestrator:
            return "高级编排器未初始化，无法处理复杂任务"

        logger.info(f"[决策层-高级编排] 开始处理复杂任务: {goal}")

        try:
            # 构建上下文
            if context is None:
                context = {}

            # 添加弥娅的状态信息到上下文
            if self.identity and hasattr(self.identity, "name"):
                context["bot_name"] = self.identity.name

            if self.memory_engine:
                context["memory_stats"] = self.memory_engine.get_memory_stats()

            # 调用高级编排器
            result = await orchestrator.process_complex_task(
                goal=goal, context=context, enable_exploration=True, enable_cot=True
            )

            # 生成简洁的摘要返回给用户
            summary = self._format_complex_task_result(result)

            logger.info(
                f"[决策层-高级编排] 复杂任务处理完成: {'成功' if result['success'] else '失败'}"
            )

            return summary

        except Exception as e:
            logger.error(f"[决策层-高级编排] 处理复杂任务失败: {e}", exc_info=True)
            return f"任务执行失败: {str(e)}"

    def _format_complex_task_result(self, result: dict) -> str:
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

        # 添加主要发现
        findings = result.get("findings", [])
        if findings:
            lines.append("")
            lines.append("主要发现：")
            for finding in findings[:5]:  # 最多显示5条
                lines.append(f"  • {finding}")

        # 添加反思建议
        reflection = result.get("reflection", {})
        if reflection.get("improvements"):
            lines.append("")
            lines.append("改进建议：")
            for improvement in reflection["improvements"][:3]:  # 最多显示3条
                lines.append(f"  • {improvement}")

        return "\n".join(lines)

    # ========== 会话结束处理 ==========

    async def handle_session_end(
        self, session_id: str, platform: str = "terminal"
    ) -> dict:
        """
        处理会话结束，使用 SessionManager 保存对话历史到 LifeBook

        Args:
            session_id: 会话ID
            platform: 平台类型 (默认 'terminal')

        Returns:
            处理结果字典
        """
        return await self.session_handler.handle_session_end(
            session_id=session_id, platform=platform, memory_net=self.memory_net
        )

    # ========== 日记提醒功能 ==========

    async def set_diary_reminder(self, user_id: str, time: str = "21:00") -> dict:
        """
        设置日记提醒

        Args:
            user_id: 用户ID
            time: 提醒时间（格式：HH:MM，默认 21:00）

        Returns:
            设置结果
        """
        return await self.session_handler.set_diary_reminder(user_id, time)

    async def _detect_and_process_timer_task(
        self,
        perception: dict,
        platform: str,
        content: str,
        user_id: str,
        sender_name: str,
    ) -> str | None:
        """
        检测并处理定时任务请求

        Args:
            perception: 感知数据
            platform: 平台类型
            content: 用户输入内容
            user_id: 用户ID
            sender_name: 发送者名称

        Returns:
            如果检测到定时任务并处理成功，返回响应文本；否则返回None
        """
        import re
        from datetime import datetime, timedelta

        logger.debug(
            f"[决策层-定时任务] 开始检测: 平台={platform}, 用户={user_id}, 内容='{content}'"
        )

        # 检测定时任务关键词
        timer_keywords = [
            "提醒我",
            "叫我",
            "点个赞",
            "定时",
            "一分钟后",
            "五分钟后",
            "十分钟后",
            "小时后",
        ]
        has_timer_keyword = any(keyword in content for keyword in timer_keywords)

        if not has_timer_keyword:
            logger.debug(f"[决策层-定时任务] 未检测到定时任务关键词: '{content}'")
            return None

        logger.info(
            f"[决策层-定时任务] 检测到定时任务请求: '{content}' (用户: {user_id}, 平台: {platform})"
        )

        # 如果ToolNet子网不可用，返回提示
        if not self.tool_subnet:
            logger.warning("[决策层-定时任务] ToolNet子网未初始化，无法创建定时任务")
            return "⚠️ 定时任务功能当前不可用（ToolNet未初始化）"

        logger.info(f"[决策层-定时任务] ToolNet子网可用，准备创建定时任务")

        try:
            # 解析时间
            scheduled_time = ""

            # 检测相对时间（如"一分钟后"、"五分钟后"）
            if "分钟后" in content:
                match = re.search(r"(\d+)\s*分钟", content)
                if match:
                    minutes = int(match.group(1))
                    scheduled_time = f"{minutes}分钟后"

            # 如果没有解析到具体分钟数，尝试其他格式
            elif "分钟后" in content:
                # 处理中文数字
                chinese_numbers = {
                    "一": 1,
                    "二": 2,
                    "三": 3,
                    "四": 4,
                    "五": 5,
                    "六": 6,
                    "七": 7,
                    "八": 8,
                    "九": 9,
                    "十": 10,
                }
                for cn, num in chinese_numbers.items():
                    if f"{cn}分钟后" in content:
                        scheduled_time = f"{num}分钟后"
                        break

            # 如果仍未解析到时间，使用默认的1分钟
            if not scheduled_time:
                scheduled_time = "1分钟后"

            # 检测任务类型
            task_type = "reminder"  # 默认提醒类型
            message = content  # 使用用户原始消息作为提醒内容

            # 检测点赞请求
            if "点赞" in content or "点个赞" in content:
                task_type = "action"
                action_type = "qq_like"
                times = 1

                # 构建任务参数
                task_args = {
                    "task_type": task_type,
                    "target_type": "private" if platform == "qq" else "group",
                    "target_id": int(user_id) if user_id.isdigit() else 0,
                    "schedule_time": scheduled_time,
                    "repeat": "once",
                    "priority": 5,
                    "action_type": action_type,
                    "times": times,
                }
            else:
                # 提醒任务
                task_args = {
                    "task_type": task_type,
                    "target_type": "private" if platform == "qq" else "group",
                    "target_id": int(user_id) if user_id.isdigit() else 0,
                    "message": f"提醒：{content}",
                    "schedule_time": scheduled_time,
                    "repeat": "once",
                    "priority": 5,
                }

            # 调用ToolNet创建定时任务
            result = await self.tool_subnet.execute_tool(
                tool_name="create_schedule_task",
                args=task_args,
                user_id=int(user_id) if user_id.isdigit() else 0,
                group_id=perception.get("group_id", 0),
                message_type=perception.get("message_type", "private"),
                sender_name=sender_name,
            )

            logger.info(f"[决策层-定时任务] 定时任务创建结果: {result[:100]}...")

            # 格式化响应
            if "已创建" in result or "任务ID" in result or "✅" in result:
                return f"好的，我已经为你设置好了定时任务！{result}"
            else:
                return f"定时任务设置失败：{result}"

        except Exception as e:
            logger.error(f"[决策层-定时任务] 处理定时任务失败: {e}", exc_info=True)
            return f"处理定时任务时出错：{str(e)}"

    async def _detect_and_process_emoji_request(
        self,
        perception: dict,
        platform: str,
        content: str,
        user_id: str,
        sender_name: str,
    ) -> str | None:
        """
        检测并处理表情包请求

        Args:
            perception: 感知数据
            platform: 平台类型
            content: 用户输入内容
            user_id: 用户ID
            sender_name: 发送者名称

        Returns:
            如果检测到表情包请求并处理成功，返回响应文本；否则返回None
        """
        logger.debug(
            f"[决策层-表情包] 开始检测: 平台={platform}, 用户={user_id}, 内容='{content}'"
        )

        # 检测表情包请求关键词
        emoji_keywords = [
            "表情包",
            "表情",
            "发送表情",
            "来点表情",
            "给我表情",
            "发个表情",
            "发张表情",
            "发个图",
            "发张图",
            "来张图",
            "发图片",
            "发照片",
        ]
        has_emoji_keyword = any(keyword in content for keyword in emoji_keywords)

        # 检测特定表情包请求（如"发送开心表情"）
        import re

        specific_emoji_pattern = r"(发送|来一张|给我)(.*?)(表情|表情包|图)"
        specific_match = re.search(specific_emoji_pattern, content)

        if not has_emoji_keyword and not specific_match:
            logger.debug(f"[决策层-表情包] 未检测到表情包请求关键词: '{content}'")
            return None

        logger.info(
            f"[决策层-表情包] 检测到表情包请求: '{content}' (用户: {user_id}, 平台: {platform})"
        )

        # 提取具体表情包名称（如果有）
        emoji_name = None
        if specific_match:
            emoji_name = specific_match.group(2).strip()
            logger.info(f"[决策层-表情包] 提取到具体表情包名称: '{emoji_name}'")

        try:
            # 根据平台类型处理表情包请求
            if platform == "qq":
                # QQ平台，需要特殊处理
                from webnet.qq.message_handler import QQMessageHandler

                # 查找消息处理器实例
                qq_handler = None
                if hasattr(self, "qq_net") and self.qq_net:
                    if hasattr(self.qq_net, "message_handler"):
                        qq_handler = self.qq_net.message_handler

                if not qq_handler:
                    logger.warning(
                        f"[决策层-表情包] 未找到QQ消息处理器，尝试通过工具调用"
                    )
                    return await self._process_emoji_via_tools(
                        perception, platform, content, user_id, sender_name, emoji_name
                    )

                # 获取群组ID和消息类型
                group_id = perception.get("group_id", 0)
                message_type = perception.get("message_type", "private")

                logger.info(
                    f"[决策层-表情包] QQ平台处理表情包请求: group_id={group_id}, message_type={message_type}, emoji_name='{emoji_name}'"
                )

                # 调用消息处理器的表情包发送方法
                if message_type == "group" and group_id > 0:
                    # 群聊
                    if hasattr(qq_handler, "_send_emoji_response"):
                        success = await qq_handler._send_emoji_response(
                            group_id, int(user_id) if user_id.isdigit() else 0
                        )
                        if success:
                            return "好的，我这就给你发送一个表情包~"
                        else:
                            return "抱歉，表情包发送失败了。可能是表情包文件不存在或者发送过程中出了点问题。"
                    else:
                        logger.error(f"[决策层-表情包] QQ消息处理器没有表情包发送方法")
                else:
                    # 私聊
                    if hasattr(qq_handler, "_send_emoji_response"):
                        success = await qq_handler._send_emoji_response(
                            0, int(user_id) if user_id.isdigit() else 0
                        )
                        if success:
                            return "好的，我这就给你发送一个表情包~"
                        else:
                            return "抱歉，表情包发送失败了。可能是表情包文件不存在或者发送过程中出了点问题。"

            # 其他平台或通过工具调用
            return await self._process_emoji_via_tools(
                perception, platform, content, user_id, sender_name, emoji_name
            )

        except Exception as e:
            logger.error(f"[决策层-表情包] 处理表情包请求失败: {e}", exc_info=True)
            return f"处理表情包请求时出错：{str(e)}"

    async def _process_emoji_via_tools(
        self,
        perception: dict,
        platform: str,
        content: str,
        user_id: str,
        sender_name: str,
        emoji_name: str = None,
    ) -> str:
        """
        通过ToolNet工具处理表情包请求

        Args:
            perception: 感知数据
            platform: 平台类型
            content: 用户输入内容
            user_id: 用户ID
            sender_name: 发送者名称
            emoji_name: 表情包名称（可选）

        Returns:
            处理结果文本
        """
        logger.info(
            f"[决策层-表情包-工具] 通过工具处理表情包请求: 平台={platform}, 用户={user_id}, 表情包名称='{emoji_name}'"
        )

        # 如果ToolNet子网不可用，返回提示
        if not self.tool_subnet:
            logger.warning("[决策层-表情包-工具] ToolNet子网不可用")
            return "抱歉，表情包功能暂时不可用。"

        try:
            # 准备工具参数
            tool_args = {
                "platform": platform,
                "user_id": user_id,
                "emoji_name": emoji_name if emoji_name else "",
                "context": content,
            }

            # 如果是QQ平台，添加额外信息
            if platform == "qq":
                tool_args.update(
                    {
                        "group_id": perception.get("group_id", 0),
                        "message_type": perception.get("message_type", "private"),
                    }
                )

            # 调用ToolNet的表情包工具
            result = await self.tool_subnet.execute_tool(
                tool_name="send_emoji",
                args=tool_args,
                user_id=int(user_id) if user_id.isdigit() else 0,
                group_id=perception.get("group_id", 0),
                message_type=perception.get("message_type", "private"),
                sender_name=sender_name,
            )

            logger.info(f"[决策层-表情包-工具] 表情包工具调用结果: {result[:100]}...")

            # 格式化响应
            if "已发送" in result or "发送成功" in result or "表情包" in result:
                return result
            else:
                # 如果工具调用失败，提供友好的回退响应
                if emoji_name:
                    return f"虽然我无法发送'{emoji_name}'表情包，但我可以用文字表达我的心情：开心(*^▽^*)"
                else:
                    return (
                        "虽然我无法发送表情包，但我可以用文字表达我的心情：开心(*^▽^*)"
                    )

        except Exception as e:
            logger.error(
                f"[决策层-表情包-工具] 通过工具处理表情包请求失败: {e}", exc_info=True
            )
            return f"处理表情包请求时出错：{str(e)}"

    def _handle_quick_commands(self, content: str, platform: str) -> Optional[str]:
        """
        快速命令处理（在AI调用之前拦截）

        Args:
            content: 用户输入
            platform: 平台类型

        Returns:
            如果是快速命令，返回响应；否则返回None让AI处理
        """
        if not self.personality:
            logger.warning("[决策层] personality为空，无法处理快捷命令")
            return None

        content_lower = content.lower().strip()
        logger.info(
            f"[决策层] 处理命令: {content}, personality: {type(self.personality)}"
        )

        # 1. 状态查询命令
        if content_lower in ["状态", "查看状态", "/状态", "状态查询"]:
            logger.info(f"[决策层] 捕获状态命令: {content}")
            profile = self.personality.get_profile()

            lines = [
                "【弥娅状态】",
                f"形态: {profile.get('current_form', 'normal')}",
            ]

            if "vectors" in profile:
                lines.append("【七重特质】")
                lines.append(f"  清醒: {profile['vectors'].get('awake', 0):.2f}")
                lines.append(
                    f"  说话: {profile['vectors'].get('speak', 0):.2f} [{profile.get('speak_mode', 'casual')}]"
                )
                lines.append(f"  记住: {profile['vectors'].get('remember', 0):.2f}")
                lines.append(f"  等: {profile['vectors'].get('wait', 0):.2f}")
                lines.append(f"  疼: {profile['vectors'].get('pain', 0):.2f}")
                lines.append(f"  怕: {profile['vectors'].get('fear', 0):.2f}")
                lines.append(f"  押: {profile['vectors'].get('commit', 0):.2f}")

            return "\n".join(lines)

        # 2. 形态切换命令
        if content_lower.startswith("/形态") or content_lower.startswith("/form"):
            from core.personality import Personality

            cmd = content.replace("/形态", "").replace("/form", "").strip().lower()
            if not cmd:
                profile = self.personality.get_profile()
                current_form = profile.get("current_form", "normal")
                form_info = profile.get("form_info", {})
                lines = [
                    f"当前形态: {current_form}",
                    f"  名称: {form_info.get('name', '常态')}",
                ]
                if profile.get("current_core_form"):
                    lines.append(f"核心形态: {profile['current_core_form']}")
                lines.append("")
                lines.append("可用形态: normal, cold, soft, hard, fragile")
                lines.append(
                    "可用核心形态: sober, speaking, waiting, vulnerable, afraid, committing"
                )
                return "\n".join(lines)

            if cmd in ["normal", "cold", "soft", "hard", "fragile"]:
                success = self.personality.set_form(cmd)
                return f"已切换到形态: {cmd}" if success else "切换失败"
            elif cmd in Personality.CORE_FORMS:
                success = self.personality.set_core_form(cmd)
                return f"已切换到核心形态: {cmd}" if success else "切换失败"
            return f"未知形态: {cmd}"

        # 3. 说话模式命令
        if content_lower.startswith("/说话") or content_lower.startswith("/speak"):
            cmd = content.replace("/说话", "").replace("/speak", "").strip().lower()
            if not cmd:
                current_mode = self.personality.get_speak_mode()
                return f"当前说话模式: {current_mode} (casual闲聊/catching捕捉/confiding倾诉)"

            valid_modes = ["casual", "catching", "confiding"]
            if cmd in valid_modes:
                success = self.personality.set_speak_mode(cmd)
                return f"已切换说话模式: {cmd}" if success else "切换失败"
            return f"未知模式: {cmd}"

        # 4. 存在性情感命令
        if content_lower.startswith("/存在") or content_lower.startswith("/exist"):
            cmd = content.replace("/存在", "").replace("/exist", "").strip().lower()
            if not cmd:
                return "【存在性情感命令】\n/存在 - 查看当前情感状态\n/存在 <情感名> - 激活特定情感\n\n可用: existential_pain, fear_of_forgotten, waiting, commitment_weight, awareness, connection_need, vulnerability_trust"
            return f"未知情感: {cmd}"

        # 不是快速命令
        return None

    def _append_qq_status_tag(self, response: str) -> str:
        """
        在QQ响应末尾附加弥娅状态标签

        Args:
            response: 原始响应

        Returns:
            附加状态标签后的响应
        """
        if not self.personality:
            return response

        try:
            profile = self.personality.get_profile()
            current_form = profile.get("current_form", "normal")
            speak_mode = profile.get("speak_mode", "casual")
            current_core = profile.get("current_core_form", "")

            # 构建状态标签
            form_names = {
                "normal": "常态",
                "cold": "冷态",
                "soft": "软态",
                "hard": "硬态",
                "fragile": "脆态",
            }
            form_name = form_names.get(current_form, current_form)

            # 核心形态简称
            core_abbrev = {
                "sober": "清醒",
                "speaking": "说话",
                "waiting": "等",
                "vulnerable": "疼",
                "afraid": "怕",
                "committing": "押",
            }
            core_name = core_abbrev.get(current_core, "") if current_core else ""

            if core_name:
                tag = f"\n\n[{form_name}|{speak_mode}|{core_name}]"
            else:
                tag = f"\n\n[{form_name}|{speak_mode}]"

            logger.debug(f"[决策层] 添加状态标签: {tag}")
            return response + tag
        except Exception as e:
            logger.debug(f"[决策层] 添加状态标签失败: {e}")
            return response
