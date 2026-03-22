"""
终端API集成模块

统一整合所有的终端API功能
"""

from .api_integration import APIIntegration
from .terminal_api_server import TerminalAPIServer

__all__ = [
    "APIIntegration",
    "TerminalAPIServer",
    "create_api_integration"
]

def create_api_integration() -> APIIntegration:
    """创建API集成实例"""
    return APIIntegration()