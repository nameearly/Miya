"""
QQ图片分析工具 handler
"""

from typing import Dict, Any
from webnet.ToolNet.tools.qq.qq_image_analyzer import QQImageAnalyzerTool


async def execute(args: Dict[str, Any], context: Any) -> str:
    """分析QQ图片"""
    try:
        tool = QQImageAnalyzerTool()
        result = await tool.execute(args, context)
        return result
    except Exception as e:
        return f"图片分析失败: {str(e)}"
