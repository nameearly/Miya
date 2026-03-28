# 插件基类
# Base Plugin Class

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.is_initialized = False
        self.logger = logging.getLogger(f"Plugin.{name}")
    
    async def initialize(self):
        self.is_initialized = True
        self.logger.info(f"插件 {self.name} 初始化完成")
        return True
    
    async def collect_context(self, user_id: int, context: Dict = None) -> Dict:
        return {}
    
    async def generate(self, context_data: Dict) -> str:
        return ""
    
    async def update_config(self, new_config: Dict):
        self.config = new_config
        return True
    
    async def shutdown(self):
        self.is_initialized = False
        return True
    
    def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "is_initialized": self.is_initialized,
            "config": self.config
        }
