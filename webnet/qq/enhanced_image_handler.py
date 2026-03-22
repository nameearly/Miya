"""
增强版QQ图片处理器
使用多模型图片分析系统，支持多个视觉模型API和故障转移
"""

import asyncio
import base64
import hashlib
import httpx
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import QQMessage

# 导入多模型分析系统
try:
    from core.multi_vision_analyzer import (
        analyze_image_multi_model, 
        ImageAnalysisResult,
        get_vision_analyzer
    )
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    MULTI_MODEL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("多模型分析系统不可用，将使用简化版")

# 导入表情包自动保存服务
try:
    from utils.auto_emoji_saver import get_auto_emoji_saver
    AUTO_SAVER_AVAILABLE = True
except ImportError:
    AUTO_SAVER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("表情包自动保存服务不可用")

logger = logging.getLogger(__name__)


class EnhancedQQImageHandler:
    """
    增强版QQ图片处理器
    使用多模型图片分析系统，支持自动故障转移
    """
    
    def __init__(self, qq_net):
        self.qq_net = qq_net
        self.image_cache = {}
        self.cache_expire_hours = 24
        
        # HTTP客户端（用于下载图片）
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # 多模型分析器
        self.multi_model_enabled = MULTI_MODEL_AVAILABLE
        self.vision_analyzer = None
        
        # 表情包自动保存服务
        self.auto_saver = None
        self._init_auto_saver()
        
        if self.multi_model_enabled:
            logger.info("[EnhancedQQImageHandler] 初始化完成 - 使用多模型图片分析系统")
        else:
            logger.warning("[EnhancedQQImageHandler] 初始化完成 - 多模型系统不可用，将使用简化模式")
    
    async def initialize(self):
        """初始化多模型分析器"""
        if self.multi_model_enabled and self.vision_analyzer is None:
            try:
                self.vision_analyzer = await get_vision_analyzer()
                stats = self.vision_analyzer.get_stats()
                logger.info(f"[EnhancedQQImageHandler] 多模型系统已初始化，{stats['enabled_models']} 个模型可用")
            except Exception as e:
                logger.error(f"[EnhancedQQImageHandler] 多模型系统初始化失败: {e}")
                self.multi_model_enabled = False
    
    def _init_auto_saver(self):
        """初始化表情包自动保存服务"""
        if AUTO_SAVER_AVAILABLE:
            try:
                self.auto_saver = get_auto_emoji_saver()
                logger.info("[EnhancedQQImageHandler] 表情包自动保存服务已初始化")
            except Exception as e:
                logger.error(f"[EnhancedQQImageHandler] 初始化表情包自动保存服务失败: {e}")
                self.auto_saver = None
        else:
            logger.warning("[EnhancedQQImageHandler] 表情包自动保存服务不可用")
            self.auto_saver = None
    
    def configure(self, enable_ocr: bool = False, enable_ai_analysis: bool = True):
        """配置处理器"""
        if self.multi_model_enabled:
            logger.info("[EnhancedQQImageHandler] 配置完成 - 使用多模型分析系统（自动故障转移）")
        else:
            logger.warning("[EnhancedQQImageHandler] 配置完成 - 使用简化模式（无多模型支持）")
    
    async def handle_image_message(self, event: Dict) -> Optional[QQMessage]:
        """处理图片消息"""
        try:
            # 确保多模型系统已初始化
            if self.multi_model_enabled and self.vision_analyzer is None:
                await self.initialize()
            
            # 提取图片信息
            image_info = self._extract_image_info(event)
            if not image_info:
                logger.warning("[EnhancedQQImageHandler] 无法提取图片信息")
                return None
            
            # 下载图片
            image_data = await self._download_image(image_info)
            if not image_data:
                logger.warning("[EnhancedQQImageHandler] 图片下载失败")
                return None
            
            # 【新增】尝试自动保存用户发送的表情包
            await self._try_auto_save_user_emoji(event, image_data, image_info)
            
            # 分析图片
            analysis_result = await self._analyze_image(image_data)
            
            # 构建回复消息
            if analysis_result.success:
                return self._create_response_message(event, analysis_result)
            else:
                logger.error(f"[EnhancedQQImageHandler] 图片分析失败: {analysis_result.error_message}")
                return self._create_error_message(event, analysis_result.error_message)
                
        except Exception as e:
            logger.error(f"[EnhancedQQImageHandler] 处理图片消息异常: {e}")
            return None
    
    async def _try_auto_save_user_emoji(self, event: Dict, image_data: bytes, image_info: Dict) -> None:
        """
        尝试自动保存用户发送的表情包
        
        Args:
            event: 原始事件数据
            image_data: 图片数据
            image_info: 图片信息
        """
        try:
            # 检查自动保存服务是否可用
            if not self.auto_saver:
                logger.debug("[EnhancedQQImageHandler] 自动保存服务不可用，跳过保存")
                return
            
            # 检查是否是用户发送的图片（不是机器人自己发送的）
            sender_id = event.get('sender', {}).get('user_id', 0)
            if sender_id == 0:
                logger.warning("[EnhancedQQImageHandler] 无法获取发送者ID，跳过保存")
                return
            
            # 检查是否@机器人或者私聊（可选，这里保存所有用户发送的图片）
            # 可以根据需要添加更复杂的逻辑
            
            logger.info(f"[EnhancedQQImageHandler] 尝试自动保存用户 {sender_id} 发送的表情包")
            
            # 调用自动保存服务
            save_result = await self.auto_saver.auto_save_emoji(
                user_id=sender_id,
                image_data=image_data,
                image_info=image_info
            )
            
            if save_result['success']:
                logger.info(f"[EnhancedQQImageHandler] 表情包自动保存成功: {save_result.get('filename', 'unknown')}")
                
                # 检查是否需要发送成功通知
                notifications_config = self.auto_saver.config.get('notifications', {})
                if notifications_config.get('on_save_success', True):
                    # 这里可以添加发送通知的逻辑
                    # 例如：self._send_save_notification(event, save_result)
                    logger.debug(f"[EnhancedQQImageHandler] 保存成功消息: {save_result['message']}")
            else:
                logger.info(f"[EnhancedQQImageHandler] 表情包自动保存跳过: {save_result['message']}")
                
                # 检查是否需要发送失败通知（通常不发送，避免骚扰）
                notifications_config = self.auto_saver.config.get('notifications', {})
                if notifications_config.get('on_save_fail', False):
                    logger.debug(f"[EnhancedQQImageHandler] 保存失败消息: {save_result['message']}")
                    
        except Exception as e:
            logger.error(f"[EnhancedQQImageHandler] 自动保存表情包异常: {e}", exc_info=True)
            # 不抛出异常，避免影响正常的图片处理流程
    
    async def _analyze_image(self, image_data: bytes) -> ImageAnalysisResult:
        """分析图片（使用多模型系统）"""
        try:
            if self.multi_model_enabled and self.vision_analyzer:
                # 使用多模型系统
                return await analyze_image_multi_model(image_data, max_retries=2)
            else:
                # 回退到简单分析
                return self._simple_image_analysis(image_data)
                
        except Exception as e:
            logger.error(f"[EnhancedQQImageHandler] 图片分析异常: {e}")
            # 返回简单分析结果
            return self._simple_image_analysis(image_data)
    
    def _simple_image_analysis(self, image_data: bytes) -> ImageAnalysisResult:
        """简单图片分析（无API）"""
        from core.multi_vision_analyzer import ImageAnalysisResult
        
        image_format = self._detect_image_format(image_data)
        size_kb = len(image_data) / 1024
        
        # 根据图片格式生成简单描述
        format_descriptions = {
            "jpeg": "这是一张JPEG格式的图片",
            "png": "这是一张PNG格式的图片", 
            "gif": "这是一张GIF动图",
            "bmp": "这是一张BMP格式的图片",
            "webp": "这是一张WebP格式的图片"
        }
        
        description = format_descriptions.get(image_format, "这是一张图片")
        description += f"，大小约为 {size_kb:.1f}KB。"
        
        # 根据大小猜测内容
        if size_kb > 500:
            description += " 图片较大，可能包含丰富的细节。"
        elif size_kb < 50:
            description += " 图片较小，可能是一个简单的图标或表情。"
        
        return ImageAnalysisResult(
            success=True,
            description=description,
            labels=["图片", "视觉内容", image_format.upper()],
            nsfw_score=0.0,
            has_text=False,
            text="",
            text_confidence=0.0,
            size_kb=size_kb,
            format=image_format,
            model_used="简单分析",
            provider="local",
            confidence=0.3,
            error_message="",
            processing_time_ms=0.0
        )
    
    def _extract_image_info(self, event: Dict) -> Optional[Dict]:
        """提取图片信息"""
        try:
            message = event.get("message", [])
            for segment in message:
                if isinstance(segment, dict) and segment.get("type") == "image":
                    data = segment.get("data", {})
                    return {
                        "url": data.get("url", ""),
                        "file": data.get("file", ""),
                        "file_size": int(data.get("file_size", 0)) if data.get("file_size") else 0,
                        "sub_type": data.get("sub_type", 0)
                    }
            return None
        except Exception as e:
            logger.error(f"[EnhancedQQImageHandler] 提取图片信息失败: {e}")
            return None
    
    async def _download_image(self, image_info: Dict) -> Optional[bytes]:
        """下载图片"""
        try:
            url = image_info.get("url", "")
            if not url:
                logger.warning("[EnhancedQQImageHandler] 图片URL为空")
                return None
            
            # 检查缓存
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.image_cache:
                cached_data = self.image_cache[cache_key]
                # 检查缓存是否过期
                if (datetime.now() - cached_data["timestamp"]).total_seconds() < self.cache_expire_hours * 3600:
                    logger.info("[EnhancedQQImageHandler] 使用缓存图片")
                    return cached_data["data"]
            
            # 下载图片
            logger.info(f"[EnhancedQQImageHandler] 下载图片: {url[:50]}...")
            response = await self.http_client.get(url, timeout=30.0)
            
            if response.status_code == 200:
                image_data = response.content
                
                # 缓存图片
                self._cache_image(cache_key, image_data)
                
                return image_data
            else:
                logger.error(f"[EnhancedQQImageHandler] 下载图片失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[EnhancedQQImageHandler] 下载图片异常: {e}")
            return None
    
    def _detect_image_format(self, image_data: bytes) -> str:
        """检测图片格式"""
        if len(image_data) < 8:
            return "unknown"
        
        if image_data.startswith(b'\xFF\xD8\xFF'):
            return "jpeg"
        elif image_data.startswith(b'\x89PNG\r\n\x1A\n'):
            return "png"
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return "gif"
        elif image_data.startswith(b'BM'):
            return "bmp"
        elif image_data.startswith(b'RIFF') and image_data[8:12] == b'WEBP':
            return "webp"
        else:
            return "unknown"
    
    def _cache_image(self, image_id: str, image_data: bytes):
        """缓存图片"""
        self.image_cache[image_id] = {
            "data": image_data,
            "timestamp": datetime.now()
        }
        
        # 清理过期缓存
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, data in self.image_cache.items():
            if (current_time - data["timestamp"]).total_seconds() > self.cache_expire_hours * 3600:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.image_cache[key]
        
        if expired_keys:
            logger.info(f"[EnhancedQQImageHandler] 清理了 {len(expired_keys)} 个过期缓存")
    
    def _create_response_message(self, event: Dict, analysis_result: ImageAnalysisResult) -> QQMessage:
        """创建回复消息（弥娅风格）"""
        from .models import QQMessage
        
        # 获取发送者ID，用于个性化回复
        sender_id = event.get("sender", {}).get("user_id", 0)
        
        # 弥娅风格的问候语（根据时间不同）
        from datetime import datetime
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "早上好呀~"
        elif 12 <= current_hour < 18:
            greeting = "下午好哦~"
        elif 18 <= current_hour < 22:
            greeting = "晚上好~"
        else:
            greeting = "夜深了~"
        
        # 构建弥娅风格的回复文本
        response_text = f"{greeting} 我看到你发来的图片啦！(｡♥‿♥｡)\n\n"
        
        # 分析结果（用弥娅的口吻表达）
        description = analysis_result.description
        
        # 如果是简单分析，添加一些亲切的表达
        if analysis_result.model_used == "简单分析":
            response_text += f"虽然暂时没法详细分析这张图片，但看起来是一张{analysis_result.format.upper()}格式的图片呢~\n"
            response_text += f"大小约{analysis_result.size_kb:.1f}KB，应该是个{self._get_size_description(analysis_result.size_kb)}的图片哦！"
        else:
            # 用更亲切的方式转述分析结果
            response_text += f"让我看看这张图片... 哇！这是一张很棒的图片呢！\n\n"
            
            # 改进描述的表达方式
            description_lines = description.split('。')
            if description_lines:
                first_line = description_lines[0].strip()
                if first_line:
                    response_text += f"👀 我看到了：{first_line}。"
                    
                    if len(description_lines) > 1:
                        second_line = description_lines[1].strip()
                        if second_line:
                            response_text += f" 还有呢，{second_line}。"
            
            # 添加弥娅的个人感想
            response_text += self._add_miya_feeling(analysis_result.labels)
        
        # 标签信息（用更可爱的表达）
        if analysis_result.labels and analysis_result.model_used != "简单分析":
            labels_text = "、".join(analysis_result.labels)
            response_text += f"\n\n🏷️ 我给这张图片贴了这些标签：{labels_text}"
        
        # 技术信息（用轻松的语气）
        if analysis_result.model_used != "简单分析":
            response_text += f"\n\n💾 图片信息：{analysis_result.format.upper()}格式，{analysis_result.size_kb:.1f}KB"
            response_text += f"\n🤖 分析工具：{analysis_result.model_used}"
            
            if analysis_result.processing_time_ms > 0:
                response_text += f"（花了{analysis_result.processing_time_ms:.0f}毫秒来分析呢~）"
        
        # 根据置信度添加不同的弥娅风格提示
        if analysis_result.confidence < 0.5:
            response_text += "\n\n✨ 小提示：这个分析结果可能不太准确哦，仅供参考啦~"
        elif analysis_result.confidence < 0.7:
            response_text += "\n\n✨ 小提示：分析结果大致正确，但可能有细微差别呢~"
        else:
            response_text += "\n\n✨ 小提示：分析结果很可靠哦！相信我的眼光吧~"
        
        # 结尾的亲切问候
        response_text += "\n\n😊 还有什么想让我看的图片吗？我随时准备好啦！"
        
        # 创建消息对象
        group_id = event.get("group_id", 0) if event.get("message_type") == "group" else 0
        message_type = event.get("message_type", "private")
        
        # 设置正确的user_id：对于私聊消息，user_id应该是发送者
        # 对于群消息，user_id应该是发送者（如果要@回复的话）
        user_id = sender_id
        
        return QQMessage(
            message=response_text,
            user_id=user_id,
            sender_id=sender_id,
            group_id=group_id,
            message_type=message_type
        )
    
    def _get_size_description(self, size_kb: float) -> str:
        """根据图片大小返回描述"""
        if size_kb < 50:
            return "小巧精致"
        elif size_kb < 200:
            return "适中可爱"
        elif size_kb < 500:
            return "内容丰富"
        else:
            return "细节满满"
    
    def _add_miya_feeling(self, labels: List[str]) -> str:
        """根据标签添加弥娅的个人感想"""
        if not labels:
            return ""
        
        feelings = []
        
        # 根据标签添加不同的感想
        if "人物" in labels:
            feelings.append("里面的人物看起来很有故事呢~")
        if "自然" in labels:
            feelings.append("大自然的色彩总是让人心情愉悦~")
        if "动物" in labels:
            feelings.append("小动物们总是那么可爱！")
        if "食物" in labels:
            feelings.append("看起来好美味呀！")
        if "建筑" in labels:
            feelings.append("建筑的风格很有特色呢~")
        if "艺术" in labels:
            feelings.append("很有艺术感的设计！")
        
        if feelings:
            return "\n\n" + " ".join(feelings[:2])  # 最多添加两个感想
        return ""
    
    def _create_error_message(self, event: Dict, error_message: str) -> QQMessage:
        """创建错误消息"""
        from .models import QQMessage
        
        response_text = f"❌ 图片分析失败\n\n"
        response_text += f"原因：{error_message}\n\n"
        response_text += "请稍后再试，或者发送其他图片。"
        
        sender_id = event.get("sender", {}).get("user_id", 0)
        group_id = event.get("group_id", 0) if event.get("message_type") == "group" else 0
        message_type = event.get("message_type", "private")
        
        # 设置正确的user_id：对于私聊消息，user_id应该是发送者
        # 对于群消息，user_id应该是发送者（如果要@回复的话）
        user_id = sender_id
        
        return QQMessage(
            message=response_text,
            user_id=user_id,
            sender_id=sender_id,
            group_id=group_id,
            message_type=message_type
        )
    
    async def close(self):
        """关闭资源"""
        await self.http_client.aclose()
        logger.info("[EnhancedQQImageHandler] 已关闭")


# 兼容性包装器
class QQImageHandler(EnhancedQQImageHandler):
    """
    兼容性包装器
    保持原有接口，但使用增强版实现
    """
    def __init__(self, qq_net):
        super().__init__(qq_net)
        logger.info("[QQImageHandler] 初始化完成 - 使用增强版多模型系统")