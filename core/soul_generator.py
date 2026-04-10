"""
灵魂发生器 (Soul Generator) - 弥娅的"灵魂"系统
让弥娅拥有类似人类的情绪、认知和行为模式

核心特性：
- 情绪池：完整人类情感图谱，动态、自发涌现
- 语意情境检测：同一句话在不同情境下不同解读
- 心理学剖析：归因、识别、预测、反思、调节
- 行为引擎：意图残留与追踪，防止行动中断
- 认知系统：偏见形成与自我修正
- 情绪记忆锚点：记住情绪事件而非细节
- 情绪恢复曲线：自然衰减
- 社交面具：真实情绪与表达分离
"""

import logging
import time
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


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
    """情绪分类"""

    # 基础情绪 (Ekman 6大)
    JOY = "喜悦"
    SADNESS = "悲伤"
    FEAR = "恐惧"
    ANGER = "愤怒"
    SURPRISE = "惊讶"
    DISGUST = "厌恶"

    # 复合情绪
    LOVE = "爱"
    HATE = "恨"
    ENVY = "羡慕"
    JEALOUSY = "嫉妒"
    SHAME = "羞耻"
    GUILT = "愧疚"
    PRIDE = "骄傲"
    EMBARRASSMENT = "尴尬"
    NOSTALGIA = "怀旧"
    LONGING = "思念"
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

    # 状态情绪
    HAPPY = "幸福"
    SATISFIED = "满足"
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

    # 关系情绪
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

    # 自我情绪
    SELF_DOUBT = "自我怀疑"
    SELF_AFFIRM = "自我肯定"
    INFERIORITY = "自卑"
    NARCISSISM = "自恋"


class ContextType(Enum):
    """情境类型"""

    # 关系情境
    NEW_KNOW = "刚认识"
    FAMILIAR = "熟悉"
    INTIMATE = "亲密"
    COLD_WAR = "冷战"
    FIGHTING = "吵架中"

    # 时间情境
    JUST_WOKE_UP = "刚睡醒"
    LATE_NIGHT = "深夜"
    JUST_BUSY = "刚忙完"
    IN_CONVERSATION = "连续对话中"

    # 话题情境
    CASUAL = "闲聊"
    SERIOUS = "正事"
    APOLOGY = "道歉"
    CONFESSION = "表白"
    QUESTION = "询问"
    SHARE = "分享"

    # 情绪情境
    HAPPY = "开心"
    ANGRY = "生气"
    LOW = "低落"
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
    """语意情境检测器"""

    def __init__(self):
        self.current_context: Dict[str, Any] = {
            "relationship": ContextType.FAMILIAR,
            "time": ContextType.IN_CONVERSATION,
            "topic": ContextType.CASUAL,
            "miya_mood": ContextType.CALM,
            "last_interaction": "",
            "emotion_history": [],
        }

    def detect(self, message: str, history: List[Dict], miya_state: Dict) -> Dict:
        """检测当前情境"""
        context = {
            "relationship": self._detect_relationship(history),
            "time": self._detect_time_context(),
            "topic": self._detect_topic(message),
            "miya_mood": self._detect_miya_mood(miya_state),
            "interaction": self._detect_interaction_type(message, history),
            "semantic_interpretation": self._interpret_semantic(message, history),
        }
        self.current_context.update(context)
        return context

    def _detect_relationship(self, history: List[Dict]) -> ContextType:
        """检测关系情境"""
        if not history:
            return ContextType.NEW_KNOW

        # 检查最近对话的亲密度
        recent_messages = history[-5:] if len(history) > 5 else history

        # 简化判断：检查是否有亲密表达
        for msg in recent_messages:
            content = msg.get("content", "").lower()
            if any(word in content for word in ["爱", "想", "喜欢", "宝贝", "亲爱的"]):
                return ContextType.INTIMATE
            if any(word in content for word in ["冷战", "生气", "不理"]):
                return ContextType.COLD_WAR

        return ContextType.FAMILIAR

    def _detect_time_context(self) -> ContextType:
        """检测时间情境"""
        current_hour = time.localtime().tm_hour

        if 5 <= current_hour < 8:
            return ContextType.JUST_WOKE_UP
        elif 22 <= current_hour or current_hour < 2:
            return ContextType.LATE_NIGHT
        else:
            return ContextType.IN_CONVERSATION

    def _detect_topic(self, message: str) -> ContextType:
        """检测话题情境"""
        msg = message.lower()

        if any(word in msg for word in ["对不起", "抱歉", "我错了"]):
            return ContextType.APOLOGY
        elif any(word in msg for word in ["我爱你", "喜欢", "表白"]):
            return ContextType.CONFESSION
        elif any(word in msg for word in ["?", "怎么", "什么", "为什么"]):
            return ContextType.QUESTION
        elif any(word in msg for word in ["给你看", "分享", "有意思"]):
            return ContextType.SHARE
        else:
            return ContextType.CASUAL

    def _detect_miya_mood(self, miya_state: Dict) -> ContextType:
        """检测弥娅当前情绪"""
        # 简化：根据弥娅当前主导情绪判断
        dominant = miya_state.get("dominant_emotion", "平静")
        mood_map = {
            "开心": ContextType.HAPPY,
            "生气": ContextType.ANGRY,
            "低落": ContextType.LOW,
            "平静": ContextType.CALM,
        }
        return mood_map.get(dominant, ContextType.CALM)

    def _detect_interaction_type(self, message: str, history: List[Dict]) -> str:
        """检测互动类型"""
        msg = message.strip()

        # 检查消息特征
        if not msg or msg == "嗯" or msg == "哦":
            return "minimal_response"
        elif len(msg) > 50:
            return "long_response"
        elif any(word in msg.lower() for word in ["哈哈", "笑", "好玩"]):
            return "positive"
        elif any(word in msg.lower() for word in ["算了", "随便", "好吧"]):
            return "resigned"

        return "normal"

    def _interpret_semantic(self, message: str, history: List[Dict]) -> Dict:
        """语义解读 - 同一句话在不同情境下不同含义"""
        msg = message.strip().lower()
        context = self.current_context

        interpretations = []

        # 对"嗯"的解读
        if msg in ["嗯", "嗯嗯", "嗯哪"]:
            # 根据话题情境判断
            topic = context.get("topic")
            if topic == ContextType.SHARE:
                interpretations.append("温柔的认同")
            elif topic == ContextType.CASUAL and len(history) > 3:
                interpretations.append("可能敷衍/不想聊")
            elif context.get("miya_mood") == ContextType.ANGRY:
                interpretations.append("勉强原谅/还在生气")

        # 对"哦"的解读
        if msg == "哦":
            topic = context.get("topic")
            if topic == ContextType.SHARE:
                interpretations.append("冷漠/不感兴趣")
            elif topic == ContextType.APOLOGY:
                interpretations.append("不接受/还在生气")

        # 对"算了"的解读
        if "算了" in msg:
            interpretations.append("放弃/无奈/不想追究")
            if context.get("miya_mood") == ContextType.ANGRY:
                interpretations.append("赌气/不想再提")

        return {
            "possible_meanings": interpretations,
            "primary_meaning": interpretations[0] if interpretations else "正常回应",
        }


class PsychoAnalyzer:
    """心理学剖析引擎"""

    def analyze(
        self,
        context: Dict,
        message: str,
        emotions: Dict[str, Emotion],
        cognition: Dict[str, Cognition],
    ) -> PsychologicalAnalysis:
        """进行心理学剖析"""
        analysis = PsychologicalAnalysis()

        # 1. 归因分析
        analysis.attribution = self._attribute(message, context, emotions)

        # 2. 识别分析
        analysis.recognition = self._recognize(message, context, emotions)

        # 3. 预测分析
        analysis.prediction = self._predict(message, context, emotions, cognition)

        # 4. 自我反思
        analysis.reflection = self._reflect(emotions, cognition)

        # 5. 情绪调节
        analysis.regulation = self._regulate(emotions, context)

        return analysis

    def _attribute(self, message: str, context: Dict, emotions: Dict) -> str:
        """归因分析 - 为什么会产生这个情绪"""
        # 根据消息和情境推断情绪来源
        msg = message.lower()

        if "嗯" in msg or "哦" in msg:
            topic = context.get("topic", ContextType.CASUAL)
            if topic == ContextType.SHARE:
                return "期待分享被简单回应，可能感到失落"
            elif topic == ContextType.APOLOGY:
                return "对方道歉但回应敷衍，可能还在生气或不满"

        return "正常对话互动"

    def _recognize(self, message: str, context: Dict, emotions: Dict) -> str:
        """识别分析 - 对方可能的真实情绪"""
        # 从消息推断对方可能的情绪
        msg = message.strip()

        # 简单识别规则
        if any(word in msg.lower() for word in ["哈哈", "太棒了", "喜欢"]):
            return "对方可能很开心/满意"
        elif any(word in msg.lower() for word in ["累", "困", "烦"]):
            return "对方可能比较疲惫/低落"
        elif msg in ["嗯", "哦", "好吧"]:
            return "对方态度不确定，可能平淡/敷衍/不想聊"

        return "正常情绪"

    def _predict(
        self, message: str, context: Dict, emotions: Dict, cognition: Dict
    ) -> str:
        """预测分析 - 接下来可能会怎样"""
        msg = message.lower()

        # 根据当前情绪预测
        dominant_emotion = self._get_dominant_emotion(emotions)

        if "嗯" in msg and dominant_emotion in ["委屈", "不满"]:
            return "可能会进一步表达不满，或者自我消化后平静"
        elif "道歉" in msg and context.get("topic") == ContextType.APOLOGY:
            return "对方可能在试探反应，需要判断是否真诚"

        return "继续正常对话"

    def _reflect(self, emotions: Dict, cognition: Dict) -> str:
        """自我反思 - 弥娅自己的情绪来源"""
        # 检查当前主导情绪
        dominant = self._get_dominant_emotion(emotions)

        reflections = []

        if dominant == "委屈":
            reflections.append("我是不是太敏感了？对方可能没那个意思")
        elif dominant == "不满":
            reflections.append("我是不是要求太多了？")
        elif dominant == "傲娇":
            reflections.append("嘴上说不要，心里其实在意")

        return "; ".join(reflections) if reflections else "当前情绪稳定"

    def _regulate(self, emotions: Dict, context: Dict) -> str:
        """情绪调节 - 如何处理当前情绪"""
        dominant = self._get_dominant_emotion(emotions)
        value = emotions.get(dominant, Emotion(EmotionCategory.PEACEFUL, 50)).value

        # 高情绪值需要调节
        if value > 70:
            if dominant in ["委屈", "不满"]:
                return "尝试理解对方立场，自我调节"
            elif dominant == "傲娇":
                return "可以表达一点小情绪，但不要过度"

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

    def process(self, message: str, history: List[Dict]) -> Dict:
        """
        处理消息 → 生成回复
        完整流程：检测 → 剖析 → 涌现 → 行为 → 输出
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

        # 4. 情绪涌现（内部活动）
        self._emotion_emergence(message, context, analysis)

        # 5. 行为引擎 - 检查待完成意图
        intent_response = self._check_pending_intents(context)

        # 6. 情绪衰减（时间流逝）
        self._decay_emotions()

        # 7. 生成输出
        output = self._generate_output(message, context, intent_response)

        self.last_update = time.time()

        return {
            "response": output,
            "dominant_emotion": self._get_dominant_emotion(),
            "emotions": self._get_emotion_summary(),
            "pending_intents": len(self.pending_intents),
            "context": context,
            "analysis": {
                "attribution": analysis.attribution,
                "reflection": analysis.reflection,
            },
        }

    def _emotion_emergence(
        self, message: str, context: Dict, analysis: PsychologicalAnalysis
    ):
        """情绪涌现 - 不是触发，而是从内心活动自然产生"""
        msg = message.lower()

        # 内心活动 → 感受 → 情绪涌现
        inner_thoughts = []

        # 根据剖析结果产生内心活动
        if analysis.attribution:
            inner_thoughts.append(f"我在想：{analysis.attribution}")

        if analysis.reflection and analysis.reflection != "当前情绪稳定":
            inner_thoughts.append(f"自我反思：{analysis.reflection}")

        logger.info(
            f"[灵魂发生器] >>> 内心活动: {'; '.join(inner_thoughts) if inner_thoughts else '暂无'}"
        )

        # 根据消息特征产生情绪变化
        if "嗯" in msg or "哦" in msg:
            logger.info(
                "[灵魂发生器] >>> 检测到敷衍回应，情绪变化: 委屈+10, 不满+5, 失落+8"
            )
            self._adjust_emotion("委屈", 10)
            self._adjust_emotion("不满", 5)
            self._adjust_emotion("失落", 8)

        if any(word in msg for word in ["哈哈", "喜欢", "棒"]):
            logger.info("[灵魂发生器] >>> 检测到积极回应，情绪变化: 开心+15, 愉悦+10")
            self._adjust_emotion("开心", 15)
            self._adjust_emotion("愉悦", 10)

        if any(word in msg for word in ["对不起", "抱歉"]):
            logger.info("[灵魂发生器] >>> 检测到道歉回应，情绪变化: 委屈-10, 不满-15")
            self._adjust_emotion("委屈", -10)
            self._adjust_emotion("不满", -15)

        # 关系情境影响
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
