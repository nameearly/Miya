"[DEPRECATED] GPT-SoVITS TTS引擎"
"调用本地GPT-SoVITS服务进行语音合成"
""
"此模块已迁移到 core.tts模块，此处仅作向后兼容。"
"推荐导入方式: from core.tts import GPTSoviTSEngine, filter_text, split_text_for_qq"
""
import warnings

# 向后兼容性导入
from core.tts.providers import GPTSoviTSEngine
from core.tts.utils import filter_text, split_text_for_qq

warnings.warn(
    "Importing from core.gpt_sovits is deprecated. "
    "Use 'from core.tts import GPTSoviTSEngine, filter_text, split_text_for_qq' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['GPTSoviTSEngine', 'filter_text', 'split_text_for_qq']
