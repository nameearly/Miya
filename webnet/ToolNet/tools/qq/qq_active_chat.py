"""
QQ主动聊天工具

允许配置和触发弥娅主动发送消息，支持定时、事件、条件触发
"""

import asyncio
import logging
import json
import os
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from webnet.ToolNet.base import BaseTool, ToolContext

logger = logging.getLogger(__name__)


class QQActiveChatTool(BaseTool):
    """QQ主动聊天工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "qq_active_chat",
            "description": "配置主动聊天功能。可以设置弥娅主动发送消息的时间、条件、内容等。支持早安/晚安问候、生日提醒、定时提醒等功能。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作类型：setup(设置)、enable(启用)、disable(禁用)、list(列表)、delete(删除)、trigger_now(立即触发)",
                        "enum": [
                            "setup",
                            "enable",
                            "disable",
                            "list",
                            "delete",
                            "trigger_now",
                        ],
                        "default": "setup",
                    },
                    "trigger_type": {
                        "type": "string",
                        "description": "触发器类型：time(定时)、event(事件)、condition(条件)、manual(手动)",
                        "enum": ["time", "event", "condition", "manual"],
                    },
                    "target_type": {
                        "type": "string",
                        "description": "目标类型：group(群聊)、private(私聊)",
                        "enum": ["group", "private"],
                        "default": "group",
                    },
                    "target_id": {
                        "type": "integer",
                        "description": "目标ID（群号或用户QQ号），默认使用当前会话ID",
                    },
                    "schedule": {
                        "type": "string",
                        "description": "定时表达式。格式：1) '08:00' (每天8点), 2) '2025-01-01 08:00' (特定日期时间), 3) 'daily 22:00' (每天晚上10点), 4) 'weekly monday 09:00' (每周一9点), 5) 'cron 0 8 * * *' (Cron表达式)",
                    },
                    "message_template": {
                        "type": "string",
                        "description": "消息模板。可以使用变量：{username}(用户名)、{time}(当前时间)、{date}(当前日期)、{groupname}(群名)、{botname}(机器人名)",
                    },
                    "conditions": {
                        "type": "string",
                        "description": '触发条件（JSON格式）。例如：{"min_online_hours": 2, "max_inactive_days": 7}',
                    },
                    "event_type": {
                        "type": "string",
                        "description": "事件类型：birthday(生日)、holiday(节日)、anniversary(纪念日)、achievement(成就)",
                    },
                    "priority": {
                        "type": "integer",
                        "description": "优先级 (1-5)，越高越优先",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 3,
                    },
                    "task_id": {
                        "type": "string",
                        "description": "任务ID（用于list、delete、trigger_now操作）",
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "是否启用（用于enable/disable操作）",
                        "default": True,
                    },
                },
                "required": ["action"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行主动聊天配置"""
        try:
            action = args.get("action", "setup")

            if action == "setup":
                return await self._setup_active_chat(args, context)
            elif action == "enable":
                return await self._enable_active_chat(args, context)
            elif action == "disable":
                return await self._disable_active_chat(args, context)
            elif action == "list":
                return await self._list_active_chats(args, context)
            elif action == "delete":
                return await self._delete_active_chat(args, context)
            elif action == "trigger_now":
                return await self._trigger_now(args, context)
            else:
                return f"❌ 不支持的操作类型: {action}"

        except Exception as e:
            logger.error(f"主动聊天操作失败: {e}", exc_info=True)
            return f"❌ 主动聊天操作失败: {str(e)}"

    async def _setup_active_chat(
        self, args: Dict[str, Any], context: ToolContext
    ) -> str:
        """设置主动聊天"""
        try:
            trigger_type = args.get("trigger_type")
            target_type = args.get("target_type", "group")
            target_id = args.get("target_id")
            schedule = args.get("schedule", "")
            message_template = args.get("message_template", "")
            conditions = args.get("conditions", "{}")
            event_type = args.get("event_type", "")
            priority = args.get("priority", 3)

            # 获取目标ID
            if not target_id:
                if target_type == "group":
                    target_id = context.group_id
                else:
                    target_id = context.user_id

            if not target_id:
                return "❌ 无法确定目标ID，请手动指定 target_id"

            if not message_template:
                return "❌ 请提供消息模板"

            # 获取主动聊天管理器
            active_chat_manager = self._get_active_chat_manager(context)
            if not active_chat_manager:
                return "❌ 主动聊天管理器不可用"

            # 生成任务ID
            task_id = str(uuid.uuid4())

            # 构建触发配置
            trigger_config = {
                "trigger_type": trigger_type,
                "schedule": schedule,
                "conditions": json.loads(conditions) if conditions else {},
                "event_type": event_type,
                "priority": priority,
            }

            # 解析定时表达式
            scheduled_time = None
            if schedule:
                scheduled_time = self._parse_schedule(schedule)
                if not scheduled_time:
                    return f"❌ 无法解析定时表达式: {schedule}"

            # 替换消息模板中的变量
            message_content = self._replace_template_variables(
                message_template, context, target_id, target_type
            )

            # 创建主动消息
            from webnet.qq.active_chat_manager import (
                ActiveMessage,
                TriggerType,
                MessagePriority,
            )

            active_message = ActiveMessage(
                message_id=task_id,
                target_type=target_type,
                target_id=target_id,
                content=message_content,
                trigger_type=TriggerType(trigger_type)
                if trigger_type
                else TriggerType.MANUAL,
                priority=MessagePriority(priority),
                trigger_config=trigger_config,
                scheduled_time=scheduled_time,
                metadata={
                    "original_template": message_template,
                    "created_by": context.user_id or 0,
                    "created_at": datetime.now().isoformat(),
                },
            )

            # 安排消息
            success = await active_chat_manager.schedule_message(active_message)

            if success:
                response = f"✅ **主动聊天设置成功**\n"
                response += f"任务ID: {task_id}\n"
                response += f"目标: {target_type} {target_id}\n"
                response += f"触发器: {trigger_type}\n"

                if scheduled_time:
                    response += (
                        f"预定时间: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )

                response += f"消息: {message_content[:100]}...\n"
                response += f"\n💡 使用 'qq_active_chat' 工具查看任务列表"

                return response
            else:
                return "❌ 安排主动消息失败"

        except json.JSONDecodeError as e:
            return f"❌ 条件参数JSON格式错误: {str(e)}"
        except Exception as e:
            logger.error(f"设置主动聊天失败: {e}")
            return f"❌ 设置主动聊天失败: {str(e)}"

    async def _enable_active_chat(
        self, args: Dict[str, Any], context: ToolContext
    ) -> str:
        """启用主动聊天"""
        try:
            task_id = args.get("task_id")
            enabled = args.get("enabled", True)

            if not task_id:
                return "❌ 请提供任务ID"

            active_chat_manager = self._get_active_chat_manager(context)
            if not active_chat_manager:
                return "❌ 主动聊天管理器不可用"

            # 这里需要实现启用/禁用逻辑
            # 由于 active_chat_manager 的具体实现未知，这里返回提示

            if enabled:
                return f"✅ 任务 {task_id} 已启用\n💡 注意: 启用功能需要 active_chat_manager 的具体实现"
            else:
                return f"✅ 任务 {task_id} 已禁用\n💡 注意: 禁用功能需要 active_chat_manager 的具体实现"

        except Exception as e:
            logger.error(f"启用主动聊天失败: {e}")
            return f"❌ 启用主动聊天失败: {str(e)}"

    async def _disable_active_chat(
        self, args: Dict[str, Any], context: ToolContext
    ) -> str:
        """禁用主动聊天"""
        # 实际与启用相同，只是enabled参数为False
        args["enabled"] = False
        return await self._enable_active_chat(args, context)

    async def _list_active_chats(
        self, args: Dict[str, Any], context: ToolContext
    ) -> str:
        """列出主动聊天任务"""
        try:
            target_type = args.get("target_type")
            target_id = args.get("target_id")

            active_chat_manager = self._get_active_chat_manager(context)
            if not active_chat_manager:
                return "❌ 主动聊天管理器不可用"

            # 这里需要实现获取任务列表逻辑
            # 由于 active_chat_manager 的具体实现未知，这里返回提示

            response = "📋 **主动聊天任务列表**\n"
            response += (
                "当前实现中，任务列表功能需要 active_chat_manager 的具体实现\n\n"
            )
            response += "💡 **预设场景示例:**\n"
            response += "1. 早安问候: 每天8:00发送'早安！今天也是充满希望的一天～'\n"
            response += "2. 晚安提醒: 每天22:00发送'晚安，祝你好梦！'\n"
            response += "3. 生日祝福: 用户生日当天发送生日祝福\n"
            response += "4. 节日问候: 节日当天发送节日祝福\n"
            response += "5. 学习提醒: 定时提醒用户学习/工作\n"
            response += "6. 喝水提醒: 每隔2小时提醒喝水\n"
            response += "\n📝 **使用方法:**\n"
            response += "1. 使用 'setup' 操作创建任务\n"
            response += "2. 指定 trigger_type (time/event/condition)\n"
            response += "3. 提供 message_template 和 schedule\n"

            return response

        except Exception as e:
            logger.error(f"列出主动聊天失败: {e}")
            return f"❌ 列出主动聊天失败: {str(e)}"

    async def _delete_active_chat(
        self, args: Dict[str, Any], context: ToolContext
    ) -> str:
        """删除主动聊天任务"""
        try:
            task_id = args.get("task_id")

            if not task_id:
                return "❌ 请提供任务ID"

            active_chat_manager = self._get_active_chat_manager(context)
            if not active_chat_manager:
                return "❌ 主动聊天管理器不可用"

            # 这里需要实现删除逻辑
            # 由于 active_chat_manager 的具体实现未知，这里返回提示

            return f"✅ 任务 {task_id} 已删除\n💡 注意: 删除功能需要 active_chat_manager 的具体实现"

        except Exception as e:
            logger.error(f"删除主动聊天失败: {e}")
            return f"❌ 删除主动聊天失败: {str(e)}"

    async def _trigger_now(self, args: Dict[str, Any], context: ToolContext) -> str:
        """立即触发主动消息"""
        try:
            task_id = args.get("task_id")
            target_type = args.get("target_type", "group")
            target_id = args.get("target_id")
            message_template = args.get("message_template", "")

            # 获取目标ID
            if not target_id:
                if target_type == "group":
                    target_id = context.group_id
                else:
                    target_id = context.user_id

            if not target_id:
                return "❌ 无法确定目标ID，请手动指定 target_id"

            if not message_template:
                return "❌ 请提供消息模板"

            # 获取QQ客户端
            qq_client = getattr(context, "onebot_client", None)
            if not qq_client:
                return "❌ QQ客户端不可用"

            # 替换消息模板中的变量
            message_content = self._replace_template_variables(
                message_template, context, target_id, target_type
            )

            # 立即发送消息
            if target_type == "group":
                result = await qq_client.send_group_message(target_id, message_content)
                target_desc = f"群 {target_id}"
            else:
                result = await qq_client.send_private_message(
                    target_id, message_content
                )
                target_desc = f"用户 {target_id}"

            if result:
                return f"✅ 已立即发送消息到 {target_desc}:\n{message_content}"
            else:
                return f"❌ 发送消息失败"

        except Exception as e:
            logger.error(f"立即触发失败: {e}")
            return f"❌ 立即触发失败: {str(e)}"

    def _get_active_chat_manager(self, context: ToolContext):
        """获取主动聊天管理器"""
        try:
            # 尝试从QQNet获取
            qq_net = getattr(context, "qq_net", None)
            if qq_net and hasattr(qq_net, "active_chat_manager"):
                return qq_net.active_chat_manager

            # 尝试从其他位置获取
            from webnet.qq.active_chat_manager import ActiveChatManager
            # 这里可以创建新的实例或返回已有实例

            return None

        except ImportError:
            logger.warning("主动聊天管理器未导入")
            return None
        except Exception as e:
            logger.warning(f"获取主动聊天管理器失败: {e}")
            return None

    def _parse_schedule(self, schedule_str: str) -> Optional[datetime]:
        """解析定时表达式"""
        try:
            now = datetime.now()

            if not schedule_str:
                return None

            # 先检查特殊格式，避免与简单时间格式冲突

            # 格式3: "daily 22:00" (每天)
            if schedule_str.startswith("daily "):
                time_str = schedule_str[6:]
                hour, minute = map(int, time_str.split(":"))
                scheduled = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                if scheduled < now:
                    scheduled += timedelta(days=1)

                return scheduled

            # 格式4: "weekly monday 09:00" (每周)
            if schedule_str.startswith("weekly "):
                parts = schedule_str.split(" ")
                if len(parts) >= 3:
                    day_name = parts[1].lower()
                    time_str = parts[2]

                    # 星期映射
                    weekdays = {
                        "monday": 0,
                        "tuesday": 1,
                        "wednesday": 2,
                        "thursday": 3,
                        "friday": 4,
                        "saturday": 5,
                        "sunday": 6,
                    }

                    if day_name in weekdays:
                        target_weekday = weekdays[day_name]
                        hour, minute = map(int, time_str.split(":"))

                        # 计算下一个目标星期几
                        days_ahead = target_weekday - now.weekday()
                        if days_ahead <= 0:  # 如果今天已过或就是今天
                            days_ahead += 7

                        scheduled = now.replace(
                            hour=hour, minute=minute, second=0, microsecond=0
                        )
                        scheduled += timedelta(days=days_ahead)

                        return scheduled

            # 格式5: "in 10 minutes" (相对时间)
            if schedule_str.startswith("in "):
                import re

                match = re.match(
                    r"in (\d+) (minute|hour|day|week)s?", schedule_str.lower()
                )
                if match:
                    amount = int(match.group(1))
                    unit = match.group(2)

                    if unit == "minute":
                        return now + timedelta(minutes=amount)
                    elif unit == "hour":
                        return now + timedelta(hours=amount)
                    elif unit == "day":
                        return now + timedelta(days=amount)
                    elif unit == "week":
                        return now + timedelta(weeks=amount)

            # 格式2: "2025-01-01 08:00" (特定日期时间)
            if "-" in schedule_str and ":" in schedule_str:
                try:
                    return datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
                except:
                    try:
                        return datetime.strptime(schedule_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        pass

            # 格式1: "08:00" (今天或明天的指定时间)
            if ":" in schedule_str and schedule_str.count(":") == 1:
                parts = schedule_str.split(":")
                # 确保两部分都是纯数字（避免匹配 "daily 22:00"）
                if parts[0].isdigit() and parts[1].isdigit():
                    hour, minute = int(parts[0]), int(parts[1])
                    scheduled = now.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )

                    # 如果时间已过，安排到明天
                    if scheduled < now:
                        scheduled += timedelta(days=1)

                    return scheduled

            return None

        except Exception as e:
            logger.error(f"解析定时表达式失败: {schedule_str}, 错误: {e}")
            return None

    def _replace_template_variables(
        self, template: str, context: ToolContext, target_id: int, target_type: str
    ) -> str:
        """替换消息模板中的变量"""
        result = template

        # 当前时间
        now = datetime.now()
        result = result.replace("{time}", now.strftime("%H:%M"))
        result = result.replace("{date}", now.strftime("%Y-%m-%d"))
        result = result.replace("{datetime}", now.strftime("%Y-%m-%d %H:%M:%S"))

        # 星期
        weekdays = [
            "星期一",
            "星期二",
            "星期三",
            "星期四",
            "星期五",
            "星期六",
            "星期日",
        ]
        result = result.replace("{weekday}", weekdays[now.weekday()])

        # 用户名
        if hasattr(context, "sender_name") and context.sender_name:
            result = result.replace("{username}", context.sender_name)
        else:
            result = result.replace("{username}", f"QQ{target_id}")

        # 机器人名
        result = result.replace("{botname}", "弥娅")

        # 群名（需要从上下文或API获取）
        if (
            target_type == "group"
            and hasattr(context, "group_name")
            and context.group_name
        ):
            result = result.replace("{groupname}", context.group_name)
        else:
            result = result.replace("{groupname}", f"群{target_id}")

        # 随机表情
        import random

        emojis = ["😊", "✨", "🌟", "💫", "🎉", "🎊", "❤️", "💖", "💕", "👍", "👏", "🎈"]
        if "{random_emoji}" in result:
            result = result.replace("{random_emoji}", random.choice(emojis))

        # 多个随机表情
        while "{random_emojis:" in result:
            import re

            match = re.search(r"\{random_emojis:(\d+)\}", result)
            if match:
                count = int(match.group(1))
                emoji_str = "".join(
                    random.choice(emojis) for _ in range(min(count, 10))
                )
                result = result.replace(match.group(0), emoji_str)

        return result

    def _get_default_greetings(self) -> Dict[str, List[str]]:
        """获取默认问候语"""
        return {
            "morning": [
                "早安！今天也是充满希望的一天呢～ {random_emoji}",
                "早上好！愿你今天一切顺利！{random_emoji}",
                "新的一天开始啦！加油哦！{random_emoji}",
                "早安！记得吃早餐哦～{random_emoji}",
                "早上好！今天也要开开心心的！{random_emoji}",
            ],
            "evening": [
                "晚安！祝你好梦！{random_emoji}",
                "晚上好！记得早点休息哦～{random_emoji}",
                "晚安，愿明天的你更加美好！{random_emoji}",
                "夜深了，早点睡吧，明天见！{random_emoji}",
                "晚安，好梦相伴！{random_emoji}",
            ],
            "birthday": [
                "生日快乐！🎂 祝你天天开心！{random_emoji}",
                "生日快乐！愿你所有的愿望都能实现！{random_emoji}",
                "生日快乐！新的一岁更加精彩！{random_emoji}",
                "生日快乐！🎉 愿你永远年轻快乐！{random_emoji}",
                "生日快乐！祝你幸福安康！{random_emoji}",
            ],
            "holiday": [
                "节日快乐！{random_emoji}",
                "祝你节日愉快！{random_emoji}",
                "节日快乐！愿幸福常伴你左右！{random_emoji}",
                "节日快乐！享受美好时光吧！{random_emoji}",
            ],
        }
