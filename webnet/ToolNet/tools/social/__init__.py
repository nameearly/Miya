"""
社交平台工具

跨端共享的社交平台交互工具。
所有弥娅实例（QQ/微信/桌面端）都可以使用这些工具。
"""

from .qq_tools import (
    QQImageTool,
    QQFileTool,
    QQEmojiTool,
    QQFileReaderTool,
    QQImageAnalyzerTool,
)
from .wechat_tools import WeChatTools
from .discord_tools import DiscordTools
from .social_base import SocialBase

__all__ = [
    "SocialBase",
    "QQImageTool",
    "QQFileTool",
    "QQEmojiTool",
    "QQFileReaderTool",
    "QQImageAnalyzerTool",
    "WeChatTools",
    "DiscordTools",
]
