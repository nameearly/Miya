"""
配置加载
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv


class Settings:
    """配置管理类"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self._config = {}
        self._load_env()

    def _load_env(self) -> None:
        """加载环境变量"""
        # 加载.env文件
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)

        # 基础配置
        self._config = {
            # 应用配置
            "app": {
                "name": "Miya",
                "version": "1.0.0",
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
            },
            # Redis配置
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
                "db": int(os.getenv("REDIS_DB", 0)),
                "password": os.getenv("REDIS_PASSWORD"),
            },
            # Milvus配置
            "milvus": {
                "host": os.getenv("MILVUS_HOST", "localhost"),
                "port": int(os.getenv("MILVUS_PORT", 19530)),
                "collection_name": os.getenv("MILVUS_COLLECTION", "miya_memory"),
            },
            # Neo4j配置
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD"),
            },
            # 人格配置
            "personality": {
                "warmth": float(os.getenv("PERSONALITY_WARMTH", 0.8)),
                "logic": float(os.getenv("PERSONALITY_LOGIC", 0.7)),
                "creativity": float(os.getenv("PERSONALITY_CREATIVITY", 0.6)),
                "empathy": float(os.getenv("PERSONALITY_EMPATHY", 0.75)),
                "resilience": float(os.getenv("PERSONALITY_RESILIENCE", 0.7)),
            },
            # 情绪配置
            "emotion": {
                "decay_rate": float(os.getenv("EMOTION_DECAY_RATE", 0.1)),
                "coloring_threshold": float(
                    os.getenv("EMOTION_COLORING_THRESHOLD", 0.7)
                ),
            },
            # 信任配置
            "trust": {
                "decay_rate": float(os.getenv("TRUST_DECAY_RATE", 0.05)),
                "initial_score": float(os.getenv("TRUST_INITIAL_SCORE", 0.5)),
                "high_threshold": float(os.getenv("TRUST_HIGH_THRESHOLD", 0.7)),
                "low_threshold": float(os.getenv("TRUST_LOW_THRESHOLD", 0.3)),
            },
            # 记忆配置
            "memory": {
                "tide_ttl": int(os.getenv("MEMORY_TIDE_TTL", 3600)),
                "dream_compression_threshold": int(
                    os.getenv("MEMORY_DREAM_THRESHOLD", 100)
                ),
            },
            # 感知配置
            "perception": {
                "activation_rate": float(os.getenv("PERCEPTION_ACTIVATION_RATE", 0.3)),
                "intensity_threshold": float(
                    os.getenv("PERCEPTION_INTENSITY_THRESHOLD", 0.5)
                ),
            },
            # 检测配置
            "detection": {
                "time_loop_threshold": int(os.getenv("DETECTION_TIME_THRESHOLD", 3600)),
                "space_distance_threshold": float(
                    os.getenv("DETECTION_SPACE_THRESHOLD", 1.0)
                ),
            },
            # 演化配置
            "evolution": {
                "sandbox_enabled": os.getenv("SANDBOX_ENABLED", "true").lower()
                == "true",
                "ab_test_enabled": os.getenv("AB_TEST_ENABLED", "true").lower()
                == "true",
            },
            # 对话上下文配置
            "conversation": {
                "enable_conversation_context": os.getenv(
                    "CONVERSATION_CONTEXT_ENABLED", "true"
                ).lower()
                == "true",
                "context_max_count": int(
                    os.getenv("CONVERSATION_CONTEXT_MAX_COUNT", "10")
                ),
                "context_max_tokens": int(
                    os.getenv("CONVERSATION_CONTEXT_MAX_TOKENS", "2000")
                ),
                "response_thresholds": {
                    "high_empathy": float(
                        os.getenv("RESPONSE_THRESHOLD_HIGH_EMPATHY", "0.8")
                    ),
                    "high_warmth": float(
                        os.getenv("RESPONSE_THRESHOLD_HIGH_WARMTH", "0.8")
                    ),
                },
            },
            # 聊天机器人关键词配置
            "chatbot_keywords": {
                "auto_respond_keywords": os.getenv(
                    "CHATBOT_AUTO_RESPOND_KEYWORDS",
                    "弥娅,miya,Miya,亲爱的,亲爱,老婆,老公,宝贝,贝贝,小可爱,小宝贝,小姐姐,小哥哥",
                ).split(","),
                "pat_pat_trigger": os.getenv("CHATBOT_PAT_PAT_TRIGGER", "拍了拍你"),
            },
            # 终端任务关键词配置
            "terminal_task_keywords": {
                "think_keywords": os.getenv(
                    "TERMINAL_TASK_THINK_KEYWORDS",
                    "打开,运行,执行,创建,删除,查看,启动,安装,卸载,配置,帮我,请,能不能",
                ).split(","),
            },
            # QQ机器人配置
            "qq": self._get_qq_config(),
            # LifeBook 记忆管理配置
            "lifebook": {
                "enabled": os.getenv("LIFEBOOK_ENABLED", "true").lower() == "true",
                "base_dir": os.getenv("LIFEBOOK_BASE_DIR", "data/lifebook"),
                "auto_summary_enabled": os.getenv(
                    "LIFEBOOK_AUTO_SUMMARY", "false"
                ).lower()
                == "true",
                "default_months_back": int(
                    os.getenv("LIFEBOOK_DEFAULT_MONTHS_BACK", 1)
                ),
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键，如 'redis.host'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def reload(self) -> None:
        """重新加载配置"""
        self._load_env()

    def get_all(self) -> Dict:
        """获取所有配置"""
        return self._config.copy()

    def update_from_dict(self, config_dict: Dict) -> None:
        """从字典更新配置"""
        for key, value in config_dict.items():
            self.set(key, value)

    def _get_qq_config(self) -> Dict:
        """获取QQ混合配置

        设计原则：
        1. 敏感配置从.env文件加载（连接信息、API密钥等）
        2. 如果存在qq_config.yaml，则加载详细功能配置
        3. 提供统一的配置结构
        """
        try:
            # 基础敏感配置从.env加载
            base_config = {
                # 基础连接配置
                "onebot_ws_url": os.getenv("QQ_ONEBOT_WS_URL", "ws://localhost:3001"),
                "onebot_token": os.getenv("QQ_ONEBOT_TOKEN", ""),
                "bot_qq": int(os.getenv("QQ_BOT_QQ", 0) or 0),
                "superadmin_qq": int(os.getenv("QQ_SUPERADMIN_QQ", 0) or 0),
                "group_whitelist": os.getenv("QQ_GROUP_WHITELIST", ""),
                "group_blacklist": os.getenv("QQ_GROUP_BLACKLIST", ""),
                "user_whitelist": os.getenv("QQ_USER_WHITELIST", ""),
                "user_blacklist": os.getenv("QQ_USER_BLACKLIST", ""),
                # 连接设置
                "reconnect_interval": float(os.getenv("QQ_RECONNECT_INTERVAL", "5.0")),
                "ping_interval": int(os.getenv("QQ_PING_INTERVAL", "20")),
                "ping_timeout": int(os.getenv("QQ_PING_TIMEOUT", "30")),
                "max_message_size": int(os.getenv("QQ_MAX_MESSAGE_SIZE", "104857600")),
                # 基础功能开关
                "ocr_enabled": os.getenv("QQ_OCR_ENABLED", "true").lower() == "true",
                "ocr_engine": os.getenv("QQ_OCR_ENGINE", "auto"),
                "active_chat_enabled": os.getenv(
                    "QQ_ACTIVE_CHAT_ENABLED", "true"
                ).lower()
                == "true",
                "task_scheduler_enabled": os.getenv(
                    "QQ_TASK_SCHEDULER_ENABLED", "true"
                ).lower()
                == "true",
            }

            # 尝试加载YAML详细配置
            yaml_config = self._load_qq_yaml_config()

            if yaml_config:
                # 合并配置：YAML详细配置 + .env基础配置
                merged_config = self._merge_qq_configs(base_config, yaml_config)
                return merged_config
            else:
                # 只有.env配置，创建简化配置结构
                return self._create_simple_qq_config(base_config)

        except Exception as e:
            print(f"[Settings] 加载QQ配置失败: {e}")
            return self._get_default_qq_config()

    def _load_qq_yaml_config(self) -> Dict:
        """加载QQ YAML配置"""
        try:
            import yaml

            yaml_paths = [
                "config/qq_config.yaml",
                "qq_config.yaml",
                "./config/qq_config.yaml",
                "./qq_config.yaml",
            ]

            for yaml_path in yaml_paths:
                if os.path.exists(yaml_path):
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f) or {}
                        if "qq" in config:
                            return config["qq"]
                    break

            return {}

        except Exception as e:
            print(f"[Settings] 加载YAML配置失败: {e}")
            return {}

    def _merge_qq_configs(self, base_config: Dict, yaml_config: Dict) -> Dict:
        """合并QQ配置"""
        merged = {
            # 1. 基础配置优先使用.env的值
            "onebot_ws_url": base_config.get("onebot_ws_url"),
            "onebot_token": base_config.get("onebot_token"),
            "bot_qq": base_config.get("bot_qq"),
            "superadmin_qq": base_config.get("superadmin_qq"),
            # 2. 连接设置
            "connection": {
                "reconnect_interval": base_config.get("reconnect_interval"),
                "ping_interval": base_config.get("ping_interval"),
                "ping_timeout": base_config.get("ping_timeout"),
                "max_message_size": base_config.get("max_message_size"),
            },
            # 3. 访问控制（从.env解析）
            "access_control": {
                "group_whitelist": self._parse_qq_list(
                    base_config.get("group_whitelist", "")
                ),
                "group_blacklist": self._parse_qq_list(
                    base_config.get("group_blacklist", "")
                ),
                "user_whitelist": self._parse_qq_list(
                    base_config.get("user_whitelist", "")
                ),
                "user_blacklist": self._parse_qq_list(
                    base_config.get("user_blacklist", "")
                ),
                "enabled": False,  # 默认禁用，除非配置了列表
            },
        }

        # 4. 添加YAML中的详细配置
        for section in [
            "multimedia",
            "image_recognition",
            "active_chat",
            "task_scheduler",
            "performance",
            "logging",
            "debug",
        ]:
            if section in yaml_config:
                merged[section] = yaml_config[section]

        # 5. 覆盖YAML中的基础开关
        if "image_recognition" in merged:
            merged["image_recognition"].setdefault("ocr", {})
            merged["image_recognition"]["ocr"]["enabled"] = base_config.get(
                "ocr_enabled", True
            )
            merged["image_recognition"]["ocr"]["engine"] = base_config.get(
                "ocr_engine", "auto"
            )

        if "active_chat" in merged:
            merged["active_chat"]["enabled"] = base_config.get(
                "active_chat_enabled", True
            )

        if "task_scheduler" in merged:
            merged["task_scheduler"]["enabled"] = base_config.get(
                "task_scheduler_enabled", True
            )

        return merged

    def _create_simple_qq_config(self, base_config: Dict) -> Dict:
        """创建简化QQ配置（只有.env时）"""
        return {
            "onebot_ws_url": base_config.get("onebot_ws_url"),
            "onebot_token": base_config.get("onebot_token"),
            "bot_qq": base_config.get("bot_qq"),
            "superadmin_qq": base_config.get("superadmin_qq"),
            "connection": {
                "reconnect_interval": base_config.get("reconnect_interval"),
                "ping_interval": base_config.get("ping_interval"),
                "ping_timeout": base_config.get("ping_timeout"),
                "max_message_size": base_config.get("max_message_size"),
            },
            "access_control": {
                "group_whitelist": self._parse_qq_list(
                    base_config.get("group_whitelist", "")
                ),
                "group_blacklist": self._parse_qq_list(
                    base_config.get("group_blacklist", "")
                ),
                "user_whitelist": self._parse_qq_list(
                    base_config.get("user_whitelist", "")
                ),
                "user_blacklist": self._parse_qq_list(
                    base_config.get("user_blacklist", "")
                ),
                "enabled": False,
            },
            "multimedia": {
                "image": {
                    "max_size": int(os.getenv("QQ_IMAGE_MAX_SIZE", "10485760")),
                    "allowed_formats": os.getenv(
                        "QQ_IMAGE_ALLOWED_FORMATS", ".jpg,.jpeg,.png,.gif,.bmp,.webp"
                    ).split(","),
                },
                "file": {
                    "max_size": int(os.getenv("QQ_FILE_MAX_SIZE", "52428800")),
                },
            },
            "image_recognition": {
                "ocr": {
                    "enabled": base_config.get("ocr_enabled", True),
                    "engine": base_config.get("ocr_engine", "auto"),
                }
            },
            "active_chat": {
                "enabled": base_config.get("active_chat_enabled", True),
                "limits": {
                    "max_daily_messages": int(os.getenv("QQ_MAX_DAILY_MESSAGES", "10")),
                    "min_interval": int(os.getenv("QQ_MIN_INTERVAL", "300")),
                },
            },
            "task_scheduler": {
                "enabled": base_config.get("task_scheduler_enabled", True),
            },
        }

    def _parse_qq_list(self, list_str: str) -> list:
        """解析逗号分隔的QQ列表"""
        if not list_str:
            return []

        try:
            return [int(qq.strip()) for qq in list_str.split(",") if qq.strip()]
        except ValueError:
            return []

    def _get_default_qq_config(self) -> Dict:
        """获取默认QQ配置"""
        return {
            "onebot_ws_url": "ws://localhost:3001",
            "onebot_token": "",
            "bot_qq": 0,
            "superadmin_qq": 0,
            "connection": {
                "reconnect_interval": 5.0,
                "ping_interval": 20,
                "ping_timeout": 30,
                "max_message_size": 104857600,
            },
            "access_control": {
                "enabled": False,
                "group_whitelist": [],
                "group_blacklist": [],
                "user_whitelist": [],
                "user_blacklist": [],
            },
            "multimedia": {
                "image": {
                    "max_size": 10485760,
                    "allowed_formats": [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ],
                },
                "file": {
                    "max_size": 52428800,
                },
            },
            "image_recognition": {
                "ocr": {
                    "enabled": True,
                    "engine": "auto",
                }
            },
            "active_chat": {
                "enabled": True,
                "limits": {
                    "max_daily_messages": 10,
                    "min_interval": 300,
                },
            },
            "task_scheduler": {
                "enabled": True,
            },
        }
