"""
QQ命令配置加载器
动态加载所有QQ端命令配置
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

_config: Optional[Dict[str, Any]] = None


def _load_config() -> Dict[str, Any]:
    """加载QQ命令配置"""
    global _config

    if _config is not None:
        return _config

    config_path = Path(__file__).parent.parent / "config" / "qq_command_config.json"

    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                _config = json.load(f)
            logger.info("QQ命令配置加载成功")
        else:
            logger.warning(f"QQ命令配置文件不存在: {config_path}")
            _config = _get_default_config()
    except Exception as e:
        logger.warning(f"加载QQ命令配置失败: {e}，使用默认配置")
        _config = _get_default_config()

    return _config


def _get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "command_aliases": {
            "help": ["帮助", "help", "?", "？"],
            "status": ["状态", "查看状态", "/状态", "状态查询"],
            "form": ["形态", "/形态", "form"],
            "speak": ["说话", "/说话", "speak"],
            "exist": ["存在", "/存在", "exist"],
            "voice": ["voice", "语音", "/voice", "/语音"],
            "text": ["text", "文本", "/text", "/文本"],
        },
        "system_commands": {
            "help": {"command": "/help", "aliases": ["帮助", "help"]},
            "status": {"command": "/状态", "aliases": ["状态", "查看状态"]},
        },
        "personality_commands": {
            "form": {
                "command": "/形态",
                "aliases": ["形态", "/形态", "form"],
            },
            "speak": {
                "command": "/说话",
                "aliases": ["说话", "/说话", "speak"],
            },
            "exist": {
                "command": "/存在",
                "aliases": ["存在", "/存在", "exist"],
            },
        },
    }


def reload_config():
    """重新加载配置"""
    global _config
    _config = None
    return _load_config()


def get_command_aliases(command_type: str) -> List[str]:
    """获取命令别名"""
    config = _load_config()
    return config.get("command_aliases", {}).get(command_type, [])


def match_command(content: str, command_type: str) -> bool:
    """检查内容是否匹配命令类型"""
    content_lower = content.lower().strip()

    aliases = get_command_aliases(command_type)
    for alias in aliases:
        alias_lower = alias.lower()
        if content_lower == alias_lower or content_lower.startswith(alias_lower):
            return True

    return False


def is_help_command(content: str) -> bool:
    """检查是否是帮助命令"""
    return match_command(content, "help")


def is_status_command(content: str) -> bool:
    """检查是否是状态命令"""
    return match_command(content, "status")


def is_form_command(content: str) -> bool:
    """检查是否是形态命令"""
    return match_command(content, "form")


def is_speak_command(content: str) -> bool:
    """检查是否是说话模式命令"""
    return match_command(content, "speak")


def is_exist_command(content: str) -> bool:
    """检查是否是存在性情感命令"""
    return match_command(content, "exist")


def is_voice_command(content: str) -> bool:
    """检查是否是语音切换命令"""
    return match_command(content, "voice")


def is_text_command(content: str) -> bool:
    """检查是否是文本切换命令"""
    return match_command(content, "text")


def is_memory_command(content: str) -> bool:
    """检查是否是记忆命令"""
    config = _load_config()
    memory_aliases = config.get("command_aliases", {}).get("memory", [])
    content_lower = content.lower().strip()

    for alias in memory_aliases:
        if content_lower.startswith(alias.lower()):
            return True
    return False


def get_memory_command_type(content: str) -> Optional[str]:
    """获取记忆命令类型"""
    config = _load_config()
    memory_config = config.get("memory_commands", {}).get("commands", {})

    content_lower = content.lower().strip()

    for cmd_type, cmd_info in memory_config.items():
        aliases = cmd_info.get("aliases", [])
        for alias in aliases:
            if content_lower == alias.lower() or content_lower.startswith(
                alias.lower()
            ):
                return cmd_type

    return None


def get_quick_response_keywords(response_type: str) -> List[str]:
    """获取快速响应关键词"""
    config = _load_config()
    return config.get("quick_responses", {}).get(response_type, {}).get("keywords", [])


def is_greeting_keyword(content: str) -> bool:
    """检查是否是问候关键词"""
    return content.lower().strip() in [
        k.lower() for k in get_quick_response_keywords("greeting")
    ]


def is_farewell_keyword(content: str) -> bool:
    """检查是否是告别关键词"""
    return content.lower().strip() in [
        k.lower() for k in get_quick_response_keywords("farewell")
    ]


def get_error_message(error_type: str) -> str:
    """获取错误消息"""
    config = _load_config()
    return config.get("error_messages", {}).get(error_type, "命令执行失败")


def format_help_message() -> str:
    """格式化帮助信息"""
    config = _load_config()

    lines = ["可用命令:"]

    sys_cmds = config.get("system_commands", {})
    for cmd_name, cmd_info in sys_cmds.items():
        if isinstance(cmd_info, dict):
            aliases = cmd_info.get("aliases", [])
            desc = cmd_info.get("description", "")
            lines.append(f"  {aliases[0] if aliases else ''} - {desc}")

    pers_cmds = config.get("personality_commands", {})
    for cmd_name, cmd_info in pers_cmds.items():
        if isinstance(cmd_info, dict):
            aliases = cmd_info.get("aliases", [])
            desc = cmd_info.get("description", "")
            lines.append(f"  {aliases[0] if aliases else ''} - {desc}")

    mode_cmds = config.get("mode_commands", {})
    for cmd_name, cmd_info in mode_cmds.items():
        if isinstance(cmd_info, dict):
            aliases = cmd_info.get("aliases", [])
            desc = cmd_info.get("description", "")
            lines.append(f"  {aliases[0] if aliases else ''} - {desc}")

    memory_cmds = config.get("memory_commands", {}).get("commands", {})
    for cmd_name, cmd_info in memory_cmds.items():
        if isinstance(cmd_info, dict):
            aliases = cmd_info.get("aliases", [])
            desc = cmd_info.get("description", "")
            lines.append(f"  {aliases[0] if aliases else ''} - {desc}")

    return "\n".join(lines)


class QQCommandConfig:
    """QQ命令配置类"""

    def __init__(self):
        self._config = _load_config()

    def match_command(self, content: str, command_type: str) -> bool:
        return match_command(content, command_type)

    def is_help(self, content: str) -> bool:
        return is_help_command(content)

    def is_status(self, content: str) -> bool:
        return is_status_command(content)

    def is_form(self, content: str) -> bool:
        return is_form_command(content)

    def is_speak(self, content: str) -> bool:
        return is_speak_command(content)

    def is_exist(self, content: str) -> bool:
        return is_exist_command(content)

    def is_voice(self, content: str) -> bool:
        return is_voice_command(content)

    def is_text(self, content: str) -> bool:
        return is_text_command(content)

    def is_memory(self, content: str) -> bool:
        return is_memory_command(content)

    def get_memory_type(self, content: str) -> Optional[str]:
        return get_memory_command_type(content)

    def get_help(self) -> str:
        return format_help_message()

    def get_error(self, error_type: str) -> str:
        return get_error_message(error_type)

    def get_quick_keywords(self, response_type: str) -> List[str]:
        return get_quick_response_keywords(response_type)

    def is_greeting(self, content: str) -> bool:
        return is_greeting_keyword(content)

    def is_farewell(self, content: str) -> bool:
        return is_farewell_keyword(content)

    def reload(self):
        """重新加载"""
        reload_config()
        self._config = _load_config()


_command_config: Optional[QQCommandConfig] = None


def get_qq_command_config() -> QQCommandConfig:
    """获取QQ命令配置实例"""
    global _command_config
    if _command_config is None:
        _command_config = QQCommandConfig()
    return _command_config
