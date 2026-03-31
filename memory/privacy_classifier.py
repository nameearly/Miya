"""
记忆隐私分类器 - 识别群聊/私聊并判断私密话题

功能：
1. 识别消息来源（群聊/私聊）
2. 判断话题是否私密
3. 根据隐私级别决定存储策略
"""

import re
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ChatType(str, Enum):
    """聊天类型"""

    PRIVATE = "private"  # 私聊
    GROUP = "group"  # 群聊


class PrivacyLevel(str, Enum):
    """隐私级别"""

    PUBLIC = "public"  # 公开 - 可共享
    CONTEXT = "context"  # 上下文 - 仅当前会话
    GROUP_PRIVATE = "group_private"  # 群内私密 - 仅群内可见
    PERSONAL = "personal"  # 个人私密 - 仅用户可见
    SECRET = "secret"  # 极密 - 仅开发者可见


@dataclass
class PrivacyClassification:
    """隐私分类结果"""

    chat_type: ChatType  # 聊天类型
    privacy_level: PrivacyLevel  # 隐私级别
    is_sensitive: bool  # 是否敏感
    sensitivity_reasons: List[str]  # 敏感原因
    should_remember: bool  # 是否应该记住
    storage_scope: str  # 存储范围 (global/user/group)


class PrivacyClassifier:
    """隐私分类器

    用于判断消息的隐私级别和存储范围
    """

    # 敏感关键词 patterns
    SENSITIVE_PATTERNS = {
        # 个人信息
        "personal_info": [
            r"(手机|电话|身份证|银行卡|密码|账号).{0,10}(号|码|码|号)",
            r"\d{11,}",  # 手机号
            r"\d{15,18}",  # 身份证号
            r"(密码|账号|用户名|登录).{0,10}(是|为|为|=|：)",
        ],
        # 健康相关
        "health": [
            r"(生病|生病|医院|看病|体检|确诊|病情|症状|治疗)",
            r"(抑郁|焦虑|心理|精神|情绪崩溃|想死|自杀)",
            r"(心脏病|高血压|糖尿病|癌症|绝症)",
        ],
        # 情感相关
        "emotion": [
            r"(暗恋|表白|追求|分手|离婚|出轨|婚外情)",
            r"(秘密|不能告诉别人|只告诉你|不要说出去)",
            r"(隐私|私密|不想让别人知道)",
        ],
        # 财务相关
        "finance": [
            r"(工资|收入|存款|负债|欠款|房贷|车贷)",
            r"(借钱|借我|还钱|欠我|转账|汇款)",
            r"(投资|理财|亏损|赚钱|生意)",
        ],
        # 位置相关
        "location": [
            r"(我在|处于|住在|在.*家|在.*公司)",
            r"(地址|定位|在哪里|来.*找我)",
        ],
    }

    # 群聊特定模式
    GROUP_SPECIFIC_PATTERNS = [
        r"@.*\s",  # @他人
        r"有人.*吗",  # 询问群成员
        r"大家.*",  # 群体话题
    ]

    # 私聊特定模式
    PRIVATE_SPECIFIC_PATTERNS = [
        r"只有.*我们两个",
        r"不想让.*知道",
        r"私密.*话",
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self._sensitive_compiled = {}
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            self._sensitive_compiled[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        self._group_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.GROUP_SPECIFIC_PATTERNS
        ]

        self._private_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.PRIVATE_SPECIFIC_PATTERNS
        ]

    def classify(
        self,
        message: str,
        chat_type: ChatType,
        group_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> PrivacyClassification:
        """分类消息的隐私级别

        Args:
            message: 消息内容
            chat_type: 聊天类型
            group_id: 群ID (如果是群聊)
            user_id: 用户ID

        Returns:
            PrivacyClassification: 分类结果
        """
        sensitivity_reasons = []
        is_sensitive = False

        # 1. 检测敏感内容
        for category, patterns in self._sensitive_compiled.items():
            for pattern in patterns:
                if pattern.search(message):
                    is_sensitive = True
                    sensitivity_reasons.append(category)
                    break

        # 2. 检测私聊特定模式
        if chat_type == ChatType.PRIVATE:
            for pattern in self._private_compiled:
                if pattern.search(message):
                    is_sensitive = True
                    sensitivity_reasons.append("private_topic")
                    break

        # 3. 确定隐私级别
        privacy_level = self._determine_privacy_level(
            chat_type, is_sensitive, sensitivity_reasons
        )

        # 4. 确定存储范围
        storage_scope = self._determine_storage_scope(
            chat_type, privacy_level, group_id, user_id
        )

        # 5. 判断是否应该记住
        should_remember = self._should_remember(privacy_level, is_sensitive)

        logger.debug(
            f"[PrivacyClassifier] chat={chat_type.value}, "
            f"privacy={privacy_level.value}, sensitive={is_sensitive}, "
            f"scope={storage_scope}"
        )

        return PrivacyClassification(
            chat_type=chat_type,
            privacy_level=privacy_level,
            is_sensitive=is_sensitive,
            sensitivity_reasons=sensitivity_reasons,
            should_remember=should_remember,
            storage_scope=storage_scope,
        )

    def _determine_privacy_level(
        self,
        chat_type: ChatType,
        is_sensitive: bool,
        reasons: List[str],
    ) -> PrivacyLevel:
        """确定隐私级别"""
        if is_sensitive:
            # 敏感内容根据原因确定级别
            if "personal_info" in reasons or "password" in reasons:
                return PrivacyLevel.SECRET
            elif "health" in reasons or "emotion" in reasons:
                return PrivacyLevel.PERSONAL
            elif "finance" in reasons or "location" in reasons:
                return PrivacyLevel.PERSONAL
            else:
                return PrivacyLevel.GROUP_PRIVATE

        # 非敏感内容根据聊天类型
        if chat_type == ChatType.PRIVATE:
            return PrivacyLevel.PERSONAL
        else:
            return PrivacyLevel.CONTEXT

    def _determine_storage_scope(
        self,
        chat_type: ChatType,
        privacy_level: PrivacyLevel,
        group_id: Optional[str],
        user_id: Optional[str],
    ) -> str:
        """确定存储范围"""
        if privacy_level == PrivacyLevel.SECRET:
            # 极密 - 仅开发者可见
            return "developer"  # 特殊标记，仅佳可见

        if privacy_level == PrivacyLevel.PERSONAL:
            # 个人私密 - 仅用户可见
            if user_id:
                return f"user:{user_id}"
            return "global"

        if privacy_level == PrivacyLevel.GROUP_PRIVATE:
            # 群内私密
            if group_id:
                return f"group:{group_id}"
            return "global"

        if privacy_level == PrivacyLevel.CONTEXT:
            # 上下文级别 - 仅当前会话
            if group_id:
                return f"group:{group_id}"
            if user_id:
                return f"user:{user_id}"
            return "global"

        # 公开内容
        return "global"

    def _should_remember(
        self,
        privacy_level: PrivacyLevel,
        is_sensitive: bool,
    ) -> bool:
        """判断是否应该记住"""
        # 敏感内容都应该记住
        if is_sensitive:
            return True

        # 私聊内容默认记住
        if privacy_level in [PrivacyLevel.PERSONAL, PrivacyLevel.SECRET]:
            return True

        # 群聊公开内容不主动记住，但可检索
        if privacy_level == PrivacyLevel.CONTEXT:
            return False

        return False

    def is_private_message(self, event: Dict) -> bool:
        """判断是否是私聊消息

        Args:
            event: 消息事件

        Returns:
            bool: 是否是私聊
        """
        message_type = event.get("message_type", "")
        group_id = event.get("group_id", 0)

        # 私聊或group_id为0
        return message_type == "private" or group_id == 0


# 全局实例
_classifier: Optional[PrivacyClassifier] = None


def get_privacy_classifier() -> PrivacyClassifier:
    """获取隐私分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = PrivacyClassifier()
    return _classifier


async def classify_message(
    message: str,
    message_type: str,
    group_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> PrivacyClassification:
    """便捷函数：分类消息隐私级别

    Args:
        message: 消息内容
        message_type: 消息类型 (group/private)
        group_id: 群ID
        user_id: 用户ID

    Returns:
        PrivacyClassification: 分类结果
    """
    classifier = get_privacy_classifier()

    # 转换类型
    chat_type = ChatType.GROUP if message_type == "group" else ChatType.PRIVATE

    return classifier.classify(
        message=message,
        chat_type=chat_type,
        group_id=str(group_id) if group_id else None,
        user_id=str(user_id) if user_id else None,
    )
