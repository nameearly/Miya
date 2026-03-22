"""
[DEPRECATED] TTS注册管理器
管理多个TTS引擎的注册、切换和调用

此模块已迁移到 core.tts.manager，此处仅作向后兼容。
推荐导入方式: from core.tts import TTSRegistry, get_tts_registry
"""
import warnings

# 向后兼容性导入
from core.tts.manager import TTSRegistry, get_tts_registry
from core.tts.base import TTSEngine

warnings.warn(
    "Importing from core.tts_registry is deprecated. "
    "Use 'from core.tts import TTSRegistry, get_tts_registry' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['TTSRegistry', 'get_tts_registry', 'TTSEngine']
