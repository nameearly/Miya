"""
弥娅终端工具模块

提供完整的终端命令执行能力：
- MiyaTerminalTool: 主终端工具（集成平台适配、安全检查）
- SystemInfoTool: 系统信息管理工具
- CommandExecutor: 命令执行器
- CommandChain: 命令链管理
- NLPParser: 自然语言解析
- PlatformAdapter: 平台适配器
"""

from .miya_terminal import (
    MiyaTerminalTool,
    get_terminal_tool,
    CommandResult,
    CommandSafetyChecker,
)
from .system_info_tool import SystemInfoTool, get_system_info_tool
from .command_executor import CommandExecutor
from .command_chain import CommandChain
from .nlp_parser import NLPParser
from .platform_adapter import (
    PlatformAdapter,
    WindowsAdapter,
    LinuxAdapter,
    MacOSAdapter,
    get_platform_adapter,
)
from .platform_detector import Platform, detect_platform
from .ultra_terminal_tools import (
    TerminalExecTool,
    FileReadTool,
    FileWriteTool,
    FileEditTool,
    FileDeleteTool,
    DirectoryTreeTool,
    CodeExecuteTool,
    ProjectAnalyzeTool,
)

TerminalTool = MiyaTerminalTool

__all__ = [
    # 主工具
    "MiyaTerminalTool",
    "get_terminal_tool",
    "TerminalTool",
    "SystemInfoTool",
    "get_system_info_tool",
    "CommandResult",
    "CommandSafetyChecker",
    # 辅助工具
    "CommandExecutor",
    "CommandChain",
    "NLPParser",
    "PlatformAdapter",
    "WindowsAdapter",
    "LinuxAdapter",
    "MacOSAdapter",
    "get_platform_adapter",
    "Platform",
    "detect_platform",
    # 超级终端工具
    "TerminalExecTool",
    "FileReadTool",
    "FileWriteTool",
    "FileEditTool",
    "FileDeleteTool",
    "DirectoryTreeTool",
    "CodeExecuteTool",
    "ProjectAnalyzeTool",
]
