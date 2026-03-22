"""
简化版QQ图片处理器
仅使用智谱GLM-4.6V-Flash视觉模型API
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
from typing import Any, Dict, Optional

from .models import QQMessage

logger = logging.getLogger(__name__)


class QQImageHandler:
    """简化版QQ图片处理器 - 仅使用视觉模型API"""
    
    def __init__(self, qq_net):
        self.qq_net = qq_net
        # 注释: 图片分析结果缓存已迁移到QQCacheManager
        # 旧实现: self.image_cache = {}, cache_expire_hours = 24
        # 新实现: 使用 qq_net.cache_manager.set_image_analysis() 和 get_image_analysis()
        
        # HTTP客户端
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("[QQImageHandler] 初始化完成 - 仅使用智谱GLM-4.6V-Flash视觉模型")
    
    def configure(self, enable_ocr: bool = False, enable_ai_analysis: bool = True):
        """配置处理器 - 仅支持视觉模型"""
        logger.info("[QQImageHandler] 配置完成 - 使用GLM-4.6V-Flash视觉模型")
    
    async def handle_image_message(self, event: Dict) -> Optional[QQMessage]:
        """处理图片消息"""
        try:
            # 提取图片信息
            image_info = self._extract_image_info(event)
            if not image_info:
                logger.warning("[QQImageHandler] 无法提取图片信息")
                return None
            
            # 下载图片
            image_data = await self._download_image(image_info)
            if not image_data:
                logger.warning("[QQImageHandler] 图片下载失败")
                return None
            
            # 计算图片ID用于缓存
            image_id = hashlib.md5(image_data).hexdigest()
            
            # 使用视觉模型分析图片
            analysis_result = await self._analyze_with_vision_model(image_data)
            
            # 缓存分析结果到QQCacheManager
            self._cache_image(image_id, analysis_result)
            
            # 构建增强的消息对象
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
            # 如果是本地文件
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
            
            # 如果是网络URL
            if url:
                response = await self.http_client.get(url)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"[QQImageHandler] 下载图片失败: HTTP {response.status_code}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"[QQImageHandler] 下载图片失败: {e}")
            return None
    
    async def _analyze_with_vision_model(self, image_data: bytes) -> Dict[str, Any]:
        """使用视觉模型分析图片"""
        try:
            # 设置智谱API环境
            api_key = os.getenv('ZHIPU_API_KEY', '')
            if not api_key:
                logger.error("[QQImageHandler] 智谱API密钥未设置")
                return self._create_empty_result()
            
            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 调用智谱GLM-4.6V-Flash API
            result = await self._call_zhipu_vision_api(api_key, image_base64)
            
            return {
                "success": True,
                "has_text": False,
                "text": "",
                "text_confidence": 0.0,
                "description": result.get("description", ""),
                "labels": result.get("labels", []),
                "nsfw_score": result.get("nsfw_score", 0.0),
                "size_kb": len(image_data) / 1024,
                "format": self._detect_image_format(image_data),
                "model": "glm-4.6v-flash",
                "provider": "zhipu",
                "api_call": True
            }
            
        except Exception as e:
            logger.error(f"[QQImageHandler] 视觉模型分析失败: {e}")
            return self._create_empty_result()
    
    async def _call_zhipu_vision_api(self, api_key: str, image_base64: str) -> Dict[str, Any]:
        """调用智谱视觉API"""
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "glm-4.6v-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请详细描述这张图片的内容，包括场景、物体、颜色、文字等所有你能看到的信息。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        try:
            response = await self.http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 简单提取标签
                labels = self._extract_labels_from_description(content)
                
                return {
                    "description": content,
                    "labels": labels,
                    "nsfw_score": 0.0,
                    "confidence": 0.8
                }
            elif response.status_code == 429:
                # 限流错误，返回友好的错误消息
                logger.warning(f"[QQImageHandler] 智谱API限流，返回备选分析")
                return {
                    "description": "图片已收到，但智谱视觉模型当前访问量过大，暂时无法详细分析。这是一个通用图片，包含视觉元素。",
                    "labels": ["图片", "视觉内容"],
                    "nsfw_score": 0.0,
                    "confidence": 0.3
                }
            else:
                logger.error(f"[QQImageHandler] 智谱API调用失败: {response.status_code}, {response.text}")
                return {
                    "description": f"图片分析服务暂时不可用（HTTP {response.status_code}）",
                    "labels": ["服务不可用"],
                    "nsfw_score": 0.0,
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"[QQImageHandler] 智谱API调用异常: {e}")
            return {
                "description": f"API调用异常: {str(e)}",
                "labels": ["网络错误"],
                "nsfw_score": 0.0,
                "confidence": 0.0
            }
    
    def _extract_labels_from_description(self, description: str) -> list:
        """从描述中提取标签"""
        labels = []
        
        # 简单关键词匹配
        keywords = {
            "人物": ["人", "人脸", "肖像", "表情", "动作", "人物"],
            "自然": ["风景", "山水", "树木", "花草", "天空", "海洋", "自然"],
            "建筑": ["建筑", "房屋", "大楼", "桥梁", "道路", "建筑"],
            "动物": ["动物", "宠物", "鸟类", "鱼类", "昆虫", "动物"],
            "文字": ["文字", "文本", "文字内容", "文档", "截图", "文字"],
            "食物": ["食物", "餐饮", "水果", "蔬菜", "饮料", "食物"],
            "车辆": ["车辆", "汽车", "飞机", "船只", "交通", "车辆"],
            "电子": ["电子", "设备", "屏幕", "界面", "科技", "电子"]
        }
        
        description_lower = description.lower()
        
        for category, words in keywords.items():
            for word in words:
                if word in description_lower:
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
    
    def _cache_image(self, image_id: str, image_analysis: Dict[str, Any]):
        """缓存图片分析结果到QQCacheManager
        
        注意: 本方法现在缓存分析结果而非原始图片数据
        旧实现将原始图片数据存储在内存中 (低效)
        新实现只缓存分析结果 (高效)
        """
        try:
            self.qq_net.cache_manager.set_image_analysis(
                image_id,
                image_analysis
            )
        except Exception as e:
            logger.warning(f"[QQImageHandler] 缓存分析结果失败: {e}")
    
    # 已删除 _cleanup_cache() 方法
    # 原因: 缓存过期管理已由QQCacheManager自动处理
    # 旧实现需要手动检查并删除过期项
    # 新实现由cache_manager统一处理，更高效且正确
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """创建空结果"""
        return {
            "success": False,
            "has_text": False,
            "text": "",
            "text_confidence": 0.0,
            "description": "分析失败",
            "labels": [],
            "nsfw_score": 0.0,
            "size_kb": 0,
            "format": "unknown",
            "model": "none",
            "provider": "none",
            "api_call": False
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.http_client.aclose()
        except:
            pass