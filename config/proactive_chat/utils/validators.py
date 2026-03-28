# 消息验证器
# Message Validator

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class MessageValidator:
    def __init__(self):
        self.max_length = 100
        self.min_length = 2
        self.sensitive_words = []  # 敏感词列表
    
    def validate(self, message: str) -> bool:
        if not message:
            return False
        
        # 检查长度
        if len(message) < self.min_length or len(message) > self.max_length:
            logger.warning(f"消息长度不符合要求: {len(message)}")
            return False
        
        # 检查敏感词
        for word in self.sensitive_words:
            if word in message:
                logger.warning(f"消息包含敏感词: {word}")
                return False
        
        return True
    
    def update_config(self, config: Dict):
        self.max_length = config.get("max_length", self.max_length)
        self.min_length = config.get("min_length", self.min_length)
        self.sensitive_words = config.get("sensitive_words", self.sensitive_words)
