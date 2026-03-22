"[DEPRECATED] 通用API TTS引擎"
"支持调用第三方TTS API服务(如Azure TTS, 百度语音, 阿里云TTS等)"
""
"此模块已迁移到 core.tts.providers，此处仅作向后兼容。"
"推荐导入方式: from core.tts import APITTSEngine"
""
import warnings

# 向后兼容性导入
from core.tts.providers import APITTSEngine

warnings.warn(
    "Importing from core.api_tts is deprecated. "
    "Use 'from core.tts import APITTSEngine' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['APITTSEngine']
