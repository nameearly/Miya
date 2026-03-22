"""
弥娅终端系统 - 统一架构

分层架构设计：
1. base - 基础接口和类型定义
2. parser - 命令解析和意图理解
3. safety - 安全检查和风险评估
4. executor - 命令执行和监控
5. knowledge - 知识库和上下文管理
6. integration - 集成层和高级接口
"""

__version__ = "1.0.0"
__author__ = "Miya AI System"

# 导出主要接口
from .base.types import *
from .base.interfaces import *

# 创建简洁的导入别名
__all__ = [
    # 类型
    "CommandIntent",
    "CommandCategory",
    "ExecutionMode",
    "TerminalStatus",
    "CommandResult",
    
    # 接口
    "ICommandParser",
    "ISafetyChecker",
    "IExecutor",
    "ITerminalController",
    
    # 主要类
    "TerminalMaster"
]