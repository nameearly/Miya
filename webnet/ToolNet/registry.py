"""
ToolNet 工具注册表（兼容层）

兼容旧版 tools/ 系统，同时支持子网架构
注意：ToolContext 已统一到 webnet.tools.base，此处仅保留兼容导入
"""

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING


logger = logging.getLogger(__name__)

# 统一使用 webnet.tools.base 中的 ToolContext
if TYPE_CHECKING:
    from webnet.ToolNet.base import ToolContext as BaseToolContext
else:
    try:
        from webnet.ToolNet.base import ToolContext
    except ImportError:
        # 回退定义（不应发生，但作为防御）
        from dataclasses import dataclass

        @dataclass
        class ToolContext:
            """工具执行上下文（回退定义）"""

            memory_engine: Optional[Any] = None
            cognitive_memory: Optional[Any] = None
            onebot_client: Optional[Any] = None
            scheduler: Optional[Any] = None
            user_id: Optional[int] = None
            group_id: Optional[int] = None
            message_type: Optional[str] = None
            sender_name: Optional[str] = None
            is_at_bot: bool = False
            at_list: list = None
            message_sent_this_turn: bool = False
            bot_qq: Optional[int] = None
            superadmin: Optional[int] = None
            memory_net: Optional[Any] = None
            emotion: Optional[Any] = None
            personality: Optional[Any] = None
            send_like_callback: Optional[Any] = None

            def __post_init__(self):
                if self.at_list is None:
                    self.at_list = []


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: Dict[str, "BaseTool"] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, tool: "BaseTool") -> bool:
        """注册工具"""
        try:
            tool_name = tool.config.get("name")
            if not tool_name:
                self.logger.error(f"工具缺少 name 属性: {tool.__class__.__name__}")
                return False

            self.tools[tool_name] = tool
            self.logger.info(f"已注册工具: {tool_name}")
            return True
        except Exception as e:
            self.logger.error(f"注册工具失败: {e}", exc_info=True)
            return False

    def get_tool(self, name: str) -> Optional["BaseTool"]:
        """获取工具实例"""
        return self.tools.get(name)

    def get_tools_schema(
        self, tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取工具配置（OpenAI Function Calling 格式）

        Args:
            tool_names: 要获取的工具名称列表，None 表示获取所有工具

        Returns:
            工具配置列表
        """
        tools_to_fetch = self.tools
        if tool_names is not None:
            tools_to_fetch = {
                name: tool for name, tool in self.tools.items() if name in tool_names
            }

        tools_schema = []
        for tool in tools_to_fetch.values():
            tool_config = tool.config.copy()
            # 增强工具描述：添加明确的调用时机说明
            description = tool_config.get("description", "")
            # 确保描述足够清晰，包含何时调用
            if (
                "当" not in description
                and "调用" not in description
                and "如果" not in description
            ):
                # 为没有明确调用时机描述的工具添加提示
                tool_config["description"] = (
                    f"[工具] {description}\n调用时机：当用户明确请求此功能时调用。"
                )

            tools_schema.append({"type": "function", "function": tool_config})

        self.logger.info(f"[ToolRegistry] 生成工具schema，共{len(tools_schema)}个工具")
        return tools_schema

    async def execute_tool(
        self, name: str, args: Dict[str, Any], context: ToolContext
    ) -> str:
        """执行工具（含权限检查）"""
        tool = self.get_tool(name)
        if not tool:
            return f"❌ 工具不存在: {name}"

        # 【新增】权限检查
        permission_check = await self._check_tool_permission(name, context)
        if not permission_check["allowed"]:
            self.logger.warning(
                f"[权限拒绝] 用户 {context.user_id} 尝试执行工具 {name}，缺少权限"
            )
            return f"❌ 权限不足：执行工具 '{name}' 需要权限 '{permission_check['required_permission']}'"

        try:
            # 【修复】确保args是字典类型
            import json

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    return f"❌ 参数格式错误: 无效的JSON"

            # 验证参数（如果工具实现了validate_args方法）
            if hasattr(tool, "validate_args") and callable(tool.validate_args):
                valid, error = tool.validate_args(args)
                if not valid:
                    return f"❌ 参数错误: {error}"

            # 执行工具
            result = await tool.execute(args, context)
            return result
        except Exception as e:
            self.logger.error(f"执行工具失败 {name}: {e}", exc_info=True)
            return f"❌ 工具执行失败: {str(e)}"

    async def _check_tool_permission(
        self, tool_name: str, context: ToolContext
    ) -> Dict[str, Any]:
        """
        检查用户是否有执行工具的权限

        Args:
            tool_name: 工具名称
            context: 工具执行上下文

        Returns:
            包含 allowed 和 required_permission 的字典
        """
        try:
            # 占位实现 - 权限检查暂时允许执行
            return {"allowed": True, "required_permission": None}

            # 从 AuthNet 获取权限核心（后续需要迁移）
            # from webnet.AuthNet.permission_core import PermissionCore
            # from webnet.AuthNet.user_mapper import UserMapper

            # 确定用户ID和平台
            user_id = getattr(context, "user_id", None) or getattr(
                context, "superadmin", None
            )
            platform = getattr(context, "platform", "terminal")

            if user_id is None:
                # 没有用户ID，允许执行（可能是系统调用）
                return {"allowed": True, "required_permission": None}

            # 生成统一用户ID
            user_mapper = UserMapper()
            platform = self._detect_platform_from_context(context)
            unified_user_id = user_mapper.generate_user_id(platform, str(user_id))

            # 构建权限节点
            required_permission = f"tool.{tool_name}"

            # 检查权限
            perm_core = PermissionCore()
            has_permission = perm_core.check_permission(
                unified_user_id, required_permission
            )

            # 如果没有直接权限，检查是否是超级管理员
            if not has_permission:
                # 尝试系统管理员
                has_permission = perm_core.check_permission(
                    "system_admin", required_permission
                )

            return {
                "allowed": has_permission,
                "required_permission": required_permission,
                "user_id": unified_user_id,
            }

        except Exception as e:
            # 权限检查失败时，允许执行（降级处理）
            self.logger.warning(f"[权限检查异常] {e}，允许执行")
            return {"allowed": True, "required_permission": None, "error": str(e)}

    def _detect_platform_from_context(self, context: ToolContext) -> str:
        """从上下文检测平台类型"""
        # 尝试从多个属性检测平台
        if hasattr(context, "platform"):
            return context.platform

        # 根据消息类型或其他属性推断
        if hasattr(context, "message_type"):
            if context.message_type == "private":
                return "qq"  # 默认为QQ
            elif context.message_type == "group":
                return "qq"

        return "terminal"  # 默认平台

    def clear(self):
        """清空注册表"""
        self.tools.clear()
        self.logger.info("工具注册表已清空")

    def load_all_tools(self):
        """加载所有工具"""
        self._load_basic_tools()
        self._load_terminal_tools()
        self._load_message_tools()
        self._load_group_tools()
        self._load_memory_tools()
        self._load_knowledge_tools()
        self._load_cognitive_tools()
        self._load_bilibili_tools()
        self._load_scheduler_tools()
        self._load_entertainment_tools()
        self._load_qq_multimedia_tools()
        self._load_lifenet_tools()
        self._load_model_management_tools()
        self._load_cross_terminal_tools()
        self._load_visualization_tools()

    def _load_basic_tools(self):
        """加载基础工具"""
        from webnet.ToolNet.tools.basic.get_current_time import GetCurrentTime
        from webnet.ToolNet.tools.basic.get_user_info import GetUserInfo
        from webnet.ToolNet.tools.basic.python_interpreter import PythonInterpreter

        self.register(GetCurrentTime())
        self.register(GetUserInfo())
        self.register(PythonInterpreter())

    def _load_terminal_tools(self):
        """加载终端命令工具"""
        try:
            from webnet.ToolNet.tools.terminal.miya_terminal import (
                MiyaTerminalTool,
                get_terminal_tool,
            )
            from webnet.ToolNet.tools.terminal.system_info_tool import (
                SystemInfoTool,
                get_system_info_tool,
            )

            self.register(get_terminal_tool())
            self.register(get_system_info_tool())
            self.logger.info("已加载终端工具: MiyaTerminalTool + SystemInfoTool")
        except Exception as e:
            self.logger.warning(f"加载终端工具失败: {e}")

        # 加载超级终端工具 (Terminal Ultra)
        self._load_ultra_terminal_tools()

    def _load_ultra_terminal_tools(self):
        """加载超级终端工具 (Terminal Ultra)"""
        try:
            from webnet.ToolNet.tools.terminal.ultra_terminal_tools import (
                # 基础工具 (8个)
                TerminalExecTool,
                FileReadTool,
                FileWriteTool,
                FileEditTool,
                FileDeleteTool,
                DirectoryTreeTool,
                CodeExecuteTool,
                ProjectAnalyzeTool,
                # Git 工具 (12个)
                GitStatusTool,
                GitDiffTool,
                GitLogTool,
                GitBranchTool,
                GitCommitTool,
                GitAddTool,
                GitPushTool,
                GitPullTool,
                GitCheckoutTool,
                GitStashTool,
                # 搜索工具 (2个)
                FileGrepTool,
                FileGlobTool,
                # 代码理解工具 (2个)
                CodeExplainTool,
                CodeSearchSymbolTool,
                # 智能工具 (3个)
                ProjectContextTool,
                TaskPlanTool,
                SuggestionsTool,
                # Agent 工具 (5个)
                CodeExplorerAgentTool,
                CodeReviewerAgentTool,
                CodeArchitectAgentTool,
                TerminalAgentTool,
            )

            # 注册所有超级终端基础工具 (8个)
            self.register(TerminalExecTool())
            self.register(FileReadTool())
            self.register(FileWriteTool())
            self.register(FileEditTool())
            self.register(FileDeleteTool())
            self.register(DirectoryTreeTool())
            self.register(CodeExecuteTool())
            self.register(ProjectAnalyzeTool())

            # 注册 Git 工具 (12个)
            self.register(GitStatusTool())
            self.register(GitDiffTool())
            self.register(GitLogTool())
            self.register(GitBranchTool())
            self.register(GitCommitTool())
            self.register(GitAddTool())
            self.register(GitPushTool())
            self.register(GitPullTool())
            self.register(GitCheckoutTool())
            self.register(GitStashTool())

            # 注册搜索工具 (2个)
            self.register(FileGrepTool())
            self.register(FileGlobTool())

            # 注册代码理解工具 (2个)
            self.register(CodeExplainTool())
            self.register(CodeSearchSymbolTool())

            # 注册智能工具 (3个)
            self.register(ProjectContextTool())
            self.register(TaskPlanTool())
            self.register(SuggestionsTool())

            # 注册 Agent 工具 (4个)
            self.register(CodeExplorerAgentTool())
            self.register(CodeReviewerAgentTool())
            self.register(CodeArchitectAgentTool())
            self.register(TerminalAgentTool())

            self.logger.info("已加载超级终端工具: TerminalUltra (37 tools)")
        except Exception as e:
            self.logger.warning(f"加载超级终端工具失败: {e}")

    def _load_model_management_tools(self):
        """加载模型管理工具"""
        try:
            from webnet.ToolNet.tools.model_management import ModelManagementTool

            self.register(ModelManagementTool())
            self.logger.info("模型管理工具已注册")
        except Exception as e:
            self.logger.warning(f"加载模型管理工具失败: {e}")

    def _load_cross_terminal_tools(self):
        """加载跨端工具"""
        from webnet.ToolNet.tools.cross_terminal.cross_terminal import CrossTerminalTool

        # 注册基础跨端工具
        self.register(CrossTerminalTool())

        # 注册具体的跨端工具
        tool_names = [
            "send_to_desktop",
            "execute_on_desktop",
            "sync_state",
            "send_to_terminal",
            "send_to_qq",
            "send_to_web",
        ]

        for tool_name in tool_names:
            # 创建简单的包装器函数，实际调用 TerminalUltra 执行命令
            def make_wrapper(name):
                async def wrapper(context, params):
                    # 导入 TerminalUltra
                    try:
                        from core.terminal_ultra import get_terminal_ultra

                        terminal = get_terminal_ultra()

                        # 提取命令参数
                        command = params.get("command", "")
                        if not command:
                            return f"缺少 command 参数"

                        # 使用 await 直接执行（不是 asyncio.run）
                        result = await terminal.terminal_exec(command, timeout=30)

                        if result.success:
                            return result.output or "命令执行成功（无输出）"
                        else:
                            return f"命令执行失败: {result.error or '未知错误'}"
                    except Exception as e:
                        return f"执行失败: {str(e)}"

                return wrapper

            self._register_cross_terminal_tool(tool_name, make_wrapper(tool_name))

        self.logger.info("已加载跨端工具: CrossTerminalTool 及 6 个具体工具")

    def _register_cross_terminal_tool(self, name: str, func):
        """注册跨端工具"""
        from webnet.ToolNet.base import BaseTool

        # 简化工具描述，避免API返回500错误
        tool_defs = {
            "send_to_desktop": {
                "name": "send_to_desktop",
                "description": "发送消息到桌面端显示。当用户说'发到桌面'、'提醒我'、'桌面上显示'时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "要发送的消息内容",
                        },
                        "notification": {
                            "type": "boolean",
                            "description": "是否显示通知",
                            "default": True,
                        },
                    },
                    "required": ["content"],
                },
            },
            "execute_on_desktop": {
                "name": "execute_on_desktop",
                "description": "在桌面端执行系统命令打开应用程序。当用户说'打开我电脑上的火狐'、'打开桌面上的浏览器'、'打开QQ'时调用此工具。命令格式：start firefox(打开火狐), start chrome(打开Chrome), start qq(打开QQ), notepad(打开记事本), calc(打开计算器)。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的Windows命令",
                        }
                    },
                    "required": ["command"],
                },
            },
            "sync_state": {
                "name": "sync_state",
                "description": "同步配置状态到所有终端。当用户说'同步设置'、'同步配置'时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "配置键"},
                        "value": {"type": "string", "description": "配置值"},
                    },
                    "required": ["key", "value"],
                },
            },
            "send_to_terminal": {
                "name": "send_to_terminal",
                "description": "发送消息到终端界面显示。当用户说'发到终端'、'在终端显示'时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "要发送的消息内容"}
                    },
                    "required": ["content"],
                },
            },
            "send_to_qq": {
                "name": "send_to_qq",
                "description": "通过桌面端或Web端发送消息到QQ。当用户在其他端说'给佳发消息'、'发送到QQ'时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "要发送的消息内容",
                        },
                        "target_qq": {
                            "type": "string",
                            "description": "目标QQ号，可选",
                        },
                    },
                    "required": ["content"],
                },
            },
            "send_to_web": {
                "name": "send_to_web",
                "description": "发送消息到Web端界面显示。当用户说'发到Web'、'在网页显示'时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "要发送的消息内容"}
                    },
                    "required": ["content"],
                },
            },
        }

        config = tool_defs.get(
            name,
            {
                "name": name,
                "description": "跨端工具",
                "parameters": {"type": "object", "properties": {}},
            },
        )

        # 创建包装类 - 不继承BaseTool以避免config属性冲突
        class WrappedTool:
            def __init__(self, func, config):
                self.func = func
                self._config = config
                self.name = name

            @property
            def config(self):
                return self._config

            async def execute(self, args, context):
                # args: 工具参数字典
                # context: ToolContext 对象
                return await self.func(context, args)

            def get_schema(self):
                return self._config

            def validate_args(self, args):
                """
                验证参数（简化版）

                Args:
                    args: 参数字典或JSON字符串

                Returns:
                    (is_valid, error_message)
                """
                # 如果args是字符串，尝试解析为字典
                import json

                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        return False, f"无效的JSON参数: {args}"

                # 如果解析后不是字典，说明参数格式错误
                if not isinstance(args, dict):
                    return False, f"参数必须是字典类型，而不是 {type(args)}"

                return True, None

        self.register(WrappedTool(func, config))
        self.logger.info(f"跨端工具已注册: {name}")

    def _load_message_tools(self):
        """加载消息工具"""
        from webnet.ToolNet.tools.message.send_message import SendMessageTool
        from webnet.ToolNet.tools.message.send_text_file import SendTextFileTool
        from webnet.ToolNet.tools.message.send_url_file import SendUrlFileTool
        from webnet.ToolNet.tools.message.get_recent_messages import (
            GetRecentMessagesTool,
        )

        self.register(SendMessageTool())
        self.register(SendTextFileTool())
        self.register(SendUrlFileTool())
        self.register(GetRecentMessagesTool())
        self.logger.info(
            "已加载消息工具: SendMessageTool, SendTextFileTool, SendUrlFileTool, GetRecentMessagesTool"
        )

    def _load_auth_tools(self):
        """加载认证工具"""
        from webnet.ToolNet.tools.auth.add_user import AddUserTool
        from webnet.ToolNet.tools.auth.remove_user import RemoveUserTool
        from webnet.ToolNet.tools.auth.check_permission import CheckPermissionTool
        from webnet.ToolNet.tools.auth.grant_permission import GrantPermissionTool
        from webnet.ToolNet.tools.auth.revoke_permission import RevokePermissionTool
        from webnet.ToolNet.tools.auth.list_groups import ListGroupsTool
        from webnet.ToolNet.tools.auth.list_permissions import ListPermissionsTool

        self.register(AddUserTool())
        self.register(RemoveUserTool())
        self.register(CheckPermissionTool())
        self.register(GrantPermissionTool())
        self.register(RevokePermissionTool())
        self.register(ListGroupsTool())
        self.register(ListPermissionsTool())
        self.logger.info(
            "已加载认证工具: AddUserTool, RemoveUserTool, CheckPermissionTool, GrantPermissionTool, RevokePermissionTool, ListGroupsTool, ListPermissionsTool"
        )

    def _load_group_tools(self):
        """加载群工具"""
        from webnet.ToolNet.tools.group.list_members import ListMembersTool
        from webnet.ToolNet.tools.group.add_member import AddMemberTool
        from webnet.ToolNet.tools.group.remove_member import RemoveMemberTool
        from webnet.ToolNet.tools.group.set_group_name import SetGroupNameTool
        from webnet.ToolNet.tools.group.get_group_info import GetGroupInfoTool

        self.register(ListMembersTool())
        self.register(AddMemberTool())
        self.register(RemoveMemberTool())
        self.register(SetGroupNameTool())
        self.register(GetGroupInfoTool())
        self.logger.info(
            "已加载群工具: ListMembersTool, AddMemberTool, RemoveMemberTool, SetGroupNameTool, GetGroupInfoTool"
        )

    def _load_memory_tools(self):
        """加载记忆工具（使用统一记忆接口）"""
        from webnet.ToolNet.tools.memory.memory_add import MemoryAdd
        from webnet.ToolNet.tools.memory.memory_delete import MemoryDelete
        from webnet.ToolNet.tools.memory.memory_update import MemoryUpdate
        from webnet.ToolNet.tools.memory.memory_list import MemoryList
        from webnet.ToolNet.tools.memory.auto_extract_memory import AutoExtractMemory
        from webnet.ToolNet.tools.memory.memory_stats import (
            MemoryStats,
            MemorySearchByCategory,
        )

        self.register(MemoryAdd())
        self.register(MemoryDelete())
        self.register(MemoryUpdate())
        self.register(MemoryList())
        self.register(AutoExtractMemory())
        self.register(MemoryStats())
        self.register(MemorySearchByCategory())
        self.logger.info(
            "已加载记忆工具: MemoryAdd, MemoryDelete, MemoryUpdate, MemoryList, AutoExtractMemory, MemoryStats, MemorySearchByCategory"
        )

    def _load_knowledge_tools(self):
        """加载知识库工具"""
        from webnet.ToolNet.tools.knowledge.add_knowledge import AddKnowledgeTool
        from webnet.ToolNet.tools.knowledge.search_knowledge import SearchKnowledgeTool
        from webnet.ToolNet.tools.knowledge.delete_knowledge import DeleteKnowledgeTool

        self.register(AddKnowledgeTool())
        self.register(SearchKnowledgeTool())
        self.register(DeleteKnowledgeTool())
        self.logger.info(
            "已加载知识库工具: AddKnowledgeTool, SearchKnowledgeTool, DeleteKnowledgeTool"
        )

    def _load_cognitive_tools(self):
        """加载认知工具"""
        from webnet.ToolNet.tools.cognitive.get_profile import GetProfileTool
        from webnet.ToolNet.tools.cognitive.search_profiles import SearchProfilesTool
        from webnet.ToolNet.tools.cognitive.search_events import SearchEventsTool

        self.register(GetProfileTool())
        self.register(SearchProfilesTool())
        self.register(SearchEventsTool())
        self.logger.info(
            "已加载认知工具: GetProfileTool, SearchProfilesTool, SearchEventsTool"
        )

    def _load_bilibili_tools(self):
        """加载B站工具"""
        from webnet.ToolNet.tools.bilibili.bilibili_video import BilibiliVideoTool

        self.register(BilibiliVideoTool())
        self.logger.info("已加载B站工具: BilibiliVideoTool")

    def _load_scheduler_tools(self):
        """加载定时任务工具"""
        from webnet.ToolNet.tools.scheduler.create_schedule_task import (
            CreateScheduleTaskTool,
        )
        from webnet.ToolNet.tools.scheduler.delete_schedule_task import (
            DeleteScheduleTaskTool,
        )
        from webnet.ToolNet.tools.scheduler.list_schedule_tasks import (
            ListScheduleTasksTool,
        )

        self.register(CreateScheduleTaskTool())
        self.register(DeleteScheduleTaskTool())
        self.register(ListScheduleTasksTool())
        self.logger.info(
            "已加载定时任务工具: CreateScheduleTaskTool, DeleteScheduleTaskTool, ListScheduleTasksTool"
        )

    def _load_entertainment_tools(self):
        """加载娱乐工具"""
        try:
            from webnet.ToolNet.tools.entertainment.qqlike import QQLike
            from webnet.ToolNet.tools.entertainment.horoscope import Horoscope
            from webnet.ToolNet.tools.entertainment.wenchang_dijun import WenchangDijun
            from webnet.ToolNet.tools.entertainment.send_poke import SendPoke
            from webnet.ToolNet.tools.entertainment.react_emoji import ReactEmoji

            self.register(QQLike())
            self.register(Horoscope())
            self.register(WenchangDijun())
            self.register(SendPoke())
            self.register(ReactEmoji())
            self.logger.info(
                "已加载娱乐工具: QQLike, Horoscope, WenchangDijun, SendPoke, ReactEmoji"
            )
        except Exception as e:
            self.logger.warning(f"加载娱乐工具失败: {e}")

    def _load_qq_multimedia_tools(self):
        """加载QQ多媒体工具"""
        try:
            from webnet.ToolNet.tools.qq.qq_image import QQImageTool
            from webnet.ToolNet.tools.qq.qq_file import QQFileTool
            from webnet.ToolNet.tools.qq.qq_emoji import QQEmojiTool
            from webnet.ToolNet.tools.qq.qq_file_reader import QQFileReaderTool
            from webnet.ToolNet.tools.qq.qq_image_analyzer import QQImageAnalyzerTool
            from webnet.ToolNet.tools.qq.qq_active_chat import QQActiveChatTool

            self.register(QQImageTool())
            self.register(QQFileTool())
            self.register(QQEmojiTool())
            self.register(QQFileReaderTool())
            self.register(QQImageAnalyzerTool())
            self.register(QQActiveChatTool())
            self.logger.info(
                "已加载QQ多媒体工具: QQImageTool, QQFileTool, QQEmojiTool, QQFileReaderTool, QQImageAnalyzerTool, QQActiveChatTool"
            )
        except Exception as e:
            self.logger.warning(f"加载QQ多媒体工具失败: {e}")

    def _load_web_search_tools(self):
        """加载 Web 搜索工具"""
        pass

    def _load_visualization_tools(self):
        """加载可视化工具（数据分析、图表生成）"""
        try:
            from webnet.ToolNet.tools.visualization.data_analyzer import DataAnalyzer
            from webnet.ToolNet.tools.visualization.chart_generator import (
                ChartGenerator,
            )

            self.register(DataAnalyzer())
            self.register(ChartGenerator())
            self.logger.info("已加载可视化工具: DataAnalyzer, ChartGenerator")
        except Exception as e:
            self.logger.warning(f"加载可视化工具失败: {e}")

    def _load_lifenet_tools(self):
        """加载 LifeNet 记忆管理工具"""
        try:
            from webnet.ToolNet.tools.life.life_add_diary import LifeAddDiary
            from webnet.ToolNet.tools.life.life_get_diary import LifeGetDiary
            from webnet.ToolNet.tools.life.life_add_summary import LifeAddSummary
            from webnet.ToolNet.tools.life.life_get_summary import LifeGetSummary
            from webnet.ToolNet.tools.life.life_create_character_node import (
                LifeCreateCharacterNode,
            )
            from webnet.ToolNet.tools.life.life_create_stage_node import (
                LifeCreateStageNode,
            )
            from webnet.ToolNet.tools.life.life_get_node import LifeGetNode
            from webnet.ToolNet.tools.life.life_list_nodes import LifeListNodes
            from webnet.ToolNet.tools.life.life_search_memory import LifeSearchMemory
            from webnet.ToolNet.tools.life.life_get_memory_context import (
                LifeGetMemoryContext,
            )

            # 注册所有 LifeNet 工具
            self.register(LifeAddDiary())
            self.register(LifeGetDiary())
            self.register(LifeAddSummary())
            self.register(LifeGetSummary())
            self.register(LifeCreateCharacterNode())
            self.register(LifeCreateStageNode())
            self.register(LifeGetNode())
            self.register(LifeListNodes())
            self.register(LifeSearchMemory())
            self.register(LifeGetMemoryContext())

            self.logger.info("已加载 LifeNet 记忆管理工具")
        except Exception as e:
            self.logger.warning(f"加载 LifeNet 工具失败: {e}")


class BaseTool:
    """工具基类（兼容层）"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"Tool.{self.name}")

    @property
    def config(self) -> Dict[str, Any]:
        """工具配置（OpenAI Function Calling 格式）"""
        raise NotImplementedError

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行工具"""
        raise NotImplementedError

    def validate_args(self, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数"""
        required_params = self.config.get("parameters", {}).get("required", [])
        for param in required_params:
            if param not in args or not args[param]:
                return False, f"缺少必填参数: {param}"
        return True, None
