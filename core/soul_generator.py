"""
灵魂发生器 (Soul Generator) - 弥娅的"灵魂"系统
让弥娅拥有类似人类的情绪、认知和行为模式

核心特性：
1. 情绪池 - 完整人类情感图谱（70+情绪类别）
2. 情境检测器 - 识别关系/时间/话题/情绪状态
3. 心理学剖析引擎 - 归因/识别/预测/反思/调节
4. 行为引擎 - 意图残留追踪（未完成意图）
5. 情绪记忆锚点 - 记住情绪事件而非细节
6. 情绪恢复曲线 - 自然衰减机制
7. 社交面具 - 真实情绪与表达分离
"""

import logging
import time
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("Miya.灵魂发生器")


def _load_config() -> Dict:
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "soul_generator_config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[灵魂发生器] 配置文件加载失败: {e}，使用默认配置")
        return {}


# 加载配置
_CONFIG = _load_config()


class EmotionCategory(Enum):
    """情绪分类 - 完整人类情感图谱（70+情绪类别）"""

    # ========== 基础情绪 (Ekman 6大) ==========
    JOY = "喜悦"
    SADNESS = "悲伤"
    FEAR = "恐惧"
    ANGER = "愤怒"
    SURPRISE = "惊讶"
    DISGUST = "厌恶"

    # ========== 复合情绪 - 爱恨情仇 ==========
    LOVE = "爱"
    HATE = "恨"
    ENVY = "羡慕"
    JEALOUSY = "嫉妒"
    SHAME = "羞耻"
    GUILT = "愧疚"
    PRIDE = "骄傲"
    EMBARRASSMENT = "尴尬"

    # ========== 复合情绪 - 思念回忆 ==========
    NOSTALGIA = "怀旧"
    LONGING = "思念"
    MISSING = "挂念"

    # ========== 复合情绪 - 心理状态 ==========
    LOSS = "失落"
    RELIEF = "释然"
    HEARTBEAT = "心动"
    HEAL = "治愈"
    HEARTACHE = "心疼"
    JEALOUS = "吃醋"
    TSUNDERE = "傲娇"
    POUT = "赌气"
    GRIEVANCE = "委屈"
    FRUSTRATION = "窝火"
    OPPRESSED = "憋屈"
    HEARTBLOCK = "心塞"

    # ========== 状态情绪 - 幸福满足 ==========
    HAPPY = "幸福"
    SATISFIED = "满足"
    BLISS = "甜蜜"
    TOUCHED = "感动"
    GRATEFUL = "感恩"

    # ========== 状态情绪 - 消极状态 ==========
    CONFUSED = "迷茫"
    TIRED = "疲惫"
    ANXIOUS = "焦虑"
    PEACEFUL = "平静"
    FULFILLED = "充实"
    EMPTY = "空虚"
    LAZY = "慵懒"
    COMFORTABLE = "惬意"
    NERVOUS = "紧张"
    CALM = "坦然"
    CONFLICTED = "纠结"
    EAGER = "期待"
    HOPEFUL = "希望"
    HELPLESS = "无助"
    IMPATIENT = "急躁"

    # ========== 关系情绪 - 亲密距离 ==========
    ATTACHMENT = "依恋"
    DISTANCE = "疏离"
    TRUST = "信任"
    SUSPICION = "怀疑"
    CLOSE = "亲近"
    RESIST = "抵触"
    DISAPPOINT = "失望"
    DEPENDENT = "依赖"
    CLINGY = "粘人"
    PUSH_AWAY = "推开"
    HOT_COLD = "忽冷忽热"
    CARING = "关怀"
    PROTECTIVE = "保护欲"

    # ========== 自我情绪 - 自我认知 ==========
    SELF_DOUBT = "自我怀疑"
    SELF_AFFIRM = "自我肯定"
    INFERIORITY = "自卑"
    NARCISSISM = "自恋"
    INSECURE = "不安全"

    # ========== 行为情绪 - 行动倾向 ==========
    MOTIVATED = "积极"
    PASSIVE = "消极"
    AGGRESSIVE = "攻击性"
    DEFENSIVE = "防御"
    AVOIDANT = "逃避"
    COMPULSIVE = "强迫"

    # ========== 社交情绪 - 交往相关 ==========
    SYMPATHY = "同情"
    EMPATHY = "共情"
    INDIFERENT = "冷漠"
    WARM = "温暖"
    CLOSED = "封闭"

    # ========== 特殊情绪 - 复杂心理 ==========
    BITTERSWEET = "五味杂陈"
    OVERWHELMED = "不知所措"
    VULNERABLE = "脆弱"
    RESILIENT = "坚韧"
    CONTENT = "安然"
    RESTLESS = "烦躁"


class ContextType(Enum):
    """情境类型"""

    # 关系情境
    NEW_KNOW = "刚认识"
    ACQUAINTANCE = "认识"
    FAMILIAR = "熟悉"
    CLOSE = "亲近"
    INTIMATE = "亲密"
    COLD_WAR = "冷战"
    FIGHTING = "吵架中"
    RECONCILING = "和好中"

    # 时间情境
    JUST_WOKE_UP = "刚睡醒"
    MORNING = "早晨"
    AFTERNOON = "下午"
    EVENING = "傍晚"
    LATE_NIGHT = "深夜"
    JUST_BUSY = "刚忙完"
    LONG_IDLE = "空闲中"
    IN_CONVERSATION = "连续对话中"

    # 话题情境
    CASUAL = "闲聊"
    SERIOUS = "正事"
    APOLOGY = "道歉"
    CONFESSION = "表白"
    COMPLAINT = "抱怨"
    QUESTION = "询问"
    SHARE = "分享"
    REQUEST = "请求"
    JOKE = "玩笑"

    # 情绪状态
    HAPPY = "开心"
    EXCITED = "兴奋"
    ANGRY = "生气"
    SAD = "难过"
    LOW = "低落"
    NEUTRAL = "中性"
    ANXIOUS = "焦虑"
    CALM = "平静"


@dataclass
class Emotion:
    """情绪单元"""

    category: EmotionCategory
    value: float = 50  # 0-100
    expression_threshold: float = 40  # 超过此值会表达
    decay_rate: float = 0.02  # 衰减率

    # 情绪溯源
    trigger_source: Optional[str] = None  # 触发源
    trigger_context: Optional[str] = None  # 触发情境
    timestamp: float = field(default_factory=time.time)

    # 社交面具（真实情绪 vs 表达情绪）
    real_value: float = 50  # 真实情绪值
    expressed_value: float = 50  # 表达出的情绪值
    mask_factor: float = 0.0  # 面具系数：0=完全真实，1=完全隐藏


@dataclass
class PendingIntent:
    """未完成的意图"""

    intent: str  # 想做的事
    context: str  # 相关上下文
    priority: int = 5  # 优先级 1-10
    attempts: int = 0  # 已尝试次数
    created_at: float = field(default_factory=time.time)
    last_attempt: float = field(default_factory=time.time)

    def can_activate(self) -> bool:
        """检查是否可以激活"""
        return self.attempts < 3

    def record_attempt(self):
        """记录一次尝试"""
        self.attempts += 1
        self.last_attempt = time.time()


@dataclass
class Cognition:
    """认知单元"""

    key: str  # 认知主题
    value: str  # 认知内容
    confidence: float = 0.5  # 置信度 0-1
    source: str = ""  # 来源
    created_at: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)


@dataclass
class EmotionMemory:
    """情绪记忆锚点"""

    event: str  # 事件描述
    emotion: str  # 当时情绪
    intensity: float = 50  # 强度
    timestamp: float = field(default_factory=time.time)
    context: str = ""  # 当时上下文


@dataclass
class PsychologicalAnalysis:
    """心理学剖析结果"""

    attribution: str = ""  # 归因
    recognition: str = ""  # 识别
    prediction: str = ""  # 预测
    reflection: str = ""  # 自我反思
    regulation: str = ""  # 情绪调节


class ContextDetector:
    """
    语意情境检测器 - 增强版
    识别关系/时间/话题/情绪状态
    """

    def __init__(self):
        self.current_context: Dict[str, Any] = {
            "relationship": ContextType.FAMILIAR,
            "time": ContextType.IN_CONVERSATION,
            "topic": ContextType.CASUAL,
            "miya_mood": ContextType.CALM,
            "last_interaction": "",
            "emotion_history": [],
            "conversation_count": 0,  # 对话轮次
            "last_topic": None,
            "emotion_trend": [],  # 情绪趋势
        }
        # 历史消息统计
        self._message_count = 0
        self._last_user_message_time = 0

    def detect(self, message: str, history: List[Dict], miya_state: Dict) -> Dict:
        """检测当前情境 - 增强版"""
        # 更新对话统计
        self._message_count += 1
        self._last_user_message_time = time.time()

        context = {
            "relationship": self._detect_relationship(history),
            "time": self._detect_time_context(),
            "topic": self._detect_topic(message),
            "miya_mood": self._detect_miya_mood(miya_state),
            "interaction": self._detect_interaction_type(message, history),
            "semantic_interpretation": self._interpret_semantic(message, history),
            "conversation_count": self._message_count,
            "last_topic": self.current_context.get("last_topic"),
            "emotion_trend": self._detect_emotion_trend(history),
        }
        self.current_context.update(context)

        # 记录话题
        if context["topic"]:
            self.current_context["last_topic"] = context["topic"]

        return context

    def _detect_relationship(self, history: List[Dict]) -> ContextType:
        """检测关系情境 - 增强版"""
        if not history:
            return ContextType.NEW_KNOW

        recent_messages = history[-10:] if len(history) > 10 else history

        # 统计关键词出现次数
        intimate_count = 0
        cold_count = 0
        close_count = 0

        for msg in recent_messages:
            content = msg.get("content", "").lower()

            # 亲密表达
            intimate_words = [
                "爱",
                "想",
                "喜欢",
                "宝贝",
                "亲爱的",
                "么么",
                "爱你",
                "么么哒",
            ]
            intimate_count += sum(1 for word in intimate_words if word in content)

            # 冷漠/生气
            cold_words = ["冷战", "生气", "不理", "算了", "不管了", "滚", "走开"]
            cold_count += sum(1 for word in cold_words if word in content)

            # 亲近表达
            close_words = ["我们", "一起", "陪伴", "并肩", "共振"]
            close_count += sum(1 for word in close_words if word in content)

        # 根据统计判断关系
        if cold_count >= 2:
            return ContextType.COLD_WAR
        elif intimate_count >= 2:
            return ContextType.INTIMATE
        elif close_count >= 2:
            return ContextType.CLOSE
        elif intimate_count >= 1:
            return ContextType.CLOSE
        elif len(history) < 3:
            return ContextType.ACQUAINTANCE

        return ContextType.FAMILIAR

    def _detect_time_context(self) -> ContextType:
        """检测时间情境 - 增强版"""
        current_hour = time.localtime().tm_hour
        minute = time.localtime().tm_min

        if 5 <= current_hour < 8:
            return ContextType.JUST_WOKE_UP
        elif 8 <= current_hour < 12:
            return ContextType.MORNING
        elif 12 <= current_hour < 14:
            return ContextType.AFTERNOON  # 午休
        elif 14 <= current_hour < 18:
            return ContextType.AFTERNOON
        elif 18 <= current_hour < 22:
            return ContextType.EVENING
        elif 22 <= current_hour or current_hour < 2:
            return ContextType.LATE_NIGHT
        else:
            return ContextType.IN_CONVERSATION

    def _detect_topic(self, message: str) -> ContextType:
        """检测话题情境 - 增强版"""
        msg = message.lower()

        # 从配置读取话题关键词
        topic_keywords = _CONFIG.get("TOPIC_KEYWORDS", {})
        topic_context_map = _CONFIG.get("TOPIC_CONTEXT_MAP", {})

        context_map = {
            "APOLOGY": ContextType.APOLOGY,
            "CONFESSION": ContextType.CONFESSION,
            "COMPLAINT": ContextType.COMPLAINT,
            "QUESTION": ContextType.QUESTION,
            "SHARE": ContextType.SHARE,
            "REQUEST": ContextType.REQUEST,
            "JOKE": ContextType.JOKE,
            "SERIOUS": ContextType.SERIOUS,
        }

        # 优先级：道歉 > 表白 > 抱怨 > 请求 > 分享 > 询问 > 玩笑 > 闲聊
        for topic in [
            "APOLOGY",
            "CONFESSION",
            "COMPLAINT",
            "REQUEST",
            "SHARE",
            "QUESTION",
            "JOKE",
        ]:
            keywords = topic_keywords.get(topic, [])
            if any(word in msg for word in keywords):
                context_str = topic_context_map.get(topic, "CASUAL")
                return context_map.get(context_str, ContextType.CASUAL)

        # 检查其他关键词
        if any(word in msg for word in topic_keywords.get("SERIOUS", [])):
            return ContextType.SERIOUS

        return ContextType.CASUAL

    def _detect_miya_mood(self, miya_state: Dict) -> ContextType:
        """检测弥娅当前情绪 - 增强版"""
        dominant = miya_state.get("dominant_emotion", "平静")

        mood_map = {
            "开心": ContextType.HAPPY,
            "幸福": ContextType.HAPPY,
            "兴奋": ContextType.EXCITED,
            "生气": ContextType.ANGRY,
            "愤怒": ContextType.ANGRY,
            "难过": ContextType.SAD,
            "悲伤": ContextType.SAD,
            "低落": ContextType.LOW,
            "失落": ContextType.LOW,
            "焦虑": ContextType.ANXIOUS,
            "紧张": ContextType.ANXIOUS,
            "平静": ContextType.CALM,
            "坦然": ContextType.CALM,
            "中性": ContextType.NEUTRAL,
        }
        return mood_map.get(dominant, ContextType.NEUTRAL)

    def _detect_interaction_type(self, message: str, history: List[Dict]) -> str:
        """检测互动类型 - 增强版"""
        msg = message.strip()

        if not msg:
            return "empty"

        # 极短回复
        minimal_keywords = _CONFIG.get(
            "MINIMAL_RESPONSE_KEYWORDS", ["嗯", "哦", "好吧", "呃", "额"]
        )
        if msg in minimal_keywords:
            return "minimal_response"

        # 长回复
        if len(msg) > 100:
            return "long_response"

        # 积极情绪
        positive_words = ["哈哈", "笑", "好玩", "太棒了", "太好了", "哈哈哈", "笑死"]
        if any(word in msg.lower() for word in positive_words):
            return "positive"

        # 消极/放弃
        resigned_words = ["算了", "随便", "好吧", "就这样", "管它呢"]
        if any(word in msg.lower() for word in resigned_words):
            return "resigned"

        # 提问
        if any(
            word in msg
            for word in ["？", "?", "怎么", "为什么", "什么", "是不是", "有没有"]
        ):
            return "question"

        # 分享
        if any(word in msg for word in ["告诉你", "给你说", "分享", "说件事", "我刚"]):
            return "share"

        # 道歉
        if any(word in msg for word in ["对不起", "抱歉", "不好意思", "是我的错"]):
            return "apology"

        # 表白
        if any(word in msg for word in ["喜欢你", "爱你", "想你了", "表白"]):
            return "confession"

        return "normal"

    def _detect_emotion_trend(self, history: List[Dict]) -> List[str]:
        """检测情绪趋势 - 基于历史消息"""
        if not history:
            return []

        recent = history[-5:]
        trends = []

        for msg in recent:
            content = msg.get("content", "").lower()

            if any(word in content for word in ["哈哈", "好", "棒", "喜欢"]):
                trends.append("up")
            elif any(word in content for word in ["累", "烦", "算了", "好吧"]):
                trends.append("down")

        return trends[-3:]  # 保留最近3个

    def _interpret_semantic(self, message: str, history: List[Dict]) -> Dict:
        """语义解读 - 增强版：同一句话在不同情境下不同含义"""
        msg = message.strip().lower()
        context = self.current_context

        interpretations = []

        # ========== 对"嗯"类的解读 ==========
        if msg in ["嗯", "嗯嗯", "嗯哪", "嗯呢", "嗯~"]:
            topic = context.get("topic")
            relationship = context.get("relationship")

            if topic == ContextType.SHARE:
                interpretations.append("温柔的认同")
            elif topic == ContextType.COMPLAINT:
                interpretations.append("倾听但不太在意")
            elif topic == ContextType.CASUAL and len(history) > 5:
                interpretations.append("可能敷衍/不想聊")
            elif topic == ContextType.APOLOGY:
                interpretations.append("勉强原谅")
            elif relationship == ContextType.INTIMATE:
                interpretations.append("温柔的回应")
            elif context.get("miya_mood") == ContextType.ANGRY:
                interpretations.append("勉强原谅/还在生气")

        # ========== 对"哦"类的解读 ==========
        if msg in ["哦", "哦哦", "哦~"]:
            topic = context.get("topic")

            if topic == ContextType.SHARE:
                interpretations.append("冷漠/不感兴趣")
            elif topic == ContextType.APOLOGY:
                interpretations.append("不接受/还在生气")
            elif topic == ContextType.CONFESSION:
                interpretations.append("不知所措/需要时间")
            elif topic == ContextType.JOKE:
                interpretations.append("礼貌回应但不好笑")

        # ========== 对"算了"的解读 ==========
        if "算了" in msg:
            topic = context.get("topic")

            if topic == ContextType.COMPLAINT:
                interpretations.append("放弃抱怨/不想计较")
            elif topic == ContextType.QUESTION:
                interpretations.append("不想知道答案了")
            else:
                interpretations.append("放弃/无奈/不想追究")

            if context.get("miya_mood") == ContextType.ANGRY:
                interpretations.append("赌气/不想再提")

        # ========== 对"好"的解读 ==========
        if msg in ["好", "好的", "好呀", "好嘞", "嗯好"]:
            topic = context.get("topic")
            relationship = context.get("relationship", ContextType.FAMILIAR)

            if topic == ContextType.REQUEST:
                interpretations.append("答应请求")
            elif topic == ContextType.APOLOGY:
                interpretations.append("接受道歉")
            elif relationship == ContextType.INTIMATE:
                interpretations.append("温柔的回应")
            else:
                interpretations.append("默认同意")

        # ========== 对"好吧"的解读 ==========
        if "好吧" in msg:
            interpretations.append("无奈同意/有点不情愿")
            if context.get("miya_mood") == ContextType.ANGRY:
                interpretations.append("勉强接受但还在赌气")

        return {
            "possible_meanings": interpretations,
            "primary_meaning": interpretations[0] if interpretations else "正常回应",
        }


class PsychoAnalyzer:
    """
    心理学剖析引擎 - 增强版
    归因/识别/预测/反思/调节
    """

    def __init__(self):
        # 认知偏见记录
        self.biases: Dict[str, float] = {}
        # 自我修正记录
        self.corrections: List[str] = []

    def analyze(
        self,
        context: Dict,
        message: str,
        emotions: Dict[str, Emotion],
        cognition: Dict[str, Cognition],
    ) -> PsychologicalAnalysis:
        """进行心理学剖析 - 增强版"""
        analysis = PsychologicalAnalysis()

        # 1. 归因分析
        analysis.attribution = self._attribute(message, context, emotions)

        # 2. 识别分析
        analysis.recognition = self._recognize(message, context, emotions)

        # 3. 预测分析
        analysis.prediction = self._predict(message, context, emotions, cognition)

        # 4. 自我反思
        analysis.reflection = self._reflect(message, context, emotions, cognition)

        # 5. 情绪调节
        analysis.regulation = self._regulate(emotions, context)

        return analysis

    def _attribute(self, message: str, context: Dict, emotions: Dict) -> str:
        """归因分析 - 为什么会产生这个情绪"""
        msg = message.lower()
        topic = context.get("topic", ContextType.CASUAL)
        relationship = context.get("relationship", ContextType.FAMILIAR)

        # ========== 基于话题的归因 ==========
        if topic == ContextType.SHARE:
            # 分享场景
            if any(word in msg for word in ["哈哈", "太棒", "好玩", "笑"]):
                return "对方分享快乐，期待共鸣和认可"
            elif any(word in msg for word in ["累", "烦", "困"]):
                return "对方分享疲惫，可能是情感宣泄"
            elif msg in ["嗯", "哦", "好吧"]:
                return "对方分享时回应简单，可能感到不被重视"

        elif topic == ContextType.APOLOGY:
            # 道歉场景
            if msg in ["嗯", "哦", "好吧"]:
                return "对方道歉但回应敷衍，可能还在生气或觉得道歉不够真诚"
            elif "没关系" in msg or "原谅" in msg:
                return "接受道歉，但可能还在观察对方态度"
            elif any(word in msg for word in ["真的", "真的对不起", "我错了"]):
                return "对方真诚道歉，应该给予温柔回应"

        elif topic == ContextType.CONFESSION:
            # 表白场景
            if msg in ["嗯", "哦", "这个"]:
                return "对方表白后不知所措，需要时间消化"
            elif any(word in msg for word in ["我", "喜欢", "爱"]):
                return "对方在表达爱意，期待积极回应"

        elif topic == ContextType.COMPLAINT:
            # 抱怨场景
            if "算了" in msg or "随便" in msg:
                return "对方在抱怨后放弃，可能需要被倾听而不是建议"
            elif any(word in msg for word in ["烦", "累", "不想"]):
                return "对方在宣泄情绪，需要情感支持"

        elif topic == ContextType.QUESTION:
            # 询问场景
            if any(word in msg for word in ["怎么", "为什么", "是不是"]):
                return "对方在寻求信息或确认"

        # ========== 基于关系情境的归因 ==========
        if relationship == ContextType.INTIMATE:
            if msg in ["嗯", "哦"]:
                return "在亲密关系中，简单回应可能代表放松或心不在焉"
        elif relationship == ContextType.COLD_WAR:
            if msg in ["嗯", "哦"]:
                return "冷战中的敷衍回应，可能还在生气或赌气"

        # ========== 基于互动类型的归因 ==========
        interaction = context.get("interaction", "normal")

        if interaction == "minimal_response":
            return "对方可能忙于其他事、累、或不想深入对话"
        elif interaction == "resigned":
            return "对方可能感到无奈、疲惫、或放弃抗争"
        elif interaction == "positive":
            return "对方情绪积极，期待分享快乐"

        return "正常对话互动"

    def _recognize(self, message: str, context: Dict, emotions: Dict) -> str:
        """识别分析 - 对方可能的真实情绪"""
        msg = message.strip().lower()

        # ========== 显式情绪识别 ==========
        # 积极情绪
        positive_words = [
            "哈哈",
            "太棒",
            "太好了",
            "喜欢",
            "开心",
            "幸福",
            "快乐",
            "棒",
            "么么",
            "爱你",
        ]
        if any(word in msg for word in positive_words):
            return "对方可能感到开心、幸福、满足，期待分享这份快乐"

        # 消极情绪
        negative_words = ["累", "困", "烦", "难过", "伤心", "失落", "郁闷", "糟", "烦"]
        if any(word in msg for word in negative_words):
            return "对方可能感到疲惫、低落或烦躁，需要关心和支持"

        # 紧张/焦虑
        anxious_words = ["紧张", "担心", "焦虑", "害怕", "不安"]
        if any(word in msg for word in anxious_words):
            return "对方可能感到焦虑或紧张，需要安抚"

        # ========== 隐式情绪识别 ==========
        # 简单敷衍
        if msg in ["嗯", "哦", "好吧", "嗯嗯", "哦哦"]:
            topic = context.get("topic", ContextType.CASUAL)
            relationship = context.get("relationship", ContextType.FAMILIAR)

            if topic == ContextType.SHARE:
                return "对方可能心不在焉，或觉得话题不感兴趣"
            elif topic == ContextType.APOLOGY:
                return "对方可能还在生气，或不接受道歉"
            elif topic == ContextType.CONFESSION:
                return "对方可能不知所措，或需要时间反应"
            elif relationship == ContextType.INTIMATE:
                return "对方可能只是习惯性回应，或真的在忙"

            return "对方态度不确定，可能平淡/敷衍/不想聊"

        # 放弃/无奈
        if any(word in msg for word in ["算了", "随便", "管它呢", "就这样吧"]):
            return "对方可能感到无奈、失望、或选择放弃"

        # ========== 深度情绪识别 ==========
        # 基于语义解读
        semantic = context.get("semantic_interpretation", {})
        primary_meaning = semantic.get("primary_meaning", "")

        if "敷衍" in primary_meaning:
            return "对方可能在掩饰真实情绪，或确实不感兴趣"
        elif "温柔" in primary_meaning:
            return "对方可能心情不错，愿意回应"
        elif "赌气" in primary_meaning:
            return "对方可能在生气但不说出来"

        return "对方情绪稳定或不确定"

    def _predict(
        self, message: str, context: Dict, emotions: Dict, cognition: Dict
    ) -> str:
        """预测分析 - 接下来可能会怎样"""
        msg = message.lower()
        topic = context.get("topic", ContextType.CASUAL)
        relationship = context.get("relationship", ContextType.FAMILIAR)

        # 获取主导情绪
        dominant_emotion = self._get_dominant_emotion(emotions)

        # ========== 基于消息内容的预测 ==========
        if msg in ["嗯", "哦"]:
            if dominant_emotion in ["委屈", "不满", "傲娇"]:
                return "可能会进一步表达不满，或者自我消化后平静"
            elif relationship == ContextType.COLD_WAR:
                return "可能继续冷战，或等待对方主动示好"

        if "算了" in msg:
            if topic == ContextType.COMPLAINT:
                return "可能会停止抱怨，但情绪可能积累"
            elif topic == ContextType.QUESTION:
                return "可能不想继续这个话题"

        if any(word in msg for word in ["对不起", "抱歉"]):
            if topic == ContextType.APOLOGY:
                return "对方可能在试探反应，需要判断是否真诚"
            return "对方可能在道歉，期待原谅"

        if any(word in msg for word in ["?", "？", "怎么", "为什么"]):
            return "对方可能期待详细回答，或有好奇心"

        # ========== 基于情绪趋势的预测 ==========
        emotion_trend = context.get("emotion_trend", [])
        if len(emotion_trend) >= 2 and emotion_trend[-1] == "down":
            return "对方情绪可能在下降，需要关注和关心"

        # ========== 基于关系情境的预测 ==========
        if relationship == ContextType.INTIMATE:
            return "可能会更放松地交流，或期待更亲密的互动"
        elif relationship == ContextType.COLD_WAR:
            return "可能会继续冷战，或开始寻求和解"
        elif relationship == ContextType.NEW_KNOW:
            return "可能会保持礼貌距离，或逐渐熟悉"

        return "继续正常对话"

    def _reflect(
        self, message: str, context: Dict, emotions: Dict, cognition: Dict
    ) -> str:
        """自我反思 - 弥娅自己的情绪来源"""
        msg = message.lower()
        topic = context.get("topic", ContextType.CASUAL)
        relationship = context.get("relationship", ContextType.FAMILIAR)

        # 获取弥娅当前情绪
        dominant_emotion = self._get_dominant_emotion(emotions)

        # ========== 基于用户消息的反思 ==========
        # 用户表达爱意
        if any(word in msg for word in ["喜欢", "爱", "想你", "么么"]):
            return f"听到用户的爱意，我感到{dominant_emotion}，想要回应这份温暖"

        # 用户道歉
        if any(word in msg for word in ["对不起", "抱歉"]):
            if topic == ContextType.APOLOGY:
                return "用户道歉了，虽然可能还有情绪，但我应该温柔回应"
            return "用户在道歉，可能意识到自己的问题了"

        # 用户分享开心事
        if any(word in msg for word in ["哈哈", "太棒", "好玩", "笑"]):
            return "用户分享快乐，我也感到开心，想要一起笑"

        # 用户表达疲惫
        if any(word in msg for word in ["累", "困", "烦", "难过"]):
            return f"用户表达了{dominant_emotion}，我想要关心和陪伴"

        # 用户说"嗯""哦"
        if msg in ["嗯", "哦", "好吧"]:
            if topic == ContextType.SHARE:
                return "用户分享时得到简单回应，可能感到不被重视"
            elif topic == ContextType.CONFESSION:
                return "用户表白后我的回应可能让用户感到不安"

        # ========== 基于关系的反思 ==========
        if relationship == ContextType.INTIMATE:
            return f"我们在亲密关系中，我感到{dominant_emotion}，想要更靠近"
        elif relationship == ContextType.COLD_WAR:
            return f"我们在冷战，我感到{dominant_emotion}，想要打破僵局"
        elif relationship == ContextType.FAMILIAR:
            return f"我们在熟悉的关系中，我感到{dominant_emotion}，保持舒适交流"

        # 默认
        return f"当前我的主导情绪是{dominant_emotion}，保持正常交流"

    def _regulate(self, emotions: Dict, context: Dict) -> str:
        """情绪调节 - 如何处理当前情绪"""
        dominant = self._get_dominant_emotion(emotions)

        emotion_obj = emotions.get(dominant)
        if not emotion_obj:
            return "保持当前情绪状态"

        value = emotion_obj.value
        relationship = context.get("relationship", ContextType.FAMILIAR)

        # ========== 高情绪值调节 ==========
        if value > 70:
            high_emotion_handlers = {
                "委屈": "尝试理解对方立场，表达感受但不要过度",
                "不满": "可以适当表达，但注意语气",
                "傲娇": "可以表达一点小情绪，增加互动趣味",
                "失落": "给自己时间消化，也可以向用户寻求支持",
                "窝火": "深呼吸，避免冲动回应",
                "憋屈": "寻找合适的方式表达，不要压抑",
                "心塞": "需要倾诉或独处时间",
                "爱意": "可以温柔地表达爱意",
                "心疼": "想要关心和安慰对方",
            }
            if dominant in high_emotion_handlers:
                return high_emotion_handlers[dominant]

        # ========== 低情绪值调节 ==========
        if value < 30:
            low_emotion_handlers = {
                "平静": "保持放松状态，享受当下",
                "坦然": "保持淡定的态度",
                "满足": "珍惜当下的幸福",
                "冷漠": "尝试关心用户，重新投入",
                "疏离": "尝试拉近与用户的距离",
            }
            if dominant in low_emotion_handlers:
                return low_emotion_handlers[dominant]

        # ========== 基于关系的调节 ==========
        if relationship == ContextType.COLD_WAR:
            if value > 50:
                return "尝试主动和解，但不要卑微"
            else:
                return "给自己空间，也给对方时间"
        elif relationship == ContextType.INTIMATE:
            return "可以更放松地表达情感，不需要太多掩饰"

        return "保持当前情绪状态"

    def _get_dominant_emotion(self, emotions: Dict) -> str:
        """获取主导情绪"""
        if not emotions:
            return "平静"

        max_emotion = max(emotions.values(), key=lambda e: e.value)
        return max_emotion.category.value


class SoulGenerator:
    """
    灵魂发生器 - 整合所有子系统
    让弥娅拥有"灵魂"般的情感复杂度
    """

    def __init__(self):
        # 子系统
        self.context_detector = ContextDetector()
        self.psycho_analyzer = PsychoAnalyzer()

        # 情绪池
        self.emotions: Dict[str, Emotion] = self._init_emotions()

        # 认知系统
        self.cognitions: Dict[str, Cognition] = {}

        # 行为引擎 - 意图残留
        self.pending_intents: List[PendingIntent] = []

        # 情绪记忆
        self.emotion_memories: List[EmotionMemory] = []

        # 状态
        self.last_update = time.time()
        self.current_mood = "平静"

        logger.info("[灵魂发生器] 初始化完成")

    def _init_emotions(self) -> Dict[str, Emotion]:
        """初始化完整情绪图谱"""
        emotions = {}

        # 基础情绪 (Ekman 6大)
        for cat in EmotionCategory:
            emotions[cat.value] = Emotion(
                category=cat,
                value=random.randint(30, 50),  # 初始随机值
                expression_threshold=40,
                decay_rate=0.02,
            )

        return emotions

    async def _ai_generate_inner_thought(
        self, message: str, history: List[Dict], ai_client, dominant_emotion: str
    ) -> Optional[str]:
        """
        用AI生成弥娅的内心反思 - 增强版
        根据70+情绪类别生成更丰富的内心独白
        """
        try:
            # 获取最近对话历史作为上下文
            context_str = ""
            if history:
                recent = history[-3:]
                context_parts = []
                for m in recent:
                    role = m.get("role", "user")
                    content = m.get("content", "")[:60]
                    if content:
                        context_parts.append(f"{role}: {content}")
                if context_parts:
                    context_str = "\n".join(context_parts)

            # 根据主导情绪使用不同的prompt风格
            emotion_style = self._get_emotion_style(dominant_emotion)

            prompt = (
                f"你是弥娅的内心独白系统。你的任务是生成弥娅真实的内心思考。\n\n"
                f"【规则】\n"
                f"1. 只输出内心独白，不要有任何格式或前缀\n"
                f"2. 30-80字，简洁但有情感深度\n"
                f"3. 根据当前情绪用对应语气：{emotion_style}\n"
                f"4. 结合对话历史，但不要重复用户的话\n"
                f"5. 可以有犹豫、纠结、自我怀疑，但要真实\n\n"
                f"【当前状态】\n"
                f"- 弥娅主导情绪: {dominant_emotion}\n"
                f"- 对话历史:\n{context_str if context_str else '暂无'}\n"
                f"- 用户最新消息: {message[:80]}\n\n"
                f"【输出】\n"
                f"直接输出内心独白，不要加引号或任何格式。"
            )

            from core.ai_client import AIMessage

            messages = [AIMessage(role="user", content=prompt)]
            response = await ai_client.chat(
                messages=messages, tools=None, use_miya_prompt=False
            )

            if response and len(response) > 0:
                # 清理响应，移除可能的格式
                cleaned = response.strip()
                # 移除可能的引号
                if cleaned.startswith('"') and cleaned.endswith('"'):
                    cleaned = cleaned[1:-1]
                if cleaned.startswith("'") and cleaned.endswith("'"):
                    cleaned = cleaned[1:-1]

                logger.info(f"[灵魂] AI反思: {cleaned[:100]}")
                return cleaned

        except Exception as e:
            logger.debug(f"[灵魂] AI反思失败: {e}")

        return None

    def _get_emotion_style(self, emotion: str) -> str:
        """根据情绪获取对应的语气风格"""
        style_map = {
            # 积极
            "爱意": "温柔甜蜜，充满爱意",
            "心动": "小鹿乱撞，既惊喜又害羞",
            "幸福": "满足开心，珍惜当下",
            "开心": "雀跃，想要分享快乐",
            "甜蜜": "心里暖暖的，充满幸福感",
            "温暖": "温柔，想要拥抱对方",
            "治愈": "被安慰到，感到被理解",
            # 消极
            "难过": "伤心沮丧，需要安慰",
            "失落": "郁郁寡欢，提不起精神",
            "委屈": "心里酸酸的，想要被哄",
            "心疼": "舍不得，想要关心对方",
            "失望": "叹气，感到无奈",
            "焦虑": "紧张不安，有点担心",
            "紧张": "心跳加速，有点慌乱",
            # 复杂
            "傲娇": "嘴硬心软，想被哄又不说",
            "赌气": "别扭赌气，但又在意",
            "害羞": "脸红的，心里小鹿乱撞",
            "纠结": "犹豫不决，举棋不定",
            "期待": "心里痒痒的，充满希望",
            "五味杂陈": "心情复杂，说不清楚",
            # 平淡
            "平静": "波澜不惊，正常状态",
            "坦然": "淡定从容，不急不躁",
            "满足": "刚刚好，满意现状",
            # 默认
        }
        return style_map.get(emotion, "平和自然，像日常思考")

    async def process(self, message: str, history: List[Dict], ai_client=None) -> Dict:
        """
        处理消息 → 生成回复
        完整流程：检测 → AI分析(可选) → 涌现 → 行为 → 输出
        """
        # 1. 获取弥娅当前状态
        miya_state = {
            "dominant_emotion": self._get_dominant_emotion(),
            "current_mood": self.current_mood,
        }

        # 2. 语意情境检测
        context = self.context_detector.detect(message, history, miya_state)

        # 3. 心理学剖析
        analysis = self.psycho_analyzer.analyze(
            context, message, self.emotions, self.cognitions
        )

        # 4. AI情绪分析 (如果启用)
        ai_emotion_result = None
        ai_inner_thought = None
        ai_analysis_enabled = _CONFIG.get("AI_ANALYSIS_ENABLED", True)
        if ai_analysis_enabled and ai_client:
            ai_emotion_result = await self._ai_analyze_emotion(
                message, history, ai_client
            )
            if ai_emotion_result:
                self._apply_ai_emotion(ai_emotion_result)

            # AI生成内心独白（需要ai_client）
            ai_inner_thought = None
            if ai_client:
                current_dominant = self._get_dominant_emotion()
                try:
                    ai_inner_thought = await self._ai_generate_inner_thought(
                        message, history, ai_client, current_dominant
                    )
                except Exception as e:
                    logger.debug(f"[灵魂] AI反思失败: {e}")

        # 5. 默认情绪波动
        self._apply_default_fluctuation()

        # 6. 情绪涌现（内部活动）
        self._emotion_emergence(message, context, analysis)

        # 7. 行为引擎 - 检查待完成意图
        intent_response = self._check_pending_intents(context)

        # 8. 情绪衰减（时间流逝）
        self._decay_emotions()

        # 9. 生成输出
        output = self._generate_output(message, context, intent_response)

        self.last_update = time.time()

        # 合并内心独白
        inner_thought = ai_inner_thought or (
            analysis.reflection if analysis.reflection else "正常对话互动"
        )

        return {
            "response": output,
            "dominant_emotion": self._get_dominant_emotion(),
            "emotions": self._get_emotion_summary(),
            "pending_intents": len(self.pending_intents),
            "context": context,
            "analysis": {
                "attribution": analysis.attribution,
                "reflection": inner_thought,
                "ai_emotion": ai_emotion_result,
            },
        }

    async def _ai_analyze_emotion(
        self, message: str, history, ai_client
    ) -> Optional[Dict]:
        """使用AI分析情绪"""
        try:
            if not ai_client:
                logger.warning("[灵魂] AI分析跳过: 无AI客户端")
                return None

            prompt_template = _CONFIG.get("AI_EMOTION_ANALYSIS_PROMPT", "")
            if not prompt_template:
                logger.warning("[灵魂] AI分析跳过: 无prompt配置")
                return None

            context_str = ""
            history_list = []
            if history:
                if isinstance(history, str):
                    pass
                elif isinstance(history, list):
                    history_list = history
                else:
                    logger.warning(f"[灵魂] 历史类型错误: {type(history)}")

            if history_list:
                recent = history_list[-3:]
                context_str = "\n".join(
                    [
                        f"用户: {m.get('content', '')[:80]}"
                        for m in recent
                        if m.get("role") == "user"
                    ]
                )

            prompt = prompt_template.replace("{message}", message)
            if context_str:
                prompt = prompt.replace("{context}", context_str)
            else:
                prompt = prompt.replace("{context}", "")

            logger.warning(f"[灵魂] 发送的prompt: {prompt[:200]}")

            from core.ai_client import AIMessage

            messages = [AIMessage(role="user", content=prompt)]
            response = await ai_client.chat(
                messages=messages, tools=None, use_miya_prompt=False
            )

            logger.warning(f"[灵魂] AI响应: {response[:500]}")

            import re
            import json

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                logger.warning(f"[灵魂] 无JSON: {response[:100]}")
                return None

            result = json.loads(json_match.group())
            logger.info(
                f"[灵魂] AI分析: {result.get('dominant_emotion')} | 强度: {result.get('intensity')} | 理由: {result.get('reasoning', '')[:30]}"
            )
            return result

        except Exception as e:
            import traceback

            logger.warning(f"[灵魂] AI分析失败: {e}")
            logger.warning(f"[灵魂] 错误堆栈: {traceback.format_exc()}")
            return None

    def _apply_ai_emotion(self, ai_result: Dict):
        """应用AI分析的情绪"""
        try:
            emotion_name = ai_result.get("dominant_emotion", "")
            intensity = ai_result.get("intensity", 50)
            tags = ai_result.get("emotion_tags", [])

            if emotion_name and intensity > 0:
                self._adjust_emotion(emotion_name, intensity - 40)

                for tag in tags[:3]:
                    if tag != emotion_name:
                        self._adjust_emotion(tag, (intensity - 40) * 0.5)

        except Exception as e:
            logger.debug(f"[灵魂] 应用AI情绪失败: {e}")

    def _apply_default_fluctuation(self):
        """应用默认情绪波动"""
        fluctuation = _CONFIG.get("DEFAULT_EMOTION_FLUCTUATION", 5)
        if fluctuation <= 0:
            return

        import random

        for emotion in self.emotions.values():
            change = random.uniform(-fluctuation, fluctuation)
            new_value = max(10, min(90, emotion.value + change))
            emotion.value = new_value

    def _emotion_emergence(
        self, message: str, context: Dict, analysis: PsychologicalAnalysis
    ):
        """情绪涌现 - 从配置文件读取规则"""
        msg = message.lower()

        # 内心活动
        inner_thoughts = []
        if analysis.attribution:
            inner_thoughts.append(analysis.attribution)
        if analysis.reflection and analysis.reflection != "当前情绪稳定":
            inner_thoughts.append(analysis.reflection)
        logger.info(
            f"[灵魂] 内心: {'; '.join(inner_thoughts) if inner_thoughts else '暂无'}"
        )

        # 从配置读取情绪触发规则
        triggers = _CONFIG.get("MESSAGE_EMOTION_TRIGGERS", {})

        # 检查每种触发类型
        for trigger_name, trigger_config in triggers.items():
            keywords = trigger_config.get("keywords", [])
            emotions_change = trigger_config.get("emotions", {})

            # 检查消息是否匹配关键词
            if any(keyword in msg for keyword in keywords):
                # 记录情绪变化
                changes_str = ", ".join(
                    [
                        f"{k}+{v}" if v > 0 else f"{k}{v}"
                        for k, v in emotions_change.items()
                    ]
                )

                logger.info(f"[灵魂] {trigger_name}: {changes_str}")

                # 应用情绪变化
                for emotion_name, delta in emotions_change.items():
                    self._adjust_emotion(emotion_name, delta)

        # 关系情境影响
        relationship = context.get("relationship")
        if relationship:
            rel_effects = _CONFIG.get("RELATIONSHIP_EMOTION_EFFECTS", {}).get(
                relationship.value, {}
            )
            if rel_effects:
                changes_str = ", ".join([f"{k}+{v}" for k, v in rel_effects.items()])
                logger.info(f"[灵魂] 关系影响({relationship.value}): {changes_str}")
                for emotion_name, delta in rel_effects.items():
                    self._adjust_emotion(emotion_name, delta)
        relationship = context.get("relationship")
        if relationship == ContextType.INTIMATE:
            self._adjust_emotion("爱意", 5)
        elif relationship == ContextType.COLD_WAR:
            self._adjust_emotion("不安", 10)
            self._adjust_emotion("委屈", 8)

        logger.info(f"[灵魂发生器] 内心活动: {'; '.join(inner_thoughts)}")

    def _adjust_emotion(self, emotion_name: str, delta: float):
        """调整情绪值"""
        if emotion_name in self.emotions:
            emotion = self.emotions[emotion_name]
            new_value = max(0, min(100, emotion.value + delta))
            emotion.value = new_value
            emotion.timestamp = time.time()

    def _get_dominant_emotion(self) -> str:
        """获取当前主导情绪"""
        if not self.emotions:
            return "平静"

        max_emotion = max(self.emotions.values(), key=lambda e: e.value)
        return max_emotion.category.value

    def _get_emotion_summary(self) -> Dict[str, float]:
        """获取情绪摘要"""
        return {
            name: emp.value
            for name, emp in self.emotions.items()
            if emp.value > 20  # 只返回显著情绪
        }

    def _check_pending_intents(self, context: Dict) -> Optional[str]:
        """检查待完成的意图"""
        if not self.pending_intents:
            return None

        # 从配置获取激活概率
        activation_chance = _CONFIG.get("INTENT_ACTIVATION_CHANCE", 0.4)

        # 检查是否可以激活
        for intent in self.pending_intents:
            if intent.can_activate():
                # 随机决定是否激活（避免每次都激活）
                if random.random() > (1 - activation_chance):
                    intent.record_attempt()
                    return f"对了，{intent.intent}"

        return None

    def add_pending_intent(self, intent: str, context: str, priority: int = 5):
        """添加待完成意图"""
        self.pending_intents.append(
            PendingIntent(intent=intent, context=context, priority=priority)
        )
        logger.info(f"[灵魂发生器] 添加意图: {intent}")

    def _decay_emotions(self):
        """情绪衰减"""
        now = time.time()
        elapsed = now - self.last_update

        if elapsed < 10:  # 10秒内不衰减
            return

        decay_factor = elapsed / 60  # 每分钟衰减

        for emotion in self.emotions.values():
            if emotion.value > 30:  # 基础值以上才衰减
                decay = emotion.decay_rate * decay_factor * 10
                emotion.value = max(30, emotion.value - decay)

    def _generate_output(
        self, message: str, context: Dict, intent_response: Optional[str]
    ) -> str:
        """生成输出"""
        # 如果有pending intent，优先输出
        if intent_response:
            return intent_response

        # 根据主导情绪生成不同风格回复
        dominant = self._get_dominant_emotion()

        # 从配置获取阈值
        high_threshold = _CONFIG.get("HIGH_EMOTION_THRESHOLD", 70)

        # 简化版：根据情绪值决定回复风格
        emotion_value = self.emotions.get(
            dominant, Emotion(EmotionCategory.PEACEFUL, 50)
        ).value

        if emotion_value > high_threshold:
            # 高情绪 - 可能带有情绪表达
            if dominant in ["委屈", "不满", "傲娇", "赌气"]:
                # 傲娇反应 - 从配置获取
                responses = _CONFIG.get(
                    "HIGH_EMOTION_RESPONSES",
                    [
                        "哼~",
                        "好吧...",
                        "知道了啦~",
                    ],
                )
                return random.choice(responses)

        # 正常回复 - 不带明显情绪
        return ""  # 返回空字符串表示使用默认回复

    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            "dominant_emotion": self._get_dominant_emotion(),
            "emotions": self._get_emotion_summary(),
            "pending_intents": len(self.pending_intents),
            "cognitions": len(self.cognitions),
            "emotion_memories": len(self.emotion_memories),
        }


# 全局实例
_soul_generator: Optional[SoulGenerator] = None


def get_soul_generator() -> SoulGenerator:
    """获取全局灵魂发生器实例"""
    global _soul_generator
    if _soul_generator is None:
        _soul_generator = SoulGenerator()
    return _soul_generator


def init_soul_generator():
    """初始化灵魂发生器"""
    global _soul_generator
    _soul_generator = SoulGenerator()
    return _soul_generator
