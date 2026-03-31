"""
命令解析模块

统一整合ai_terminal_system.py和intelligent_executor.py的命令解析功能
"""

from .command_parser import CommandParser
from .intent_analyzer import IntentAnalyzer
from .command_normalizer import CommandNormalizer

__all__ = [
    "CommandParser",
    "IntentAnalyzer", 
    "CommandNormalizer",
    "create_command_parser"
]

def create_command_parser() -> CommandParser:
    """创建命令解析器实例"""
    return CommandParser()