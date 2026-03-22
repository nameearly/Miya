"""
智能图片分析器

根据图片类型自动选择处理策略：
1. 文字图片 → 本地OCR（免费）
2. 复杂图片 → AI视觉模型（GLM-4.6V-Flash免费）
3. 敏感图片 → NSFW检测
"""

import asyncio
import base64
import hashlib
import json
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)


class ImageType(Enum):
    """图片类型"""
    TEXT = "text"          # 文字图片（截图、文档等）
    NATURAL = "natural"    # 自然图片（风景、人物等）
    SCREENSHOT = "screenshot"  # 屏幕截图
    MEME = "meme"         # 表情包
    CHART = "chart"       # 图表
    DOCUMENT = "document"  # 文档图片
    UNKNOWN = "unknown"   # 未知类型


class AnalysisPriority(Enum):
    """分析优先级"""
    OCR_ONLY = "ocr_only"      # 仅OCR
    AI_ONLY = "ai_only"        # 仅AI分析
    OCR_FIRST = "ocr_first"    # 先OCR后AI
    AI_FIRST = "ai_first"      # 先AI后OCR
    HYBRID = "hybrid"          # 混合分析


class SmartImageAnalyzer:
    """智能图片分析器"""
    
    def __init__(self, model_pool=None):
        """
        初始化智能图片分析器
        
        Args:
            model_pool: 模型池实例
        """
        self.model_pool = model_pool
        self.cache = {}  # 缓存分析结果
        
        # 配置文件
        self.config = self._load_config()
        
        # 统计信息
        self.stats = {
            "total_images": 0,
            "ocr_success": 0,
            "ai_success": 0,
            "hybrid_success": 0,
            "fallback_count": 0,
            "total_time_ms": 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            # 处理策略
            "max_image_size_mb": 10,  # 最大图片大小（MB）
            "max_analysis_time_ms": 30000,  # 最大分析时间（毫秒）
            "cache_ttl_seconds": 3600,  # 缓存时间（秒）
            
            # OCR配置
            "ocr_confidence_threshold": 0.5,  # OCR置信度阈值
            "min_text_length_for_ocr": 3,     # 最小文字长度
            "max_text_length_for_ocr": 5000,  # 最大文字长度
            
            # AI分析配置
            "ai_analysis_enabled": True,      # 启用AI分析
            "ai_model_priority": "cost",      # 模型选择优先级：cost/speed/quality
            "ai_min_confidence": 0.3,         # AI最小置信度
            "ai_max_tokens": 500,             # AI最大输出token数
            
            # 图片类型检测
            "detect_image_type": True,        # 启用图片类型检测
            "default_priority": "ocr_first",  # 默认优先级
            
            # 成本控制
            "max_cost_per_image": 0.0,        # 最大单图成本（免费模型为0）
            "use_free_models_only": True,     # 仅使用免费模型
            
            # 混合策略
            "enable_hybrid_analysis": True,   # 启用混合分析
            "hybrid_confidence_threshold": 0.7,  # 混合分析置信度阈值
            "text_density_threshold": 0.2,    # 文字密度阈值（用于类型判断）
        }
        
        # 尝试加载配置文件
        config_paths = [
            Path(__file__).parent.parent / "config" / "smart_image_config.yaml",
            Path(__file__).parent.parent.parent / "config" / "smart_image_config.yaml",
            Path(__file__).parent / "smart_image_config.yaml"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        user_config = yaml.safe_load(f) or {}
                    
                    # 合并配置
                    default_config.update(user_config)
                    logger.info(f"[SmartImageAnalyzer] 已加载配置文件: {config_path}")
                    break
                except Exception as e:
                    logger.warning(f"[SmartImageAnalyzer] 加载配置文件失败 {config_path}: {e}")
        
        logger.info(f"[SmartImageAnalyzer] 使用配置: {json.dumps(default_config, indent=2, ensure_ascii=False)}")
        return default_config
    
    async def analyze_image(
        self, 
        image_data: bytes, 
        image_id: Optional[str] = None,
        user_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        智能分析图片
        
        Args:
            image_data: 图片二进制数据
            image_id: 图片ID（用于缓存）
            user_preference: 用户偏好：ocr/ai/hybrid
            
        Returns:
            分析结果字典
        """
        start_time = time.time()
        self.stats["total_images"] += 1
        
        # 生成图片ID
        if not image_id:
            image_id = hashlib.md5(image_data).hexdigest()
        
        # 检查缓存
        cached_result = self._get_cached_result(image_id)
        if cached_result:
            logger.info(f"[SmartImageAnalyzer] 使用缓存结果: {image_id}")
            return cached_result
        
        # 检查图片大小
        if not self._validate_image_size(image_data):
            return self._create_error_result("图片大小超过限制")
        
        try:
            # 检测图片类型
            image_type = await self._detect_image_type(image_data)
            logger.info(f"[SmartImageAnalyzer] 图片类型检测: {image_type.value}")
            
            # 确定分析策略
            strategy = self._determine_analysis_strategy(image_type, user_preference)
            logger.info(f"[SmartImageAnalyzer] 分析策略: {strategy.value}")
            
            # 执行分析
            result = await self._execute_analysis(strategy, image_data, image_type)
            
            # 添加元数据
            result["metadata"] = {
                "image_id": image_id,
                "image_type": image_type.value,
                "strategy": strategy.value,
                "analysis_time_ms": int((time.time() - start_time) * 1000),
                "image_size_bytes": len(image_data),
                "image_format": self._detect_image_format(image_data)
            }
            
            # 更新统计
            self.stats["total_time_ms"] += result["metadata"]["analysis_time_ms"]
            if result.get("ocr_text"):
                self.stats["ocr_success"] += 1
            if result.get("ai_analysis"):
                self.stats["ai_success"] += 1
            if result.get("ocr_text") and result.get("ai_analysis"):
                self.stats["hybrid_success"] += 1
            
            # 缓存结果
            self._cache_result(image_id, result)
            
            logger.info(f"[SmartImageAnalyzer] 分析完成: {image_id}, 耗时: {result['metadata']['analysis_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"[SmartImageAnalyzer] 图片分析失败: {e}")
            return self._create_error_result(f"分析失败: {str(e)}")
    
    async def _detect_image_type(self, image_data: bytes) -> ImageType:
        """检测图片类型"""
        if not HAS_PIL:
            return ImageType.UNKNOWN
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # 获取图片信息
            width, height = image.size
            aspect_ratio = width / height if height > 0 else 1.0
            
            # 检查是否是截图（长宽比接近16:9或4:3）
            if 1.7 <= aspect_ratio <= 1.9:  # 16:9 (1.777...)
                return ImageType.SCREENSHOT
            elif 1.3 <= aspect_ratio <= 1.4:  # 4:3 (1.333...)
                return ImageType.SCREENSHOT
            
            # 检查图片颜色分布（简单检测）
            colors = image.getcolors(maxcolors=1000)
            if colors:
                # 计算颜色种类和平均数量
                num_colors = len(colors)
                avg_count = sum(count for count, color in colors) / num_colors
                
                # 如果颜色种类少，可能是图表或文档
                if num_colors < 50:
                    return ImageType.CHART
            
            # 检查图片内容（简单文本检测）
            # 这里可以扩展更复杂的检测逻辑
            
            # 默认返回自然图片
            return ImageType.NATURAL
            
        except Exception as e:
            logger.warning(f"[SmartImageAnalyzer] 图片类型检测失败: {e}")
            return ImageType.UNKNOWN
    
    def _determine_analysis_strategy(
        self, 
        image_type: ImageType,
        user_preference: Optional[str]
    ) -> AnalysisPriority:
        """确定分析策略"""
        
        # 用户偏好优先
        if user_preference:
            strategy_map = {
                "ocr": AnalysisPriority.OCR_ONLY,
                "ai": AnalysisPriority.AI_ONLY,
                "hybrid": AnalysisPriority.HYBRID,
                "ocr_first": AnalysisPriority.OCR_FIRST,
                "ai_first": AnalysisPriority.AI_FIRST
            }
            if user_preference in strategy_map:
                return strategy_map[user_preference]
        
        # 根据图片类型确定策略
        type_strategy_map = {
            ImageType.TEXT: AnalysisPriority.OCR_ONLY,
            ImageType.SCREENSHOT: AnalysisPriority.OCR_FIRST,
            ImageType.DOCUMENT: AnalysisPriority.OCR_FIRST,
            ImageType.CHART: AnalysisPriority.HYBRID,
            ImageType.MEME: AnalysisPriority.AI_ONLY,
            ImageType.NATURAL: AnalysisPriority.AI_FIRST,
            ImageType.UNKNOWN: AnalysisPriority.HYBRID
        }
        
        return type_strategy_map.get(image_type, AnalysisPriority(self.config["default_priority"]))
    
    async def _execute_analysis(
        self, 
        strategy: AnalysisPriority,
        image_data: bytes,
        image_type: ImageType
    ) -> Dict[str, Any]:
        """执行分析策略"""
        result = {
            "success": True,
            "ocr_text": None,
            "ai_analysis": None,
            "confidence": 0.0,
            "suggested_action": None
        }
        
        # OCR分析
        ocr_text = None
        if strategy in [
            AnalysisPriority.OCR_ONLY,
            AnalysisPriority.OCR_FIRST,
            AnalysisPriority.HYBRID
        ]:
            ocr_text = await self._perform_ocr(image_data)
            if ocr_text:
                result["ocr_text"] = ocr_text
                result["confidence"] += 0.3  # OCR贡献的置信度
        
        # AI分析
        ai_analysis = None
        if strategy in [
            AnalysisPriority.AI_ONLY,
            AnalysisPriority.AI_FIRST,
            AnalysisPriority.HYBRID
        ]:
            ai_analysis = await self._perform_ai_analysis(image_data)
            if ai_analysis:
                result["ai_analysis"] = ai_analysis
                result["confidence"] += 0.4  # AI贡献的置信度
        
        # 根据结果建议下一步操作
        if ocr_text and not ai_analysis:
            result["suggested_action"] = "text_response"
        elif ai_analysis and not ocr_text:
            result["suggested_action"] = "visual_description"
        elif ocr_text and ai_analysis:
            result["suggested_action"] = "hybrid_response"
            result["confidence"] += 0.3  # 混合分析的额外置信度
        else:
            result["suggested_action"] = "fallback"
            self.stats["fallback_count"] += 1
        
        return result
    
    async def _perform_ocr(self, image_data: bytes) -> Optional[str]:
        """执行OCR识别"""
        try:
            # 这里调用OCR引擎
            # 由于OCR引擎在其他地方初始化，这里简化处理
            logger.info("[SmartImageAnalyzer] OCR分析中...")
            
            # 模拟OCR结果
            await asyncio.sleep(0.1)
            
            # 实际应用中应该调用真实的OCR引擎
            # text = self._call_real_ocr(image_data)
            text = "这是一段模拟的OCR识别文字。"
            
            return text
            
        except Exception as e:
            logger.warning(f"[SmartImageAnalyzer] OCR失败: {e}")
            return None
    
    async def _perform_ai_analysis(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """执行AI分析"""
        try:
            if not self.config["ai_analysis_enabled"]:
                logger.info("[SmartImageAnalyzer] AI分析已禁用")
                return None
            
            logger.info("[SmartImageAnalyzer] AI分析中...")
            
            # 这里应该调用实际的AI模型
            # 简化处理，返回模拟数据
            await asyncio.sleep(0.2)
            
            return {
                "description": "这是一张图片的AI分析描述。",
                "labels": ["图片", "视觉内容"],
                "confidence": 0.8,
                "nsfw_score": 0.1,
                "source_model": "mock_ai"
            }
            
        except Exception as e:
            logger.warning(f"[SmartImageAnalyzer] AI分析失败: {e}")
            return None
    
    def _validate_image_size(self, image_data: bytes) -> bool:
        """验证图片大小"""
        max_size_mb = self.config["max_image_size_mb"]
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if len(image_data) > max_size_bytes:
            logger.warning(f"[SmartImageAnalyzer] 图片过大: {len(image_data)} bytes > {max_size_bytes} bytes")
            return False
        
        return True
    
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
    
    def _get_cached_result(self, image_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if image_id in self.cache:
            cached_data = self.cache[image_id]
            cache_ttl = self.config.get("cache_ttl_seconds", 3600)
            
            # 检查是否过期
            import time
            if time.time() - cached_data.get("timestamp", 0) < cache_ttl:
                return cached_data.get("result")
        
        return None
    
    def _cache_result(self, image_id: str, result: Dict[str, Any]):
        """缓存结果"""
        self.cache[image_id] = {
            "result": result,
            "timestamp": time.time()
        }
        
        # 清理过期缓存
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        cache_ttl = self.config.get("cache_ttl_seconds", 3600)
        current_time = time.time()
        
        expired_keys = []
        for key, data in self.cache.items():
            if current_time - data.get("timestamp", 0) > cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"[SmartImageAnalyzer] 清理了 {len(expired_keys)} 个过期缓存")
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "success": False,
            "error": error_message,
            "ocr_text": None,
            "ai_analysis": None,
            "confidence": 0.0,
            "suggested_action": "fallback",
            "metadata": {
                "analysis_time_ms": 0,
                "image_size_bytes": 0,
                "image_format": "unknown"
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_time = 0
        if self.stats["total_images"] > 0:
            avg_time = self.stats["total_time_ms"] / self.stats["total_images"]
        
        return {
            **self.stats,
            "avg_time_ms": avg_time,
            "success_rate": (self.stats["ocr_success"] + self.stats["ai_success"]) / max(self.stats["total_images"], 1),
            "cache_size": len(self.cache),
            "config": self.config
        }


# 快速使用示例
async def example_usage():
    """使用示例"""
    analyzer = SmartImageAnalyzer()
    
    # 模拟图片数据
    with open("example.jpg", "rb") as f:
        image_data = f.read()
    
    # 分析图片
    result = await analyzer.analyze_image(image_data)
    
    print("分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 获取统计信息
    stats = analyzer.get_stats()
    print("\n统计信息:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())