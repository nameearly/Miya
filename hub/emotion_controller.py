"""
情绪控制器 (Emotion Controller)

职责：
1. 情绪状态更新（基于用户输入）
2. 情绪染色（影响AI响应）
3. 情绪衰减机制
"""
import logging
from typing import Dict, Any


logger = logging.getLogger(__name__)


class EmotionController:
    """
    情绪控制器
    
    单一职责：处理所有与情绪相关的逻辑
    """

    def __init__(self, emotion_instance: Any):
        """
        初始化情绪控制器
        
        Args:
            emotion_instance: 情绪系统实例
        """
        self.emotion = emotion_instance
        logger.info("[情绪控制器] 初始化完成")

    def update_from_input(self, content: str) -> None:
        """
        从用户输入中检测情绪并更新情绪状态
        
        Args:
            content: 用户输入内容
        """
        positive_keywords = ['开心', '高兴', '快乐', '喜欢', '爱', 'happy', 'love', 'joy']
        negative_keywords = ['难过', '伤心', '悲伤', '生气', '讨厌', 'sad', 'angry', 'hate']
        surprise_keywords = ['惊讶', '意外', 'wow', '天哪']
        fear_keywords = ['害怕', '恐惧', 'scared', 'afraid']

        if any(keyword in content for keyword in positive_keywords):
            self.emotion.apply_coloring('joy', 0.3)
        elif any(keyword in content for keyword in negative_keywords):
            self.emotion.apply_coloring('sadness', 0.4)
        elif any(keyword in content for keyword in surprise_keywords):
            self.emotion.apply_coloring('surprise', 0.3)
        elif any(keyword in content for keyword in fear_keywords):
            self.emotion.apply_coloring('fear', 0.2)

    def influence_response(self, response: str) -> str:
        """
        对响应进行情绪染色
        
        Args:
            response: 原始响应
            
        Returns:
            染色后的响应
        """
        return self.emotion.influence_response(response)

    def decay_coloring(self) -> None:
        """
        执行情绪衰减
        """
        self.emotion.decay_coloring()

    def get_emotion_state(self) -> Dict:
        """
        获取当前情绪状态
        
        Returns:
            情绪状态字典
        """
        return self.emotion.get_emotion_state()

    def apply_coloring(self, emotion_type: str, intensity: float) -> None:
        """
        应用情绪染色
        
        Args:
            emotion_type: 情绪类型
            intensity: 强度
        """
        self.emotion.apply_coloring(emotion_type, intensity)
