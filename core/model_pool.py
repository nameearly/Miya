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
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

from core.system_config import get_api_url

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型枚举"""

    SIMPLE_CHAT = "simple_chat"
    COMPLEX_REASONING = "complex_reasoning"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    TOOL_CALLING = "tool_calling"
    CREATIVE_WRITING = "creative_writing"
    CHINESE_UNDERSTANDING = "chinese_understanding"
    SUMMARIZATION = "summarization"
    MULTIMODAL = "multimodal"
    TASK_PLANNING = "task_planning"


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
    third: str = ""


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
        """加载模型配置 - 从 multi_model_config.json 加载模型，从 text_config.json 加载任务分类"""
        try:
            # 从 multi_model_config.json 加载模型配置
            json_config = self._load_json_config()
            if json_config:
                self._config = json_config
                self._parse_json_config(json_config)
                logger.info("[ModelPool] 从multi_model_config.json加载模型配置")

            # 从 text_config.json 加载任务分类配置
            self._load_task_classification()

        except Exception as e:
            logger.error(f"[ModelPool] 加载配置失败: {e}")
            self._set_default_config()

    def _load_task_classification(self):
        """从 text_config.json 加载任务分类配置"""
        try:
            tc_path = self._project_root / "config" / "text_config.json"
            if tc_path.exists():
                with open(tc_path, "r", encoding="utf-8") as f:
                    tc = json.load(f)
                task_config = tc.get("task_classification", {})
                if task_config:
                    self._config["task_classification"] = task_config
                    logger.info("[ModelPool] 从text_config.json加载任务分类配置")
        except Exception as e:
            logger.debug(f"[ModelPool] 任务分类配置加载失败: {e}")

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
                        "anthropic": ModelProvider.OPENAI,  # Anthropic 使用 OpenAI 兼容格式
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

            if "routing_strategy" in config:
                for task_type, route_data in config["routing_strategy"].items():
                    route = ModelRoute(
                        task_type=task_type,
                        primary=route_data.get("primary", ""),
                        secondary=route_data.get("secondary", ""),
                        third=route_data.get("third", ""),
                        fallback=route_data.get("fallback", ""),
                    )
                    self._routes[task_type] = route
                logger.info(
                    f"[ModelPool] 路由策略解析完成，共 {len(self._routes)} 个路由"
                )

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
        """设置默认配置 - 所有模型必须从 multi_model_config.json 加载"""
        # 不再设置任何硬编码默认模型
        # 所有模型配置、路由、端点都必须从 multi_model_config.json 加载
        pass

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

    # ========== 任务分类 ==========

    def _classify_by_keywords(self, user_input: str) -> TaskType:
        """关键词分类（快速回退方案）"""
        tc = self._config.get("task_classification", {})

        if not isinstance(user_input, str):
            return TaskType.SIMPLE_CHAT

        if not user_input:
            return TaskType.SIMPLE_CHAT

        input_lower = user_input.lower()

        if any(kw in input_lower for kw in tc.get("tool_calling", [])):
            return TaskType.TOOL_CALLING

        code_kws = tc.get("code_keywords", [])
        if any(kw in input_lower for kw in code_kws):
            gen_triggers = tc.get("code_generation_triggers", [])
            if any(kw in input_lower for kw in gen_triggers):
                return TaskType.CODE_GENERATION
            return TaskType.CODE_ANALYSIS

        reasoning_kws = tc.get("complex_reasoning", [])
        indicators = tc.get("complex_indicators", [])
        if any(kw in input_lower for kw in reasoning_kws + indicators):
            return TaskType.COMPLEX_REASONING

        if any(kw in input_lower for kw in tc.get("creative_writing", [])):
            return TaskType.CREATIVE_WRITING

        if any(kw in input_lower for kw in tc.get("summarization", [])):
            return TaskType.SUMMARIZATION

        if any(kw in input_lower for kw in tc.get("task_planning", [])):
            return TaskType.TASK_PLANNING

        threshold = tc.get("chinese_ratio_threshold", 0.5)
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", user_input))
        if chinese_chars > len(user_input) * threshold:
            return TaskType.CHINESE_UNDERSTANDING

        return TaskType(tc.get("default_task", "simple_chat"))

    async def classify_task(self, user_input: str, context: Dict = None) -> TaskType:
        """
        分类任务类型（LLM 智能分类 + 关键词回退）

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            任务类型
        """
        tc = self._config.get("task_classification", {})

        # 处理非字符串输入
        if not isinstance(user_input, str):
            if isinstance(user_input, list):
                content_str = ""
                for item in user_input:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content_str += item.get("data", {}).get("text", "")
                        elif item.get("type") == "image":
                            return TaskType.SIMPLE_CHAT
                    elif isinstance(item, str):
                        content_str += item
                user_input = content_str if content_str else ""
            else:
                user_input = str(user_input)

        if not user_input:
            return TaskType.SIMPLE_CHAT

        # 检查是否启用 LLM 分类
        mode = tc.get("mode", "keyword")
        if mode == "llm":
            try:
                llm_model_id = tc.get("llm_model", "qwen_7b")
                model_config = self.get_model(llm_model_id)

                if model_config and model_config.api_key and model_config.base_url:
                    from core.ai_client import AIClientFactory

                    client = AIClientFactory.create_client(
                        provider=model_config.provider.value,
                        api_key=model_config.api_key,
                        model=model_config.name,
                        base_url=model_config.base_url,
                    )

                    if client and hasattr(client, "client") and client.client:
                        task_names = [t.value for t in TaskType]
                        prompt = (
                            f"请将以下用户输入分类为以下任务类型之一。\n"
                            f"任务类型: {', '.join(task_names)}\n\n"
                            f"用户输入: {user_input}\n\n"
                            f"只返回任务类型名称，不要其他内容。"
                        )

                        import asyncio

                        timeout = tc.get("llm_timeout", 10)
                        response = await asyncio.wait_for(
                            client.client.chat.completions.create(
                                model=client.model,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=50,
                                temperature=0.1,
                            ),
                            timeout=timeout,
                        )

                        result = response.choices[0].message.content.strip()
                        if result in task_names:
                            logger.debug(
                                f"[ModelPool] LLM 分类: {user_input[:30]}... → {result}"
                            )
                            return TaskType(result)
                        else:
                            logger.debug(
                                f"[ModelPool] LLM 返回未知类型: {result}，回退到关键词"
                            )
            except Exception as e:
                logger.debug(f"[ModelPool] LLM 分类失败: {e}，回退到关键词")

        # 关键词回退
        return self._classify_by_keywords(user_input)

    # ========== 使用统计 ==========

    def __init__(self):
        if self._initialized:
            return

        load_dotenv()

        self._project_root = Path(__file__).parent.parent
        self._config = {}
        self._models: Dict[str, ModelConfig] = {}
        self._routes: Dict[str, ModelRoute] = {}
        self._endpoints: Dict[str, EndpointConfig] = {}
        self._usage_stats: Dict[str, Dict] = {}
        self._initialized = False

        self._load_config()
        self._initialized = True

    def record_usage(self, model_key: str, input_tokens: int, output_tokens: int):
        """记录模型使用情况"""
        if model_key not in self._usage_stats:
            self._usage_stats[model_key] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
            }

        stats = self._usage_stats[model_key]
        stats["requests"] += 1
        stats["input_tokens"] += input_tokens
        stats["output_tokens"] += output_tokens

        model_info = self._config.get("models", {}).get(model_key, {})
        pricing = model_info.get("cost_per_1k_tokens", {})
        cost = (
            input_tokens * pricing.get("input", 0)
            + output_tokens * pricing.get("output", 0)
        ) / 1000
        stats["cost"] += cost

    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return self._usage_stats

    def get_total_cost(self) -> float:
        """获取总成本"""
        return sum(stats["cost"] for stats in self._usage_stats.values())

    def reset_stats(self):
        """重置统计"""
        self._usage_stats = {}
        logger.info("[ModelPool] 模型使用统计已重置")


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
