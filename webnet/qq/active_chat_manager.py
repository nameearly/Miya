"""
QQ主动聊天管理器 v2.0

允许弥娅主动发起聊天，支持：
1. 智能上下文感知 - 根据记忆和上下文主动跟进
2. 定时问候 - 早安、晚安等
3. 待办提醒 - 用户提到的计划自动跟进
4. 情感关怀 - 根据情绪状态主动关心
"""

import asyncio
import logging
import json
import os
import re
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random

# 导入动态生成系统
try:
    from config.proactive_chat import DynamicMessageGenerator, ProactiveChatConfigLoader

    DYNAMIC_GENERATION_AVAILABLE = True
except ImportError:
    DYNAMIC_GENERATION_AVAILABLE = False

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """消息优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TriggerType(Enum):
    """触发类型"""

    CONTEXT = "context"  # 上下文触发（智能跟进）
    TIME = "time"  # 定时触发
    EVENT = "event"  # 事件触发
    CONDITION = "condition"  # 条件触发
    MANUAL = "manual"  # 手动触发
    GREETING = "greeting"  # 问候触发


class ContextType(Enum):
    """上下文类型"""

    ACTIVITY = "activity"  # 活动（去上课、去上班）
    PLAN = "plan"  # 计划（要去、准备）
    REMINDER = "reminder"  # 提醒（三分钟后提醒我）
    APPOINTMENT = "appointment"  # 预约
    TASK = "task"  # 任务
    QUESTION = "question"  # 问题（等待回答）
    EMOTION = "emotion"  # 情绪关注


@dataclass
class UserContext:
    """用户上下文（用于智能跟进）"""

    context_id: str
    user_id: int
    context_type: ContextType
    content: str  # 原始内容
    expectation: str  # 预期结果/后续
    created_at: datetime
    follow_up_at: Optional[datetime] = None  # 跟进时间
    follow_up_sent: bool = False
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "context_id": self.context_id,
            "user_id": self.user_id,
            "context_type": self.context_type.value,
            "content": self.content,
            "expectation": self.expectation,
            "created_at": self.created_at.isoformat(),
            "follow_up_at": self.follow_up_at.isoformat()
            if self.follow_up_at
            else None,
            "follow_up_sent": self.follow_up_sent,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


class IntelligentActiveChatManager:
    """智能主动聊天管理器 - 基于上下文感知"""

    # 人设配置（从PersonalityLoader加载）
    _personality_config: Dict[str, Any] = {}
    _personality_loader = None

    # 期望到工具动作的映射
    EXPECTATION_TO_TOOL_ACTION = {
        "点赞": "qq_like",
        "给赞": "qq_like",
        "点个赞": "qq_like",
        "拍一拍": "send_poke",
        "拍一下": "send_poke",
    }

    # 上下文触发模式
    ACTIVITY_PATTERNS = [
        (r"(去|上)(课|学|学校|教室)", "activity", "课程"),
        (r"(去|上)(班|工作)", "activity", "工作"),
        (r"(去|吃)(饭|午餐|晚餐|早饭|早餐)", "activity", "餐饮"),
        (r"(去|做|锻炼|跑步|健身|打球)", "activity", "运动"),
        (r"(去|看|电影|电视剧)", "activity", "娱乐"),
        (r"(去|医院|看病|检查)", "activity", "医疗"),
        (r"(睡|休息|午休|小憩)", "activity", "休息"),
        (r"(出门|出去|回家|回来)", "activity", "出行"),
    ]

    PLAN_PATTERNS = [
        (r"(要|准备|打算|计划)(去|做)", "plan", "计划"),
        (r"(待会|等会|一会儿)(去|做|吃)", "plan", "计划"),
        (r"(马上|立刻|这就)(去|做|吃)", "plan", "计划"),
    ]

    # 提醒模式 - 检测"X分钟后/秒后提醒我"等
    REMINDER_PATTERNS = [
        # 数字 + 时间单位 + 提醒
        (r"(\d+)\s*(分钟|分|秒|小时后)(?:提醒|叫我|通知)", "reminder", "提醒"),
        # 中文数字 + 时间单位 + 提醒
        (
            r"(一二三四五六七八九十百)\s*(分钟|分|秒|小时后)(?:提醒|叫我|通知)",
            "reminder",
            "提醒",
        ),
        # "X分钟后" 格式
        (r"(\d+)\s*分钟(?:后|之)?(?:提醒|叫我|通知)", "reminder", "提醒"),
        (r"(\d+)\s*秒(?:后|之)?(?:提醒|叫我|通知)", "reminder", "提醒"),
        # 泡面/煮饭 + 提醒
        (
            r"(泡面|泡|煮|做)(?:好了|完了|完成)?(?:后|)?(?:提醒|叫我|通知)",
            "reminder",
            "提醒",
        ),
        # 点赞
        (r"(点|个|给我)(?:个)?赞", "reminder", "点赞"),
        # 通用提醒
        (r"(提醒|叫我|通知)(?:我|他)?", "reminder", "提醒"),
    ]

    QUESTION_PATTERNS = [
        (r"(\?|？)(.*)", "question", "问题"),
        (r"(怎么|如何|为什么|是不是|能不能)", "question", "问题"),
    ]

    def __init__(self, qq_net):
        self.qq_net = qq_net
        self.pending_messages: Dict[str, "ActiveMessage"] = {}
        self.sent_messages: List["ActiveMessage"] = []
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.running = False

        # 智能上下文跟踪
        self.user_contexts: Dict[str, List[UserContext]] = {}  # user_id -> contexts

        # 自动触发配置
        self.auto_trigger_enabled = True  # 默认启用自动触发
        self.trigger_cooldown = 300  # 触发冷却时间（秒）

        # 检查间隔
        self.check_interval = 60  # 秒

        # 上下文过期时间（小时）
        self.context_expiry_hours = 24

        # 初始化人设加载器
        self._init_personality_loader()

        # 数据持久化路径
        self.data_dir = None
        self._init_data_dir()

        # 加载持久化数据
        self._load_persisted_data()

        # 用户最后互动时间（用于空闲检测）
        self.user_last_interaction: Dict[str, datetime] = {}

        # 动态消息生成器
        self.dynamic_generator = None
        logger.info(
            f"[IntelligentActiveChat] DYNAMIC_GENERATION_AVAILABLE = {DYNAMIC_GENERATION_AVAILABLE}"
        )
        if DYNAMIC_GENERATION_AVAILABLE:
            try:
                # 创建配置加载器
                config_loader = ProactiveChatConfigLoader()
                self.dynamic_generator = DynamicMessageGenerator(config_loader)
                logger.info("[IntelligentActiveChat] 动态消息生成器创建成功")
            except Exception as e:
                logger.error(f"[IntelligentActiveChat] 动态消息生成器创建失败: {e}")
                self.dynamic_generator = None
        else:
            logger.warning("[IntelligentActiveChat] 动态生成系统不可用")

    def _init_personality_loader(self):
        """初始化人设加载器并加载配置"""
        try:
            from core.personality_loader import get_personality_loader

            IntelligentActiveChatManager._personality_loader = get_personality_loader()
            IntelligentActiveChatManager._personality_config = (
                IntelligentActiveChatManager._personality_loader.load("default")
            )
            logger.info("[IntelligentActiveChat] 人设配置加载成功")
            self._log_loaded_templates()
        except Exception as e:
            logger.warning(
                f"[IntelligentActiveChat] 人设配置加载失败: {e}, 使用默认配置"
            )
            IntelligentActiveChatManager._personality_config = {}

    def _log_loaded_templates(self):
        """记录已加载的模板配置"""
        config = IntelligentActiveChatManager._personality_config
        if not config:
            return

        template_keys = [
            "greetings",
            "check_in_responses",
            "comfort_responses",
            "encourage_responses",
            "listen_responses",
            "poke_responses",
        ]

        for key in template_keys:
            if key in config:
                count = len(config[key]) if isinstance(config[key], list) else 0
                logger.info(f"[IntelligentActiveChat] 已加载模板 {key}: {count}条")

    def _get_personality_template(self, key: str, default: Any = None) -> Any:
        """从人设配置获取模板"""
        config = IntelligentActiveChatManager._personality_config
        if not config:
            return default
        return config.get(key, default)

    def _get_random_template(self, key: str, default: List[str] = None) -> str:
        """从配置中随机获取一条模板"""
        templates = self._get_personality_template(key, default or [])
        if not templates:
            return "在。"
        return random.choice(templates)

    def _init_data_dir(self):
        """初始化数据目录"""
        try:
            from pathlib import Path

            base_dir = (
                Path(__file__).parent.parent.parent.parent / "data" / "active_chat"
            )
            base_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir = base_dir
            logger.info(f"[IntelligentActiveChat] 数据目录: {self.data_dir}")
        except Exception as e:
            logger.error(f"[IntelligentActiveChat] 初始化数据目录失败: {e}")
            self.data_dir = None

    def _load_persisted_data(self):
        """加载持久化数据"""
        if not self.data_dir:
            return

        try:
            # 加载上下文
            contexts_path = self.data_dir / "user_contexts.json"
            if contexts_path.exists():
                with open(contexts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id, contexts_list in data.items():
                        self.user_contexts[user_id] = []
                        for ctx_data in contexts_list:
                            try:
                                ctx_data["created_at"] = datetime.fromisoformat(
                                    ctx_data["created_at"]
                                )
                                if ctx_data.get("follow_up_at"):
                                    ctx_data["follow_up_at"] = datetime.fromisoformat(
                                        ctx_data["follow_up_at"]
                                    )
                                ctx_data["context_type"] = ContextType(
                                    ctx_data["context_type"]
                                )
                                ctx = UserContext(**ctx_data)
                                self.user_contexts[user_id].append(ctx)
                            except Exception as e:
                                logger.error(
                                    f"[IntelligentActiveChat] 加载上下文失败: {e}"
                                )

            # 加载用户偏好
            prefs_path = self.data_dir / "user_preferences.json"
            if prefs_path.exists():
                with open(prefs_path, "r", encoding="utf-8") as f:
                    self.user_preferences = json.load(f)

            total_contexts = sum(len(v) for v in self.user_contexts.values())
            logger.info(
                f"[IntelligentActiveChat] 数据加载完成: {total_contexts}个上下文, {len(self.user_preferences)}用户"
            )

        except Exception as e:
            logger.error(f"[IntelligentActiveChat] 加载数据失败: {e}")

    def _save_persisted_data(self):
        """保存持久化数据"""
        if not self.data_dir:
            return

        try:
            # 保存上下文
            contexts_path = self.data_dir / "user_contexts.json"
            data = {}
            for user_id, contexts in self.user_contexts.items():
                data[user_id] = [ctx.to_dict() for ctx in contexts]
            with open(contexts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 保存用户偏好
            prefs_path = self.data_dir / "user_preferences.json"
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"[IntelligentActiveChat] 保存数据失败: {e}")

    def extract_context_from_message(
        self, user_id: int, message: str, group_id: int = None
    ) -> Optional[UserContext]:
        """
        从消息中提取上下文

        例如：
        - "去上课了" -> UserContext(activity, "去上课了", "下课")
        - "待会要去开会" -> UserContext(plan, "待会要去开会", "会议")
        - "30秒后提醒我" -> UserContext(reminder, "30秒后提醒我", "提醒")
        - "三分钟后提醒我" -> UserContext(reminder, "三分钟后提醒我", "提醒")
        """
        message = message.strip()

        # 检查提醒模式（优先检测）
        for pattern, ctx_type, expectation in self.REMINDER_PATTERNS:
            match = re.search(pattern, message)
            if match:
                follow_up = self._infer_reminder_follow_up(message, match)
                follow_up_time = self._parse_reminder_time(message)
                ctx = self._create_context(
                    user_id, message, ctx_type, follow_up, group_id
                )
                if ctx and follow_up_time:
                    ctx.follow_up_at = follow_up_time
                return ctx

        # 检查活动模式
        for pattern, ctx_type, expectation in self.ACTIVITY_PATTERNS:
            if re.search(pattern, message):
                follow_up = self._infer_follow_up(message, ctx_type)
                return self._create_context(
                    user_id, message, ctx_type, follow_up, group_id
                )

        # 检查计划模式
        for pattern, ctx_type, expectation in self.PLAN_PATTERNS:
            if re.search(pattern, message):
                follow_up = self._infer_follow_up(message, ctx_type)
                return self._create_context(
                    user_id, message, ctx_type, follow_up, group_id
                )

        return None

    def _parse_reminder_time(self, message: str) -> Optional[datetime]:
        """解析提醒时间"""
        import re

        # 中文数字映射
        chinese_nums = {
            "零": 0,
            "一": 1,
            "二": 2,
            "两": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
        }

        def parse_chinese_num(s):
            """解析中文数字"""
            if s in chinese_nums:
                return chinese_nums[s]
            # 处理 "十几" 的情况
            if s.startswith("十"):
                if len(s) == 1:
                    return 10
                return 10 + chinese_nums.get(s[1], 0)
            return None

        # 尝试匹配阿拉伯数字
        match = re.search(r"(\d+)\s*(秒|分钟|分|时|小时|天|分钟后|秒后)", message)
        if match:
            value = int(match.group(1))
            unit = match.group(2).rstrip("后")  # 去掉可能的"后"字

            now = datetime.now()
            if unit in ["秒"]:
                return now + timedelta(seconds=value)
            elif unit in ["分钟", "分"]:
                return now + timedelta(minutes=value)
            elif unit in ["时", "小时"]:
                return now + timedelta(hours=value)
            elif unit in ["天"]:
                return now + timedelta(days=value)

        # 尝试匹配中文数字
        chinese_pattern = r"(一二三四五六七八九十|十?[一二三四五六七八九]|二十[一二三四五六七八九十]?|三十[一二]?)\s*(秒|分钟|分|时|小时|天|分钟后|秒后)"
        match = re.search(chinese_pattern, message)
        if match:
            num_str = match.group(1)
            unit = match.group(2).rstrip("后")

            value = parse_chinese_num(num_str)
            if value is not None:
                now = datetime.now()
                if unit in ["秒"]:
                    return now + timedelta(seconds=value)
                elif unit in ["分钟", "分"]:
                    return now + timedelta(minutes=value)
                elif unit in ["时", "小时"]:
                    return now + timedelta(hours=value)
                elif unit in ["天"]:
                    return now + timedelta(days=value)

        # 默认30分钟
        return datetime.now() + timedelta(minutes=30)

    def _infer_reminder_follow_up(self, message: str, match) -> str:
        """推断提醒内容"""
        if "泡面" in message or "泡面" in message:
            return "泡面好了"
        elif "煮" in message:
            return "煮好了"
        elif "点赞" in message or "点个赞" in message:
            return "点赞"
        elif "提醒" in message:
            return "提醒时间到了"
        return "时间到了"

    def _infer_follow_up(self, message: str, context_type: str) -> str:
        """根据上下文类型推断跟进内容"""
        if context_type == "activity":
            # 活动 -> 询问结果
            if any(kw in message for kw in ["课", "学"]):
                return "下课"
            elif any(kw in message for kw in ["班", "工作"]):
                return "下班"
            elif any(kw in message for kw in ["饭", "吃"]):
                return "吃完"
            elif any(kw in message for kw in ["锻炼", "健身", "跑步", "运动"]):
                return "锻炼完"
            elif any(kw in message for kw in ["电影", "看"]):
                return "看完"
            elif any(kw in message for kw in ["医院", "看病"]):
                return "看完医生"
            elif any(kw in message for kw in ["睡", "休息", "午休"]):
                return "醒来"
            elif any(kw in message for kw in ["出门", "出去"]):
                return "回来"
            return "回来"

        elif context_type == "plan":
            return "执行"

        return "后续"

    def _create_context(
        self,
        user_id: int,
        message: str,
        context_type: str,
        expectation: str,
        group_id: int = None,
    ) -> UserContext:
        """创建用户上下文"""
        import uuid

        return UserContext(
            context_id=str(uuid.uuid4()),
            user_id=user_id,
            context_type=ContextType(context_type),
            content=message,
            expectation=expectation,
            created_at=datetime.now(),
            follow_up_at=datetime.now() + timedelta(minutes=30),  # 默认30分钟后跟进
            relevance_score=1.0,
            metadata={"group_id": group_id},
        )

    def add_context(self, context: UserContext):
        """添加用户上下文"""
        user_id_str = str(context.user_id)

        if user_id_str not in self.user_contexts:
            self.user_contexts[user_id_str] = []

        # 检查是否重复（包括已发送的）
        for existing in self.user_contexts[user_id_str]:
            if existing.content == context.content:
                # 如果之前的还没有发送，更新它
                if not existing.follow_up_sent:
                    existing.follow_up_at = context.follow_up_at
                    existing.relevance_score = max(
                        existing.relevance_score, context.relevance_score
                    )
                    logger.info(
                        f"[IntelligentActiveChat] 更新已有上下文: user={context.user_id}, "
                        f"content={context.content[:30]}, follow_up_at={context.follow_up_at}"
                    )
                    self._save_persisted_data()
                    return
                else:
                    # 如果之前的已经发送了，创建新的（带时间戳区分）
                    context.content = f"{context.content} [重复#{datetime.now().strftime('%H:%M:%S')}]"
                    logger.info(
                        f"[IntelligentActiveChat] 检测到重复但已发送，创建新上下文: "
                        f"user={context.user_id}, content={context.content[:30]}"
                    )
                    break

        self.user_contexts[user_id_str].append(context)
        self._cleanup_old_contexts(user_id_str)
        self._save_persisted_data()
        logger.info(
            f"[IntelligentActiveChat] 添加新上下文: user={context.user_id}, "
            f"content={context.content[:30]}, type={context.context_type.value}, "
            f"follow_up_at={context.follow_up_at}"
        )

    def _cleanup_old_contexts(self, user_id: str):
        """清理过期的上下文"""
        now = datetime.now()
        expiry = timedelta(hours=self.context_expiry_hours)

        self.user_contexts[user_id] = [
            ctx
            for ctx in self.user_contexts[user_id]
            if (now - ctx.created_at) < expiry and not ctx.follow_up_sent
        ]

    def get_pending_contexts(self, user_id: int) -> List[UserContext]:
        """获取待跟进的上下文"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_contexts:
            return []

        now = datetime.now()
        pending = []

        for ctx in self.user_contexts[user_id_str]:
            if not ctx.follow_up_sent and ctx.follow_up_at and ctx.follow_up_at <= now:
                pending.append(ctx)

        # 按相关性排序
        pending.sort(key=lambda x: x.relevance_score, reverse=True)
        return pending

    async def generate_follow_up_message(self, context: UserContext) -> str:
        """根据上下文生成跟进消息 - 动态生成版本"""
        try:
            # 动态生成跟进消息
            return await self._generate_dynamic_follow_up(context)
        except Exception as e:
            logger.error(f"[ActiveChat] 动态生成跟进消息失败: {e}")
            return None

    async def _generate_dynamic_follow_up(self, context: UserContext) -> str:
        """动态生成跟进消息"""
        try:
            # 优先使用动态生成系统
            if self.dynamic_generator and self.dynamic_generator.is_initialized:
                # 准备上下文数据
                context_data = {
                    "expectation": context.expectation,
                    "content": context.content,
                    "context_type": context.context_type.value
                    if context.context_type
                    else None,
                    "metadata": context.metadata,
                    "created_at": context.created_at,
                }

                # 使用动态生成器生成消息
                message = await self.dynamic_generator.generate_message(
                    user_id=context.user_id, context=context_data
                )

                if message:
                    logger.debug(
                        f"[ActiveChat] 动态生成跟进消息成功: {message[:50]}..."
                    )
                    return message

            # 如果动态生成系统不可用，使用传统方法
            return self._generate_traditional_follow_up(context)

        except Exception as e:
            logger.error(f"[ActiveChat] 动态生成跟进消息失败: {e}")
            return self._generate_traditional_follow_up(context)

    def _generate_traditional_follow_up(self, context: UserContext) -> str:
        """传统跟进消息生成（备用）"""
        expectation = context.expectation
        # 传统生成逻辑 - 从人设配置中获取
        templates = self._get_personality_template("follow_up_templates", [])

        # 如果有配置模板，随机选择一个
        if templates:
            import random

            template = random.choice(templates)
            # 替换占位符
            template = template.replace("{expectation}", expectation)
            template = template.replace(
                "{content}", context.content[:20] if context.content else ""
            )
            return template

        # 回退到简单的默认消息
        if expectation == "下课":
            return "学完了？感觉怎么样。"
        elif expectation == "下班":
            return "下班了？今天辛苦了。"
        elif expectation == "吃完":
            return "吃完了？好吃吗。"
        elif expectation == "锻炼完":
            return "锻炼完了？累吗。"
        elif expectation == "看完":
            return "看完了？怎么样。"
        elif expectation == "看完医生":
            return "看完了？医生怎么说。"
        elif expectation == "醒来":
            return "醒了？休息好了吗。"
        elif expectation == "回来":
            return "回来了？今天怎么样。"
        elif expectation == "执行":
            return "事情怎么样了。"
        elif expectation == "提醒":
            return "提醒时间到了。"
        elif expectation == "泡面好了":
            return "泡面好了。去吃吧。"
        elif expectation == "点赞":
            return "该点赞了。"
        else:
            return f"{expectation}？怎么样了。"

    async def generate_greeting_message(self, time_key: str) -> str:
        """生成问候消息 - 动态生成版本"""
        try:
            # 优先使用动态生成系统
            if self.dynamic_generator and self.dynamic_generator.is_initialized:
                return await self._generate_dynamic_greeting(time_key)

            # 如果动态生成系统不可用，使用传统方法
            return self._generate_traditional_greeting(time_key)

        except Exception as e:
            logger.error(f"[ActiveChat] 生成问候消息失败: {e}")
            return "在。"

    async def _generate_dynamic_greeting(self, time_key: str) -> str:
        """动态生成问候消息"""
        try:
            # 检查动态生成器是否可用
            if not self.dynamic_generator:
                return self._generate_traditional_greeting(time_key)

            # 准备上下文数据
            context_data = {
                "time_key": time_key,
                "timestamp": datetime.now(),
            }

            # 使用动态生成器生成消息
            message = await self.dynamic_generator.generate_message(
                user_id=0,  # 问候消息没有特定用户
                context=context_data,
            )

            if message:
                logger.debug(f"[ActiveChat] 动态生成问候消息成功: {message[:50]}...")
                return message

            # 如果动态生成失败，使用传统方法
            return self._generate_traditional_greeting(time_key)

        except Exception as e:
            logger.error(f"[ActiveChat] 动态生成问候消息失败: {e}")
            return self._generate_traditional_greeting(time_key)

        except Exception as e:
            logger.error(f"[ActiveChat] 动态生成问候消息失败: {e}")
            return self._generate_traditional_greeting(time_key)

    def _generate_traditional_greeting(self, time_key: str) -> str:
        """传统问候消息生成（备用）"""
        # 使用人设配置中的问候语
        templates = self._get_personality_template("greetings", [])
        if templates:
            import random

            return random.choice(templates)

        # 回退到默认消息
        return "在。"

    async def start(self):
        """启动智能主动聊天管理器"""
        if self.running:
            logger.warning("[ActiveChat] 已在运行中，忽略启动请求")
            return

        self.running = True
        logger.info("=" * 60)
        logger.info("[ActiveChat] ========== 智能主动聊天管理器启动 ==========")
        logger.info(f"[ActiveChat]   - 检查间隔: {self.check_interval}秒")
        logger.info(f"[ActiveChat]   - 上下文过期时间: {self.context_expiry_hours}小时")
        logger.info(
            f"[ActiveChat]   - 问候功能: {'启用' if self.auto_trigger_enabled else '禁用'}"
        )
        logger.info(
            f"[ActiveChat]   - 已加载上下文数: {sum(len(v) for v in self.user_contexts.values())}"
        )
        logger.info(f"[ActiveChat]   - 已注册用户数: {len(self.user_preferences)}")

        # 初始化动态生成器
        if self.dynamic_generator:
            try:
                await self.dynamic_generator.initialize()
                logger.info(
                    f"[ActiveChat]   - 动态生成器: 已初始化 (插件数: {len(self.dynamic_generator.plugins)})"
                )
            except Exception as e:
                logger.error(f"[ActiveChat]   - 动态生成器初始化失败: {e}")
        else:
            logger.info("[ActiveChat]   - 动态生成器: 未启用")

        logger.info("=" * 60)

        # 启动检查循环
        asyncio.create_task(self._check_loop())
        logger.info("[ActiveChat] 检查循环已启动")

    async def stop(self):
        """停止智能主动聊天管理器"""
        if not self.running:
            logger.warning("[ActiveChat] 未运行，忽略停止请求")
            return

        self.running = False
        logger.info("[ActiveChat] 智能主动聊天管理器已停止")
        logger.info(
            f"[ActiveChat]   - 本次运行期间发送消息: {len(self.sent_messages)}条"
        )
        logger.info(f"[ActiveChat]   - 待发送消息: {len(self.pending_messages)}条")

    async def _check_loop(self):
        """检查循环 - 检查需要跟进的上下文"""
        check_count = 0
        while self.running:
            check_count += 1
            now = datetime.now()

            try:
                # 详细日志（每10次检查输出一次）
                if check_count % 10 == 1:
                    logger.info(
                        f"[ActiveChat] [#{check_count}] 检查开始 {now.strftime('%H:%M:%S')}"
                    )

                # 1. 检查上下文跟进
                context_count = await self._check_context_follow_ups()

                # 2. 检查定时问候
                greeting_count = await self._check_greetings()

                # 3. 检查定时主动聊天
                scheduled_count = await self._check_scheduled_messages()

                # 详细日志（每次都输出，帮助调试）
                total_pending = sum(
                    len(self.get_pending_contexts(int(k)))
                    for k in self.user_contexts.keys()
                )
                if context_count > 0 or total_pending > 0 or check_count % 10 == 1:
                    logger.info(
                        f"[ActiveChat] [#{check_count}] 检查完成: "
                        f"contexts={context_count}, greetings={greeting_count}, "
                        f"scheduled={scheduled_count}, pending_total={total_pending}"
                    )

            except Exception as e:
                logger.error(f"[ActiveChat] 检查循环异常: {e}", exc_info=True)

            await asyncio.sleep(self.check_interval)

    async def _check_context_follow_ups(self) -> int:
        """检查并执行上下文跟进，返回处理数量"""
        now = datetime.now()
        processed = 0

        for user_id_str, contexts in list(self.user_contexts.items()):
            user_id = int(user_id_str)
            pending = self.get_pending_contexts(user_id)

            for context in pending:
                # 检查冷却时间（提醒类消息使用特殊冷却时间）
                prefs = self.user_preferences.get(user_id_str, {})

                # 提醒类消息使用更短的冷却时间（10秒），避免延迟太久
                if context.context_type == ContextType.REMINDER:
                    min_interval = prefs.get("min_interval_reminder", 10)
                else:
                    min_interval = prefs.get("min_interval", 300)

                last_sent = prefs.get("last_message_time")

                if last_sent:
                    last_time = datetime.fromisoformat(last_sent)
                    elapsed = (now - last_time).total_seconds()
                    if elapsed < min_interval:
                        # 提醒类消息更宽容，即使在冷却中也考虑发送
                        if context.context_type == ContextType.REMINDER:
                            # 检查提醒时间是否已经过了很久（比如超过2分钟）
                            overdue_seconds = elapsed - min_interval
                            if overdue_seconds < 120:  # 超过2分钟才强制发送
                                logger.warning(
                                    f"[ActiveChat] 用户{user_id}提醒冷却中 "
                                    f"({elapsed:.0f}s/{min_interval}s)，跳过"
                                )
                                continue
                            else:
                                logger.warning(
                                    f"[ActiveChat] 用户{user_id}提醒已超时2分钟，强制发送"
                                )
                        else:
                            logger.warning(
                                f"[ActiveChat] 用户{user_id}冷却中 "
                                f"({elapsed:.0f}s/{min_interval}s)，跳过"
                            )
                            continue

                # 检查是否需要执行工具动作（如点赞、拍一拍等）
                expectation = context.expectation
                tool_action = self.EXPECTATION_TO_TOOL_ACTION.get(expectation)

                if (
                    tool_action
                    and hasattr(self.qq_net, "tool_registry")
                    and self.qq_net.tool_registry
                ):
                    # 执行工具动作
                    logger.info(
                        f"[ActiveChat] [工具动作] 用户={user_id} "
                        f"期望={expectation} -> 工具={tool_action}"
                    )

                    try:
                        from core.tool_adapter import ToolAdapter

                        adapter = ToolAdapter()
                        adapter.set_tool_registry(self.qq_net.tool_registry)

                        # 构建工具上下文
                        tool_context = {
                            "onebot_client": getattr(
                                self.qq_net, "onebot_client", None
                            ),
                            "send_like_callback": getattr(
                                getattr(self.qq_net, "onebot_client", None),
                                "send_like",
                                None,
                            )
                            if getattr(self.qq_net, "onebot_client", None)
                            else None,
                            "user_id": user_id,
                            "group_id": context.metadata.get("group_id"),
                            "message_type": "private"
                            if not context.metadata.get("group_id")
                            else "group",
                            "sender_name": "active_chat",
                        }

                        # 根据工具类型准备参数
                        args = {}
                        if tool_action == "qq_like":
                            args = {"target_user_id": user_id, "times": 1}
                        elif tool_action == "send_poke":
                            args = {
                                "target_user_id": user_id,
                                "group_id": context.metadata.get("group_id")
                                if context.metadata.get("group_id")
                                else None,
                            }

                        result = await adapter.execute_tool(
                            tool_action, args, tool_context
                        )
                        logger.info(f"工具动作已执行: {result}")

                        # 标记为已处理
                        context.follow_up_sent = True
                        prefs["last_message_time"] = now.isoformat()
                        self._save_persisted_data()
                        processed += 1

                        logger.info(
                            f"[ActiveChat] [工具动作成功] -> 用户{user_id} "
                            f"动作={tool_action}"
                        )
                        continue  # 跳过消息发送

                    except Exception as e:
                        logger.error(
                            f"[ActiveChat] 工具动作执行失败: {e}", exc_info=True
                        )
                        # 如果工具执行失败，回退到发送消息

                # 生成跟进消息（原有逻辑）
                follow_up_msg = await self.generate_follow_up_message(context)

                logger.info(
                    f"[ActiveChat] [上下文跟进] 用户={user_id} "
                    f"类型={context.context_type.value} "
                    f'内容="{context.content[:30]}..." '
                    f'预期="{context.expectation}"'
                )

                # 发送消息
                success = await self._send_follow_up(user_id, context, follow_up_msg)

                if success:
                    context.follow_up_sent = True
                    prefs["last_message_time"] = now.isoformat()
                    self._save_persisted_data()
                    processed += 1

                    logger.info(
                        f"[ActiveChat] [发送成功] -> 用户{user_id} "
                        f'"{follow_up_msg[:50]}..."'
                    )
                else:
                    logger.warning(
                        f"[ActiveChat] [发送失败] -> 用户{user_id} "
                        f'"{follow_up_msg[:50]}..."'
                    )

        return processed

    async def _check_greetings(self) -> int:
        """检查并发送问候消息"""
        now = datetime.now()
        sent = 0

        # 问候时间配置
        greeting_times = {
            "morning": (6, 9),  # 6-9点早安
            "afternoon": (11, 14),  # 11-14点午安
            "evening": (17, 21),  # 17-21点晚安
            "night": (21, 24),  # 21-24点晚安
        }

        for user_id_str, prefs in list(self.user_preferences.items()):
            if not prefs.get("enable_greeting", True):
                continue

            user_id = int(user_id_str)
            current_hour = now.hour

            # 检查是否在问候时间窗口
            greeting_key = None
            for key, (start, end) in greeting_times.items():
                if start <= current_hour < end:
                    greeting_key = key
                    break

            if not greeting_key:
                continue

            # 检查上次问候时间
            last_greeting = prefs.get("last_greeting_time")
            if last_greeting:
                last_time = datetime.fromisoformat(last_greeting)
                hours_since = (now - last_time).total_seconds() / 3600
                if hours_since < 4:  # 至少4小时问候一次
                    continue

            # 生成问候消息
            greeting_msg = await self.generate_greeting_message(greeting_key)

            logger.info(
                f"[ActiveChat] [定时问候] 用户={user_id} "
                f"时间={greeting_key} ({current_hour}点)"
            )

            success = await self.qq_net.send_private_message(user_id, greeting_msg)

            if success:
                prefs["last_greeting_time"] = now.isoformat()
                self._save_persisted_data()
                sent += 1

                logger.info(
                    f"[ActiveChat] [问候已发送] -> 用户{user_id} "
                    f'"{greeting_msg[:30]}..."'
                )

        return sent

    async def _check_scheduled_messages(self) -> int:
        """检查并执行定时消息"""
        now = datetime.now()
        sent = 0

        # 遍历定时消息
        for msg_id, message in list(self.pending_messages.items()):
            if message.status not in ["pending", "scheduled"]:
                continue

            # 检查是否到达发送时间
            if message.scheduled_time and message.scheduled_time > now:
                remaining = (message.scheduled_time - now).total_seconds()
                if remaining > 60:  # 只记录超过1分钟的消息
                    continue

            logger.info(
                f"[ActiveChat] [定时消息] ID={msg_id} "
                f"目标={message.target_type}:{message.target_id} "
                f"类型={message.trigger_type.value}"
            )

            # 发送消息
            success = await self._send_scheduled_message(msg_id, message)

            if success:
                sent += 1

        return sent

    async def _send_follow_up(
        self, user_id: int, context: UserContext, message: str
    ) -> bool:
        """发送跟进消息"""
        logger.debug(
            f'[ActiveChat] [_send_follow_up] 准备发送: user={user_id}, msg="{message[:50]}..."'
        )

        try:
            group_id = context.metadata.get("group_id")

            if group_id:
                logger.debug(f"[ActiveChat] 发送到群: group_id={group_id}")
                success = await self.qq_net.send_group_message(group_id, message)
            else:
                logger.debug(f"[ActiveChat] 发送到用户: user_id={user_id}")
                success = await self.qq_net.send_private_message(user_id, message)

            if success:
                logger.info(
                    f"[ActiveChat] [发送成功] user={user_id} "
                    f"type={context.context_type.value} "
                    f'msg="{message[:40]}"'
                )
            else:
                logger.warning(f"[ActiveChat] [发送失败] user={user_id}")

            return success

        except Exception as e:
            logger.error(f"[ActiveChat] [异常] 发送跟进消息失败: {e}", exc_info=True)
            return False

    async def _send_scheduled_message(
        self, msg_id: str, message: "ActiveMessage"
    ) -> bool:
        """发送定时消息"""
        try:
            logger.info(
                f"[ActiveChat] [定时消息] 发送: target={message.target_type}:{message.target_id} "
                f'content="{message.content[:50]}..."'
            )

            message.status = "sending"

            if message.target_type == "group":
                success = await self.qq_net.send_group_message(
                    message.target_id, message.content
                )
            else:
                success = await self.qq_net.send_private_message(
                    message.target_id, message.content
                )

            if success:
                message.status = "sent"
                message.sent_at = datetime.now()
                self.pending_messages.pop(msg_id, None)
                self.sent_messages.append(message)

                logger.info(
                    f"[ActiveChat] [定时消息成功] ID={msg_id} -> "
                    f"{message.target_type}:{message.target_id}"
                )
            else:
                message.status = "failed"
                message.retry_count += 1
                logger.warning(f"[ActiveChat] [定时消息失败] ID={msg_id}")

            self._save_persisted_data()
            return success

        except Exception as e:
            logger.error(f"[ActiveChat] [定时消息异常] ID={msg_id}: {e}", exc_info=True)
            return False

    def set_user_preference(self, user_id: int, preferences: Dict[str, Any]):
        """设置用户偏好"""
        user_id_str = str(user_id)
        self.user_preferences.setdefault(user_id_str, {}).update(preferences)
        self._save_persisted_data()
        logger.info(f"[IntelligentActiveChat] 用户 {user_id} 偏好已更新: {preferences}")

    def get_user_preference(self, user_id: int) -> Dict[str, Any]:
        """获取用户偏好"""
        return self.user_preferences.get(str(user_id), {}).copy()

    def get_pending_contexts_info(self, user_id: int) -> List[Dict]:
        """获取用户的待跟进上下文信息"""
        contexts = self.get_pending_contexts(user_id)
        return [ctx.to_dict() for ctx in contexts]

    def cancel_context(self, context_id: str, user_id: int) -> bool:
        """取消上下文跟进"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_contexts:
            return False

        for ctx in self.user_contexts[user_id_str]:
            if ctx.context_id == context_id:
                ctx.follow_up_sent = True  # 标记为已发送
                self._save_persisted_data()
                logger.info(f"[IntelligentActiveChat] 上下文已取消: {context_id}")
                return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        total_contexts = sum(len(v) for v in self.user_contexts.values())
        pending_contexts = sum(
            len(self.get_pending_contexts(int(k))) for k in self.user_contexts.keys()
        )

        return {
            "total_contexts": total_contexts,
            "pending_contexts": pending_contexts,
            "total_users": len(self.user_contexts),
            "running": self.running,
            "last_check": datetime.now().isoformat(),
        }

    def get_pending_messages(self) -> List["ActiveMessage"]:
        """获取待发消息列表"""
        return list(self.pending_messages.values())


@dataclass
class ActiveMessage:
    """主动消息定义"""

    message_id: str
    target_type: str  # "group" 或 "private"
    target_id: int
    content: str
    trigger_type: TriggerType
    priority: MessagePriority
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_time: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, scheduled, sent, failed, cancelled
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查消息是否已过期"""
        if self.scheduled_time:
            expire_after = self.metadata.get("expire_after_hours", 24)
            expire_time = self.scheduled_time + timedelta(hours=expire_after)
            return datetime.now() > expire_time
        return False

    def should_retry(self) -> bool:
        """检查是否应该重试"""
        return self.status == "failed" and self.retry_count < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "content": self.content,
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "trigger_config": self.trigger_config,
            "created_at": self.created_at.isoformat(),
            "scheduled_time": self.scheduled_time.isoformat()
            if self.scheduled_time
            else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveMessage":
        """从字典创建"""
        # 解析时间
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now()
        )
        scheduled_time = (
            datetime.fromisoformat(data["scheduled_time"])
            if data.get("scheduled_time")
            else None
        )
        sent_at = (
            datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None
        )

        return cls(
            message_id=data["message_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            content=data["content"],
            trigger_type=TriggerType(data["trigger_type"]),
            priority=MessagePriority(data["priority"]),
            trigger_config=data.get("trigger_config", {}),
            created_at=created_at,
            scheduled_time=scheduled_time,
            sent_at=sent_at,
            status=data.get("status", "pending"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )


class ActiveChatManager:
    """主动聊天管理器"""

    def __init__(self, qq_net):
        self.qq_net = qq_net
        self.pending_messages: Dict[str, ActiveMessage] = {}
        self.sent_messages: List[ActiveMessage] = []
        self.user_preferences: Dict[int, Dict[str, Any]] = {}  # 用户聊天偏好
        self.running = False

        # 触发器和检查器
        self.triggers: List[Any] = []
        self.check_interval = 60  # 检查间隔（秒）

        # 自动触发配置
        self.auto_trigger_enabled = True  # 默认启用自动触发
        self.trigger_cooldown = 300  # 触发冷却时间（秒）
        self.last_trigger_times: Dict[int, datetime] = {}  # 用户最后触发时间

        # 动态问候消息生成
        self._greeting_templates = {}  # 空模板，使用动态生成

        # 数据持久化路径
        self.data_dir = None
        self._init_data_dir()

        # 加载持久化数据
        self._load_persisted_data()

    def _init_data_dir(self):
        """初始化数据目录"""
        try:
            from pathlib import Path

            base_dir = (
                Path(__file__).parent.parent.parent.parent / "data" / "active_chat"
            )
            base_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir = base_dir
            logger.info(f"[ActiveChatManager] 数据目录: {self.data_dir}")
        except Exception as e:
            logger.error(f"[ActiveChatManager] 初始化数据目录失败: {e}")
            self.data_dir = None

    def _load_persisted_data(self):
        """加载持久化数据"""
        if not self.data_dir:
            return

        try:
            # 加载待发消息
            pending_path = self.data_dir / "pending_messages.json"
            if pending_path.exists():
                with open(pending_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for msg_data in data:
                        try:
                            msg = ActiveMessage.from_dict(msg_data)
                            self.pending_messages[msg.message_id] = msg
                        except Exception as e:
                            logger.error(f"[ActiveChatManager] 加载消息失败: {e}")

            # 加载已发消息
            sent_path = self.data_dir / "sent_messages.json"
            if sent_path.exists():
                with open(sent_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for msg_data in data:
                        try:
                            msg = ActiveMessage.from_dict(msg_data)
                            self.sent_messages.append(msg)
                        except Exception as e:
                            logger.error(f"[ActiveChatManager] 加载已发消息失败: {e}")

            # 加载用户偏好
            prefs_path = self.data_dir / "user_preferences.json"
            if prefs_path.exists():
                with open(prefs_path, "r", encoding="utf-8") as f:
                    self.user_preferences = json.load(f)

            logger.info(
                f"[ActiveChatManager] 数据加载完成: {len(self.pending_messages)}待发, {len(self.sent_messages)}已发, {len(self.user_preferences)}用户"
            )

        except Exception as e:
            logger.error(f"[ActiveChatManager] 加载数据失败: {e}")

    def _save_persisted_data(self):
        """保存持久化数据"""
        if not self.data_dir:
            return

        try:
            # 保存待发消息
            pending_path = self.data_dir / "pending_messages.json"
            pending_data = [msg.to_dict() for msg in self.pending_messages.values()]
            with open(pending_path, "w", encoding="utf-8") as f:
                json.dump(pending_data, f, ensure_ascii=False, indent=2)

            # 保存已发消息（只保存最近1000条）
            sent_path = self.data_dir / "sent_messages.json"
            recent_sent = (
                self.sent_messages[-1000:]
                if len(self.sent_messages) > 1000
                else self.sent_messages
            )
            sent_data = [msg.to_dict() for msg in recent_sent]
            with open(sent_path, "w", encoding="utf-8") as f:
                json.dump(sent_data, f, ensure_ascii=False, indent=2)

            # 保存用户偏好
            prefs_path = self.data_dir / "user_preferences.json"
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)

            logger.debug(f"[ActiveChatManager] 数据保存完成")

        except Exception as e:
            logger.error(f"[ActiveChatManager] 保存数据失败: {e}")

    async def schedule_message(
        self,
        target_type: str,
        target_id: int,
        content: str,
        trigger_type: TriggerType = TriggerType.TIME,
        trigger_config: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        安排主动消息

        Args:
            target_type: 目标类型，"group" 或 "private"
            target_id: 目标ID（群号或用户QQ号）
            content: 消息内容
            trigger_type: 触发类型
            trigger_config: 触发器配置
            priority: 消息优先级
            metadata: 额外元数据

        Returns:
            消息ID
        """
        import uuid

        # 生成消息ID
        message_id = str(uuid.uuid4())

        # 检查用户偏好
        if not self._check_user_preference(target_id):
            raise ValueError(f"用户 {target_id} 不允许主动消息")

        # 构建消息
        trigger_config = trigger_config or {}
        metadata = metadata or {}

        # 设置计划时间
        scheduled_time = None
        if trigger_type == TriggerType.TIME:
            scheduled_time = self._parse_schedule_time(trigger_config)

        message = ActiveMessage(
            message_id=message_id,
            target_type=target_type,
            target_id=target_id,
            content=content,
            trigger_type=trigger_type,
            priority=priority,
            trigger_config=trigger_config,
            scheduled_time=scheduled_time,
            metadata=metadata,
        )

        # 验证消息
        if not self._validate_message(message):
            raise ValueError("消息验证失败")

        # 添加到待发队列
        self.pending_messages[message_id] = message

        # 持久化保存
        self._save_persisted_data()

        logger.info(
            f"[ActiveChatManager] 消息已安排: {message_id} -> {target_type}:{target_id}"
        )

        return message_id

    def _check_user_preference(self, user_id: int) -> bool:
        """检查用户是否允许主动消息"""
        user_prefs = self.user_preferences.get(str(user_id), {})

        # 默认允许，除非用户明确拒绝
        allow_active = user_prefs.get("allow_active_chat", True)

        # 检查静默时段
        if allow_active:
            quiet_hours = user_prefs.get("quiet_hours", [])
            current_hour = datetime.now().hour
            if current_hour in quiet_hours:
                logger.debug(
                    f"[ActiveChatManager] 用户 {user_id} 处于静默时段 {current_hour}点"
                )
                return False

        return allow_active

    def _parse_schedule_time(self, trigger_config: Dict[str, Any]) -> datetime:
        """解析计划时间"""
        now = datetime.now()

        # 解析cron表达式
        if "cron" in trigger_config:
            cron_expr = trigger_config["cron"]
            # 简化实现，只支持基本格式
            # TODO: 实现完整的cron解析
            return now + timedelta(minutes=1)

        # 解析具体时间
        elif "time" in trigger_config:
            time_str = trigger_config["time"]
            try:
                if ":" in time_str:
                    # HH:MM 格式
                    hour, minute = map(int, time_str.split(":"))
                    scheduled = datetime(now.year, now.month, now.day, hour, minute)
                    if scheduled <= now:
                        scheduled += timedelta(days=1)
                    return scheduled
                else:
                    # 相对时间，如 "10分钟后"
                    import re

                    match = re.search(r"(\d+)\s*分钟后", time_str)
                    if match:
                        minutes = int(match.group(1))
                        return now + timedelta(minutes=minutes)
            except Exception as e:
                logger.error(f"[ActiveChatManager] 解析时间失败: {e}")

        # 默认：1分钟后
        return now + timedelta(minutes=1)

    def _validate_message(self, message: ActiveMessage) -> bool:
        """验证消息合法性"""
        # 检查目标ID
        if message.target_id <= 0:
            return False

        # 检查消息内容
        if not message.content or len(message.content.strip()) == 0:
            return False

        # 检查发送时机
        if message.scheduled_time and message.scheduled_time < datetime.now():
            # 如果计划时间已过，调整为立即发送
            message.scheduled_time = datetime.now() + timedelta(seconds=10)

        # 检查每日消息限制
        user_id = message.target_id
        today = datetime.now().date()

        # 统计今日已发送消息
        today_sent = sum(
            1
            for msg in self.sent_messages
            if msg.target_id == user_id and msg.sent_at and msg.sent_at.date() == today
        )

        max_daily = self.user_preferences.get(str(user_id), {}).get(
            "max_daily_messages", 10
        )
        if today_sent >= max_daily:
            logger.warning(
                f"[ActiveChatManager] 用户 {user_id} 今日消息已达上限: {today_sent}/{max_daily}"
            )
            return False

        return True

    async def start(self):
        """启动主动聊天管理器"""
        if self.running:
            return

        self.running = True
        logger.info("[ActiveChatManager] 主动聊天管理器已启动")

        # 启动检查循环
        asyncio.create_task(self._check_loop())

    async def stop(self):
        """停止主动聊天管理器"""
        self.running = False
        logger.info("[ActiveChatManager] 主动聊天管理器已停止")

    async def _check_loop(self):
        """检查循环"""
        while self.running:
            try:
                await self._check_and_send_messages()
                await self._check_triggers()

            except Exception as e:
                logger.error(f"[ActiveChatManager] 检查循环异常: {e}")

            # 等待下一次检查
            await asyncio.sleep(self.check_interval)

    async def _check_and_send_messages(self):
        """检查并发送待发消息"""
        now = datetime.now()
        messages_to_send = []

        # 找出需要发送的消息
        for msg_id, message in list(self.pending_messages.items()):
            # 检查消息状态
            if message.status not in ["pending", "scheduled", "failed"]:
                continue

            # 检查计划时间
            if message.scheduled_time and message.scheduled_time <= now:
                messages_to_send.append((msg_id, message))
            elif (
                not message.scheduled_time
                and message.trigger_type == TriggerType.MANUAL
            ):
                # 手动触发的消息立即发送
                messages_to_send.append((msg_id, message))

        # 按优先级排序
        messages_to_send.sort(key=lambda x: x[1].priority.value, reverse=True)

        # 发送消息
        for msg_id, message in messages_to_send:
            await self._send_message(msg_id, message)

    async def _send_message(self, msg_id: str, message: ActiveMessage):
        """发送消息"""
        try:
            # 更新状态
            message.status = "sending"

            # 发送消息
            if message.target_type == "group":
                await self.qq_net.send_group_message(message.target_id, message.content)
            else:
                await self.qq_net.send_private_message(
                    message.target_id, message.content
                )

            # 更新状态
            message.status = "sent"
            message.sent_at = datetime.now()

            # 移动到已发列表
            self.pending_messages.pop(msg_id, None)
            self.sent_messages.append(message)

            # 限制已发列表大小
            if len(self.sent_messages) > 1000:
                self.sent_messages = self.sent_messages[-1000:]

            # 记录发送历史
            await self._record_sent_message(message)

            # 保存数据
            self._save_persisted_data()

            logger.info(
                f"[ActiveChatManager] 消息已发送: {msg_id} -> {message.target_type}:{message.target_id}"
            )

        except Exception as e:
            # 处理失败
            await self._handle_send_failure(msg_id, message, e)

    async def _handle_send_failure(
        self, msg_id: str, message: ActiveMessage, error: Exception
    ):
        """处理发送失败"""
        logger.error(f"[ActiveChatManager] 消息发送失败 {msg_id}: {error}")

        message.status = "failed"
        message.retry_count += 1

        # 检查是否需要重试
        if message.should_retry():
            # 安排重试
            retry_delay = min(300 * (2**message.retry_count), 3600)  # 指数退避
            message.scheduled_time = datetime.now() + timedelta(seconds=retry_delay)
            message.status = "pending"

            logger.info(
                f"[ActiveChatManager] 消息 {msg_id} 将在 {retry_delay} 秒后重试"
            )
        else:
            # 重试次数用尽
            logger.error(f"[ActiveChatManager] 消息 {msg_id} 重试次数用尽")

            # 发送失败通知（可选）
            await self._send_failure_notification(message, error)

        # 保存数据
        self._save_persisted_data()

    async def _record_sent_message(self, message: ActiveMessage):
        """记录已发送消息到记忆系统"""
        try:
            memory_net = getattr(self.qq_net, "memory_net", None)
            if not memory_net:
                return

            await memory_net.record_active_chat(
                target_id=message.target_id,
                content=message.content,
                message_type=message.target_type,
                trigger_type=message.trigger_type.value,
                priority=message.priority.value,
                timestamp=message.sent_at or datetime.now(),
                metadata=message.metadata,
            )

        except Exception as e:
            logger.warning(f"[ActiveChatManager] 记录到记忆系统失败: {e}")

    async def _send_failure_notification(
        self, message: ActiveMessage, error: Exception
    ):
        """发送失败通知"""
        # 可以在这里实现失败通知逻辑
        # 例如：发送给管理员，或记录到日志系统
        pass

    async def _check_triggers(self):
        """检查触发器"""
        # 这里可以集成各种触发器
        # 例如：定时触发器、事件触发器、条件触发器

        # 示例：早安问候触发器
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:
            await self._trigger_morning_greetings()

    async def _trigger_morning_greetings(self):
        """触发早安问候"""
        # 这里可以实现早安问候逻辑
        # 例如：向所有允许主动聊天的用户发送早安问候
        pass

    def set_user_preference(self, user_id: int, preferences: Dict[str, Any]):
        """设置用户偏好"""
        user_id_str = str(user_id)

        if user_id_str not in self.user_preferences:
            self.user_preferences[user_id_str] = {}

        self.user_preferences[user_id_str].update(preferences)

        # 保存数据
        self._save_persisted_data()

        logger.info(f"[ActiveChatManager] 用户 {user_id} 偏好已更新: {preferences}")

    def get_user_preference(self, user_id: int) -> Dict[str, Any]:
        """获取用户偏好"""
        return self.user_preferences.get(str(user_id), {}).copy()

    def get_pending_messages(self) -> List[ActiveMessage]:
        """获取待发消息列表"""
        return list(self.pending_messages.values())

    def get_sent_messages(self, limit: int = 100) -> List[ActiveMessage]:
        """获取已发消息列表"""
        return (
            self.sent_messages[-limit:]
            if len(self.sent_messages) > limit
            else self.sent_messages
        )

    def cancel_message(self, message_id: str) -> bool:
        """取消消息"""
        if message_id in self.pending_messages:
            message = self.pending_messages[message_id]
            message.status = "cancelled"
            self.pending_messages.pop(message_id, None)

            # 保存数据
            self._save_persisted_data()

            logger.info(f"[ActiveChatManager] 消息已取消: {message_id}")
            return True

        return False

    def cleanup_expired_messages(self):
        """清理过期消息"""
        expired_ids = []

        for msg_id, message in self.pending_messages.items():
            if message.is_expired():
                expired_ids.append(msg_id)

        for msg_id in expired_ids:
            self.pending_messages.pop(msg_id, None)

        if expired_ids:
            logger.info(f"[ActiveChatManager] 清理了 {len(expired_ids)} 个过期消息")
            self._save_persisted_data()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        now = datetime.now()
        today = now.date()

        # 今日统计数据
        today_sent = sum(
            1
            for msg in self.sent_messages
            if msg.sent_at and msg.sent_at.date() == today
        )

        today_failed = sum(
            1
            for msg in self.sent_messages
            if msg.status == "failed" and msg.sent_at and msg.sent_at.date() == today
        )

        return {
            "total_pending": len(self.pending_messages),
            "total_sent": len(self.sent_messages),
            "today_sent": today_sent,
            "today_failed": today_failed,
            "total_users": len(self.user_preferences),
            "running": self.running,
            "last_check": now.isoformat(),
        }
