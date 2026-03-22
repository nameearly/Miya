"[NOTICE] TTSNet - TTS子网"
"此模块的实现已迁移到 core.tts.subnet"
"保持此文件以进行向后兼容性，推荐直接导入: from core.tts import TTSNet"
""
import warnings

# 向后兼容性导入重定向
from core.tts.subnet import TTSNet

warnings.warn(
    "Importing TTSNet from webnet.tts is deprecated. "
    "Use 'from core.tts import TTSNet' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['TTSNet']
