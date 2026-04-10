"""
发送消息工具 - 迁移示例
从 MessageNet 迁移到 ToolNet
"""

from typing import Dict, Any
from webnet.ToolNet.base import BaseTool, ToolContext
import logging

logger = logging.getLogger(__name__)


class SendMessageTool(BaseTool):
    """发送消息工具 - 迁移示例"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "send_message",
            "description": "发送消息到指定群或私聊。当用户需要发送消息时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "要发送的消息内容"},
                    "group_id": {
                        "type": "integer",
                        "description": "群号（可选，默认为当前群）",
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "用户ID（可选，用于私聊）",
                    },
                },
                "required": ["message"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """
        发送消息

        Args:
            args: {
                message: 消息内容
                group_id: 群号（可选）
                user_id: 用户ID（可选）
            }
            context: 执行上下文
                - onebot_client: OneBot 客户端
                - group_id: 当前群号
                - user_id: 当前用户ID

        Returns:
            执行结果字符串
        """
        message = args.get("message", "")
        target_group_id = args.get("group_id")
        target_user_id = args.get("user_id")

        if not message:
            return "❌ 消息内容不能为空"

        # 检查 OneBot 客户端是否可用
        if not context.onebot_client:
            # 尝试从 context 的其他属性获取 onebot_client
            onebot_from_context = getattr(context, "onebot_from_context", None)
            if onebot_from_context:
                logger.info("[send_message] 使用备用的 onebot_client")
                context.onebot_client = onebot_from_context
            else:
                # 【修复】将原始消息内容嵌入 FINAL 响应中，供 AI 客户端提取使用
                # 格式: [FINAL]消息内容|||TARGET:group_123 或 TARGET:user_456
                target_info = (
                    f"group_{target_group_id}"
                    if target_group_id
                    else f"user_{target_user_id}"
                    if target_user_id
                    else "unknown"
                )
                logger.info(f"[send_message] 消息将通过响应路径发送: {message[:50]}...")
                return f"[FINAL]{message}|||TARGET:{target_info}"

        try:
            # 确定发送目标
            send_group_id = target_group_id or context.group_id

            # 发送群消息
            if send_group_id:
                await context.onebot_client.send_group_message(
                    group_id=send_group_id, message=message
                )
                logger.info(f"已发送群消息到群 {send_group_id}")
                return f"✅ 消息已发送到群 {send_group_id}"

            # 发送私聊消息
            elif target_user_id:
                await context.onebot_client.send_private_message(
                    user_id=target_user_id, message=message
                )
                logger.info(f"已发送私聊消息给用户 {target_user_id}")
                return f"✅ 消息已发送给用户 {target_user_id}"

            else:
                return "❌ 需要指定群号或用户ID"

        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            return f"❌ 发送消息失败: {str(e)}"
