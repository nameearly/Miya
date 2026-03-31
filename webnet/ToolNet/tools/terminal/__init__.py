#!/usr/bin/env python3
"""
弥娅终端工具 - 兼容旧API
"""

from core.terminal_ultra import TerminalUltra, get_terminal_ultra


class TerminalTool:
    """终端工具 - 兼容旧API"""

    config = {"name": "terminal", "description": "弥娅终端工具"}

    def __init__(self):
        self.ultra = get_terminal_ultra()

    async def execute_command(self, command: str, timeout: int = 60):
        """执行命令"""
        return await self.ultra.terminal_exec(command, timeout=timeout)

    async def read_file(self, file_path: str, offset: int = 0, limit: int = None):
        """读取文件"""
        return await self.ultra.file_read(file_path, offset=offset, limit=limit)

    async def write_file(self, file_path: str, content: str):
        """写入文件"""
        return await self.ultra.file_write(file_path, content)

    async def edit_file(self, file_path: str, old_string: str, new_string: str):
        """编辑文件"""
        return await self.ultra.file_edit(file_path, old_string, new_string)

    async def glob(self, pattern: str, path: str = "."):
        """查找文件"""
        return await self.ultra.file_glob(pattern, path)

    async def grep(self, pattern: str, path: str = "."):
        """搜索内容"""
        return await self.ultra.file_grep(pattern, path)

    async def get_system_info(self):
        """获取系统信息"""
        return await self.ultra.get_tools_list()


__all__ = ["TerminalTool", "get_terminal_ultra"]
