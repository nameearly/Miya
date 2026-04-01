"""
弥娅多模型图片分析系统
支持多个视觉模型API，实现自动故障转移和智能路由
"""

import asyncio
import base64
import hashlib
import httpx
import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.system_config import get_api_url, get_constant

logger = logging.getLogger(__name__)


class VisionModelType(Enum):
    """视觉模型类型枚举"""

    GLM_46V_FLASH = "glm-4.6v-flash"  # 智谱免费多模态模型
    GLM_4V = "glm-4v"  # 智谱GLM-4V
    QWEN_VL = "qwen-vl"  # 通义千问视觉模型
    OPENAI_GPT4O = "gpt-4o-mini"  # OpenAI GPT-4o mini
    DEEPSEEK_VISION = "deepseek-vision"  # DeepSeek视觉模型
    SILICONFLOW_VL = "siliconflow-vl"  # 硅基流动视觉模型
    LOCAL_CLIP = "clip-local"  # 本地CLIP模型（备选）
    SIMPLE_ANALYSIS = "simple-analysis"  # 简单分析（无API）


@dataclass
class VisionModelConfig:
    """视觉模型配置"""

    name: str
    model_type: VisionModelType
    provider: str
    api_base: str
    api_key: str = ""  # 直接存储API密钥
    api_key_env: str = ""  # 环境变量名（保留兼容）
    enabled: bool = True
    cost_per_call: float = 0.0
    max_tokens: int = 500
    timeout: int = 30
    priority: int = 1
    last_used: datetime = None
    error_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0


@dataclass
class ImageAnalysisResult:
    """图片分析结果"""

    success: bool
    description: str
    labels: List[str]
    nsfw_score: float
    has_text: bool = False
    text: str = ""
    text_confidence: float = 0.0
    size_kb: float = 0.0
    format: str = ""
    model_used: str = ""
    provider: str = ""
    confidence: float = 0.0
    error_message: str = ""
    processing_time_ms: float = 0.0


class MultiVisionAnalyzer:
    """
    多模型图片分析器
    支持多个视觉模型API，实现智能路由、故障转移和负载均衡
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.models: Dict[str, VisionModelConfig] = {}
        self.model_stats: Dict[str, Dict] = {}
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

        # 关键词映射
        self.keyword_mapping = {
            "人物": [
                "人",
                "人脸",
                "肖像",
                "表情",
                "动作",
                "人物",
                "面部",
                "微笑",
                "眼神",
            ],
            "自然": [
                "风景",
                "山水",
                "树木",
                "花草",
                "天空",
                "海洋",
                "自然",
                "山脉",
                "河流",
            ],
            "建筑": [
                "建筑",
                "房屋",
                "大楼",
                "桥梁",
                "道路",
                "建筑",
                "室内",
                "室外",
                "城市",
            ],
            "动物": ["动物", "宠物", "鸟类", "鱼类", "昆虫", "动物", "猫", "狗", "鸟"],
            "文字": [
                "文字",
                "文本",
                "文字内容",
                "文档",
                "截图",
                "文字",
                "代码",
                "印刷",
            ],
            "食物": ["食物", "餐饮", "水果", "蔬菜", "饮料", "食物", "美食", "烹饪"],
            "车辆": ["车辆", "汽车", "飞机", "船只", "交通", "车辆", "自行车", "摩托"],
            "电子": ["电子", "设备", "屏幕", "界面", "科技", "电子", "手机", "电脑"],
            "艺术": ["艺术", "绘画", "设计", "摄影", "色彩", "构图", "风格", "创意"],
            "运动": ["运动", "体育", "健身", "比赛", "运动员", "动作", "球场"],
        }

    async def initialize(self):
        """初始化多模型分析器 - 使用模型池"""
        async with self._initialization_lock:
            if self._initialized:
                return

            logger.info("[MultiVisionAnalyzer] 初始化多模型图片分析系统...")

            from core.model_pool import get_model_pool, ModelType

            model_pool = get_model_pool()
            vision_models = model_pool.get_models_by_type(ModelType.VISION)

            priority_map = {
                "zhipu_glm_46v_flash": 1,
                "siliconflow_qwen_vl": 2,
                "minicpm_v": 3,
            }

            self.models = {}
            available_models = []

            for model_config in vision_models:
                if model_config.api_key and model_config.base_url:
                    model_id = model_config.id
                    priority = priority_map.get(model_id, 5)
                    # 映射 provider 到旧格式以保持兼容
                    provider_map = {
                        "zhipu": "zhipu",
                        "siliconflow": "siliconflow",
                        "openai": "openai",
                        "deepseek": "deepseek",
                        "local": "local",
                    }
                    provider = provider_map.get(
                        model_config.provider.value, model_config.provider.value
                    )

                    # 为每个模型创建合适的 VisionModelType
                    if model_id == "zhipu_glm_46v_flash":
                        v_model_type = VisionModelType.GLM_46V_FLASH
                    elif model_id == "siliconflow_qwen_vl":
                        v_model_type = VisionModelType.SILICONFLOW_VL
                    elif model_id == "minicpm_v":
                        v_model_type = VisionModelType.LOCAL_CLIP
                    else:
                        v_model_type = VisionModelType.SIMPLE_ANALYSIS

                    vision_config = VisionModelConfig(
                        name=model_config.name,
                        model_type=v_model_type,
                        provider=provider,
                        api_base=model_config.base_url,
                        api_key=model_config.api_key if model_config.api_key else "",
                        api_key_env="",
                        enabled=True,
                        max_tokens=model_config.max_tokens,
                        timeout=model_config.timeout_seconds,
                        priority=priority,
                    )
                    self.models[model_id] = vision_config
                    available_models.append(model_id)
                    logger.info(
                        f"[MultiVisionAnalyzer] {model_config.name} 已启用 (来自模型池)"
                    )

            self.models["simple_analysis"] = VisionModelConfig(
                name="简单图片分析",
                model_type=VisionModelType.SIMPLE_ANALYSIS,
                provider="local",
                api_base="",
                api_key_env="",
                cost_per_call=0.0,
                max_tokens=0,
                timeout=5,
                priority=99,
            )

            if not available_models:
                logger.warning(
                    "[MultiVisionAnalyzer] 没有可用的视觉模型API，将使用本地分析"
                )

            self._initialized = True
            logger.info(
                f"[MultiVisionAnalyzer] 初始化完成，已启用 {len(available_models)} 个视觉模型"
            )

    async def analyze_image(
        self, image_data: bytes, max_retries: int = 3
    ) -> ImageAnalysisResult:
        """
        分析图片（多模型智能路由）

        Args:
            image_data: 图片二进制数据
            max_retries: 最大重试次数

        Returns:
            ImageAnalysisResult 对象
        """
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        # 获取图片基本信息
        image_size_kb = len(image_data) / 1024
        image_format = self._detect_image_format(image_data)
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # 选择最佳模型
        selected_model = await self._select_best_model()

        # 尝试分析
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"[MultiVisionAnalyzer] 使用 {selected_model.name} 分析图片 (尝试 {attempt + 1}/{max_retries})"
                )

                if selected_model.model_type == VisionModelType.SIMPLE_ANALYSIS:
                    # 简单分析（无API）
                    result = self._simple_image_analysis(image_data)
                else:
                    # API调用
                    result = await self._call_vision_api(
                        selected_model, image_base64, image_format
                    )

                # 更新模型统计
                self._update_model_stats(selected_model, success=True)

                # 计算处理时间
                processing_time_ms = (time.time() - start_time) * 1000

                return ImageAnalysisResult(
                    success=True,
                    description=result.get("description", ""),
                    labels=result.get("labels", []),
                    nsfw_score=result.get("nsfw_score", 0.0),
                    has_text=result.get("has_text", False),
                    text=result.get("text", ""),
                    text_confidence=result.get("text_confidence", 0.0),
                    size_kb=image_size_kb,
                    format=image_format,
                    model_used=selected_model.name,
                    provider=selected_model.provider,
                    confidence=result.get("confidence", 0.8),
                    processing_time_ms=processing_time_ms,
                )

            except Exception as e:
                logger.warning(
                    f"[MultiVisionAnalyzer] {selected_model.name} 分析失败: {e}"
                )

                # 更新模型统计
                self._update_model_stats(selected_model, success=False)

                # 选择下一个模型
                selected_model = await self._select_fallback_model(selected_model)

                if selected_model is None or attempt == max_retries - 1:
                    # 所有模型都失败了，返回简单分析结果
                    processing_time_ms = (time.time() - start_time) * 1000
                    simple_result = self._simple_image_analysis(image_data)

                    return ImageAnalysisResult(
                        success=True,  # 简单分析总是成功
                        description=simple_result["description"],
                        labels=simple_result["labels"],
                        nsfw_score=simple_result["nsfw_score"],
                        size_kb=image_size_kb,
                        format=image_format,
                        model_used="简单分析",
                        provider="local",
                        confidence=0.3,
                        processing_time_ms=processing_time_ms,
                    )

        # 不应该到达这里
        processing_time_ms = (time.time() - start_time) * 1000
        return self._create_error_result("所有模型分析失败", processing_time_ms)

    async def _select_best_model(self) -> VisionModelConfig:
        """选择最佳模型（基于优先级、成本和可用性）"""
        available_models = [
            model
            for model in self.models.values()
            if model.enabled and model.model_type != VisionModelType.SIMPLE_ANALYSIS
        ]

        if not available_models:
            # 回退到简单分析
            return self.models["simple_analysis"]

        # 按优先级排序
        available_models.sort(key=lambda m: m.priority)

        # 选择优先级最高且最近错误最少的模型
        best_model = available_models[0]
        for model in available_models:
            if model.error_count < best_model.error_count:
                best_model = model

        return best_model

    async def _select_fallback_model(
        self, current_model: VisionModelConfig
    ) -> Optional[VisionModelConfig]:
        """选择备用模型"""
        available_models = [
            model
            for model in self.models.values()
            if model.enabled and model != current_model
        ]

        if not available_models:
            return None

        # 按优先级排序
        available_models.sort(key=lambda m: m.priority)

        # 选择错误最少的模型
        best_fallback = available_models[0]
        for model in available_models:
            if model.error_count < best_fallback.error_count:
                best_fallback = model

        return best_fallback

    async def _call_vision_api(
        self, model_config: VisionModelConfig, image_base64: str, image_format: str
    ) -> Dict[str, Any]:
        """调用视觉模型API"""
        api_key = model_config.api_key
        if not api_key:
            raise ValueError(f"缺少 {model_config.name} 的API密钥")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        prompt = "请详细描述这张图片的内容，包括场景、物体、颜色、风格等。"

        if model_config.provider == "zhipu":
            # 智谱API格式
            url = f"{model_config.api_base}/chat/completions"
            payload = {
                "model": model_config.model_type.value,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": model_config.max_tokens,
            }

        elif model_config.provider in ["openai", "deepseek", "siliconflow"]:
            # OpenAI兼容格式
            url = f"{model_config.api_base}/chat/completions"
            payload = {
                "model": model_config.model_type.value,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": model_config.max_tokens,
            }

        elif model_config.provider == "dashscope":
            # 通义千问格式 - 使用环境变量中的模型名称
            qwen_vl_model = os.getenv("DASHSCOPE_QWEN_VL_MODEL", "qwen-vl-plus")
            url = f"{model_config.api_base}/chat/completions"
            payload = {
                "model": qwen_vl_model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"text": prompt},
                                {
                                    "image": f"data:image/{image_format};base64,{image_base64}"
                                },
                            ],
                        }
                    ]
                },
                "parameters": {"max_tokens": model_config.max_tokens},
            }

        else:
            raise ValueError(f"不支持的提供商: {model_config.provider}")

        try:
            response = await self.http_client.post(
                url, json=payload, headers=headers, timeout=model_config.timeout
            )

            if response.status_code == 200:
                result = response.json()

                # 提取分析结果
                if model_config.provider == "zhipu":
                    content = (
                        result.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                elif model_config.provider == "dashscope":
                    content = result.get("output", {}).get("text", "")
                else:
                    content = (
                        result.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                labels = self._extract_labels_from_description(content)

                return {
                    "description": content,
                    "labels": labels,
                    "nsfw_score": 0.0,
                    "confidence": 0.8,
                    "has_text": False,
                    "text": "",
                    "text_confidence": 0.0,
                }
            else:
                error_msg = f"API调用失败: HTTP {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text[:100]}"
                raise ValueError(error_msg)

        except httpx.TimeoutException:
            raise ValueError(f"{model_config.name} API调用超时")
        except Exception as e:
            raise ValueError(f"{model_config.name} API调用异常: {str(e)[:100]}")

    def _simple_image_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """简单图片分析（无API）- 使用PIL进行本地分析"""
        try:
            from PIL import Image
            import io
            import colorsys

            image_format = self._detect_image_format(image_data)
            size_kb = len(image_data) / 1024

            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            aspect_ratio = width / height if height > 0 else 1

            # 缩小图片以加快分析
            small = image.resize((50, 50))
            pixels = list(small.getdata())

            # 颜色分析
            avg_r, avg_g, avg_b = 0, 0, 0
            bright_pixels = 0
            dark_pixels = 0
            warm_pixels = 0
            cool_pixels = 0
            for p in pixels:
                if isinstance(p, (tuple, list)) and len(p) >= 3:
                    r, g, b = p[:3]
                    avg_r += r
                    avg_g += g
                    avg_b += b
                    brightness = (r + g + b) / 3
                    if brightness > 180:
                        bright_pixels += 1
                    elif brightness < 80:
                        dark_pixels += 1
                    if r > g and r > b:
                        warm_pixels += 1
                    elif b > r and b > g:
                        cool_pixels += 1

            total = len(pixels)
            avg_r /= total
            avg_g /= total
            avg_b /= total

            # 判断色调
            hue = colorsys.rgb_to_hsv(avg_r, avg_g, avg_b)[0]
            if 0.0 <= hue < 0.15 or hue >= 0.85:
                tone = "红色调"
            elif 0.15 <= hue < 0.25:
                tone = "橙色调"
            elif 0.25 <= hue < 0.4:
                tone = "黄色调"
            elif 0.4 <= hue < 0.5:
                tone = "绿色调"
            elif 0.5 <= hue < 0.7:
                tone = "蓝色调"
            else:
                tone = "紫色调"

            # 判断亮度
            if bright_pixels / total > 0.5:
                brightness_desc = "明亮"
            elif dark_pixels / total > 0.5:
                brightness_desc = "暗淡"
            else:
                brightness_desc = "中等亮度"

            # 判断冷暖色
            if warm_pixels > cool_pixels:
                color_temp = "暖色调"
            else:
                color_temp = "冷色调"

            # 判断形状
            if aspect_ratio > 1.5:
                shape_desc = "横向宽图"
            elif aspect_ratio < 0.67:
                shape_desc = "纵向长图"
            elif abs(aspect_ratio - 1.0) < 0.1:
                shape_desc = "正方形"
            else:
                shape_desc = "标准比例"

            # 判断是否可能是表情包
            is_emoji_like = (
                width <= 500
                and height <= 500
                and size_kb < 500
                and (image_format == "gif" or image_format == "png")
            )

            # 判断是否可能是截图
            is_screenshot = (
                width >= 800
                and height >= 600
                and image_format == "png"
                and avg_b > avg_r
                and avg_b > avg_g
            )

            # 生成描述
            description = f"这是一张{image_format.upper()}格式的图片"
            description += f"，尺寸为{width}×{height}像素"
            description += f"，大小约{size_kb:.1f}KB"
            description += f"，{shape_desc}"
            description += f"，{brightness_desc}"
            description += f"，{color_temp}"
            description += f"，{tone}"

            if image_format == "gif":
                description += "，这是一张GIF动图"
            if is_emoji_like:
                description += "，看起来像是一个表情包"
            if is_screenshot:
                description += "，可能是一张截图"

            # 生成标签
            labels = [image_format.upper()]
            if is_emoji_like:
                labels.extend(
                    ["表情包", "表情", "动图" if image_format == "gif" else "静态表情"]
                )
            if is_screenshot:
                labels.append("截图")
            labels.append(brightness_desc)
            labels.append(color_temp)
            labels.append(tone)
            labels.append(shape_desc)

            if size_kb > 500:
                labels.append("大图")
            elif size_kb < 50:
                labels.append("小图")

            return {
                "description": description,
                "labels": list(dict.fromkeys(labels)),
                "nsfw_score": 0.0,
                "confidence": 0.4,
                "has_text": False,
                "text": "",
                "text_confidence": 0.0,
            }

        except Exception as e:
            logger.warning(f"简单图片分析失败: {e}")
            image_format = self._detect_image_format(image_data)
            size_kb = len(image_data) / 1024
            description = f"{image_format.upper()}格式图片，大小{size_kb:.1f}KB"
            return {
                "description": description,
                "labels": [image_format.upper(), "图片"],
                "nsfw_score": 0.0,
                "confidence": 0.3,
                "has_text": False,
                "text": "",
                "text_confidence": 0.0,
            }

    def _extract_labels_from_description(self, description: str) -> List[str]:
        """从描述中提取标签"""
        labels = []
        description_lower = description.lower()

        for category, keywords in self.keyword_mapping.items():
            for keyword in keywords:
                if keyword in description_lower:
                    labels.append(category)
                    break

        # 去重
        labels = list(set(labels))

        # 如果没有标签，添加通用标签
        if not labels:
            labels = ["图片", "视觉内容"]

        return labels

    def _detect_image_format(self, image_data: bytes) -> str:
        """检测图片格式"""
        if len(image_data) < 8:
            return "unknown"

        if image_data.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        elif image_data.startswith(b"GIF87a") or image_data.startswith(b"GIF89a"):
            return "gif"
        elif image_data.startswith(b"BM"):
            return "bmp"
        elif image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
            return "webp"
        else:
            return "unknown"

    def _update_model_stats(self, model: VisionModelConfig, success: bool):
        """更新模型统计信息"""
        model_id = None
        for mid, m in self.models.items():
            if m == model:
                model_id = mid
                break

        if not model_id:
            return

        if model_id not in self.model_stats:
            self.model_stats[model_id] = {
                "total_calls": 0,
                "success_calls": 0,
                "error_calls": 0,
                "last_call_time": None,
                "avg_response_time": 0.0,
            }

        stats = self.model_stats[model_id]
        stats["total_calls"] += 1
        stats["last_call_time"] = datetime.now()

        if success:
            stats["success_calls"] += 1
            model.success_count += 1
            model.error_count = max(0, model.error_count - 1)  # 成功时减少错误计数
        else:
            stats["error_calls"] += 1
            model.error_count += 1

    def _create_error_result(
        self, error_message: str, processing_time_ms: float
    ) -> ImageAnalysisResult:
        """创建错误结果"""
        return ImageAnalysisResult(
            success=False,
            description=error_message,
            labels=["错误", "分析失败"],
            nsfw_score=0.0,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_models": len(self.models),
            "enabled_models": sum(1 for m in self.models.values() if m.enabled),
            "model_stats": self.model_stats,
            "initialized": self._initialized,
        }

    async def close(self):
        """关闭资源"""
        await self.http_client.aclose()
        logger.info("[MultiVisionAnalyzer] 已关闭")


# 全局实例
_global_analyzer: Optional[MultiVisionAnalyzer] = None


async def get_vision_analyzer() -> MultiVisionAnalyzer:
    """获取全局多模型视觉分析器实例"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = MultiVisionAnalyzer()
        await _global_analyzer.initialize()
    return _global_analyzer


async def analyze_image_multi_model(
    image_data: bytes, max_retries: int = 3
) -> ImageAnalysisResult:
    """
    使用多模型分析图片（便捷函数）

    Args:
        image_data: 图片二进制数据
        max_retries: 最大重试次数

    Returns:
        ImageAnalysisResult 对象
    """
    analyzer = await get_vision_analyzer()
    return await analyzer.analyze_image(image_data, max_retries)
