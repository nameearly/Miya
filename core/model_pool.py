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

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import os

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

        self._project_root = Path(__file__).parent.parent
        self._config = {}
        self._models: Dict[str, ModelConfig] = {}
        self._routes: Dict[str, ModelRoute] = {}
        self._endpoints: Dict[str, EndpointConfig] = {}
        self._initialized = False

        self._load_config()
        self._initialized = True

    def _load_config(self):
        """加载模型配置"""
        try:
            # 1. 首先加载JSON配置（multi_model_config.json，包含实际API密钥）
            json_config = self._load_json_config()

            if json_config:
                self._config = json_config
                self._parse_legacy_config(json_config)
                logger.info("[ModelPool] 从JSON加载模型配置")

                # 2. 尝试加载YAML配置作为补充（统一模型池配置）
                yaml_config = self._load_yaml_config()
                if yaml_config:
                    # 合并YAML中的额外模型和路由
                    self._merge_yaml_config(yaml_config)
                    logger.info("[ModelPool] 合并YAML配置补充")

                return

            # 3. 如果没有JSON，尝试加载YAML配置
            yaml_config = self._load_yaml_config()

            if yaml_config:
                self._config = yaml_config
                self._parse_config(yaml_config)
                logger.info("[ModelPool] 从YAML加载统一模型配置")
                return

            # 4. 使用默认配置
            self._set_default_config()
            logger.warning("[ModelPool] 使用默认模型配置")

        except Exception as e:
            logger.error(f"[ModelPool] 加载配置失败: {e}")
            self._set_default_config()

    def _load_yaml_config(self) -> Optional[Dict]:
        """加载YAML配置"""
        try:
            yaml_paths = [
                self._project_root / "config" / "unified_model_config.yaml",
                self._project_root / "unified_model_config.yaml",
            ]

            for yaml_path in yaml_paths:
                if yaml_path.exists():
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)

                    logger.info(f"[ModelPool] 从 {yaml_path} 加载YAML配置")
                    return config

            return None

        except Exception as e:
            logger.error(f"[ModelPool] 加载YAML配置失败: {e}")
            return None

    def _load_json_config(self) -> Optional[Dict]:
        """加载JSON配置"""
        try:
            json_paths = [
                self._project_root / "config" / "multi_model_config.json",
                self._project_root / "multi_model_config.json",
            ]

            for json_path in json_paths:
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        config = json.load(f)

                    logger.info(f"[ModelPool] 从 {json_path} 加载JSON配置")
                    return config

            return None

        except Exception as e:
            logger.error(f"[ModelPool] 加载JSON配置失败: {e}")
            return None

    def _parse_config(self, config: Dict):
        """解析统一配置"""
        try:
            # 解析模型
            if "models" in config:
                for model_id, model_data in config["models"].items():
                    self._parse_model_config(model_id, model_data)

            # 解析路由
            if "model_routing" in config:
                routing_config = config["model_routing"]

                # 解析任务路由
                if "tasks" in routing_config:
                    for task_type, route_data in routing_config["tasks"].items():
                        self._parse_route_config(task_type, route_data)

                # 解析端配置
                if "endpoints" in routing_config:
                    for endpoint_id, endpoint_data in routing_config[
                        "endpoints"
                    ].items():
                        self._parse_endpoint_config(endpoint_id, endpoint_data)

            logger.info(f"[ModelPool] 解析完成，共 {len(self._models)} 个模型")

        except Exception as e:
            logger.error(f"[ModelPool] 解析配置失败: {e}")
            raise

    def _merge_yaml_config(self, yaml_config: Dict):
        """合并YAML配置到已加载的JSON配置中

        用于补充JSON中没有的模型和路由配置
        """
        try:
            # 合并模型（只添加JSON中不存在的模型）
            if "models" in yaml_config:
                for model_id, model_data in yaml_config["models"].items():
                    if model_id not in self._models:
                        self._parse_model_config(model_id, model_data)
                        logger.info(f"[ModelPool] 从YAML添加模型: {model_id}")

            # 合并路由
            if "model_routing" in yaml_config:
                routing_config = yaml_config["model_routing"]

                # 合并任务路由
                if "tasks" in routing_config:
                    for task_type, route_data in routing_config["tasks"].items():
                        if task_type not in self._routes:
                            self._parse_route_config(task_type, route_data)

                # 合并端配置
                if "endpoints" in routing_config:
                    for endpoint_id, endpoint_data in routing_config[
                        "endpoints"
                    ].items():
                        if endpoint_id not in self._endpoints:
                            self._parse_endpoint_config(endpoint_id, endpoint_data)

            logger.info(
                f"[ModelPool] YAML配置合并完成，当前共 {len(self._models)} 个模型"
            )

        except Exception as e:
            logger.error(f"[ModelPool] 合并YAML配置失败: {e}")

    def _parse_model_config(self, model_id: str, model_data: Dict):
        """解析单个模型配置"""
        try:
            # 处理API密钥的环境变量，支持 ${VAR} 和 ${VAR:-default} 格式
            api_key = model_data.get("api_key", "")
            if api_key and api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                if ":-" in env_var:
                    var_name, default_value = env_var.split(":-", 1)
                    api_key = os.getenv(var_name, default_value)
                else:
                    api_key = os.getenv(env_var, "")

            base_url = model_data.get("base_url", "")
            if base_url and base_url.startswith("${") and base_url.endswith("}"):
                env_part = base_url[2:-1]
                if ":-" in env_part:
                    var_name, default_value = env_part.split(":-", 1)
                    base_url = os.getenv(var_name, default_value)
                else:
                    base_url = os.getenv(env_part, "")

            # 处理模型名称的环境变量
            model_name = model_data.get("name", model_id)
            if model_name and model_name.startswith("${") and model_name.endswith("}"):
                env_part = model_name[2:-1]
                if ":-" in env_part:
                    var_name, default_value = env_part.split(":-", 1)
                    model_name = os.getenv(var_name, default_value)
                else:
                    model_name = os.getenv(env_part, model_name)

            # 创建模型配置
            config = ModelConfig(
                id=model_id,
                name=model_name,
                type=ModelType(model_data.get("type", "text")),
                provider=ModelProvider(model_data.get("provider", "local")),
                base_url=base_url or None,
                api_key=api_key or None,
                description=model_data.get("description", ""),
                capabilities=model_data.get("capabilities", []),
                cost_per_1k_tokens=model_data.get("cost_per_1k_tokens"),
                latency=model_data.get("latency", "medium"),
                quality=model_data.get("quality", "good"),
                max_tokens=model_data.get("max_tokens", 4096),
                max_image_size=model_data.get("max_image_size"),
                supported_formats=model_data.get("supported_formats", []),
                languages=model_data.get("languages", []),
                use_gpu=model_data.get("use_gpu", False),
                timeout_seconds=model_data.get("timeout_seconds", 30),
                model_path=model_data.get("model_path"),
            )

            self._models[model_id] = config

        except Exception as e:
            logger.error(f"[ModelPool] 解析模型 {model_id} 失败: {e}")

    def _parse_route_config(self, task_type: str, route_data: Dict):
        """解析路由配置"""
        try:
            route = ModelRoute(
                task_type=task_type,
                primary=route_data.get("primary"),
                secondary=route_data.get("secondary"),
                fallback=route_data.get("fallback"),
                cost_priority=route_data.get("cost_priority", 1.0),
                speed_priority=route_data.get("speed_priority", 1.0),
                quality_priority=route_data.get("quality_priority", 1.0),
            )

            self._routes[task_type] = route

        except Exception as e:
            logger.error(f"[ModelPool] 解析路由 {task_type} 失败: {e}")

    def _parse_endpoint_config(self, endpoint_id: str, endpoint_data: Dict):
        """解析端配置"""
        try:
            endpoint = EndpointConfig(
                endpoint_id=endpoint_id,
                enabled_models=endpoint_data.get("enabled_models", []),
                default_models=endpoint_data.get("defaults", {}),
            )

            self._endpoints[endpoint_id] = endpoint

        except Exception as e:
            logger.error(f"[ModelPool] 解析端配置 {endpoint_id} 失败: {e}")

    def _parse_legacy_config(self, config: Dict):
        """解析旧的JSON配置"""
        try:
            # 解析模型
            if "models" in config:
                for model_id, model_data in config["models"].items():
                    # 转换旧格式到新格式
                    legacy_model = {
                        "name": model_data.get("name", model_id),
                        "type": "text",  # 旧配置只有文本模型
                        "provider": model_data.get("provider", "openai"),
                        "base_url": model_data.get("base_url", ""),
                        "api_key": model_data.get("api_key", ""),
                        "description": model_data.get("description", ""),
                        "capabilities": model_data.get("capabilities", []),
                        "cost_per_1k_tokens": model_data.get("cost_per_1k_tokens"),
                        "latency": model_data.get("latency", "medium"),
                        "quality": model_data.get("quality", "good"),
                    }

                    self._parse_model_config(model_id, legacy_model)

            # 解析路由
            if "model_routing" in config:
                for task_type, route_data in config["model_routing"].items():
                    self._parse_route_config(task_type, route_data)

            logger.info(f"[ModelPool] 解析旧配置完成，共 {len(self._models)} 个模型")

        except Exception as e:
            logger.error(f"[ModelPool] 解析旧配置失败: {e}")

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
                "zhipu_glm_46v_flash": ModelConfig(
                    id="zhipu_glm_46v_flash",
                    name="glm-4.6v-flash",
                    type=ModelType.VISION,
                    provider=ModelProvider.ZHIPU,
                    base_url=os.getenv("ZHIPU_API_BASE") or get_api_url("zhipu"),
                    api_key=os.getenv("ZHIPU_API_KEY", ""),
                    description="智谱GLM-4.6V-Flash 视觉模型",
                    capabilities=["image_description", "vision_understanding"],
                    supported_formats=["jpg", "png", "gif", "webp"],
                    max_tokens=800,
                ),
                "siliconflow_qwen_vl": ModelConfig(
                    id="siliconflow_qwen_vl",
                    name="Qwen/Qwen2.5-VL-72B-Instruct",
                    type=ModelType.VISION,
                    provider=ModelProvider.SILICONFLOW,
                    base_url=os.getenv("SILICONFLOW_API_BASE")
                    or get_api_url("siliconflow"),
                    api_key=os.getenv("SILICONFLOW_API_KEY", ""),
                    description="硅基流动 Qwen-VL 视觉模型",
                    capabilities=["image_description", "vision_understanding"],
                    supported_formats=["jpg", "png", "gif", "webp"],
                    max_tokens=500,
                ),
                "minicpm_v": ModelConfig(
                    id="minicpm_v",
                    name="MiniCPM-V",
                    type=ModelType.VISION,
                    provider=ModelProvider.LOCAL,
                    description="本地 MiniCPM-V 视觉模型",
                    capabilities=["image_description", "vision_understanding"],
                    supported_formats=["jpg", "png"],
                    max_tokens=500,
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
                    primary="zhipu_glm_46v_flash",
                    secondary="siliconflow_qwen_vl",
                    fallback="minicpm_v",
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
