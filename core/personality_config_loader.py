"""
人格配置加载器
集中管理人格向量、阈值、权重等配置
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

_config: Optional[Dict[str, Any]] = None


def _load_config() -> Dict[str, Any]:
    """加载人格配置"""
    global _config

    if _config is not None:
        return _config

    config_path = Path(__file__).parent.parent / "config" / "personality_config.json"

    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                _config = json.load(f)
            logger.info("人格配置加载成功")
        else:
            logger.warning(f"人格配置文件不存在: {config_path}")
            _config = _get_default_config()
    except Exception as e:
        logger.warning(f"加载人格配置失败: {e}，使用默认配置")
        _config = _get_default_config()

    return _config


def _get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "thresholds": {
            "high_empathy": 0.8,
            "high_warmth": 0.8,
            "high_resilience": 0.8,
            "high_logic": 0.7,
            "high_creativity": 0.7,
            "very_high": 0.9,
            "very_low": 0.2,
            "low": 0.3,
            "medium": 0.5,
        },
        "response_thresholds": {
            "greeting_empathy": 0.8,
            "greeting_warmth": 0.8,
            "deep_conversation_empathy": 0.85,
            "help_warmth": 0.85,
            "comforting_warmth": 0.7,
        },
        "trait_weights": {
            "casual_chat": {
                "warmth": 0.4,
                "empathy": 0.3,
                "creativity": 0.2,
                "logic": 0.1,
            },
            "deep_conversation": {
                "empathy": 0.4,
                "warmth": 0.3,
                "resilience": 0.2,
                "logic": 0.1,
            },
            "creative_task": {
                "creativity": 0.5,
                "logic": 0.2,
                "warmth": 0.2,
                "empathy": 0.1,
            },
            "analytical_task": {
                "logic": 0.5,
                "creativity": 0.2,
                "resilience": 0.2,
                "empathy": 0.1,
            },
            "comforting": {"warmth": 0.5, "empathy": 0.4, "resilience": 0.1},
        },
        "learning_rates": {
            "positive_interaction": {
                "warmth": 0.02,
                "empathy": 0.01,
                "resilience": 0.01,
            },
            "negative_interaction": {
                "warmth": -0.02,
                "empathy": 0.01,
                "resilience": -0.01,
            },
            "creative_task": {"creativity": 0.02, "logic": 0.01, "warmth": -0.01},
            "analytical_task": {"logic": 0.02, "creativity": 0.01, "warmth": -0.01},
            "crisis_situation": {"resilience": 0.02, "empathy": 0.01, "warmth": 0.01},
        },
        "fallback_values": {
            "warmth": 0.5,
            "empathy": 0.5,
            "resilience": 0.5,
            "logic": 0.5,
            "creativity": 0.5,
        },
    }


def reload_config():
    """重新加载配置"""
    global _config
    _config = None
    return _load_config()


def get_threshold(key: str, default: float = 0.5) -> float:
    """获取阈值"""
    config = _load_config()
    return config.get("thresholds", {}).get(key, default)


def get_response_threshold(key: str, default: float = 0.5) -> float:
    """获取响应阈值"""
    config = _load_config()
    return config.get("response_thresholds", {}).get(key, default)


def get_trait_weights(scene: str = "casual_chat") -> Dict[str, float]:
    """获取特质权重"""
    config = _load_config()
    return config.get("trait_weights", {}).get(scene, config.get("fallback_values", {}))


def get_learning_rates(
    interaction_type: str = "positive_interaction",
) -> Dict[str, float]:
    """获取学习率"""
    config = _load_config()
    return config.get("learning_rates", {}).get(interaction_type, {})


def get_fallback_value(trait: str) -> float:
    """获取回退值"""
    config = _load_config()
    return config.get("fallback_values", {}).get(trait, 0.5)


def get_personality_vector(trait: str, profile: Dict) -> float:
    """获取人格向量值，带回退"""
    if not profile:
        return get_fallback_value(trait)

    vectors = profile.get("vectors", {})
    return vectors.get(trait, get_fallback_value(trait))


def is_high_trait(trait: str, value: float) -> bool:
    """检查是否是高特质"""
    return value >= get_threshold(f"high_{trait}", 0.8)


class PersonalityConfig:
    """人格配置类"""

    def __init__(self):
        self._config = _load_config()

    def get_threshold(self, key: str, default: float = 0.5) -> float:
        return get_threshold(key, default)

    def get_response_threshold(self, key: str, default: float = 0.5) -> float:
        return get_response_threshold(key, default)

    def get_weights(self, scene: str) -> Dict[str, float]:
        return get_trait_weights(scene)

    def get_learning_rates(self, interaction_type: str) -> Dict[str, float]:
        return get_learning_rates(interaction_type)

    def get_fallback(self, trait: str) -> float:
        return get_fallback_value(trait)


_personality_config: Optional[PersonalityConfig] = None


def get_personality_config() -> PersonalityConfig:
    """获取人格配置实例"""
    global _personality_config
    if _personality_config is None:
        _personality_config = PersonalityConfig()
    return _personality_config
