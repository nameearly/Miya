#!/usr/bin/env python3
"""
弥娅终端工具包 - 统一终端工具入口
"""

from core.terminal_ultra import TerminalUltra, get_terminal_ultra
from .miya_terminal import MiyaTerminalTool
from .system_info_tool import SystemInfoTool
from .ultra_terminal_tools import (
    TerminalExecTool,
    FileReadTool,
    FileEditTool,
    FileWriteTool,
    FileDeleteTool,
    FileCopyTool,
    FileMoveTool,
    DirectoryTreeTool,
    CodeExecuteTool,
    ProjectAnalyzeTool,
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
    FileGrepTool,
    FileGlobTool,
    CodeExplainTool,
    CodeSearchSymbolTool,
    ProjectContextTool,
    TaskPlanTool,
    SuggestionsTool,
    CodeExplorerAgentTool,
    CodeReviewerAgentTool,
    CodeArchitectAgentTool,
    TerminalAgentTool,
    ListSkillsTool,
)


# 兼容旧API
class TerminalTool:
    """终端工具 - 兼容旧API，包装TerminalUltra"""

    config = {"name": "terminal", "description": "弥娅终端工具"}

    def __init__(self):
        self.ultra = get_terminal_ultra()

    async def execute_command(self, command: str, timeout: int = 60):
        return await self.ultra.terminal_exec(command, timeout=timeout)

    async def read_file(self, file_path: str, offset: int = 0, limit: int = None):
        return await self.ultra.file_read(file_path, offset=offset, limit=limit)

    async def write_file(self, file_path: str, content: str):
        return await self.ultra.file_write(file_path, content)

    async def edit_file(self, file_path: str, old_string: str, new_string: str):
        return await self.ultra.file_edit(file_path, old_string, new_string)

    async def glob(self, pattern: str, path: str = "."):
        return await self.ultra.file_glob(pattern, path)

    async def grep(self, pattern: str, path: str = "."):
        return await self.ultra.file_grep(pattern, path)

    async def get_system_info(self):
        return await self.ultra.get_tools_list()


__all__ = [
    "TerminalUltra",
    "get_terminal_ultra",
    "TerminalTool",
    "MiyaTerminalTool",
    "SystemInfoTool",
    "TerminalExecTool",
    "FileReadTool",
    "FileEditTool",
    "FileWriteTool",
    "FileDeleteTool",
    "FileCopyTool",
    "FileMoveTool",
    "DirectoryTreeTool",
    "CodeExecuteTool",
    "ProjectAnalyzeTool",
    "GitStatusTool",
    "GitDiffTool",
    "GitLogTool",
    "GitBranchTool",
    "GitCommitTool",
    "GitAddTool",
    "GitPushTool",
    "GitPullTool",
    "GitCheckoutTool",
    "GitStashTool",
    "FileGrepTool",
    "FileGlobTool",
    "CodeExplainTool",
    "CodeSearchSymbolTool",
    "ProjectContextTool",
    "TaskPlanTool",
    "SuggestionsTool",
    "CodeExplorerAgentTool",
    "CodeReviewerAgentTool",
    "CodeArchitectAgentTool",
    "TerminalAgentTool",
    "ListSkillsTool",
]
