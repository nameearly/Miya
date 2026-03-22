"""
知识库模块

统一整合所有的知识库功能
"""

from .knowledge_base import KnowledgeBase

__all__ = [
    "KnowledgeBase",
    "create_knowledge_base"
]

def create_knowledge_base() -> KnowledgeBase:
    """创建知识库实例"""
    return KnowledgeBase()