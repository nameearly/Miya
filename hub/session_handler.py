"""会话处理辅助模块

负责会话的保存、结束处理和日记提醒
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from memory.session_manager import SessionManager, SessionCategory

logger = logging.getLogger(__name__)


class SessionHandler:
    """会话处理器
    
    职责：
    - 处理会话结束和保存
    - 管理日记提醒
    - 压缩对话历史
    """

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        初始化会话处理器

        Args:
            session_manager: SessionManager实例
        """
        self.session_manager = session_manager

    async def handle_session_end(
        self,
        session_id: str,
        platform: str = 'terminal',
        memory_net=None
    ) -> Dict:
        """
        处理会话结束，使用 SessionManager 保存对话历史到 LifeBook

        Args:
            session_id: 会话ID
            platform: 平台类型 (默认 'terminal')
            memory_net: MemoryNet实例

        Returns:
            处理结果字典
        """
        try:
            logger.info(f"[会话处理] 开始处理会话结束: {session_id} (平台: {platform})")

            # 使用 SessionManager 保存会话
            if not self.session_manager:
                logger.warning("[会话处理] SessionManager 未初始化，使用旧方法保存")
                return await self._handle_session_end_legacy(session_id, platform, memory_net)

            # 获取对话历史
            full_session_id = f"{platform}_{session_id}"

            messages = await self.session_manager.get_conversation_messages(
                session_id=session_id,
                platform=platform,
                limit=100
            )

            if not messages:
                logger.info("[会话处理] 对话历史为空，无需保存")
                return {"success": True, "message": "对话历史为空"}

            # 使用 SessionManager 保存
            category = self.session_manager.platform_category_map.get(platform, SessionCategory.TERMINAL)
            result = await self.session_manager.save_session(
                session_id=session_id,
                platform=platform,
                messages=messages,
                category=category
            )

            logger.info(f"[会话处理] 会话结束处理完成: {result.get('message')}")
            return result

        except Exception as e:
            logger.error(f"[会话处理] 处理会话结束失败: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    async def _handle_session_end_legacy(
        self,
        session_id: str,
        platform: str = 'terminal',
        memory_net=None
    ) -> Dict:
        """
        传统会话结束处理方法（当 SessionManager 不可用时使用）

        Args:
            session_id: 会话ID
            platform: 平台类型
            memory_net: MemoryNet实例

        Returns:
            处理结果字典
        """
        try:
            logger.info(f"[会话处理-传统] 开始处理会话结束: {session_id}")

            # 1. 获取对话历史
            user_id = 'default'
            full_session_id = f"{platform}_{user_id}"

            if not memory_net or not memory_net.conversation_history:
                logger.warning("[会话处理-传统] memory_net 未初始化，无法保存对话历史")
                return {"success": False, "message": "memory_net 未初始化"}

            messages = await memory_net.conversation_history.get_history(
                full_session_id,
                limit=100
            )

            if not messages:
                logger.info("[会话处理-传统] 对话历史为空，无需保存")
                return {"success": True, "message": "对话历史为空"}

            # 2. 压缩为 Markdown 摘要
            summary = self._compress_conversation_to_markdown(messages)

            # 3. 存储到 LifeBook
            if hasattr(memory_net, 'memory_engine') and memory_net.memory_engine:
                # 创建标题
                date_str = datetime.now().strftime("%Y-%m-%d")
                title = f"终端会话 - {date_str}"

                # 存储到潮汐记忆（作为 LifeBook 的底层存储）
                entry_id = f"terminal_session_{date_str}_{int(datetime.now().timestamp())}"
                memory_net.memory_engine.store_tide(
                    entry_id,
                    {
                        'type': 'terminal_session',
                        'title': title,
                        'content': summary,
                        'session_id': session_id,
                        'date': date_str,
                        'timestamp': datetime.now().isoformat(),
                    }
                )
                logger.info(f"[会话处理-传统] 对话历史已保存到记忆系统: {entry_id}")

            # 4. 清空短期对话历史
            if memory_net.conversation_history:
                await memory_net.conversation_history.clear_session(full_session_id)
                logger.info(f"[会话处理-传统] 短期对话历史已清空: {full_session_id}")

            return {
                "success": True,
                "message": "对话历史已保存，短期记忆已清空",
                "summary": summary[:200] + "..." if len(summary) > 200 else summary
            }

        except Exception as e:
            logger.error(f"[会话处理-传统] 处理会话结束失败: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    async def set_diary_reminder(self, user_id: str, time: str = "21:00") -> Dict:
        """
        设置日记提醒

        Args:
            user_id: 用户ID
            time: 提醒时间（格式：HH:MM，默认 21:00）

        Returns:
            设置结果
        """
        try:
            if not self.session_manager:
                return {"success": False, "message": "SessionManager 未初始化"}

            result = await self.session_manager.schedule_diary_reminder(user_id, time)

            if result:
                return {
                    "success": True,
                    "message": f"已设置 {time} 的日记提醒，届时我会提醒你记日记哦~"
                }
            else:
                return {"success": False, "message": "设置提醒失败"}

        except Exception as e:
            logger.error(f"[会话处理] 设置日记提醒失败: {e}")
            return {"success": False, "message": str(e)}

    def _compress_conversation_to_markdown(self, messages: List) -> str:
        """
        将对话历史压缩为 Markdown 格式摘要

        Args:
            messages: 对话消息列表

        Returns:
            Markdown 格式的摘要
        """
        if not messages:
            return ""

        lines = [f"# 终端会话记录\n"]
        lines.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append(f"**会话ID**: {messages[0].session_id if hasattr(messages[0], 'session_id') else 'unknown'}\n")
        lines.append("\n## 对话内容\n")

        # 简化对话，只保留关键信息
        user_requests = []
        miya_responses = []

        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            role = msg.role if hasattr(msg, 'role') else 'unknown'

            # 提取关键操作
            if role == 'user':
                if any(kw in content for kw in ['打开', '启动', '运行', '执行', '安装', '检查']):
                    user_requests.append(content)
            elif role == 'assistant':
                if '已打开' in content or '已启动' in content or '已创建' in content or '会话ID' in content:
                    miya_responses.append(content.split('\n')[0][:100])

        # 生成摘要
        if user_requests:
            lines.append("### 用户操作\n")
            for req in user_requests[-5:]:  # 最多5条
                lines.append(f"- {req}\n")

        if miya_responses:
            lines.append("\n### 系统响应\n")
            for resp in miya_responses[-5:]:
                lines.append(f"- {resp}\n")

        # 添加总结
        lines.append("\n## 总结\n")
        if user_requests:
            lines.append(f"本次会话共执行了 {len(user_requests)} 个操作。\n")

        return "".join(lines)
