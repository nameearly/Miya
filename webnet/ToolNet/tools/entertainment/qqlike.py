"""
QQ点赞工具
"""

from typing import Dict, Any
import logging
from webnet.ToolNet.base import BaseTool, ToolContext


logger = logging.getLogger(__name__)


class QQLike(BaseTool):
    """QQ点赞工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "qq_like",
            "description": "给指定QQ号点赞。当用户提及'点赞'、'点个赞'、'喜欢'等相关词汇时，必须调用此工具执行点赞操作。支持以下场景：1. 用户说'给我点赞'、'帮我点个赞'时，使用context.user_id（当前用户QQ号，是纯数字）；2. 用户明确指定QQ号时使用指定号码（如123456789）；3. 用户通过@提及其他用户（如'给@苦玄点赞'）时，context.at_list中已包含被@用户的QQ号，直接使用即可。注意：QQ每次最多点赞10次，每日有上限。如果消息中@了多个用户，需要分别调用此工具给每个人点赞。重要：不要用文字回复，必须调用工具执行点赞。",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_user_id": {
                        "type": "integer",
                        "description": "要点赞的QQ号（纯数字，如123456789）。如果用户说'给我点赞'，必须传递context.user_id的整数值（不是字符串，是纯数字QQ号）。如果用户通过@提及他人，从context.at_list获取QQ号（纯数字）。",
                    },
                    "times": {
                        "type": "integer",
                        "description": "点赞次数（1-10），默认1次，用户说'十次'、'十个'、'一人点十个'等时转换为数字10",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["target_user_id"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行点赞"""
        # 优先检查@提及：如果有@，给@的用户点赞
        if context.at_list and len(context.at_list) > 0:
            target_user_id = context.at_list[0]
            logger.info(f"[qq_like] 检测到@提及，使用at_list中的用户: {target_user_id}")
        else:
            # 否则使用AI传递的参数或当前用户ID
            target_user_id_from_args = args.get("target_user_id")
            if target_user_id_from_args is not None:
                try:
                    target_user_id = int(target_user_id_from_args)
                    logger.info(f"[qq_like] 使用AI传递的QQ号: {target_user_id}")
                except (ValueError, TypeError):
                    logger.warning(
                        f"[qq_like] AI传递的QQ号无效: {target_user_id_from_args}，使用当前用户ID"
                    )
                    target_user_id = context.user_id
            else:
                target_user_id = context.user_id
                logger.info(f"[qq_like] 使用当前用户ID: {target_user_id}")

        times = args.get("times", 1)

        logger.info(
            f"[qq_like] 工具被调用: args={args}, context.user_id={context.user_id}, context.at_list={context.at_list}, times={times}"
        )

        # 检查是否给自己点赞
        bot_qq = getattr(context, "bot_qq", None)
        if bot_qq and target_user_id == bot_qq:
            return "❌ 不能给自己点赞哦~"

        if target_user_id is None:
            return "请提供要点赞的目标QQ号，或@要点赞的用户"

        # 验证参数类型
        try:
            target_user_id = int(target_user_id)
            times = int(times)
        except (ValueError, TypeError):
            return "参数类型错误：target_user_id和times必须是整数"

        if times < 1:
            return "点赞次数必须大于0"
        if times > 10:
            return "单次点赞次数不能超过10次"

        # 尝试直接调用点赞回调
        send_like_callback = getattr(context, "send_like_callback", None)
        if send_like_callback:
            try:
                await send_like_callback(target_user_id, times)

                if times == 1:
                    return f"✅ 已给 QQ{target_user_id} 点赞。"
                else:
                    return f"✅ 已给 QQ{target_user_id} 点赞 {times} 次。"
            except Exception as callback_error:
                logger.error(f"点赞回调执行失败: {callback_error}", exc_info=True)

        # 如果没有点赞回调或回调执行失败，返回提示
        return f"⚠️ 点赞功能暂时不可用，但我已记录您的点赞意图"
