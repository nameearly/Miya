"""
[DEPRECATED] TTS引擎抽象基类
定义所有TTS引擎必须实现的接口

此模块已迁移到 core.tts.base，此处仅作向后兼容。
推荐导入方式: from core.tts import TTSEngine
"""

import warnings

# 向后兼容性导入
from core.tts.base import TTSEngine

warnings.warn(
    "Importing from core.tts_engine is deprecated. "
    "Use 'from core.tts import TTSEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TTSEngine"]
