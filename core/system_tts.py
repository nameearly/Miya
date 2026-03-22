"[DEPRECATED] 系统TTS引擎"
"调用Windows/macOS/Linux的系统TTS功能"
""
"此模块已迁移到 core.tts.providers，此处仅作向后兼容。"
"推荐导入方式: from core.tts import SystemTTSEngine"
""
import warnings

# 向后兼容性导入
from core.tts.providers import SystemTTSEngine

warnings.warn(
    "Importing from core.system_tts is deprecated. "
    "Use 'from core.tts import SystemTTSEngine' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['SystemTTSEngine']
