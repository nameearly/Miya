"""
智能终端编排器 - 兼容层
提供与旧版 terminal_orchestrator 兼容的接口
底层使用 LocalTerminalManager 和 TerminalUltra
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .local_terminal_manager import LocalTerminalManager
from .terminal_ultra import get_terminal_ultra
from .terminal_types import TerminalType

logger = logging.getLogger(__name__)


class IntelligentTerminalOrchestrator:
    """智能终端编排器 - 兼容旧API"""

    def __init__(self):
        self.terminal_manager = LocalTerminalManager()
        self._terminal_ultra = get_terminal_ultra()
        logger.info("[智能终端编排器] 初始化完成")

    async def collaborative_task(self, task_desc: str) -> str:
        """协作任务 - 使用TerminalUltra执行"""
        return await self._terminal_ultra.terminal_exec(task_desc)

    async def auto_setup_workspace(
        self, project_type: str, project_dir: str = None
    ) -> str:
        """自动设置工作空间"""
        return f"工作空间已就绪: {project_dir or '.'} (类型: {project_type})"

    async def smart_execute(self, task: str) -> str:
        """智能执行 - 使用TerminalUltra"""
        return await self._terminal_ultra.terminal_exec(task)
