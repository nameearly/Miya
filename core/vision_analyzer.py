"""
视觉分析器

使用模型池中的视觉模型进行图片分析
支持智谱GLM-4.6V-Flash等免费模型
"""

import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional, List
import httpx

from .model_pool import get_model_pool, ModelConfig

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """视觉分析器"""
    
    def __init__(self):
        self.model_pool = get_model_pool()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.cache = {}
        
        logger.info("[VisionAnalyzer] 视觉分析器初始化完成")
    
    async def analyze_image(self, image_data: bytes, task_type: str = "image_description") -> Dict[str, Any]:
        """
        分析图片
        
        Args:
            image_data: 图片二进制数据
            task_type: 任务类型，默认为"image_description"
            
        Returns:
            分析结果
        """
        try:
            # 选择模型（优先选择免费模型）
            model_config = self._select_model_for_task(task_type)
            if not model_config:
                logger.error("[VisionAnalyzer] 未找到合适的视觉模型")
                return self._create_error_result("未找到合适的视觉模型")
            
            logger.info(f"[VisionAnalyzer] 使用模型分析图片: {model_config.id} ({model_config.provider})")
            
            # 根据模型提供商调用对应的API
            result = await self._call_vision_api(model_config, image_data, task_type)
            
            # 添加模型信息
            result["model"] = {
                "id": model_config.id,
                "name": model_config.name,
                "provider": str(model_config.provider),
                "cost_per_1k_tokens": model_config.cost_per_1k_tokens,
                "description": model_config.description
            }
            
            return result
            
        except Exception as e:
            logger.error(f"[VisionAnalyzer] 图片分析失败: {e}", exc_info=True)
            return self._create_error_result(f"分析失败: {str(e)}")
    
    def _select_model_for_task(self, task_type: str) -> Optional[ModelConfig]:
        """选择模型"""
        try:
            # 获取模型池中的所有视觉模型
            all_models = self.model_pool.list_all_models()
            
            # 筛选视觉模型
            vision_models = []
            for model in all_models:
                if hasattr(model, 'type') and model.type == 'vision':
                    vision_models.append(model)
            
            if not vision_models:
                logger.warning("[VisionAnalyzer] 未找到视觉模型")
                return None
            
            # 根据任务类型和成本优先选择
            sorted_models = sorted(
                vision_models,
                key=lambda m: (
                    # 优先选择免费模型
                    0 if hasattr(m, 'cost_per_1k_tokens') and m.cost_per_1k_tokens.get('input', 1) == 0 else 1,
                    # 其次根据优先级排序
                    -getattr(m, 'priority', 0) if hasattr(m, 'priority') else 0,
                    # 最后根据成本排序
                    getattr(m, 'cost_per_1k_tokens', {}).get('input', 0)
                )
            )
            
            # 尝试选择前3个模型
            for model in sorted_models[:3]:
                try:
                    # 检查模型是否有API密钥
                    if not self._check_model_availability(model):
                        continue
                    
                    logger.info(f"[VisionAnalyzer] 选择模型: {model.id}")
                    return model
                    
                except Exception as e:
                    logger.warning(f"[VisionAnalyzer] 模型 {model.id} 不可用: {e}")
                    continue
            
            logger.warning("[VisionAnalyzer] 所有视觉模型都不可用")
            return None
            
        except Exception as e:
            logger.error(f"[VisionAnalyzer] 选择模型失败: {e}")
            return None
    
    def _check_model_availability(self, model_config: ModelConfig) -> bool:
        """检查模型是否可用"""
        try:
            # 检查是否有API密钥
            if hasattr(model_config, 'api_key'):
                api_key = model_config.api_key
                if not api_key or api_key.startswith("${") or "example" in api_key.lower():
                    return False
            
            # 检查是否有基础URL
            if hasattr(model_config, 'base_url'):
                base_url = model_config.base_url
                if not base_url or base_url.startswith("${"):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"[VisionAnalyzer] 检查模型可用性失败: {e}")
            return False
    
    async def _call_vision_api(
        self, 
        model_config: ModelConfig, 
        image_data: bytes,
        task_type: str
    ) -> Dict[str, Any]:
        """调用视觉API"""
        provider = str(model_config.provider).lower()
        
        if provider == "zhipu":
            return await self._call_zhipu_api(model_config, image_data, task_type)
        elif provider in ["openai", "siliconflow"]:
            return await self._call_openai_compatible_api(model_config, image_data, task_type)
        elif provider == "local":
            return await self._call_local_analysis(image_data, task_type)
        else:
            logger.warning(f"[VisionAnalyzer] 不支持的模型提供商: {provider}")
            return self._create_error_result(f"不支持的模型提供商: {provider}")
    
    async def _call_zhipu_api(
        self, 
        model_config: ModelConfig, 
        image_data: bytes,
        task_type: str
    ) -> Dict[str, Any]:
        """调用智谱AI API"""
        try:
            # 获取API配置
            api_key = model_config.api_key
            base_url = model_config.base_url
            model_name = model_config.name
            
            # 构建请求
            url = f"{base_url}/chat/completions"
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._get_prompt_for_task(task_type)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
                            }
                        }
                    ]
                }
            ]
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": 500
            }
            
            # 发送请求
            logger.info(f"[VisionAnalyzer] 调用智谱API: {model_name}")
            response = await self.http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # 解析结果
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = result.get("usage", {})
                
                return {
                    "success": True,
                    "description": content,
                    "labels": self._extract_labels_from_description(content),
                    "confidence": 0.8,  # 默认置信度
                    "nsfw_score": 0.0,  # 智谱API没有NSFW检测
                    "usage": usage,
                    "raw_response": result
                }
            else:
                logger.error(f"[VisionAnalyzer] 智谱API调用失败: {response.status_code}, {response.text}")
                return self._create_error_result(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[VisionAnalyzer] 智谱API调用异常: {e}", exc_info=True)
            return self._create_error_result(f"API调用异常: {str(e)}")
    
    async def _call_openai_compatible_api(
        self, 
        model_config: ModelConfig, 
        image_data: bytes,
        task_type: str
    ) -> Dict[str, Any]:
        """调用OpenAI兼容API"""
        try:
            # 获取API配置
            api_key = model_config.api_key
            base_url = model_config.base_url
            model_name = model_config.name
            
            # 构建请求
            url = f"{base_url}/chat/completions"
            
            # 构建消息（OpenAI格式）
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._get_prompt_for_task(task_type)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
                            }
                        }
                    ]
                }
            ]
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": 500
            }
            
            # 发送请求
            logger.info(f"[VisionAnalyzer] 调用OpenAI兼容API: {model_name}")
            response = await self.http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # 解析结果
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = result.get("usage", {})
                
                return {
                    "success": True,
                    "description": content,
                    "labels": self._extract_labels_from_description(content),
                    "confidence": 0.8,
                    "nsfw_score": 0.0,
                    "usage": usage,
                    "raw_response": result
                }
            else:
                logger.error(f"[VisionAnalyzer] OpenAI兼容API调用失败: {response.status_code}, {response.text}")
                return self._create_error_result(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[VisionAnalyzer] OpenAI兼容API调用异常: {e}", exc_info=True)
            return self._create_error_result(f"API调用异常: {str(e)}")
    
    async def _call_local_analysis(self, image_data: bytes, task_type: str) -> Dict[str, Any]:
        """本地分析（备用方案）"""
        try:
            # 使用PIL进行简单分析
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # 简单分析
            description = f"这是一张{width}x{height}像素的图片。"
            
            # 尝试检测图片类型
            if width > height:
                orientation = "横向"
            else:
                orientation = "纵向"
            
            description += f" 图片为{orientation}。"
            
            # 检测图片亮度
            try:
                grayscale = image.convert('L')
                histogram = grayscale.histogram()
                brightness = sum(i * hist for i, hist in enumerate(histogram)) / sum(histogram)
                
                if brightness > 150:
                    description += " 图片较亮。"
                elif brightness < 100:
                    description += " 图片较暗。"
                else:
                    description += " 图片亮度适中。"
            except:
                pass
            
            return {
                "success": True,
                "description": description,
                "labels": ["本地分析", f"{width}x{height}", orientation],
                "confidence": 0.5,
                "nsfw_score": 0.0,
                "usage": {},
                "raw_response": {}
            }
            
        except Exception as e:
            logger.error(f"[VisionAnalyzer] 本地分析失败: {e}")
            return self._create_error_result(f"本地分析失败: {str(e)}")
    
    def _get_prompt_for_task(self, task_type: str) -> str:
        """根据任务类型获取提示词"""
        prompts = {
            "image_description": "请详细描述这张图片的内容。",
            "visual_qa": "请分析这张图片并回答相关问题。",
            "document_understanding": "请识别并分析这张图片中的文档内容。",
            "image_analysis": "请全面分析这张图片，包括内容、风格、情绪等。",
            "text_extraction": "请提取图片中的所有文字内容。",
            "object_detection": "请识别图片中的所有物体和场景。"
        }
        
        return prompts.get(task_type, "请分析这张图片。")
    
    def _extract_labels_from_description(self, description: str) -> List[str]:
        """从描述中提取标签"""
        # 简单实现：基于关键词提取标签
        keywords = {
            "文字": ["文字", "文本", "文字内容", "文档", "截图"],
            "人物": ["人", "人脸", "肖像", "表情", "动作"],
            "自然": ["风景", "山水", "树木", "花草", "天空", "海洋"],
            "建筑": ["建筑", "房屋", "大楼", "桥梁", "道路"],
            "动物": ["动物", "宠物", "鸟类", "鱼类", "昆虫"],
            "食物": ["食物", "餐饮", "水果", "蔬菜", "饮料"],
            "交通": ["车辆", "汽车", "飞机", "船只", "交通"],
            "科技": ["电子", "设备", "屏幕", "界面", "科技"]
        }
        
        labels = []
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
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "success": False,
            "error": error_message,
            "description": "",
            "labels": [],
            "confidence": 0.0,
            "nsfw_score": 0.0,
            "usage": {},
            "raw_response": {}
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.http_client.aclose()
        except:
            pass


# 全局实例
_vision_analyzer_instance = None

def get_vision_analyzer() -> VisionAnalyzer:
    """获取视觉分析器实例"""
    global _vision_analyzer_instance
    
    if _vision_analyzer_instance is None:
        try:
            _vision_analyzer_instance = VisionAnalyzer()
        except Exception as e:
            logger.error(f"[VisionAnalyzer] 初始化失败: {e}")
            # 返回一个模拟的视觉分析器
            _vision_analyzer_instance = MockVisionAnalyzer()
    
    return _vision_analyzer_instance


class MockVisionAnalyzer:
    """模拟视觉分析器（用于测试）"""
    
    def __init__(self):
        logger.warning("[VisionAnalyzer] 使用模拟视觉分析器")
    
    async def analyze_image(self, image_data: bytes, task_type: str = "image_description") -> Dict[str, Any]:
        """模拟分析图片"""
        await asyncio.sleep(0.1)  # 模拟延迟
        
        return {
            "success": True,
            "description": "这是一张图片的模拟分析结果。",
            "labels": ["模拟", "测试", "图片"],
            "confidence": 0.7,
            "nsfw_score": 0.05,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            },
            "model": {
                "id": "mock_vision_model",
                "name": "Mock Vision Model",
                "provider": "mock",
                "description": "模拟视觉模型"
            }
        }
    
    async def cleanup(self):
        """清理资源"""
        pass