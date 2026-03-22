"""
记忆系统模块 v3.0

统一的记忆存储和检索系统
"""

# 统一记忆系统（核心）
from .unified_memory import (
    UnifiedMemoryManager,
    get_unified_memory,
    MemoryType,
    MemoryPriority,
    MemoryItem,
    EmbeddingService,
    HistorianRewriter,
)

# 适配器
from .unified_memory_adapter import (
    UnifiedMemoryAdapter,
    create_memory_adapter,
)

# 兼容旧接口（使用新系统作为后端）
from .undefined_memory import (
    UndefinedMemoryAdapter,
    get_undefined_memory_adapter,
)

__all__ = [
    # 核心系统
    "UnifiedMemoryManager",
    "get_unified_memory",
    "MemoryType",
    "MemoryPriority",
    "MemoryItem",
    "EmbeddingService",
    "HistorianRewriter",
    # 适配器
    "UnifiedMemoryAdapter",
    "create_memory_adapter",
    # 兼容旧接口
    "UndefinedMemoryAdapter",
    "get_undefined_memory_adapter",
]
