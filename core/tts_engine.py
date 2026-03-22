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
    stacklevel=2
)

__all__ = ['TTSEngine']

    @abstractmethod
    def get_voice_list(self) -> list:
        """
        获取可用音色列表

        Returns:
            list: 音色列表
        """
        pass

    def set_voice(self, voice_id: str):
        """
        设置音色

        Args:
            voice_id: 音色ID
        """
        raise NotImplementedError(f"{self.engine_name} engine does not support voice selection")

    def set_speed(self, speed: float):
        """
        设置语速

        Args:
            speed: 语速倍率 (0.5-2.0)
        """
        raise NotImplementedError(f"{self.engine_name} engine does not support speed adjustment")

    def set_volume(self, volume: float):
        """
        设置音量

        Args:
            volume: 音量 (0.0-1.0)
        """
        raise NotImplementedError(f"{self.engine_name} engine does not support volume adjustment")

    def cleanup(self):
        """清理资源"""
        self.is_initialized = False

    def __repr__(self):
        return f"<TTSEngine: {self.engine_name}>"
