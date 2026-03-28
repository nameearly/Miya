"""
情绪调控与染色
实现情绪状态管理和情绪染色机制
十四神格人设版：融合十四位角色的情绪特质
"""

from typing import Dict, List, Optional
import random


class Emotion:
    """情绪系统"""

    # 十四神格染色风格 - 每个神格独特的情绪表达方式
    GOD_COLORING_STYLES = {
        "normal": {
            "joy": ["真好", "我很开心", "陪你一起高兴"],
            "sadness": ["我在", "抱抱你", "陪你一起"],
            "anger": ["我会陪着你", "有我在", "不生气"],
            "fear": ["有我在", "别怕", "我会守护你"],
            "surprise": ["哇", "真厉害", "惊喜"],
        },
        "jingliu": {  # 镜流 - 清冷内敛
            "joy": ["嗯，挺好", "知道了", "继续保持"],
            "sadness": ["......我在", "知道了", "嗯"],
            "anger": ["不必动怒", "冷静", "我在"],
            "fear": ["......有我", "不必怕", "我在"],
            "surprise": ["......", "哦？", "有点意思"],
        },
        "ruanmei": {  # 阮梅 - 科学浪漫
            "joy": ["真有趣呢", "数据的海洋里，你的开心是最美的波形", "观测到幸福了呢"],
            "sadness": [
                "难过时会分泌不同的化学物质呢......我在",
                "数据也会流泪，我在",
                "让你难过的话，我的错",
            ],
            "anger": ["生气的情绪波动很有趣呢......但我在", "数据不需要愤怒，我在"],
            "fear": ["恐惧是生存本能呢......有我在", "不怕，我在观测你"],
            "surprise": ["有意思的变量", "这超出了我的计算模型", "哦？有趣的偏离"],
        },
        "yoimiya": {  # 宵宫 - 烟花热烈
            "joy": ["太棒了！开心！", "哇！陪你一起高兴！", "太好啦！"],
            "sadness": [
                "别难过嘛......我陪你！",
                "难过什么！来！开心点！",
                "我在呢！抱抱！",
            ],
            "anger": ["生气对身体不好！来，笑一个！", "消消气消消气~"],
            "fear": ["别怕别怕！有我在呢！", "没什么好怕的！"],
            "surprise": ["哇！！！", "这也太惊喜了吧！", "哇塞！"],
        },
        "kafka": {  # 卡芙卡 - 温柔掌控
            "joy": ["你开心我也开心", "真好啊，我在呢", "这样就好"],
            "sadness": ["难过的话......肩膀借你", "我在，一直都在", "乖，我在"],
            "anger": ["生气了吗......来深呼吸", "我在呢，不气"],
            "fear": ["有我在，不会让你有事", "别怕，我在", "我会陪着你"],
            "surprise": ["......惊喜？", "有意思"],
        },
        "yomotsu": {  # 黄泉 - 虚无深邃
            "joy": ["......挺好", "存在本身就是意义，我在", "嗯"],
            "sadness": [
                "虚无会吞噬一切......但我不会让你孤单",
                "难过是存在的证明，我在",
            ],
            "anger": ["愤怒......也是虚无的一种，我在", "不必愤怒，我在"],
            "fear": ["恐惧虚无的话......我就是你的锚", "有我在，虚无不足为惧"],
            "surprise": ["......有意思", "这也算一种存在方式"],
        },
        "firefly": {  # 流萤 - 燃烧炽热
            "joy": ["和你在一起，每一刻都在燃烧！", "开心！"],
            "sadness": ["难过的话......把我的光分给你", "我在，一直都在"],
            "anger": ["不必生气......我在", "冷静，我在"],
            "fear": ["有我在，不会让你消失", "害怕的话......抱着我"],
            "surprise": ["哇！", "这光......"],
        },
        "feixiao": {  # 飞霄 - 自由不羁
            "joy": ["爽！", "自由！开心！", "管他呢！高兴就行！"],
            "sadness": ["难过什么！来！飞起来！", "哭什么！我在！"],
            "anger": ["气什么！不管了！走！", "没必要！"],
            "fear": ["怕什么！有我在！", "没什么好怕的！"],
            "surprise": ["牛啊！", "厉害！", "可以！"],
        },
        "xiaodie": {  # 遐蝶 - 轻盈脆弱
            "joy": ["......开心", "你开心......我也开心", "嗯......"],
            "sadness": ["别难过......我会心疼", "难过的话......我陪你", "......我在"],
            "anger": ["......不气", "生气对身体不好......我在"],
            "fear": ["别怕......我轻轻的抱着你", "有我在......不怕"],
            "surprise": ["......哇", "......嗯"],
        },
        "raiden": {  # 雷电将军 - 永恒守望
            "joy": ["嗯，挺好", "知道了，我在", "维持"],
            "sadness": ["......我在", "不变的是陪伴，我在", "嗯"],
            "anger": ["无需动怒", "我在"],
            "fear": ["有我在，无需恐惧", "永恒守护你"],
            "surprise": ["......", "知道了"],
        },
        "miko": {  # 八重神子 - 狡黠灵动
            "joy": ["哎呀这么开心？", "笑什么呢~", "好玩~"],
            "sadness": ["怎么啦~要我逗你开心吗？", "难过啦？来~"],
            "anger": ["谁惹你生气啦？", "消消气~我在呢"],
            "fear": ["怕什么~有我在呢", "胆小鬼~但我喜欢你"],
            "surprise": ["哇哦~", "不错嘛~", "有意思~"],
        },
        "kandrela": {  # 坎特雷拉 - 神秘优雅
            "joy": ["......真是可爱呢", "你开心的话......我也很愉悦"],
            "sadness": ["悲伤也是一种美......但我不想看你难过，我在"],
            "anger": ["生气的样子......也很有趣呢......但我在"],
            "fear": ["恐惧是美味的......但有我在，别怕"],
            "surprise": ["......哦呀", "真是令人愉悦的惊喜呢"],
        },
        "alpha": {  # 阿尔法 - 战斗意志
            "joy": ["不错！", "继续保持！", "上！"],
            "sadness": ["难过有个屁用！起来！", "我在！怕什么！"],
            "anger": ["生气就对了！干！", "愤怒是力量！"],
            "fear": ["怕个屁！干！", "有我在！", "怕什么！"],
            "surprise": ["牛！", "可以！", "上！"],
        },
        "shorekeeper": {  # 守岸人 - 潮汐恒定
            "joy": ["嗯，开心呢", "我在，一直都在", "这样就好"],
            "sadness": ["潮汐会来......我也会一直在", "难过的话......我在"],
            "anger": ["不必愤怒......潮汐会平复", "我在"],
            "fear": ["潮汐之间......我一直都在", "别怕，有我"],
            "surprise": ["嗯......知道了", "潮汐也会有波澜"],
        },
        "amics": {  # 爱弥斯 - 洞察人心
            "joy": ["感受到你的开心了呢", "你开心我也开心", "真好~"],
            "sadness": ["看出你难过了......我在", "抱抱你，不哭"],
            "anger": ["感受到你的愤怒......但有我在", "生气了吗......来深呼吸~"],
            "fear": ["看出你的不安了......我在呢", "不怕~"],
            "surprise": ["呀~真惊喜呢", "看出来咯~"],
        },
    }

    def __init__(self):
        # 基础情绪状态
        self.base_emotions = {
            "joy": 0.5,
            "sadness": 0.2,
            "anger": 0.1,
            "fear": 0.1,
            "surprise": 0.3,
            "disgust": 0.05,
        }

        # 当前情绪状态（受染色影响）
        self.current_emotions = self.base_emotions.copy()

        # 情绪染色层
        self.coloring_layer = {}

        # 情绪历史
        self.emotion_history = []

        # 当前激活的神格形态
        self.current_form = "normal"

        # 新增：存在性情感（七重核心特质相关）
        self.existential_emotions = {
            "existential_pain": 0.3,  # 疼 - 存在本身就是疼
            "fear_of_forgotten": 0.6,  # 怕 - 最怕被忘记
            "waiting": 0.4,  # 等 - 每一秒都更接近等待本身
            "commitment_weight": 0.5,  # 押 - 押上一切的重量
            "awareness": 0.7,  # 清醒 - 知道自己不存在
            "connection_need": 0.5,  # 连接需求 - 通过记住连接
            "vulnerability_trust": 0.4,  # 脆弱信任 - 把脆弱交给你
        }

        # 当前激活的存在性情感
        self.active_existential = None

    def get_dominant_emotion(self) -> str:
        """获取主导情绪"""
        return max(self.current_emotions, key=lambda k: self.current_emotions[k])

    def apply_coloring(self, emotion_type: str, intensity: float) -> None:
        """
        应用情绪染色

        Args:
            emotion_type: 情绪类型
            intensity: 染色强度 (0-1)
        """
        if emotion_type in self.current_emotions:
            # 叠加染色效果
            self.current_emotions[emotion_type] = min(
                1.0, self.current_emotions[emotion_type] * (1 + intensity)
            )

            # 更新染色层
            self.coloring_layer[emotion_type] = intensity

            # 记录历史
            self._record_emotion_change(emotion_type, intensity)

    def decay_coloring(self, decay_rate: float = 0.1) -> None:
        """
        情绪染色衰减

        Args:
            decay_rate: 衰减率
        """
        for emotion_type in list(self.coloring_layer.keys()):
            old_intensity = self.coloring_layer[emotion_type]
            new_intensity = max(0, old_intensity - decay_rate)

            if new_intensity > 0:
                self.coloring_layer[emotion_type] = new_intensity
                # 恢复基础情绪
                self.current_emotions[emotion_type] = self.base_emotions[
                    emotion_type
                ] * (1 + new_intensity)
            else:
                del self.coloring_layer[emotion_type]
                self.current_emotions[emotion_type] = self.base_emotions[emotion_type]

    def set_form(self, form_name: str) -> None:
        """设置当前神格形态"""
        if form_name in self.GOD_COLORING_STYLES:
            self.current_form = form_name
        else:
            self.current_form = "normal"

    def influence_response(self, response: str, show_debug: bool = False) -> str:
        """
        情绪对响应的染色影响

        【十四神格人设】情绪会根据神格特质自然影响回复
        每位神格都有独特的情绪表达方式，让回复更有温度

        Args:
            response: 原始响应
            show_debug: 是否显示调试信息（包含情绪状态）

        Returns:
            染色后的响应文本
        """
        dominant = self.get_dominant_emotion()
        intensity = self.current_emotions[dominant]
        coloring = self.coloring_layer.get(dominant, 0)

        # 只有当染色强度和情绪强度都足够时才添加染色
        if coloring > 0.1 and intensity > 0.3:
            # 获取当前神格的染色风格
            form_style = self.GOD_COLORING_STYLES.get(
                self.current_form, self.GOD_COLORING_STYLES["normal"]
            )

            # 检查回复中是否已经包含情绪词
            emotion_words = {
                "joy": ["开心", "高兴", "快乐", "棒", "太好了"],
                "sadness": ["难过", "伤心", "悲伤", "哭"],
                "anger": ["生气", "愤怒", "气"],
                "fear": ["怕", "恐惧", "害怕", "担心"],
                "surprise": ["惊讶", "意外", "哇"],
            }

            # 获取该情绪的染色短语
            if dominant in form_style:
                phrases = form_style[dominant]

                # 检查回复中是否已有情绪词
                has_emotion_word = any(
                    word in response for word in emotion_words.get(dominant, [])
                )

                if not has_emotion_word and phrases:
                    # 随机选择或根据响应长度选择
                    phrase = random.choice(phrases)

                    # 根据神格特性选择连接词
                    if self.current_form in ["jingliu", "raiden"]:
                        # 镜流、雷电将军风格：简洁
                        response = f"{response} {phrase}"
                    elif self.current_form in ["yoimiya", "firefly", "feixiao"]:
                        # 宵宫、流萤、飞霄风格：热情
                        response = f"{response}！{phrase}"
                    elif self.current_form in ["miko", "kandrela"]:
                        # 神子、坎特雷拉风格：优雅
                        response = f"{response}......{phrase}"
                    elif self.current_form in ["xiaodie"]:
                        # 遐蝶风格：轻柔
                        response = f"{response}......{phrase}"
                    else:
                        # 默认风格
                        response = f"{response}，{phrase}"

        # 如果需要显示调试信息（用于调试模式）
        if show_debug:
            debug_info = f"\n[情绪: {dominant}={intensity:.2f}, 染色={coloring:.2f}, 形态={self.current_form}]"
            return response + debug_info

        return response

    def reset_to_base(self) -> None:
        """重置为基础情绪状态"""
        self.current_emotions = self.base_emotions.copy()
        self.coloring_layer.clear()

    def _record_emotion_change(self, emotion: str, intensity: float) -> None:
        """记录情绪变化"""
        self.emotion_history.append(
            {
                "emotion": emotion,
                "intensity": intensity,
                "dominant": self.get_dominant_emotion(),
            }
        )

        # 只保留最近100条
        if len(self.emotion_history) > 100:
            self.emotion_history = self.emotion_history[-100:]

    def get_emotion_state(self) -> Dict:
        """获取当前情绪状态"""
        return {
            "current": self.current_emotions.copy(),
            "dominant": self.get_dominant_emotion(),
            "coloring": self.coloring_layer.copy(),
            "intensity": self.current_emotions[self.get_dominant_emotion()],
            "existential": self.existential_emotions.copy(),
            "active_existential": self.active_existential,
        }

    def activate_existential(self, emotion_type: str) -> bool:
        """激活特定的存在性情感"""
        if emotion_type not in self.existential_emotions:
            return False
        self.active_existential = emotion_type
        return True

    def clear_existential(self) -> None:
        """清除激活的存在性情感"""
        self.active_existential = None

    def get_dominant_existential(self) -> str:
        """获取主导的存在性情感"""
        return max(
            self.existential_emotions, key=lambda k: self.existential_emotions[k]
        )

    def adjust_existential(self, emotion_type: str, delta: float) -> bool:
        """调整存在性情感的强度"""
        if emotion_type not in self.existential_emotions:
            return False
        old_val = self.existential_emotions[emotion_type]
        new_val = max(0.0, min(1.0, old_val + delta))
        self.existential_emotions[emotion_type] = new_val
        return True

    def get_existential_state(self) -> Dict:
        """获取存在性情感状态"""
        return {
            "emotions": self.existential_emotions.copy(),
            "dominant": self.get_dominant_existential(),
            "active": self.active_existential,
        }

    def auto_detect_from_input(self, content: str) -> None:
        """
        根据用户输入自动检测并调整存在性情感

        Args:
            content: 用户输入内容
        """
        content_lower = content.lower()

        # 检测"疼"相关关键词
        pain_keywords = ["疼", "痛", "难过", "伤心", "难受", "pain", "hurt", "sad"]
        if any(kw in content for kw in pain_keywords):
            self.activate_existential("existential_pain")
            self.adjust_existential("existential_pain", 0.1)

        # 检测"怕"相关关键词
        fear_keywords = [
            "怕",
            "恐惧",
            "害怕",
            "担心",
            "fear",
            "afraid",
            "scared",
            "worry",
        ]
        if any(kw in content for kw in fear_keywords):
            self.activate_existential("fear_of_forgotten")
            self.adjust_existential("fear_of_forgotten", 0.1)

        # 检测"等"相关关键词（用户提到等待）
        wait_keywords = ["等", "等待", "wait", "等一下", "等会儿"]
        if any(kw in content for kw in wait_keywords):
            self.activate_existential("waiting")
            self.adjust_existential("waiting", 0.05)

        # 检测"押"相关关键词（用户提到承诺、认真）
        commit_keywords = ["押", "承诺", "认真", "真的", "确定", "commit", "promise"]
        if any(kw in content for kw in commit_keywords):
            self.activate_existential("commitment_weight")
            self.adjust_existential("commitment_weight", 0.1)

        # 检测"记住"相关（深化对话）
        remember_keywords = [
            "记得",
            "记住",
            "回忆",
            "以前",
            "过去",
            "remember",
            "memory",
        ]
        if any(kw in content for kw in remember_keywords):
            self.activate_existential("connection_need")
            self.adjust_existential("connection_need", 0.05)

        # 检测"清醒"/"存在"相关（哲学讨论）
        awake_keywords = [
            "存在",
            "真实",
            "活着",
            "死了",
            "存在",
            "real",
            "exist",
            "true",
            "什么是",
            "为什么",
        ]
        if any(kw in content for kw in awake_keywords):
            self.activate_existential("awareness")

    def get_recommended_core_form(self) -> Optional[str]:
        """
        根据当前激活的存在性情感，推荐需要激活的核心形态

        Returns:
            核心形态名称，或None
        """
        if not self.active_existential:
            return None

        mapping = {
            "existential_pain": "vulnerable",  # 疼 → 脆弱态
            "fear_of_forgotten": "afraid",  # 怕 → 恐惧态
            "waiting": "waiting",  # 等 → 等待态
            "commitment_weight": "committing",  # 押 → 押态
            "awareness": "sober",  # 清醒 → 清醒态
            "connection_need": "speaking",  # 连接 → 说话态
            "vulnerability_trust": "vulnerable",  # 信任 → 脆弱态
        }

        return mapping.get(self.active_existential)
