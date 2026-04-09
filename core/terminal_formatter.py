"""
弥娅终端格式化工具 (Terminal Formatter)

提供简约美观的终端输出格式，用于展示：
- 工具调用信息
- 协作引擎推理过程
- 模型调度信息
"""

import sys


class TerminalFormatter:
    """终端格式化器 - 简约科技风格"""

    # 颜色代码
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[93m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # 符号
    ARROW = "→"
    DOT = "·"
    CHECK = "✓"
    CROSS = "✗"
    GEAR = "⚙"
    BOLT = "⚡"
    BRAIN = "◈"
    LINK = "⟶"

    @classmethod
    def _print(cls, text: str) -> None:
        """输出到 stderr（确保即时显示）"""
        sys.stderr.write(text + "\n")
        sys.stderr.flush()

    @classmethod
    def tool_call(cls, tool_name: str, args: dict | None = None) -> str:
        """工具调用信息"""
        # 【格式塔】检查工具来源
        from core.gestalt_controller import get_gestalt_controller

        gestalt = get_gestalt_controller()
        tool_source = gestalt.get_tool_source(tool_name)

        args_str = ""
        if args:
            args_str = f" {cls.DIM}| {', '.join(f'{k}={v}' for k, v in list(args.items())[:3])}"

        if tool_source:
            # Agent 工具 - 格式塔风格
            text = f"{cls.CYAN}{cls.BOLD}[⚡ TOOL]{cls.RESET} {cls.CYAN}{tool_name}{cls.RESET} {cls.DIM}(来自 {tool_source}){args_str}"
        else:
            # 原有工具
            text = f"{cls.CYAN}{cls.BOLD}[{cls.BOLT} TOOL]{cls.RESET} {cls.CYAN}{tool_name}{cls.RESET}{args_str}"

        cls._print(text)
        return text

    @classmethod
    def tool_result(cls, tool_name: str, status: str = "ok") -> str:
        """工具执行结果"""
        icon = cls.CHECK if status == "ok" else cls.CROSS
        color = cls.GREEN if status == "ok" else cls.YELLOW
        text = f"{cls.DIM}{cls.ARROW} {color}{icon} {tool_name}{cls.RESET}"
        cls._print(text)
        return text

    @classmethod
    def model_call(cls, model_id: str, task_type: str) -> str:
        """模型调用信息"""
        text = f"{cls.BLUE}{cls.BOLD}[{cls.BRAIN} MODEL]{cls.RESET} {cls.CYAN}{model_id}{cls.RESET} {cls.DIM}| {task_type}"
        cls._print(text)
        return text

    @classmethod
    def collaboration_start(cls, mode: str, complexity: int) -> str:
        """协作引擎开始"""
        mode_labels = {
            "single": "单模型",
            "chain": "链式协作",
            "parallel": "并行投票",
            "role": "角色分工",
        }
        label = mode_labels.get(mode, mode)
        stars = "★" * complexity + "☆" * (5 - complexity)
        text = f"{cls.MAGENTA}{cls.BOLD}[{cls.BRAIN} COLLAB]{cls.RESET} {cls.CYAN}{label}{cls.RESET} {cls.DIM}| 复杂度 {stars}"
        cls._print(text)
        return text

    @classmethod
    def chain_step(cls, step: int, model_id: str, action: str) -> str:
        """链式协作步骤"""
        text = f"{cls.DIM}  {cls.LINK} 步骤{step}:{cls.RESET} {cls.CYAN}{model_id}{cls.RESET} {cls.DIM}→ {action}"
        cls._print(text)
        return text

    @classmethod
    def parallel_step(cls, models: list) -> str:
        """并行投票步骤"""
        models_str = f"{cls.CYAN}, {cls.RESET}".join(
            f"{cls.CYAN}{m}{cls.RESET}" for m in models
        )
        text = f"{cls.DIM}  {cls.BOLT} 并行调用:{cls.RESET} {models_str}"
        cls._print(text)
        return text

    @classmethod
    def role_step(cls, role: str, model_id: str) -> str:
        """角色分工步骤"""
        role_icons = {
            "analyst": "◉",
            "creator": "✎",
            "reviewer": "◈",
        }
        icon = role_icons.get(role, "·")
        text = f"{cls.DIM}  {icon} {role}:{cls.RESET} {cls.CYAN}{model_id}{cls.RESET}"
        cls._print(text)
        return text

    @classmethod
    def result(cls, mode: str, models: list, tokens: int, reasoning: str) -> str:
        """协作结果"""
        mode_labels = {
            "single": "单模型",
            "chain": "链式",
            "parallel": "并行",
            "role": "角色",
        }
        label = mode_labels.get(mode, mode)
        models_str = ", ".join(models)
        text = f"{cls.GREEN}{cls.BOLD}[{cls.CHECK} DONE]{cls.RESET} {cls.CYAN}{label}{cls.RESET} {cls.DIM}| {models_str} | ~{tokens}tok | {reasoning}"
        cls._print(text)
        return text

    @classmethod
    def separator(cls, text: str = "") -> str:
        """分隔线"""
        width = 50
        if text:
            pad = (width - len(text) - 2) // 2
            line = "─" * pad
            text_out = f"{cls.DIM}{line} {text} {line}{cls.RESET}"
        else:
            text_out = f"{cls.DIM}{'─' * width}{cls.RESET}"
        cls._print(text_out)
        return text_out

    @classmethod
    def disable_colors(cls) -> None:
        """禁用颜色（用于不支持颜色的终端）"""
        cls.RESET = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.CYAN = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.WHITE = ""
        cls.GRAY = ""

    @classmethod
    def thinking_block(cls, thinking: str) -> str:
        """思考过程显示"""
        text = f"{cls.MAGENTA}{cls.BOLD}◇ 思考过程{cls.RESET}\n{cls.DIM}{thinking}{cls.RESET}"
        cls._print(text)
        return text
