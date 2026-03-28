# 配置加载器
# Config Loader

import logging
import asyncio
import yaml
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class ProactiveChatConfigLoader:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "D:/AI_MIYA_Facyory/MIYA/Miya/config/personalities/_base.yaml"
        self.config: Dict = {}
        self.proactive_chat_config: Dict = {}
        self.is_loaded = False
        
    async def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                full_config = yaml.safe_load(f)
            
            self.proactive_chat_config = full_config.get("proactive_chat", {})
            self.is_loaded = True
            logger.info("配置加载成功")
            return True
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return False
    
    async def reload_config(self):
        return await self.load_config()
    
    def get_plugin_config(self, plugin_name: str) -> Dict:
        return self.proactive_chat_config.get(plugin_name, {})
    
    def get_stats(self) -> Dict:
        return {
            "is_loaded": self.is_loaded,
            "config_path": self.config_path,
            "has_proactive_chat": bool(self.proactive_chat_config)
        }
