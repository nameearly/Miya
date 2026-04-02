#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弥娅统一模型池管理器

设计目标:
1. 所有端共享同一个模型池 (QQ、终端、Web等)
2. 支持文本和视觉模型
3. 统一的API密钥管理
4. 智能模型选择和路由
5. 预算控制和监控
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

from core.system_config import get_api_url

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """模型类型枚举"""

    TEXT = "text"
    VISION = "vision"
    OCR = "ocr"
    MULTIMODAL = "multimodal"
    SAFETY = "safety"
    LOCAL = "local"


class ModelProvider(str, Enum):
    """模型提供商枚举"""

    OPENAI = "openai"
    LOCAL = "local"
    AZURE = "azure"
    DEEPSEEK = "deepseek"
    SILICONFLOW = "siliconflow"
    ZHIPU = "zhipu"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """模型配置数据类"""

    id: str
    name: str
    type: ModelType
    provider: ModelProvider
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: str = ""
    capabilities: List[str] = field(default_factory=list)

    # 成本配置
    cost_per_1k_tokens: Optional[Dict[str, float]] = None

    # 性能配置
    latency: str = "medium"  # fast, medium, slow
    quality: str = "good"  # excellent, good, fair
    max_tokens: int = 4096

    # 视觉特定配置
    max_image_size: Optional[str] = None
    supported_formats: List[str] = field(default_factory=list)

    # OCR特定配置
    languages: List[str] = field(default_factory=list)
    use_gpu: bool = False
    timeout_seconds: int = 30

    # 本地模型配置
    model_path: Optional[str] = None


@dataclass
class ModelRoute:
    """模型路由配置"""

    task_type: str
    primary: str
    secondary: str
    fallback: str
    cost_priority: float = 1.0
    speed_priority: float = 1.0
    quality_priority: float = 1.0


@dataclass
class EndpointConfig:
    """端特定配置"""

    endpoint_id: str
    enabled_models: List[str]
    default_models: Dict[str, str]


class ModelPool:
    """统一模型池管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 加载环境变量
        load_dotenv()

        self._project_root = Path(__file__).parent.parent
        self._config = {}
        self._models: Dict[str, ModelConfig] = {}
        self._routes: Dict[str, ModelRoute] = {}
        self._endpoints: Dict[str, EndpointConfig] = {}
        self._initialized = False

        self._load_config()
        self._initialized = True

    def _load_config(self):
        """加载模型配置 - 优先从JSON文件加载"""
        try:
            # 从 multi_model_config.json 加载模型配置
            json_config = self._load_json_config()
            if json_config:
                self._config = json_config
                self._parse_json_config(json_config)
                logger.info("[ModelPool] 从multi_model_config.json加载模型配置")
                return

            # 没有JSON则使用默认配置
            self._set_default_config()
            logger.info("[ModelPool] 使用默认模型配置")

        except Exception as e:
            logger.error(f"[ModelPool] 加载配置失败: {e}")
            self._set_default_config()

    def _load_json_config(self) -> Optional[Dict]:
        """加载JSON配置"""
        try:
            json_path = self._project_root / "config" / "multi_model_config.json"
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"[ModelPool] 从 {json_path} 加载JSON配置")
                return config
            return None
        except Exception as e:
            logger.error(f"[ModelPool] 加载JSON配置失败: {e}")
            return None

    def _parse_json_config(self, config: Dict):
        """解析JSON配置"""
        try:
            if "models" in config:
                for model_id, model_data in config["models"].items():
                    # 优先使用配置的type字段
                    type_str = model_data.get("type", "")
                    if type_str == "vision":
                        model_type = ModelType.VISION
                    elif type_str == "ocr":
                        model_type = ModelType.OCR
                    elif type_str == "safety":
                        model_type = ModelType.SAFETY
                    elif type_str == "local":
                        model_type = ModelType.LOCAL
                    else:
                        # 从capabilities推断类型
                        capabilities = model_data.get("capabilities", [])
                        if (
                            "image_description" in capabilities
                            or "vision_understanding" in capabilities
                        ):
                            model_type = ModelType.VISION
                        elif (
                            "text_extraction" in capabilities
                            or "chinese_ocr" in capabilities
                        ):
                            model_type = ModelType.OCR
                        elif (
                            "content_safety" in capabilities
                            or "nsfw_detection" in capabilities
                        ):
                            model_type = ModelType.SAFETY
                        else:
                            model_type = ModelType.TEXT

                    # 确定提供商
                    provider_name = model_data.get("provider", "openai")
                    provider_map = {
                        "openai": ModelProvider.OPENAI,
                        "siliconflow": ModelProvider.SILICONFLOW,
                        "zhipu": ModelProvider.ZHIPU,
                        "deepseek": ModelProvider.DEEPSEEK,
                    }
                    provider = provider_map.get(provider_name, ModelProvider.OPENAI)

                    model_config = ModelConfig(
                        id=model_id,
                        name=model_data.get("name", model_id),
                        type=model_type,
                        provider=provider,
                        base_url=model_data.get("base_url", ""),
                        api_key=model_data.get("api_key", ""),
                        description=model_data.get("description", ""),
                        capabilities=capabilities,
                        cost_per_1k_tokens=model_data.get("cost_per_1k_tokens"),
                        latency=model_data.get("latency", "medium"),
                        quality=model_data.get("quality", "good"),
                    )
                    self._models[model_id] = model_config

            logger.info(f"[ModelPool] JSON配置解析完成，共 {len(self._models)} 个模型")
        except Exception as e:
            logger.error(f"[ModelPool] 解析JSON配置失败: {e}")

    # YAML配置已废弃
    def _load_yaml_config(self) -> Optional[Dict]:
        """加载YAML配置 - 已废弃，统一使用默认配置"""
        return None

    # 以下方法已废弃，统一使用默认配置
    # def _parse_config(self, config: Dict): ...
    # def _merge_yaml_config(self, yaml_config: Dict): ...
    # def _parse_legacy_config(self, config: Dict): ...

    def _set_default_config(self):
        """设置默认配置"""
        try:
            # 添加默认的文本模型
            default_models = {
                "deepseek_v3": ModelConfig(
                    id="deepseek_v3",
                    name="deepseek-chat",
                    type=ModelType.TEXT,
                    provider=ModelProvider.DEEPSEEK,
                    base_url=os.getenv("DEEPSEEK_API_BASE") or get_api_url("deepseek"),
                    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                    description="DeepSeek V3 官方模型",
                    capabilities=[
                        "simple_chat",
                        "chinese_understanding",
                        "tool_calling",
                    ],
                    cost_per_1k_tokens={"input": 0.00014, "output": 0.00028},
                ),
                "qwen_27b": ModelConfig(
                    id="qwen_27b",
                    name="Qwen/Qwen3-30B-A3B",
                    type=ModelType.TEXT,
                    provider=ModelProvider.SILICONFLOW,
                    base_url=os.getenv("SILICONFLOW_API_BASE")
                    or get_api_url("siliconflow"),
                    api_key=os.getenv("SILICONFLOW_API_KEY", ""),
                    description="硅基流动 Qwen3-30B-A3B 高性能模型",
                    capabilities=[
                        "simple_chat",
                        "chinese_understanding",
                        "tool_calling",
                        "reasoning",
                    ],
                    cost_per_1k_tokens={"input": 0.0003, "output": 0.0003},
                ),
                "paddleocr": ModelConfig(
                    id="paddleocr",
                    name="paddleocr",
                    type=ModelType.OCR,
                    provider=ModelProvider.LOCAL,
                    description="百度PaddleOCR",
                    capabilities=["text_extraction", "chinese_ocr"],
                    languages=["ch", "en"],
                    use_gpu=False,
                    timeout_seconds=30,
                ),
            }

            self._models.update(default_models)

            # 添加默认路由
            default_routes = {
                "simple_chat": ModelRoute(
                    task_type="simple_chat",
                    primary="deepseek_v3",
                    secondary="deepseek_v3",
                    fallback="deepseek_v3",
                ),
                "text_extraction": ModelRoute(
                    task_type="text_extraction",
                    primary="paddleocr",
                    secondary="paddleocr",
                    fallback="paddleocr",
                ),
                "image_description": ModelRoute(
                    task_type="image_description",
                    primary="siliconflow_qwen_vl",
                    secondary="zhipu_glm_46v_flash",
                    fallback="simple_analysis",
                ),
            }

            self._routes.update(default_routes)

            # 添加默认端配置
            default_endpoints = {
                "qq": EndpointConfig(
                    endpoint_id="qq",
                    enabled_models=[
                        "deepseek_v3",
                        "paddleocr",
                        "zhipu_glm_46v_flash",
                        "siliconflow_qwen_vl",
                        "minicpm_v",
                    ],
                    default_models={
                        "chat": "deepseek_v3",
                        "ocr": "paddleocr",
                        "vision": "zhipu_glm_46v_flash",
                    },
                )
            }

            self._endpoints.update(default_endpoints)

        except Exception as e:
            logger.error(f"[ModelPool] 设置默认配置失败: {e}")

    # ========== 公共API ==========

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """获取指定模型配置"""
        return self._models.get(model_id)

    def get_models_by_type(self, model_type: ModelType) -> List[ModelConfig]:
        """按类型获取模型"""
        return [model for model in self._models.values() if model.type == model_type]

    def get_models_by_capability(self, capability: str) -> List[ModelConfig]:
        """按能力获取模型"""
        return [
            model for model in self._models.values() if capability in model.capabilities
        ]

    def get_route(self, task_type: str) -> Optional[ModelRoute]:
        """获取任务路由"""
        return self._routes.get(task_type)

    def get_endpoint_config(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """获取端配置"""
        return self._endpoints.get(endpoint_id)

    def select_model_for_task(
        self, task_type: str, endpoint_id: str = None, priority: str = "balanced"
    ) -> Optional[ModelConfig]:
        """为任务选择模型"""
        try:
            # 1. 获取路由配置
            route = self.get_route(task_type)
            if not route:
                logger.warning(f"[ModelPool] 未找到任务 {task_type} 的路由配置")
                return None

            # 2. 考虑端配置
            endpoint_models = []
            if endpoint_id:
                endpoint_config = self.get_endpoint_config(endpoint_id)
                if endpoint_config:
                    endpoint_models = endpoint_config.enabled_models

            # 3. 根据优先级选择模型
            candidates = []

            # 检查主模型
            if route.primary in self._models:
                if not endpoint_models or route.primary in endpoint_models:
                    candidates.append((route.primary, 1.0))

            # 检查备用模型
            if route.secondary in self._models:
                if not endpoint_models or route.secondary in endpoint_models:
                    candidates.append((route.secondary, 0.7))

            if route.fallback in self._models:
                if not endpoint_models or route.fallback in endpoint_models:
                    candidates.append((route.fallback, 0.5))

            if not candidates:
                logger.warning(f"[ModelPool] 没有可用的模型用于任务 {task_type}")
                return None

            # 4. 根据优先级调整权重
            if priority == "cost":
                # 成本优先
                candidates = sorted(
                    candidates,
                    key=lambda x: (
                        self._models[x[0]].cost_per_1k_tokens.get("input", 1.0)
                        if self._models[x[0]].cost_per_1k_tokens
                        else 1.0
                    ),
                )
            elif priority == "speed":
                # 速度优先
                candidates = sorted(
                    candidates,
                    key=lambda x: (
                        1.0
                        if self._models[x[0]].latency == "fast"
                        else 0.5
                        if self._models[x[0]].latency == "medium"
                        else 0.1
                    ),
                    reverse=True,
                )
            elif priority == "quality":
                # 质量优先
                candidates = sorted(
                    candidates,
                    key=lambda x: (
                        1.0
                        if self._models[x[0]].quality == "excellent"
                        else 0.7
                        if self._models[x[0]].quality == "good"
                        else 0.3
                    ),
                    reverse=True,
                )

            # 返回最佳模型
            best_model_id = candidates[0][0]
            best_model = self._models[best_model_id]

            logger.info(
                f"[ModelPool] 为任务 {task_type} 选择模型: {best_model_id} ({priority})"
            )
            return best_model

        except Exception as e:
            logger.error(f"[ModelPool] 选择模型失败: {e}")
            return None

    def get_endpoint_default_model(
        self, endpoint_id: str, model_type: str
    ) -> Optional[ModelConfig]:
        """获取端特定类型的默认模型"""
        try:
            endpoint_config = self.get_endpoint_config(endpoint_id)
            if not endpoint_config:
                return None

            model_id = endpoint_config.default_models.get(model_type)
            if not model_id:
                return None

            return self.get_model(model_id)

        except Exception as e:
            logger.error(f"[ModelPool] 获取端默认模型失败: {e}")
            return None

    def create_ai_client(
        self, model_id: str = None, task_type: str = None, endpoint: str = "qq"
    ):
        """从模型配置创建AI客户端

        Args:
            model_id: 直接指定模型ID
            task_type: 根据任务类型选择模型
            endpoint: 端点ID

        Returns:
            AIClient实例或None
        """
        try:
            from core.ai_client import AIClientFactory

            model_config = None

            if model_id:
                model_config = self.get_model(model_id)
            elif task_type:
                model_config = self.select_model_for_task(task_type, endpoint)
            else:
                model_config = self.select_model_for_task("simple_chat", endpoint)

            if not model_config:
                logger.warning("[ModelPool] 未找到可用模型配置")
                return None

            if not model_config.api_key or not model_config.base_url:
                logger.warning(f"[ModelPool] 模型 {model_id} 缺少API密钥或URL")
                return None

            client = AIClientFactory.create_client(
                provider=model_config.provider.value,
                api_key=model_config.api_key,
                model=model_config.name,
                base_url=model_config.base_url,
            )

            logger.info(
                f"[ModelPool] 创建AI客户端: {model_config.id} ({model_config.name})"
            )
            return client

        except Exception as e:
            logger.error(f"[ModelPool] 创建AI客户端失败: {e}")
            return None

    def get_model_configs_for_manager(self) -> Dict[str, "ModelConfig"]:
        """获取所有有有效API密钥的模型配置（用于多模型管理器）

        Returns:
            {model_id: ModelConfig}
        """
        result = {}
        for model_id, config in self._models.items():
            if config.api_key and config.base_url:
                result[model_id] = config
        return result

    def list_all_models(self) -> List[ModelConfig]:
        """列出所有模型"""
        return list(self._models.values())

    def reload(self):
        """重新加载配置"""
        logger.info("[ModelPool] 重新加载配置...")
        self._models.clear()
        self._routes.clear()
        self._endpoints.clear()
        self._load_config()


# 全局实例和便捷函数
_model_pool_instance = None


def get_model_pool() -> ModelPool:
    """获取模型池实例"""
    global _model_pool_instance
    if _model_pool_instance is None:
        _model_pool_instance = ModelPool()
    return _model_pool_instance


def get_model(model_id: str) -> Optional[ModelConfig]:
    """获取模型配置"""
    return get_model_pool().get_model(model_id)


def select_model_for_task(
    task_type: str, endpoint_id: str = None, priority: str = "balanced"
) -> Optional[ModelConfig]:
    """为任务选择模型"""
    return get_model_pool().select_model_for_task(task_type, endpoint_id, priority)


def get_qq_model(model_type: str, priority: str = "balanced") -> Optional[ModelConfig]:
    """获取QQ端模型（便捷函数）"""
    return get_model_pool().select_model_for_task(model_type, "qq", priority)


if __name__ == "__main__":
    # 测试代码
    import sys

    logging.basicConfig(level=logging.INFO)

    pool = get_model_pool()

    print("模型池测试:")
    print(f"总模型数: {len(pool.list_all_models())}")

    # 测试文本模型
    chat_model = pool.select_model_for_task("simple_chat", "qq", "balanced")
    if chat_model:
        print(f"QQ聊天模型: {chat_model.id} ({chat_model.description})")

    # 测试视觉模型
    ocr_model = pool.select_model_for_task("text_extraction", "qq", "cost")
    if ocr_model:
        print(f"QQ OCR模型: {ocr_model.id} ({ocr_model.description})")

    # 列出所有模型类型
    text_models = pool.get_models_by_type(ModelType.TEXT)
    vision_models = pool.get_models_by_type(ModelType.VISION)
    ocr_models = pool.get_models_by_type(ModelType.OCR)

    print(f"文本模型: {len(text_models)} 个")
    print(f"视觉模型: {len(vision_models)} 个")
    print(f"OCR模型: {len(ocr_models)} 个")

    sys.exit(0)
