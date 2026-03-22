"""
终端系统基础模块

包含所有共享的数据类型、枚举和接口定义
"""

from .types import *
from .interfaces import *
from .exceptions import *

__all__ = [
    # 类型和枚举
    "CommandIntent",
    "CommandCategory", 
    "ExecutionMode",
    "TerminalStatus",
    "CommandComplexity",
    "RiskLevel",
    
    # 数据结构
    "CommandAnalysis",
    "CommandResult",
    "ExecutionContext",
    "ProcessInfo",
    
    # 接口
    "ICommandParser",
    "ISafetyChecker", 
    "IExecutor",
    "IContextManager",
    "IMonitor",
    
    # 异常
    "CommandExecutionError",
    "SafetyViolationError",
    "TerminalConnectionError",
    "InvalidCommandError"
]