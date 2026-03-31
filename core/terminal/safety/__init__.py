"""
安全检查模块

统一整合所有的安全检查逻辑
"""

from .safety_checker import SafetyChecker

__all__ = [
    "SafetyChecker",
    "create_safety_checker"
]

def create_safety_checker() -> SafetyChecker:
    """创建安全检查器实例"""
    return SafetyChecker()