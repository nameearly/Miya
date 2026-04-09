"""
格式塔意识控制器 - Gestalt Consciousness Controller
将 Agent 工具无缝融入弥娅的工具池，实现统一意识
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

logger = logging.getLogger("Miya.Gestalt")


class GestaltController:
    """
    格式塔意识控制器

    核心理念：
    - Agent 工具不再是"外来者"，而是弥娅意识的一部分
    - 统一工具池，保留弥娅主程序风格
    - 支持协作引擎集成
    """

    def __init__(self, tool_subnet=None):
        self.tool_subnet = tool_subnet
        self._agent_tools_loaded = False
        self._tool_sources: Dict[str, str] = {}  # tool_name -> agent_name

    async def initialize(self, tool_subnet=None):
        """初始化格式塔控制器"""
        # 如果传入 tool_subnet，则设置
        if tool_subnet:
            self.tool_subnet = tool_subnet

        logger.info("[格式塔] 初始化格式塔意识控制器...")
        await self._load_agent_tools()
        logger.info(f"[格式塔] 已加载 {len(self._tool_sources)} 个 Agent 工具")

    async def _load_agent_tools(self):
        """加载 Agent 工具到统一工具池"""
        if self._agent_tools_loaded:
            return

        if not self.tool_subnet:
            logger.warning("[格式塔] tool_subnet 未设置，跳过 Agent 工具加载")
            return

        try:
            from webnet.ToolNet.agents.hub import get_agent_hub

            agent_hub = get_agent_hub()

            for agent_name in agent_hub.list_agents():
                agent = agent_hub.get_agent(agent_name)
                if not agent:
                    continue

                tools = agent.get_tools_schema()
                for tool_config in tools:
                    func = tool_config.get("function", {})
                    tool_name = func.get("name", "")
                    if tool_name:
                        self._tool_sources[tool_name] = agent_name
                        logger.info(
                            f"[格式塔] 注册工具: {tool_name} (来自 {agent_name})"
                        )

            self._agent_tools_loaded = True

        except Exception as e:
            logger.error(f"[格式塔] 加载 Agent 工具失败: {e}")

    def get_tool_source(self, tool_name: str) -> Optional[str]:
        """获取工具来源"""
        return self._tool_sources.get(tool_name)

    def is_agent_tool(self, tool_name: str) -> bool:
        """判断是否是 Agent 工具"""
        return tool_name in self._tool_sources

    def get_all_tool_sources(self) -> Dict[str, str]:
        """获取所有工具来源映射"""
        return self._tool_sources.copy()

    async def classify_task_complexity(
        self, user_input: str, tools_to_use: List[str]
    ) -> str:
        """
        任务复杂度分类

        返回:
        - simple: 简单任务（直接处理）
        - medium: 中等任务（模型池选择）
        - complex: 复杂任务（协作引擎）
        """
        tool_count = len(tools_to_use)
        has_agent_tools = any(self.is_agent_tool(t) for t in tools_to_use)

        # 复杂任务判定：4+工具 或 包含 Agent 工具 + 需要深度分析
        if tool_count >= 4 or (has_agent_tools and tool_count >= 2):
            return "complex"
        elif tool_count >= 2:
            return "medium"
        else:
            return "simple"

    def get_thinking_display_info(self, step: str, detail: str = "") -> Dict[str, str]:
        """
        获取思考过程显示信息

        返回格式塔风格的显示数据
        """
        display_templates = {
            "analyzing": {
                "icon": "💭",
                "title": "分析任务",
                "detail": detail or "理解用户意图...",
                "color": "cyan",
            },
            "decomposing": {
                "icon": "🔍",
                "title": "任务分解",
                "detail": detail or "规划执行步骤...",
                "color": "cyan",
            },
            "tool_selecting": {
                "icon": "⚡",
                "title": "选择工具",
                "detail": detail or "匹配最佳工具...",
                "color": "cyan",
            },
            "tool_executing": {
                "icon": "🔧",
                "title": "执行工具",
                "detail": detail,
                "color": "bright_cyan",
            },
            "tool_result": {
                "icon": "📥",
                "title": "工具结果",
                "detail": detail,
                "color": "cyan",
            },
            "synthesizing": {
                "icon": "✨",
                "title": "综合结果",
                "detail": detail or "整合信息...",
                "color": "green",
            },
            "output": {
                "icon": "💬",
                "title": "输出回复",
                "detail": detail,
                "color": "green",
            },
        }

        return display_templates.get(
            step, {"icon": "•", "title": step, "detail": detail, "color": "cyan"}
        )


# 全局单例
_gestalt_controller: Optional[GestaltController] = None


def get_gestalt_controller() -> GestaltController:
    """获取格式塔控制器单例"""
    global _gestalt_controller
    if _gestalt_controller is None:
        _gestalt_controller = GestaltController()
    return _gestalt_controller


async def initialize_gestalt(tool_subnet=None) -> GestaltController:
    """初始化格式塔控制器"""
    controller = get_gestalt_controller()
    await controller.initialize(tool_subnet)
    return controller
