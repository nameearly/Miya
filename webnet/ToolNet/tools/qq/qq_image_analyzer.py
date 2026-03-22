"""
QQ图片分析工具

支持图片内容识别、OCR文字提取、图片描述等
"""

import asyncio
import logging
import os
import base64
import tempfile
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

import httpx
from PIL import Image
import io

from webnet.ToolNet.base import BaseTool, ToolContext

logger = logging.getLogger(__name__)


class QQImageAnalyzerTool(BaseTool):
    """QQ图片分析工具"""
    
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "qq_image_analyzer",
            "description": "分析图片内容。支持OCR文字识别、图片描述、内容分析等。当用户发送图片并询问内容时，自动调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "分析类型：ocr(文字识别)、describe(图片描述)、analyze(综合分析)、nsfw(安全检测)",
                        "enum": ["ocr", "describe", "analyze", "nsfw"],
                        "default": "ocr"
                    },
                    "image_source": {
                        "type": "string",
                        "description": "图片来源：local(本地文件)、url(网络地址)、base64(Base64编码)、context(从上下文获取)",
                        "enum": ["local", "url", "base64", "context"],
                        "default": "context"
                    },
                    "image_path": {
                        "type": "string",
                        "description": "图片路径、URL或Base64数据（当image_source不为context时使用）"
                    },
                    "language": {
                        "type": "string",
                        "description": "OCR语言：chi_sim(简体中文)、eng(英文)、jpn(日文)、auto(自动检测)",
                        "enum": ["chi_sim", "eng", "jpn", "auto"],
                        "default": "auto"
                    },
                    "detail_level": {
                        "type": "string",
                        "description": "分析详细程度：basic(基础)、detailed(详细)",
                        "enum": ["basic", "detailed"],
                        "default": "basic"
                    }
                },
                "required": ["action"]
            }
        }
    
    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行图片分析"""
        try:
            action = args.get("action", "ocr")
            image_source = args.get("image_source", "context")
            image_path = args.get("image_path", "")
            language = args.get("language", "auto")
            detail_level = args.get("detail_level", "basic")
            
            # 获取图片数据
            image_data = await self._get_image_data(image_source, image_path, context)
            if not image_data:
                return "❌ 无法获取图片数据，请提供图片路径或确保上下文中有图片信息"
            
            # 根据操作类型处理
            if action == "ocr":
                return await self._perform_ocr(image_data, language, detail_level)
            elif action == "describe":
                return await self._describe_image(image_data, detail_level)
            elif action == "analyze":
                return await self._analyze_image(image_data, detail_level)
            elif action == "nsfw":
                return await self._nsfw_check(image_data)
            else:
                return f"❌ 不支持的操作类型: {action}"
                
        except Exception as e:
            logger.error(f"图片分析失败: {e}", exc_info=True)
            return f"❌ 图片分析失败: {str(e)}"
    
    async def _get_image_data(
        self, 
        image_source: str, 
        image_path: str, 
        context: ToolContext
    ) -> Optional[bytes]:
        """获取图片数据"""
        try:
            if image_source == "context":
                # 从上下文获取图片
                if hasattr(context, 'image_data') and context.image_data:
                    return context.image_data
                elif hasattr(context, 'file_path') and context.file_path:
                    # 检查是否是图片文件
                    ext = os.path.splitext(context.file_path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        with open(context.file_path, 'rb') as f:
                            return f.read()
                return None
                
            elif image_source == "local":
                # 本地文件
                if not os.path.exists(image_path):
                    return None
                
                with open(image_path, 'rb') as f:
                    return f.read()
                
            elif image_source == "url":
                # 网络URL
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_path, timeout=30.0)
                    if response.status_code == 200:
                        return response.content
                    else:
                        logger.error(f"下载图片失败: HTTP {response.status_code}")
                        return None
                        
            elif image_source == "base64":
                # Base64数据
                if ',' in image_path:
                    image_path = image_path.split(',', 1)[1]
                
                try:
                    return base64.b64decode(image_path)
                except:
                    return None
                    
            else:
                logger.error(f"不支持的图片来源: {image_source}")
                return None
                
        except Exception as e:
            logger.error(f"获取图片数据失败: {e}")
            return None
    
    async def _perform_ocr(self, image_data: bytes, language: str, detail_level: str) -> str:
        """执行OCR文字识别"""
        try:
            # 尝试导入OCR库
            ocr_result = await self._ocr_with_paddle(image_data, language)
            
            if not ocr_result:
                # 尝试其他OCR引擎
                ocr_result = await self._ocr_with_tesseract(image_data, language)
            
            if not ocr_result:
                return "❌ OCR识别失败，请确保已安装OCR引擎或尝试其他图片"
            
            text = ocr_result.get("text", "")
            confidence = ocr_result.get("confidence", 0.0)
            
            if not text.strip():
                return "📷 **图片文字识别结果**\n未检测到文字内容"
            
            response = f"📷 **图片文字识别结果**\n"
            response += f"置信度: {confidence:.1%}\n"
            
            if detail_level == "detailed":
                # 添加详细分析
                lines = text.split('\n')
                char_count = len(text)
                line_count = len(lines)
                
                response += f"字符数: {char_count}\n"
                response += f"行数: {line_count}\n"
                
                # 统计中文字符比例
                chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                if chinese_chars > 0:
                    chinese_ratio = chinese_chars / char_count * 100
                    response += f"中文字符: {chinese_chars} ({chinese_ratio:.1f}%)\n"
            
            response += f"\n--- 识别到的文字 ---\n{text}"
            
            return response
            
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return f"❌ OCR识别失败: {str(e)}"
    
    async def _ocr_with_paddle(self, image_data: bytes, language: str) -> Optional[Dict[str, Any]]:
        """使用PaddleOCR进行文字识别"""
        try:
            # 检查是否安装了PaddleOCR
            import paddleocr
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name
            
            try:
                # 初始化OCR
                from paddleocr import PaddleOCR
                
                # 根据语言选择模型
                if language == "auto":
                    # 自动检测：先尝试中文，如果没有中文再尝试英文
                    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
                elif language == "chi_sim":
                    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
                elif language == "eng":
                    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
                elif language == "jpn":
                    ocr = PaddleOCR(use_angle_cls=True, lang='japan', use_gpu=False)
                else:
                    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
                
                # 执行OCR
                result = ocr.ocr(tmp_path, cls=True)
                
                # 解析结果
                text_parts = []
                total_confidence = 0.0
                count = 0
                
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) >= 2:
                            text_info = line[1]
                            if text_info:
                                text = text_info[0]
                                confidence = text_info[1]
                                text_parts.append(text)
                                total_confidence += confidence
                                count += 1
                
                if text_parts:
                    full_text = '\n'.join(text_parts)
                    avg_confidence = total_confidence / count if count > 0 else 0.0
                    
                    return {
                        "text": full_text,
                        "confidence": avg_confidence,
                        "engine": "paddleocr"
                    }
                    
            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        except ImportError:
            logger.debug("PaddleOCR未安装，跳过")
        except Exception as e:
            logger.warning(f"PaddleOCR识别失败: {e}")
        
        return None
    
    async def _ocr_with_tesseract(self, image_data: bytes, language: str) -> Optional[Dict[str, Any]]:
        """使用Tesseract进行文字识别"""
        try:
            # 检查是否安装了Tesseract
            import pytesseract
            from PIL import Image
            
            # 将图片数据转换为PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # 设置语言参数
            lang_param = None
            if language == "chi_sim":
                lang_param = "chi_sim"
            elif language == "eng":
                lang_param = "eng"
            elif language == "jpn":
                lang_param = "jpn"
            elif language == "auto":
                # 尝试多种语言
                lang_param = "chi_sim+eng"
            
            # 执行OCR
            text = pytesseract.image_to_string(image, lang=lang_param)
            
            if text.strip():
                return {
                    "text": text.strip(),
                    "confidence": 0.8,  # Tesseract不直接提供置信度
                    "engine": "tesseract"
                }
                
        except ImportError:
            logger.debug("Tesseract未安装，跳过")
        except Exception as e:
            logger.warning(f"Tesseract识别失败: {e}")
        
        return None
    
    async def _describe_image(self, image_data: bytes, detail_level: str) -> str:
        """生成图片描述"""
        try:
            # 检查是否有AI图片描述能力
            if hasattr(self, '_describe_with_ai'):
                description = await self._describe_with_ai(image_data, detail_level)
                if description:
                    response = f"🎨 **图片描述**\n{description}"
                    return response
            
            # 基础描述：分析图片基本信息
            try:
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                format_name = image.format or "未知"
                mode = image.mode
                
                response = f"🎨 **图片基本信息**\n"
                response += f"尺寸: {width} × {height} 像素\n"
                response += f"格式: {format_name}\n"
                response += f"色彩模式: {mode}\n"
                response += f"文件大小: {len(image_data) / 1024:.1f} KB\n"
                
                # 简单分析
                if width > height:
                    orientation = "横向"
                elif height > width:
                    orientation = "纵向"
                else:
                    orientation = "正方形"
                
                response += f"方向: {orientation}\n"
                
                if detail_level == "detailed":
                    # 计算平均颜色
                    try:
                        # 缩小图片以加快处理
                        small_image = image.resize((100, 100))
                        colors = small_image.getcolors(10000)
                        if colors:
                            # 找到最常见的颜色
                            colors.sort(key=lambda x: x[0], reverse=True)
                            most_common = colors[0][1]
                            
                            if isinstance(most_common, (tuple, list)) and len(most_common) >= 3:
                                r, g, b = most_common[:3]
                                response += f"主色调: RGB({r}, {g}, {b})\n"
                    except:
                        pass
                
                return response
                
            except Exception as e:
                logger.warning(f"图片基本分析失败: {e}")
                return "❌ 图片分析失败，无法获取基本信息"
            
        except Exception as e:
            logger.error(f"生成图片描述失败: {e}")
            return f"❌ 生成图片描述失败: {str(e)}"
    
    async def _analyze_image(self, image_data: bytes, detail_level: str) -> str:
        """综合分析图片"""
        try:
            response = "🔍 **图片综合分析**\n\n"
            
            # 1. 基础信息
            try:
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                
                response += f"📐 **基础信息**\n"
                response += f"尺寸: {width} × {height} 像素\n"
                response += f"宽高比: {width/height:.2f}:1\n"
                response += f"总像素: {width * height:,}\n"
                response += f"文件大小: {len(image_data) / 1024:.1f} KB\n"
                
                if width > 1920 or height > 1080:
                    response += "📱 这是一张高分辨率图片\n"
                elif width < 640 and height < 480:
                    response += "📱 这是一张小尺寸图片\n"
                
            except Exception as e:
                response += f"❌ 基础信息获取失败: {str(e)}\n"
            
            response += "\n"
            
            # 2. 文字识别
            ocr_result = await self._ocr_with_paddle(image_data, "auto")
            if not ocr_result:
                ocr_result = await self._ocr_with_tesseract(image_data, "auto")
            
            if ocr_result and ocr_result.get("text", "").strip():
                text = ocr_result["text"]
                confidence = ocr_result.get("confidence", 0.0)
                
                response += f"📝 **文字识别** (置信度: {confidence:.1%})\n"
                
                # 显示前几行文字
                lines = text.split('\n')
                preview_lines = lines[:5]  # 显示前5行
                for i, line in enumerate(preview_lines):
                    if line.strip():
                        response += f"  {i+1}. {line[:50]}{'...' if len(line) > 50 else ''}\n"
                
                if len(lines) > 5:
                    response += f"  ... 还有 {len(lines) - 5} 行未显示\n"
                
                # 简单分析
                char_count = len(text)
                line_count = len([l for l in lines if l.strip()])
                
                response += f"  统计: {char_count} 字符, {line_count} 行\n"
            else:
                response += f"📝 **文字识别**\n未检测到文字内容\n"
            
            response += "\n"
            
            # 3. 图片类型分析
            try:
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                format_name = image.format or "未知"
                
                response += f"🖼️ **图片类型**\n"
                response += f"格式: {format_name}\n"
                response += f"色彩模式: {image.mode}\n"
                
                # 猜测图片类型
                if format_name.upper() in ['JPEG', 'JPG']:
                    response += "📸 可能是一张照片或截图\n"
                elif format_name.upper() == 'PNG':
                    response += "🖥️ 可能是一张截图或带有透明度的图片\n"
                elif format_name.upper() == 'GIF':
                    response += "🎬 这是一张GIF动图\n"
                elif format_name.upper() == 'BMP':
                    response += "💾 这是一张位图图片\n"
                
            except Exception as e:
                response += f"❌ 图片类型分析失败: {str(e)}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"图片综合分析失败: {e}")
            return f"❌ 图片综合分析失败: {str(e)}"
    
    async def _nsfw_check(self, image_data: bytes) -> str:
        """NSFW（不适宜内容）检测"""
        try:
            response = "🛡️ **图片安全检测**\n"
            
            # 基本安全检查
            try:
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                
                # 检查图片尺寸
                if width * height > 10000 * 10000:  # 超过1亿像素
                    response += "⚠️ 警告: 图片尺寸过大\n"
                
                # 检查图片比例
                aspect_ratio = width / height
                if aspect_ratio > 10 or aspect_ratio < 0.1:
                    response += "⚠️ 警告: 图片比例异常\n"
                
                # 简单肤色检测（基础实现）
                try:
                    # 将图片缩小以加快处理
                    small_image = image.resize((100, 100))
                    pixels = list(small_image.getdata())
                    
                    skin_pixels = 0
                    for pixel in pixels:
                        if isinstance(pixel, (tuple, list)) and len(pixel) >= 3:
                            r, g, b = pixel[:3]
                            # 简单的肤色检测规则
                            if r > 95 and g > 40 and b > 20 and \
                               max(r, g, b) - min(r, g, b) > 15 and \
                               abs(r - g) > 15 and r > g and r > b:
                                skin_pixels += 1
                    
                    skin_ratio = skin_pixels / len(pixels)
                    if skin_ratio > 0.3:  # 30%以上可能是肤色
                        response += f"⚠️ 注意: 检测到大量肤色区域 ({skin_ratio:.1%})\n"
                        
                except:
                    pass
                
                response += "✅ 基本安全检查通过\n"
                
            except Exception as e:
                response += f"❌ 安全检查失败: {str(e)}\n"
            
            response += "\n💡 **安全建议**\n"
            response += "1. 避免分享个人隐私图片\n"
            response += "2. 注意图片版权问题\n"
            response += "3. 不要分享不适宜内容\n"
            response += "4. 保护个人和他人隐私\n"
            
            return response
            
        except Exception as e:
            logger.error(f"NSFW检测失败: {e}")
            return f"❌ 安全检测失败: {str(e)}"
    
    async def _describe_with_ai(self, image_data: bytes, detail_level: str) -> Optional[str]:
        """使用AI模型描述图片"""
        # 这里可以集成各种AI图片描述API
        # 例如: 百度AI、腾讯AI、OpenAI等
        
        # 当前实现为空，需要根据实际可用的AI服务进行实现
        return None