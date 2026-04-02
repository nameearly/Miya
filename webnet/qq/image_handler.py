"""
统一版QQ图片处理器
使用模型池中的多模型视觉分析系统，支持智能路由和故障转移
"""

import asyncio
import base64
import hashlib
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# 禁用SSL警告
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

import httpx

from .models import QQMessage

logger = logging.getLogger(__name__)

MULTI_MODEL_AVAILABLE = False
_vision_analyzer = None


async def get_vision_analyzer():
    """获取视觉分析器实例"""
    global _vision_analyzer
    if _vision_analyzer is None:
        from core.multi_vision_analyzer import get_vision_analyzer as _get_analyzer

        _vision_analyzer = await _get_analyzer()
    return _vision_analyzer


class QQImageHandler:
    """统一版QQ图片处理器 - 使用多模型视觉分析系统"""

    def __init__(self, qq_net, personality=None):
        self.qq_net = qq_net
        self.personality = personality
        # 禁用SSL验证（Windows环境需要）
        self.http_client = httpx.AsyncClient(
            timeout=60.0, verify=False, headers={"User-Agent": "Miya/1.0"}
        )
        self._analyzer = None
        logger.info("[QQImageHandler] 初始化完成 - 使用多模型视觉分析系统")

    async def _get_analyzer(self):
        """获取或初始化视觉分析器"""
        if self._analyzer is None:
            self._analyzer = await get_vision_analyzer()
        return self._analyzer

    def configure(self, enable_ocr: bool = False, enable_ai_analysis: bool = True):
        """配置处理器"""
        logger.info("[QQImageHandler] 配置完成 - 使用多模型视觉分析系统")

    async def handle_image_message(self, event: Dict) -> Optional[QQMessage]:
        """处理图片消息"""
        try:
            image_info = self._extract_image_info(event)
            if not image_info:
                logger.warning("[QQImageHandler] 无法提取图片信息")
                return None

            image_data = await self._download_image(image_info)
            if not image_data:
                logger.warning("[QQImageHandler] 图片下载失败")
                return None

            image_id = hashlib.md5(image_data).hexdigest()

            analysis_result = await self._analyze_image(image_data)

            self._cache_image(image_id, analysis_result)

            # 自动保存表情包
            await self._auto_save_emoji(event, image_data, image_info)

            message = QQMessage.from_dict(event)
            message.image_data = image_data
            message.image_info = image_info
            message.image_analysis = analysis_result
            message.has_image = True

            logger.info(f"[QQImageHandler] 图片消息处理完成")

            return message

        except Exception as e:
            logger.error(f"[QQImageHandler] 处理图片消息失败: {e}", exc_info=True)
            return None

    async def _auto_save_emoji(self, event: Dict, image_data: bytes, image_info: Dict):
        """自动保存用户发送的表情包"""
        try:
            from utils.auto_emoji_saver import get_auto_emoji_saver

            # 获取发送者ID
            user_id = event.get("user_id") or event.get("sender_id")
            if not user_id:
                logger.debug("[QQImageHandler] 无法获取用户ID，跳过自动保存")
                return

            # 获取自动保存服务
            auto_saver = get_auto_emoji_saver()
            if not auto_saver or not auto_saver.is_enabled():
                logger.debug("[QQImageHandler] 自动保存功能未启用")
                return

            # 执行自动保存
            save_result = await auto_saver.auto_save_emoji(
                user_id=user_id, image_data=image_data, image_info=image_info
            )

            if save_result.get("success"):
                logger.info(f"[QQImageHandler] 用户 {user_id} 的表情包已自动保存")
            else:
                logger.debug(
                    f"[QQImageHandler] 自动保存跳过: {save_result.get('message', '')}"
                )

        except Exception as e:
            logger.warning(f"[QQImageHandler] 自动保存表情包失败: {e}")

    def _extract_image_info(self, event: Dict) -> Optional[Dict[str, Any]]:
        """从事件中提取图片信息"""
        message = event.get("message", [])

        for segment in message:
            if isinstance(segment, dict):
                seg_type = segment.get("type")
                if seg_type == "image":
                    data = segment.get("data", {})
                    return {
                        "url": data.get("url", ""),
                        "file": data.get("file", ""),
                        "type": "image",
                        "size": data.get("size", 0),
                    }

        return None

    async def _download_image(self, image_info: Dict) -> Optional[bytes]:
        """下载图片"""
        url = image_info.get("url")
        file_path = image_info.get("file")

        if not url and not file_path:
            return None

        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()

            if url:
                response = await self.http_client.get(url)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(
                        f"[QQImageHandler] 下载图片失败: HTTP {response.status_code}"
                    )
                    return None

            return None

        except Exception as e:
            logger.error(f"[QQImageHandler] 下载图片失败: {e}")
            return None

    async def _analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """使用多模型视觉分析系统分析图片"""
        try:
            analyzer = await self._get_analyzer()

            from core.multi_vision_analyzer import ImageAnalysisResult

            result = await analyzer.analyze_image(image_data, max_retries=3)

            if result.success:
                return {
                    "success": True,
                    "has_text": result.has_text,
                    "text": result.text or "",
                    "text_confidence": result.text_confidence,
                    "description": result.description or "",
                    "labels": result.labels or [],
                    "nsfw_score": result.nsfw_score,
                    "size_kb": result.size_kb,
                    "format": result.format,
                    "model": result.model_used,
                    "provider": result.provider,
                    "confidence": result.confidence,
                    "processing_time_ms": result.processing_time_ms,
                    "api_call": result.model_used != "简单分析",
                }
            else:
                return self._create_fallback_result(image_data)

        except Exception as e:
            logger.error(f"[QQImageHandler] 视觉模型分析失败: {e}")
            return self._create_fallback_result(image_data)

    def _create_fallback_result(self, image_data: bytes) -> Dict[str, Any]:
        """创建fallback结果（使用本地简单分析）"""
        try:
            from PIL import Image
            import io
            import json
            from pathlib import Path

            # 加载配置
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "text_config.json"
            )
            with open(config_path, "r", encoding="utf-8") as f:
                full_config = json.load(f)
            vision_config = full_config.get("vision", {})
            simple_config = vision_config.get("simple_analysis", {})
            fallback_config = vision_config.get("fallback", {})

            image_format = self._detect_image_format(image_data)
            size_kb = len(image_data) / 1024

            image = Image.open(io.BytesIO(image_data))
            width, height = image.size

            desc_template = simple_config.get(
                "description_template",
                "这是一张{format}格式的图片，尺寸为{width}×{height}像素，大小约{size_kb:.1f}KB。",
            )
            description = desc_template.format(
                format=image_format.upper(), width=width, height=height, size_kb=size_kb
            )

            labels = [image_format.upper(), "图片"]
            size_tags = simple_config.get("size_tags", {})
            if width <= 200 and height <= 200:
                labels.append(size_tags.get("small", "小图"))
            elif width >= 800 or height >= 800:
                labels.append(size_tags.get("large", "大图"))

            return {
                "success": True,
                "has_text": False,
                "text": "",
                "text_confidence": 0.0,
                "description": description,
                "labels": labels,
                "nsfw_score": 0.0,
                "size_kb": size_kb,
                "format": image_format,
                "model": "本地分析",
                "provider": "local",
                "confidence": 0.3,
                "api_call": False,
            }

        except Exception as e:
            logger.warning(f"[QQImageHandler] Fallback分析也失败: {e}")
            import json
            from pathlib import Path

            config_path = (
                Path(__file__).parent.parent.parent / "config" / "text_config.json"
            )
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    full_config = json.load(f)
                fallback_desc = (
                    full_config.get("vision", {})
                    .get("fallback", {})
                    .get("api_error", "图片分析失败")
                )
                error_desc = fallback_desc.format(error=str(e)[:50])
            except:
                error_desc = "图片分析失败"

            return {
                "success": False,
                "has_text": False,
                "text": "",
                "text_confidence": 0.0,
                "description": error_desc,
                "labels": ["分析失败"],
                "nsfw_score": 0.0,
                "size_kb": len(image_data) / 1024,
                "format": "unknown",
                "model": "none",
                "provider": "none",
                "confidence": 0.0,
                "api_call": False,
            }

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

    def _cache_image(self, image_id: str, image_analysis: Dict[str, Any]):
        """缓存图片分析结果"""
        try:
            if (
                hasattr(self, "qq_net")
                and self.qq_net
                and hasattr(self.qq_net, "cache_manager")
            ):
                self.qq_net.cache_manager.set_image_analysis(image_id, image_analysis)
        except Exception as e:
            logger.warning(f"[QQImageHandler] 缓存分析结果失败: {e}")

    async def cleanup(self):
        """清理资源"""
        try:
            await self.http_client.aclose()
        except:
            pass
