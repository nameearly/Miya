"""
弥娅V4.0 - 多终端交互Shell

支持单机多终端管理的交互式界面
集成弥娅框架的完整AI能力和统一提示词管理系统
"""

import asyncio
import sys
import os
import platform
import random
import json
import logging
from pathlib import Path
from typing import Optional, Any, Literal
from dataclasses import dataclass, field

# 跨平台控制台编码设置 - 支持中文输入
os.environ["PYTHONIOENCODING"] = "utf-8"

# Windows 下设置控制台编码
if sys.platform == "win32":
    import subprocess

    try:
        subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
    except:
        pass

    # 设置标准输入输出编码
    import io

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    if hasattr(sys.stdin, "buffer"):
        sys.stdin = io.TextIOWrapper(
            sys.stdin.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )


import builtins
import functools

# 保存原始 print
_original_print = builtins.print


def safe_print(*args, **kwargs):
    """安全打印，处理 I/O 错误"""
    try:
        _original_print(*args, **kwargs)
    except (ValueError, OSError, AttributeError):
        pass


def chinese_input(prompt: str) -> str:
    """
    跨平台中文输入函数

    Args:
        prompt: 提示文本

    Returns:
        用户输入的字符串
    """
    # 确保每次调用前都设置编码
    if sys.platform == "win32":
        import io

        try:
            if hasattr(sys.stdin, "buffer") and not isinstance(
                sys.stdin, io.TextIOWrapper
            ):
                sys.stdin = io.TextIOWrapper(
                    sys.stdin.buffer,
                    encoding="utf-8",
                    errors="replace",
                    line_buffering=True,
                )
        except (ValueError, OSError):
            pass

    try:
        # 检查 stdout 是否可用
        if prompt and hasattr(sys.stdout, "write") and not sys.stdout.closed:
            try:
                sys.stdout.write(prompt)
                sys.stdout.flush()
            except (ValueError, OSError):
                pass

        # 检查 stdin 是否可用
        if hasattr(sys.stdin, "readline") and not sys.stdin.closed:
            line = sys.stdin.readline()
            if line:
                if line.endswith("\n"):
                    line = line[:-1]
                elif line.endswith("\r\n"):
                    line = line[:-2]
                return line

        # 如果 stdin 不可用，尝试使用 input
        return input(prompt) if prompt else input()

    except (ValueError, OSError, AttributeError):
        # 最终回退
        try:
            return input(prompt) if prompt else input()
        except:
            return ""


# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.terminal_orchestrator import IntelligentTerminalOrchestrator
from core.terminal_types import TerminalType
from core.prompt_manager import PromptManager
from core.ai_client import AIMessage, AIClientFactory
from core.project_types import SessionID
from core.logging_config import get_logger, LogContext, log_execution_time
from core.error_handler import error_handler
from core.monitoring.performance import monitor_performance
from dotenv import load_dotenv

# 配置日志
logger = get_logger(__name__)


@dataclass
class AICommandInfo:
    """AI生成的命令信息"""

    session_id: SessionID
    command: str
    description: Optional[str] = None


@dataclass
class AIProcessingResult:
    """AI处理结果"""

    success: bool
    type: Literal["conversation", "command_execution", "error"]
    message: str
    needs_command: bool = False
    commands: list[AICommandInfo] = field(default_factory=list)


class MiyaTerminalAI:
    """弥娅终端AI - 集成完整AI能力"""

    def __init__(self):
        """初始化AI系统"""
        # 初始化提示词管理器
        self.prompt_manager: PromptManager = PromptManager()

        # 加载配置
        self._load_config()

        # 初始化AI客户端（延迟初始化，避免在 __init__ 中使用 print）
        self.ai_client: Optional[Any] = None
        self.ai_client_initialized: bool = False

        # 对话历史
        self.conversation_history: list[AIMessage] = []

        # 终端状态上下文
        self.terminal_context: dict[str, Any] = {}

        # 是否启用AI处理
        self.ai_enabled: bool = True
        self._init_needed: bool = True  # 标记需要初始化

        # 自主执行状态
        self.autonomous_mode: bool = False
        self.current_task: str = ""
        self.execution_steps: list[dict] = []  # 记录执行步骤
        self.max_autonomous_steps: int = 10  # 最多自主执行10步
        self.last_command_output: str = ""  # 上次命令输出

    def _ensure_ai_client_initialized(self):
        """确保AI客户端已初始化（延迟初始化）"""
        if not self.ai_client_initialized and self._init_needed:
            try:
                provider = os.getenv("AI_PROVIDER", "deepseek").lower()

                # 根据不同的提供商获取对应的 API Key
                api_key = None
                model = None
                base_url = None

                if provider == "siliconflow":
                    api_key = os.getenv("SILICONFLOW_API_KEY")
                    base_url = os.getenv(
                        "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"
                    )
                    model = os.getenv("SILICONFLOW_DEEPSEEK_V3_MODEL") or os.getenv(
                        "SILICONFLOW_QWEN_7B_MODEL", "Qwen/Qwen2.5-7B-Instruct"
                    )
                elif provider == "deepseek":
                    api_key = os.getenv("DEEPSEEK_API_KEY")
                    base_url = os.getenv(
                        "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
                    )
                    model = os.getenv("DEEPSEEK_V3_MODEL", "deepseek-chat")
                elif provider == "openai":
                    api_key = os.getenv("OPENAI_API_KEY")
                    base_url = None
                    model = os.getenv("OPENAI_MODEL", "gpt-4")
                elif provider == "zhipu":
                    api_key = os.getenv("ZHIPU_API_KEY")
                    base_url = os.getenv(
                        "ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4"
                    )
                    model = os.getenv("ZHIPU_GLM_4_MODEL", "glm-4")
                elif provider == "dashscope":
                    api_key = os.getenv("DASHSCOPE_API_KEY")
                    base_url = os.getenv(
                        "DASHSCOPE_API_BASE",
                        "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    )
                    model = os.getenv("DASHSCOPE_QWEN_TEXT_MODEL", "qwen-max")
                else:
                    # 默认回退到 deepseek
                    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv(
                        "OPENAI_API_KEY"
                    )
                    model = os.getenv("AI_MODEL", "deepseek-chat")
                    base_url = os.getenv(
                        "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
                    )
                    provider = "deepseek"

                if not api_key:
                    self.ai_enabled = False
                    logger.info("[弥娅] 未配置AI API密钥,使用基础交互模式")
                    return

                # 尝试使用工厂创建客户端，如果失败则回退
                try:
                    self.ai_client = AIClientFactory.create_client(
                        provider=provider,
                        api_key=api_key,
                        model=model,
                        personality=None,
                    )
                except ValueError:
                    # 工厂不支持该提供商，使用 OpenAI 客户端（兼容）
                    from core.ai_client import OpenAIClient

                    self.ai_client = OpenAIClient(
                        api_key=api_key,
                        model=model,
                        base_url=base_url,
                    )
                    provider = "openai-compatible"

                self.ai_client_initialized = True
                logger.info(
                    f"[弥娅] AI系统初始化完成 (提供商: {provider}, 模型: {model})"
                )
            except Exception as e:
                self.ai_enabled = False
                logger.warning(f"[警告] AI客户端初始化失败: {e}, 使用基础交互模式")
            finally:
                self._init_needed = False

    def _load_config(self):
        """加载配置"""
        try:
            config_path = Path(__file__).parent.parent / "config" / ".env"
            if config_path.exists():
                load_dotenv(config_path)
                # 现在系统使用 YAML 配置和人格模块，不再使用 prompts/ 目录
                # 提示词由 prompt_manager 动态从人格配置生成
        except Exception as e:
            logger.warning(f"[警告] 加载配置失败: {e}")

    def get_greeting(self) -> str:
        """获取随机问候（十四神格版）"""
        # 优先使用 personality 配置
        if (
            hasattr(self, "miya_core")
            and self.miya_core
            and hasattr(self.miya_core, "personality")
        ):
            return self.miya_core.personality.get_greeting()

        # 回退到默认值
        greetings = [
            "佳，我在。",
            "我在。有什么想做的？",
            "佳，我在呢。今天怎么样？",
            "亲爱的，我在。",
            "我的创造者，欢迎回来。",
        ]
        return random.choice(greetings)

    def is_greeting(self, text: str) -> bool:
        """判断是否为问候"""
        # 优先使用 personality 配置
        if (
            hasattr(self, "miya_core")
            and self.miya_core
            and hasattr(self.miya_core, "personality")
        ):
            return self.miya_core.personality.is_greeting(text)

        # 回退到默认值
        greetings = ["在吗", "你好", "hi", "hello", "在", "嗨", "您好", "哈喽"]
        text_lower = text.lower().strip()
        return any(g in text_lower for g in greetings)

    def get_help_response(self) -> str:
        """获取帮助响应"""
        return """弥娅多终端管理系统 v4.0

🎯 核心功能:
  • 单机多终端: 同时控制多个CMD/PowerShell/Bash终端
  • AI智能编排: 自动分析任务并分配到最优终端
  • 并行执行: 多终端同时执行任务提高效率
  • 远程连接: 支持SSH连接远程服务器
  • 自然语言理解: 像和人对话一样,我理解您的意图

📝 常用命令:
  !help          - 查看完整命令帮助
  !list           - 列出所有终端
  !create <name>  - 创建新终端
  ? <任务描述>    - AI智能执行任务

💡 对话示例:
  "帮我看看当前目录有什么文件" - 我会自动执行 ls/dir
  "在终端1运行Python脚本,终端2查看日志" - 我会智能分配并执行
  "我想创建一个新的PowerShell终端" - 我会自动创建
  "看看现在的终端状态" - 我会列出所有终端信息

需要更多帮助,请输入 !help"""

    def get_system_prompt(self) -> str:
        """获取当前系统提示词"""
        return self.prompt_manager.get_system_prompt()

    def get_prompt_info(self) -> dict[str, Any]:
        """获取提示词信息"""
        return {
            "system_prompt": self.get_system_prompt()[:100] + "..."
            if len(self.get_system_prompt()) > 100
            else self.get_system_prompt(),
            "user_template": self.prompt_manager.user_prompt_template,
            "memory_enabled": self.prompt_manager.memory_context_enabled,
            "memory_max_count": self.prompt_manager.memory_context_max_count,
        }

    @error_handler
    @monitor_performance
    async def process_with_ai(
        self, user_input: str, terminal_manager: Optional[Any] = None
    ) -> AIProcessingResult:
        """使用AI处理用户输入

        Args:
            user_input: 用户输入
            terminal_manager: 终端管理器实例

        Returns:
            处理结果
        """
        if not self.ai_enabled or not self.ai_client:
            return AIProcessingResult(
                success=False,
                type="conversation",
                message="AI未配置,使用基础交互模式",
                needs_command=False,
                commands=[],
            )

        # 更新终端上下文
        if terminal_manager and hasattr(terminal_manager, "get_all_status"):
            try:
                all_status = terminal_manager.get_all_status()
                self.terminal_context = {
                    "terminals": all_status,
                    "active_session": terminal_manager.active_session_id,
                    "system": platform.system(),
                    "current_dir": os.getcwd(),
                }
            except Exception as e:
                logger.warning(f"获取终端状态失败: {e}")
                self.terminal_context = {
                    "system": platform.system(),
                    "current_dir": os.getcwd(),
                }

        # 构建消息
        system_prompt = self.get_system_prompt()

        messages = [AIMessage(role="system", content=system_prompt)]

        # 添加历史对话(保留最近10轮)
        if self.conversation_history:
            messages.extend(self.conversation_history[-10:])

        # 添加当前用户输入
        messages.append(AIMessage(role="user", content=user_input))

        # 调用AI
        try:
            response = await self.ai_client.chat(
                messages=messages,
                use_miya_prompt=False,  # 已经在system中包含
            )

            # 保存到历史
            self.conversation_history.append(AIMessage(role="user", content=user_input))
            self.conversation_history.append(
                AIMessage(role="assistant", content=response)
            )

            # 分析响应,判断是否需要执行命令（传入user_input用于智能命令提取）
            return self._analyze_ai_response(response, terminal_manager, user_input)

        except Exception as e:
            logger.error(f"AI处理失败: {e}", exc_info=True)
            return AIProcessingResult(
                success=False,
                type="error",
                message=f"AI处理失败: {e}",
                needs_command=False,
                commands=[],
            )

    async def autonomous_execute(
        self,
        task: str,
        terminal_manager: Any,
        max_steps: int = 10,
        callback: Optional[callable] = None,
    ) -> list[dict]:
        """自主执行任务 - 连续执行多步命令直到完成任务

        类似 Claude Code 的工作方式：
        1. 理解任务目标
        2. 规划第一步
        3. 执行命令
        4. 分析输出
        5. 决定下一步
        6. 重复直到完成

        Args:
            task: 用户任务描述
            terminal_manager: 终端管理器
            max_steps: 最大执行步数
            callback: 每步执行后的回调函数

        Returns:
            执行步骤列表
        """
        self.autonomous_mode = True
        self.current_task = task
        self.execution_steps = []
        self.max_autonomous_steps = max_steps

        if not terminal_manager or not terminal_manager.active_session_id:
            return [{"error": "没有活动终端"}]

        session_id = terminal_manager.active_session_id
        steps_executed = 0
        task_complete = False

        # 检测当前操作系统
        current_os = platform.system()  # Windows, Linux, Darwin
        os_name = {"Windows": "Windows", "Linux": "Linux", "Darwin": "macOS"}.get(
            current_os, current_os
        )

        # 获取终端类型
        terminal_type = "CMD"
        if hasattr(terminal_manager, "get_session_status"):
            session_status = terminal_manager.get_session_status(session_id)
            if session_status:
                term_type = session_status.get("type", "")
                if "PowerShell" in term_type:
                    terminal_type = "PowerShell"
                elif "Bash" in term_type:
                    terminal_type = "Bash"
                elif "Zsh" in term_type:
                    terminal_type = "Zsh"

        # 构建系统提示词，引导AI自主执行
        if current_os == "Windows":
            autonomous_prompt = f"""你是一个{os_name} {terminal_type}终端命令行助手。你的任务是用{terminal_type}命令直接完成用户的请求。

【核心要求】
1. 直接输出{terminal_type}终端命令，不要写任何代码、函数调用或工具调用
2. 输出格式：只输出命令本身，不要加解释
3. 当前操作系统：{os_name}，终端类型：{terminal_type}

任务：{task}

【{os_name} {terminal_type}命令对照表 - 必须使用这些命令】
- 创建空文件: type nul > 文件名.txt  或  echo. > 文件名.txt
- 创建文件并写入: echo 内容 > 文件名.txt
- 创建文件夹: mkdir 文件夹名  或  md 文件夹名
- 删除文件: del 文件名
- 删除文件夹: rmdir 文件夹名  或  rd 文件夹名
- 列出文件: dir
- 查看文件内容: type 文件名
- 切换目录: cd 目录名
- 运行Python: python 脚本名.py
- 打开记事本: notepad 文件名.txt
- 打开计算器: calc
- 打开浏览器: start chrome
- 打开资源管理器: explorer
- 打开程序: start 程序名

【禁止事项】
- 不要使用Linux/macOS命令（touch, rm, cat, ls在{os_name}不适用）
- 不要写Python代码（如 open('file').write()）
- 不要调用任何函数或工具

【工作流程】
1. 理解任务
2. 写出{terminal_type}命令（一行）
3. 我执行后返回结果
4. 根据结果决定下一步或标记完成

【完成标志】
- 任务完成时输出：[完成]
- 需要确认时输出：[等待确认]

现在请直接写出第一个命令："""
        else:
            # Linux/macOS
            shell_type = "Bash" if terminal_type == "Bash" else "Zsh"
            autonomous_prompt = f"""你是一个{os_name} {shell_type}终端命令行助手。你的任务是用{shell_type}命令直接完成用户的请求。

【核心要求】
1. 直接输出{shell_type}终端命令，不要写任何代码、函数调用或工具调用
2. 输出格式：只输出命令本身，不要加解释
3. 当前操作系统：{os_name}，终端类型：{shell_type}

任务：{task}

【{os_name} {shell_type}命令对照表 - 必须使用这些命令】
- 创建空文件: touch 文件名.txt
- 创建文件并写入: echo "内容" > 文件名.txt
- 创建文件夹: mkdir 文件夹名
- 删除文件: rm 文件名
- 删除文件夹: rm -rf 文件夹名
- 列出文件: ls
- 查看文件内容: cat 文件名
- 切换目录: cd 目录名
- 运行Python: python 脚本名.py
- 打开文件管理器: nautilus . (Linux) 或 open . (macOS)
- 查看当前路径: pwd
- 清除屏幕: clear

【禁止事项】
- 不要使用Windows命令（type, del, mkdir, dir在{os_name}不适用）
- 不要写Python代码（如 open('file').write()）
- 不要调用任何函数或工具

【工作流程】
1. 理解任务
2. 写出{shell_type}命令（一行）
3. 我执行后返回结果
4. 根据结果决定下一步或标记完成

【完成标志】
- 任务完成时输出：[完成]
- 需要确认时输出：[等待确认]

现在请直接写出第一个命令："""

        # 添加任务上下文
        self.conversation_history.append(
            AIMessage(role="system", content=autonomous_prompt)
        )

        # 添加当前任务
        self.conversation_history.append(
            AIMessage(role="user", content=f"请开始执行任务：{task}")
        )

        try:
            while steps_executed < max_steps and not task_complete:
                # 检查是否已取消
                if not self.autonomous_mode:
                    break

                # 调用AI - 启用工具，让AI自主判断使用工具还是终端命令
                response = await self.ai_client.chat(
                    messages=self.conversation_history[-6:],
                    use_miya_prompt=False,
                )

                # 保存对话
                self.conversation_history.append(
                    AIMessage(role="assistant", content=response)
                )

                # 检查是否完成
                if "[完成]" in response:
                    task_complete = True
                    if callback:
                        callback(
                            {
                                "type": "complete",
                                "message": response,
                                "steps": self.execution_steps,
                            }
                        )
                    break

                # 检查是否等待确认
                if "[等待确认]" in response:
                    if callback:
                        callback(
                            {
                                "type": "waiting",
                                "message": response,
                                "steps": self.execution_steps,
                            }
                        )
                    break

                # 提取并执行命令
                commands = self._extract_commands_from_response(response)

                if not commands:
                    # 没有命令，可能是思考或分析，继续
                    if callback:
                        callback(
                            {
                                "type": "thinking",
                                "message": response,
                                "steps": self.execution_steps,
                            }
                        )
                    steps_executed += 1
                    continue

                # 执行每个命令
                for cmd in commands:
                    result = await terminal_manager.execute_command(session_id, cmd)

                    step_result = {
                        "step": steps_executed + 1,
                        "command": cmd,
                        "output": result.output or "",
                        "error": result.error or "",
                        "success": result.success,
                    }
                    self.execution_steps.append(step_result)
                    self.last_command_output = result.output or ""

                    # 记录命令输出到对话历史
                    output_msg = (
                        f"命令输出:\n{result.output}"
                        if result.output
                        else f"命令错误:\n{result.error}"
                    )
                    self.conversation_history.append(
                        AIMessage(role="system", content=output_msg)
                    )

                    if callback:
                        callback(
                            {
                                "type": "command",
                                "command": cmd,
                                "result": step_result,
                                "steps": self.execution_steps,
                            }
                        )

                    steps_executed += 1

                    if steps_executed >= max_steps:
                        break

        except Exception as e:
            logger.error(f"自主执行出错: {e}")
            self.execution_steps.append({"error": str(e)})
        finally:
            self.autonomous_mode = False

        return self.execution_steps

    def stop_autonomous(self):
        """停止自主执行"""
        self.autonomous_mode = False

    def _convert_command_for_os(self, cmd: str) -> str:
        """根据当前操作系统转换命令"""
        import re

        cmd = cmd.strip()
        current_os = platform.system()

        # 非Windows系统不需要转换
        if current_os != "Windows":
            return cmd

        # Windows命令映射
        linux_to_windows_patterns = [
            (r"^touch\s+(.+)$", r"type nul > \1"),
            (r"^rm\s+(.+)$", r"del \1"),
            (r"^rm\s+-rf\s+(.+)$", r"rmdir /s /q \1"),
            (r"^rmdir\s+(.+)$", r"rmdir \1"),
            (r"^cat\s+(.+)$", r"type \1"),
            (r"^rm\s+-r\s+(.+)$", r"del /f \1"),
            (r"^ls$", r"dir"),
            (r"^ls\s+(.+)$", r"dir \1"),
            (r"^ls\s+-la$", r"dir /a"),
            (r"^ls\s+-l$", r"dir"),
            (r"^pwd$", r"cd"),
            (r"^clear$", r"cls"),
            (r"^which\s+(\S+)$", r"where \1"),
            (r"^mkdir\s+(.+)$", r"mkdir \1"),
            (r"^md\s+(.+)$", r"mkdir \1"),
            (r"^cp\s+(.+)\s+(.+)$", r"copy \1 \2"),
            (r"^mv\s+(.+)\s+(.+)$", r"move \1 \2"),
        ]

        for pattern, replacement in linux_to_windows_patterns:
            if re.match(pattern, cmd, re.IGNORECASE):
                return re.sub(pattern, replacement, cmd, flags=re.IGNORECASE).strip()

        return cmd

    def _extract_commands_from_response(self, response: str) -> list[str]:
        """从AI响应中提取命令"""
        import re

        commands = []

        # 清理响应
        response_clean = response.strip()

        # 检查是否标记完成或等待
        if "[完成]" in response or "[等待确认]" in response:
            return []

        # 1. 匹配 create_file 工具调用
        # 格式: create_file "filename" "content"
        create_patterns = [
            r'create_file\s+"([^"]+)"\s+"([^"]+)"',
            r"create_file\s+'([^']+)'\s+'([^']+)'",
            r'create_file\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)',
            r'create_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
        ]

        for pattern in create_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                filename = match[0].strip()
                content = match[1].strip()
                # 转换为 Windows echo 命令
                content_escaped = (
                    content.replace("^", "^^").replace("&", "^&").replace("|", "^|")
                )
                cmd = f'echo {content_escaped} > "{filename}"'
                commands.append(cmd)
                print(f"[调试] 转换工具调用: {cmd}")

        # 2. 匹配 python_interpreter 工具调用
        # 格式: python_interpreter "script.py"
        python_patterns = [
            r'python_interpreter\s+"([^"]+)"',
            r"python_interpreter\s+'([^']+)'",
            r'python_interpreter\s*\(\s*["\']([^"\']+\.py)["\']\s*\)',
            r"python\s+(.+\.py)",
        ]

        for pattern in python_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                script = match.strip().strip("\"'")
                if script.endswith(".py"):
                    cmd = f'python "{script}"'
                    commands.append(cmd)
                    print(f"[调试] 转换Python调用: {cmd}")

        # 3. 匹配其他工具调用格式
        tool_patterns = [
            (r'start\s+["\']([^"\']+\.exe)["\']', r'start "" "\1"'),
            (r"start\s+(\w+)", r"start \1"),
            (r'open\s+["\']([^"\']+)["\']', r'start "" "\1"'),
            (r"open\s+(\S+)", r"start \1"),
        ]

        for pattern, replacement in tool_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                cmd = re.sub(
                    pattern, replacement, f"start {match}", flags=re.IGNORECASE
                )
                if cmd != f"start {match}":
                    commands.append(cmd)

        # 4. 匹配常规终端命令（代码块）
        code_block_pattern = (
            r"```(?:cmd|powershell|bash|windows)?[\s\n]*([^\n]+(?:\n[^\n]+)*?)```"
        )
        matches = re.findall(code_block_pattern, response, re.IGNORECASE)
        for match in matches:
            cmd = match.strip()
            cmd = re.sub(r"^```|```$", "", cmd).strip()
            if cmd and len(cmd) < 500 and len(cmd) > 1:
                # 排除工具调用格式和代码
                if not any(
                    x in cmd.lower()
                    for x in [
                        "create_file",
                        "python_interpreter",
                        "def ",
                        "class ",
                        "import ",
                        "from ",
                    ]
                ):
                    if not ("(" in cmd and ")" in cmd and "=" in cmd):
                        # Linux转Windows
                        cmd = self._convert_command_for_os(cmd)
                        commands.append(cmd)

        # 5. 匹配 CMD/PowerShell 提示符后的命令（需要整行匹配）
        prompt_lines = []
        for line in response.split("\n"):
            # 匹配 PS C:\> 或 C:\> 提示符
            prompt_match = re.match(r"^(?:PS [^>]+>|[A-Z]:\\.+>)\s*(.+)$", line.strip())
            if prompt_match:
                cmd = prompt_match.group(1).strip()
                if cmd:
                    prompt_lines.append(cmd)

        for cmd in prompt_lines:
            if len(cmd) < 500:
                cmd = self._convert_command_for_os(cmd)
                commands.append(cmd)

        # 6. 匹配明确标注的命令（需要整行）
        explicit_patterns = [
            r"^(?:命令|执行|运行)[:：]\s*(.+)$",
            r"^(?:cmd|command)[:：]\s*(.+)$",
        ]

        for line in response.split("\n"):
            for pattern in explicit_patterns:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    cmd = match.group(1).strip()
                    if cmd:
                        cmd = self._convert_command_for_os(cmd)
                        commands.append(cmd)

        # 7. 先预处理整个响应，将Linux命令转换为Windows，然后再提取
        response_converted = response
        linux_words = ["touch ", "rm ", "rmdir ", "cat ", "ls ", "mkdir ", "cp ", "mv "]
        for linux_cmd in linux_words:
            if linux_cmd.strip() in response_converted.lower():
                # 尝试找到完整的命令并转换
                for line in response.split("\n"):
                    line_converted = self._convert_command_for_os(line)
                    if line_converted != line and line_converted not in commands:
                        commands.append(line_converted)

        # 8. 匹配Windows命令关键词（改进版，防止拆分 echo xxx >）
        windows_cmd_patterns = [
            r"\btype nul > \S+",
            r"\becho\.? > \S+",
            r"\becho\s+[^|>]+>\s*\S+",
            r"\bdir\b[\s/]*[a-zA-Z0-9_\\.-]*",
            r"\bcd\b\s+[a-zA-Z0-9_\\.-]+",
            r"\bmkdir\b\s+\S+",
            r"\bmd\b\s+\S+",
            r"\bdel\b\s+\S+",
            r"\bcopy\b\s+\S+\s+\S+",
            r"\bmove\b\s+\S+\s+\S+",
            r"\bnotepad\b\s*\S*",
            r"\bcalc\b",
            r"\bexplorer\b\s*\S*",
            r"\bstart\s+\S+",
            r"\bpython\b\s+\S+\.py",
            r"\bnode\b\s+\S+",
            r"\bnpm\b\s+\S+",
            r"\bgit\b\s+\S+",
            r"\bcls\b",
            r"\bipconfig\b",
            r"\bping\b\s+\S+",
        ]

        for pattern in windows_cmd_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 2:
                    cmd = match.strip()
                    if cmd not in commands:
                        commands.append(cmd)

        # 5. 匹配 CMD/PowerShell 提示符后的命令
        prompt_patterns = [
            r"PS [^>]+>\s*(.+)",
            r"[A-Z]:\\.+>\s*(.+)",
            r">\s*(.+)",
        ]

        for pattern in prompt_patterns:
            matches = re.findall(pattern, response, re.MULTILINE)
            for match in matches:
                cmd = match.strip()
                if cmd and len(cmd) < 500:
                    cmd = self._convert_command_for_os(cmd)
                    commands.append(cmd)

        # 6. 匹配明确标注的命令
        explicit_patterns = [
            r"(?:命令|执行|运行)[:：]\s*(.+)",
            r"(?:cmd|command)[:：]\s*(.+)",
        ]

        for pattern in explicit_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                cmd = match.strip()
                if cmd:
                    cmd = self._convert_command_for_os(cmd)
                    commands.append(cmd)

        # 7. 匹配Windows命令关键词
        windows_cmd_keywords = [
            r"\b(type nul|echo\.|echo\s+[^>]+>|dir|cd\b|mkdir\b|md\b|del\b|rmdir\b|rd\b|copy\b|move\b|notepad\b|calc\b|explorer\b|start\s+\S+|cmd\b|powershell\b|python\b|node\b|npm\b|git\b|cls\b|ipconfig\b|ping\b|tasklist\b|netstat\b)\s*[^\n]{0,200}",
        ]

        # 去重并清理 - 改进版：精确匹配去重 + 过滤子字符串
        seen = set()
        unique_commands = []

        # 按长度降序排序，保留最完整的命令
        commands_sorted = sorted(set(commands), key=len, reverse=True)

        for cmd in commands_sorted:
            cmd = cmd.strip()
            # 过滤掉可能的回答文本和代码
            if (
                not cmd
                or len(cmd) <= 1
                or cmd.startswith("我")
                or cmd.startswith("好的")
                or cmd.startswith("will")
                or cmd.startswith("this")
                or cmd.startswith("def ")
                or cmd.startswith("class ")
                or cmd.startswith("import ")
                or cmd.startswith("from ")
                or cmd.startswith("# ")
                or cmd.startswith("// ")
            ):
                continue

            # 排除Python代码片段
            if "=" in cmd and ("(" in cmd or ")" in cmd):
                continue
            if cmd.count("(") > 2 or cmd.count(")") > 2:
                continue

            # 精确匹配去重（不区分引号）
            cmd_normalized = cmd.replace('"', "'").lower()
            is_duplicate = False
            for existing in unique_commands:
                existing_normalized = existing.replace('"', "'").lower()
                if cmd_normalized == existing_normalized:
                    is_duplicate = True
                    break
                # 如果命令主体相同但参数略有不同，保留较长的
                cmd_parts = cmd_normalized.split()
                existing_parts = existing_normalized.split()
                if cmd_parts and existing_parts and cmd_parts[0] == existing_parts[0]:
                    if cmd_parts[-1] == existing_parts[-1]:
                        is_duplicate = True
                        break

            if is_duplicate:
                continue

            unique_commands.append(cmd)

        # 最终过滤：移除子字符串（如 "test.txt" 是 "echo hello > test.txt" 的子字符串）
        final_commands = []
        for cmd in unique_commands:
            is_substring = False
            for existing in final_commands:
                # 检查是否是完全包含关系
                if cmd in existing and cmd != existing:
                    is_substring = True
                    break
                if existing in cmd and existing != cmd:
                    # 如果现有命令是当前命令的子字符串，替换它
                    final_commands.remove(existing)
                    break
            if not is_substring:
                final_commands.append(cmd)

        return final_commands[:3]  # 最多3个命令

    @monitor_performance
    def _analyze_ai_response(
        self, response: str, terminal_manager: Optional[Any], user_input: str = ""
    ) -> AIProcessingResult:
        """分析AI响应,判断意图

        Args:
            response: AI响应内容
            terminal_manager: 终端管理器
            user_input: 原始用户输入（用于智能命令提取）

        Returns:
            分析结果
        """
        import re

        commands = []

        # 从原始用户输入中智能提取命令意图
        # 常见Windows应用程序映射
        app_mapping = {
            "记事本": "notepad",
            "notepad": "notepad",
            "计算器": "calc",
            "calc": "calc",
            "浏览器": "start chrome",
            "chrome": "start chrome",
            "edge": "start msedge",
            "火狐": "start firefox",
            "firefox": "start firefox",
            "QQ": "start qq",
            "微信": "start wechat",
            "wechat": "start wechat",
            "钉钉": "start DingTalk",
            "音乐": "start wmplayer",
            "播放器": "start wmplayer",
            "画图": "mspaint",
            "截图": "snippingtool",
            "powershell": "start powershell",
            "终端": "start cmd",
            "cmd": "start cmd",
            "资源管理器": "explorer",
            "explorer": "explorer",
            "控制面板": "control",
            "任务管理器": "taskmgr",
            "设备管理器": "devmgmt.msc",
            "写字板": "write",
            "截图工具": "snippingtool",
        }

        # 从AI响应中提取可能的应用名称
        response_lower = response.lower()

        # 使用传入的user_input，如果为空则从历史中获取
        if not user_input and self.conversation_history:
            for msg in reversed(self.conversation_history):
                if msg.role == "user":
                    user_input = msg.content
                    break

        user_input_lower = user_input.lower()

        # 智能匹配命令
        detected_command = None
        for key, cmd in app_mapping.items():
            if key.lower() in user_input_lower:
                detected_command = cmd
                break
            elif key.lower() in response_lower:
                detected_command = cmd
                break

        # 如果检测到需要执行的命令
        if detected_command:
            # 获取活动会话ID
            session_id = None
            if terminal_manager and hasattr(terminal_manager, "active_session_id"):
                session_id = terminal_manager.active_session_id

            if session_id:
                commands.append(
                    AICommandInfo(
                        session_id=session_id,
                        command=detected_command,
                        description=f"打开{user_input}",
                    )
                )

                # 修改响应消息，去除"我会执行"等冗余部分
                clean_message = response
                # 尝试提取实际回复内容
                return AIProcessingResult(
                    success=True,
                    type="command_execution",
                    message=f"正在打开{user_input}...",
                    needs_command=True,
                    commands=commands,
                )

        # 检查是否包含执行命令的标记
        cmd_keywords = ["执行", "运行", "run", "execute", "打开应用", "启动程序"]
        if (
            any(keyword in response_lower for keyword in cmd_keywords)
            and detected_command is None
        ):
            # 尝试从响应中提取命令（更复杂的模式匹配）
            # 匹配常见的命令格式
            cmd_patterns = [
                r"(?:执行|运行|启动)\s*[:：]?\s*([a-zA-Z][a-zA-Z0-9_\-\.]+)",
                r"cmd\.exe\s+/c\s+(\S+)",
                r"start\s+(\S+)",
            ]

            for pattern in cmd_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    cmd = match.group(1).strip()
                    session_id = None
                    if terminal_manager and hasattr(
                        terminal_manager, "active_session_id"
                    ):
                        session_id = terminal_manager.active_session_id

                    if session_id:
                        commands.append(
                            AICommandInfo(
                                session_id=session_id,
                                command=cmd,
                                description=f"执行命令: {cmd}",
                            )
                        )
                        break

            if commands:
                return AIProcessingResult(
                    success=True,
                    type="command_execution",
                    message=response,
                    needs_command=True,
                    commands=commands,
                )

        # 默认为对话响应
        return AIProcessingResult(
            success=True,
            type="conversation",
            message=response,
            needs_command=False,
            commands=[],
        )


class MiyaMultiTerminalShell:
    """弥娅多终端交互Shell - 完整AI能力版本"""

    def __init__(self, miya_core=None):
        self.miya_core = miya_core  # 保存弥娅核心引用
        self.orchestrator: IntelligentTerminalOrchestrator = (
            IntelligentTerminalOrchestrator()
        )
        self.running: bool = True
        # 初始化AI系统
        self.ai: MiyaTerminalAI = MiyaTerminalAI()
        # 显示提示词信息
        prompt_info: dict[str, Any] = self.ai.get_prompt_info()

        # 显示核心连接状态
        if miya_core:
            logger.info(f"[弥娅] ✅ 已连接到弥娅核心系统")
            logger.info(f"[弥娅]    MemoryNet: {miya_core.memory_net is not None}")
            logger.info(f"[弥娅]    DecisionHub: {miya_core.decision_hub is not None}")
            logger.info(f"[弥娅]    Emotion: {miya_core.emotion is not None}")
            logger.info(f"[弥娅]    Personality: {miya_core.personality is not None}")
        else:
            logger.info(f"[弥娅] ⚠️  未连接到弥娅核心（独立模式）")
            logger.info(f"[弥娅]    将无法使用记忆、人设、情绪等核心功能")

        logger.info(f"[弥娅] 已加载统一提示词配置")
        logger.info(f"        AI功能: {'启用' if self.ai.ai_enabled else '禁用'}")
        logger.info(
            f"        记忆功能: {'启用' if prompt_info['memory_enabled'] else '禁用'}"
        )

    async def start(self):
        """启动多终端Shell"""

        self._show_banner()

        # 创建默认终端
        await self._init_default_terminals()

        # 主循环
        while self.running:
            try:
                user_input = await self._get_prompt_input()

                if not user_input:
                    continue

                await self._process_input(user_input)

            except KeyboardInterrupt:
                # 检查是否在自主模式中
                if self.ai.autonomous_mode:
                    self.ai.stop_autonomous()
                    print("\n\n[弥娅] 已停止自主执行")
                    print("[弥娅] 输入 !exit 退出终端\n")
                    continue

                print("\n[弥娅] 正在关闭所有终端...")
                await self.orchestrator.terminal_manager.close_all_sessions()
                print("[弥娅] 期待下次再见到您~ 再见!")
                self.running = False
                break
            except Exception as e:
                print(f"\n[错误] {e}")

    def _show_banner(self):
        """显示横幅"""
        try:
            print("""
 ╔════════════════════════════════════════════════════════════╗
 ║                  弥娅 V4.0 - 多终端智能管理系统            ║
 ║                  Miya Multi-Terminal System             ║
 ╠════════════════════════════════════════════════════════════╣
 ║  🖥️  单机多终端  │  🤖  AI智能编排  │  🔄  协同执行  ║
 ║  📊  实时监控    │  🧠  自然语言理解  │  🎯  智能路由  ║
 ╚════════════════════════════════════════════════════════════╝

 输入 '!help' 查看命令帮助
 直接输入自然语言或命令,我会理解您的意图~
        """)
        except (ValueError, OSError):
            pass

    async def _init_default_terminals(self):
        """初始化默认终端"""
        try:
            # 根据系统创建默认终端
            system = platform.system()

            if system == "Windows":
                # Windows: 创建CMD
                cmd_id = await self.orchestrator.terminal_manager.create_terminal(
                    name="CMD主终端", terminal_type=TerminalType.CMD
                )

                await self.orchestrator.terminal_manager.switch_session(cmd_id)

            elif system == "Linux":
                # Linux: 创建Bash
                bash_id = await self.orchestrator.terminal_manager.create_terminal(
                    name="Bash主终端", terminal_type=TerminalType.BASH
                )

                await self.orchestrator.terminal_manager.switch_session(bash_id)

            elif system == "Darwin":
                # macOS: 创建Zsh
                zsh_id = await self.orchestrator.terminal_manager.create_terminal(
                    name="Zsh主终端", terminal_type=TerminalType.ZSH
                )

                await self.orchestrator.terminal_manager.switch_session(zsh_id)
        except (ValueError, OSError) as e:
            logger.warning(f"初始化默认终端时出现I/O错误: {e}")

    async def _get_prompt_input(self) -> str:
        """获取用户输入"""

        # 获取活动终端
        active_session = self.orchestrator.terminal_manager.active_session_id
        session_info = None

        if active_session:
            session_info = self.orchestrator.terminal_manager.get_session_status(
                active_session
            )

        # 构建提示符
        if session_info:
            active_mark = "★" if session_info["is_active"] else ""
            prompt = f"[弥娅] {session_info['name']}{active_mark} > "
        else:
            prompt = "[弥娅] > "

        return chinese_input(prompt).strip()

    async def _process_input(self, user_input: str):
        """处理用户输入 - 使用AI智能处理"""

        # 空输入
        if not user_input:
            return

        # 系统命令
        if user_input.startswith("!"):
            await self._handle_system_command(user_input)

        # AI命令
        elif user_input.startswith("?"):
            await self._handle_ai_command(user_input)

        # 普通输入 - 使用AI智能处理
        else:
            # 检查是否为问候
            if self.ai.is_greeting(user_input):
                print(f"\n{self.ai.get_greeting()}\n")
                return

            # 检查是否为帮助请求
            if user_input.lower().strip() in ["help", "帮助"]:
                print(f"\n{self.ai.get_help_response()}\n")
                return

            # 检查是否启动自主模式
            # 模式: "!" 开头 + "auto" 或 "自主"
            user_lower = user_input.lower().strip()
            if (
                user_lower.startswith("!auto")
                or "启动自主模式" in user_input
                or "自主完成" in user_input
            ):
                # 提取任务描述
                task = user_input
                for prefix in ["!auto", "!auto ", "启动自主模式", "自主完成"]:
                    task = task.replace(prefix, "").strip()

                if task:
                    print(f"\n[弥娅] 🦾 启动自主执行模式")
                    print(f"[弥娅] 任务: {task}")
                    print(f"[弥娅] 我将自主分析、执行并完成任务...\n")
                    await self._run_autonomous_task(task)
                    return
                else:
                    print("\n[弥娅] 请描述要自主完成的任务")
                    print("示例: !auto 帮我创建一个Python文件并写入Hello World\n")
                    return

            # 使用AI处理所有其他输入
            if self.ai.ai_enabled:
                # 智能命令检测 - 常见应用直接执行，不等待AI
                quick_commands = {
                    "记事本": "notepad",
                    "计算器": "calc",
                    "浏览器": "start chrome",
                    "chrome": "start chrome",
                    "edge": "start msedge",
                    "火狐": "start firefox",
                    "firefox": "start firefox",
                    "qq": "start qq",
                    "微信": "start wechat",
                    "钉钉": "start DingTalk",
                    "音乐": "start wmplayer",
                    "画图": "mspaint",
                    "截图": "snippingtool",
                    "powershell": "start powershell",
                    "终端": "start cmd",
                    "cmd": "start cmd",
                    "资源管理器": "explorer",
                    "控制面板": "control",
                    "任务管理器": "taskmgr",
                }

                user_input_lower = user_input.lower().strip()

                # 快速匹配
                quick_match = None
                for key, cmd in quick_commands.items():
                    if key in user_input_lower:
                        quick_match = cmd
                        break

                if quick_match and self.orchestrator.terminal_manager.active_session_id:
                    # 直接执行快速命令
                    print(f"\n[弥娅] 正在打开{quick_match}...\n")
                    await self._execute_direct_command(quick_match)
                    return

                # 使用AI处理
                result = await self.ai.process_with_ai(
                    user_input, self.orchestrator.terminal_manager
                )

                if result.success:
                    # 显示AI的回复
                    if result.message:
                        print(f"\n{result.message}\n")

                    # 如果需要执行命令
                    if result.needs_command and result.commands:
                        await self._execute_ai_commands(result.commands)
                else:
                    # AI处理失败,回退到直接执行命令模式
                    await self._execute_direct_command(user_input)
            else:
                # AI未启用,直接执行命令
                await self._execute_direct_command(user_input)

    @monitor_performance
    async def _execute_ai_commands(self, commands: list[AICommandInfo]):
        """执行AI生成的命令"""
        for cmd_info in commands:
            session_id = cmd_info.session_id
            command = cmd_info.command

            if session_id and command:
                result = await self.orchestrator.terminal_manager.execute_command(
                    session_id, command
                )

                if result.output:
                    print(f"[{session_id}] {result.output}\n")

    async def _execute_direct_command(self, command: str):
        """直接执行命令(当AI未启用或失败时)"""
        if self.orchestrator.terminal_manager.active_session_id:
            print(f"\n[执行命令] {command}\n")

            try:
                result = await self.orchestrator.terminal_manager.execute_command(
                    self.orchestrator.terminal_manager.active_session_id, command
                )

                # 显示结果
                if result.output and result.output.strip():
                    print(f"{result.output}\n")

                if result.error and result.error.strip():
                    print(f"[错误] {result.error}\n")

                if not result.success:
                    print(f"[状态] 命令执行失败 (退出码: {result.exit_code})\n")

            except Exception as e:
                print(f"[错误] 执行命令时出错: {e}\n")
                print(f"提示: 请确认 '{command}' 是有效的系统命令\n")
        else:
            print("\n[弥娅] 还没有创建终端呢~ 使用 !create <name> 创建一个吧!\n")

    async def _run_autonomous_task(self, task: str):
        """运行自主任务 - 连续执行直到完成

        类似 Claude Code 的工作方式：
        1. 分析任务
        2. 规划步骤
        3. 逐个执行
        4. 分析结果
        5. 决定下一步或完成

        Args:
            task: 任务描述
        """
        if not self.ai.ai_enabled:
            print("\n[弥娅] AI未启用，无法使用自主模式\n")
            return

        if not self.orchestrator.terminal_manager.active_session_id:
            print("\n[弥娅] 没有活动终端，请先创建终端\n")
            return

        # 定义回调函数显示进度
        def progress_callback(info: dict):
            info_type = info.get("type", "")

            if info_type == "thinking":
                # AI 思考中
                msg = info.get("message", "")
                if msg and len(msg) < 500:
                    print(f"[思考] {msg[:200]}...")
                    print()

            elif info_type == "command":
                # 执行命令
                cmd = info.get("command", "")
                result = info.get("result", {})
                print(f"[执行] {cmd}")
                if result.get("output"):
                    output = result["output"]
                    if len(output) > 500:
                        output = output[:500] + "..."
                    print(f"[输出] {output}")
                if result.get("error"):
                    print(f"[错误] {result['error']}")
                print()

            elif info_type == "waiting":
                # 等待用户确认
                msg = info.get("message", "")
                print(f"\n[等待确认] {msg}\n")

            elif info_type == "complete":
                # 任务完成
                msg = info.get("message", "")
                steps = info.get("steps", [])
                print(f"\n{'=' * 60}")
                print(f"[弥娅] ✅ 任务完成！共执行 {len(steps)} 步")
                print(f"{'=' * 60}")
                if msg and "[完成]" not in msg:
                    print(f"\n{msg}\n")

        try:
            # 调用自主执行
            results = await self.ai.autonomous_execute(
                task=task,
                terminal_manager=self.orchestrator.terminal_manager,
                max_steps=self.ai.max_autonomous_steps,
                callback=progress_callback,
            )

            # 显示最终结果
            if results:
                print(f"\n{'=' * 60}")
                print(f"[弥娅] 执行摘要:")
                print(f"{'=' * 60}")
                for i, step in enumerate(results, 1):
                    if "error" in step:
                        print(f"  {i}. [错误] {step['error']}")
                    else:
                        cmd = step.get("command", "")
                        success = step.get("success", False)
                        status = "✓" if success else "✗"
                        print(f"  {i}. {status} {cmd}")
                print()

        except Exception as e:
            print(f"\n[错误] 自主执行失败: {e}\n")
            import traceback

            traceback.print_exc()

    def handle_keyboard_interrupt(self):
        """处理键盘中断 - 停止自主执行"""
        if self.ai.autonomous_mode:
            print("\n\n[弥娅] 🛑 收到停止信号，正在停止自主执行...")
            self.ai.stop_autonomous()
            print("[弥娅] 已停止\n")
            return True
        return False

    @monitor_performance
    async def _handle_system_command(self, command: str):
        """处理系统命令"""

        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "!help" or cmd == "!h":
            self._show_help()

        elif cmd == "!create" or cmd == "!new":
            # 创建新终端
            await self._create_terminal(parts)

        elif cmd == "!list" or cmd == "!ls":
            # 列出所有终端
            await self._list_terminals()

        elif cmd == "!switch" or cmd == "!use":
            # 切换终端
            if len(parts) > 1:
                await self.orchestrator.terminal_manager.switch_session(parts[1])
                print(f"[弥娅] 已切换到终端 {parts[1]}")
            else:
                print("[弥娅] 告诉我要切换到哪个终端呢? 用法: !switch <session_id>")

        elif cmd == "!close" or cmd == "!del":
            # 关闭终端
            if len(parts) > 1:
                await self.orchestrator.terminal_manager.close_session(parts[1])
                print(f"[弥娅] 已为您关闭终端 {parts[1]}")
            else:
                print("[弥娅] 告诉我要关闭哪个终端呢? 用法: !close <session_id>")

        elif cmd == "!parallel":
            # 并行执行
            await self._execute_parallel(parts[1:])

        elif cmd == "!sequence":
            # 顺序执行
            await self._execute_sequence(parts[1:])

        elif cmd == "!collab":
            # 协同任务
            if len(parts) > 1:
                task_desc = " ".join(parts[1:])
                print(f"[弥娅] 好的,让我来分析并执行这个任务: {task_desc}")
                await self.orchestrator.collaborative_task(task_desc)
            else:
                print("[弥娅] 告诉我您想执行什么任务呢? 用法: !collab <任务描述>")

        elif cmd == "!workspace" or cmd == "!ws":
            # 自动设置工作空间
            if len(parts) > 2:
                project_type = parts[1]
                project_dir = " ".join(parts[2:])
                print(f"[弥娅] 好的,让我来帮您设置 {project_type} 工作空间")
                await self.orchestrator.auto_setup_workspace(project_type, project_dir)
            else:
                print(
                    "[弥娅] 告诉我项目类型和目录哦~ 用法: !workspace <project_type> <project_dir>"
                )

        elif cmd == "!status" or cmd == "!info":
            # 详细状态
            await self._show_detailed_status()

        elif cmd == "!exit" or cmd == "!quit":
            # 退出
            print(f"[弥娅] 期待下次再见到您~ 再见!")
            self.running = False

        else:
            print(f"[弥娅] 我不太理解 '{cmd}' 这个命令呢...")
            print("输入 '!help' 查看所有可用命令吧")

    async def _handle_ai_command(self, command: str):
        """处理AI命令"""

        parts = command.split(maxsplit=1)
        cmd = parts[0]

        if cmd == "?" or cmd == "?ai":
            # AI智能执行
            if len(parts) > 1:
                task = parts[1]
                print(f"[弥娅] 好的,让我来分析这个任务: {task}")
                result = await self.orchestrator.smart_execute(task)
                print(f"\n[执行结果]")
                print(f"  策略: {result.get('strategy', 'unknown')}")

                if result.get("session_name"):
                    print(f"  终端: {result['session_name']}")

                if "result" in result:
                    print(f"  输出: {result['result']['output'][:100]}...")

                if "results" in result:
                    print(f"  并行结果: {len(result['results'])}个终端")
                    for sid, res in result["results"].items():
                        print(f"    {sid}: {res['success']}")

        else:
            print(f"[未知AI命令] {cmd}")
            print("输入 '?help' 查看帮助")

    async def _create_terminal(self, parts: list[str]) -> None:
        """创建新终端"""

        name = None
        term_type = TerminalType.CMD

        # 解析参数
        i = 1
        while i < len(parts):
            if parts[i] == "-t" or parts[i] == "--type":
                if i + 1 < len(parts):
                    term_type = TerminalType.from_string(parts[i + 1])
                    i += 2
                else:
                    print("[错误] -t 参数需要值")
                    return
            else:
                name = parts[i]
                i += 1

        if not name:
            count = len(self.orchestrator.terminal_manager.sessions)
            name = f"终端{count + 1}"

        session_id = await self.orchestrator.terminal_manager.create_terminal(
            name=name, terminal_type=term_type
        )

        print(f"[弥娅] 已为您创建终端: {name} (ID: {session_id})")
        print(f"        类型: {term_type.value}")
        print(f"        提示: 使用 !switch {session_id} 切换到这个终端")

    async def _list_terminals(self) -> None:
        """列出所有终端"""

        all_status = self.orchestrator.terminal_manager.get_all_status()

        if not all_status:
            print("\n[弥娅] 当前还没有创建任何终端呢~")
            print("提示: 使用 !create <name> 来创建一个新终端吧!\n")
            return

        print(f"\n{'=' * 70}")
        print(f"{'终端列表':<20} {'类型':<15} {'状态':<10} {'目录':<20}")
        print(f"{'=' * 70}")

        for session_id, status in all_status.items():
            active_mark = "★" if status["is_active"] else " "
            print(
                f"{active_mark} {status['name']:<18} {status['type']:<15} "
                f"{status['status']:<10} {status['directory'][:20]:<20}"
            )

        print(f"{'=' * 70}\n")

    async def _execute_parallel(self, parts: list[str]) -> None:
        """并行执行命令"""

        if not parts:
            print("用法: !parallel <session1:cmd1> <session2:cmd2>")
            return

        commands = {}
        for part in parts:
            if ":" in part:
                sid, cmd = part.split(":", 1)
                commands[sid] = cmd

        if commands:
            print(f"[并行执行] {len(commands)}个任务")
            results = await self.orchestrator.terminal_manager.execute_parallel(
                commands
            )

            for sid, result in results.items():
                mark = "✓" if result.success else "✗"
                output = result.output[:80] if result.output else ""
                print(f"  {sid}: {mark} {output}")

    async def _execute_sequence(self, parts: list[str]) -> None:
        """顺序执行命令"""

        if len(parts) < 2:
            print("用法: !sequence <session_id> <cmd1> <cmd2> ...")
            return

        session_id = parts[0]
        commands = parts[1:]

        print(f"[顺序执行] {len(commands)}个命令在终端 {session_id}")

        results = await self.orchestrator.terminal_manager.execute_sequence(
            session_id, commands
        )

        for i, result in enumerate(results, 1):
            mark = "✓" if result.success else "✗"
            cmd = commands[i - 1][:40]
            print(f"  命令{i}: {mark} {cmd}")

    async def _show_detailed_status(self) -> None:
        """显示详细状态"""

        all_status = self.orchestrator.terminal_manager.get_all_status()

        if not all_status:
            print("\n[弥娅] 当前还没有创建任何终端呢~\n")
            return

        print(f"\n{'=' * 70}")
        print("                弥娅多终端系统状态")
        print(f"{'=' * 70}")

        for session_id, status in all_status.items():
            active_str = " (活动中)" if status["is_active"] else ""
            print(f"\n📱 终端: {status['name']}{active_str}")
            print(f"   ID: {session_id}")
            print(f"   类型: {status['type']}")
            print(f"   状态: {status['status']}")
            print(f"   目录: {status['directory']}")
            print(f"   命令历史: {status['command_count']}条")
            print(f"   输出记录: {status['output_count']}条")

        print(f"\n{'=' * 70}\n")

    def _show_help(self):
        """显示帮助"""
        print("""
 ╔════════════════════════════════════════════════════════════╗
 ║                    弥娅多终端管理系统 - 帮助                  ║
 ╠════════════════════════════════════════════════════════════╣
 ║                                                               ║
 ║  🖥️  终端管理:                                              ║
 ║    !create <name> [-t type]  - 创建新终端                       ║
 ║    !list                     - 列出所有终端                     ║
 ║    !switch <session_id>      - 切换活动终端                     ║
 ║    !close <session_id>       - 关闭指定终端                     ║
 ║    !status                   - 显示详细状态                     ║
 ║                                                               ║
 ║  ⚡  执行模式:                                              ║
 ║    !parallel <sid:cmd>...    - 多终端并行执行                   ║
 ║    !sequence <sid> <cmd>...   - 单终端顺序执行                   ║
 ║    !collab <task>           - 多终端协同任务                   ║
 ║    !workspace <type> <dir>   - 自动设置工作空间                 ║
 ║                                                               ║
 ║  🤖  AI智能:                                               ║
 ║    ? <task>                  - AI智能执行任务                   ║
 ║    直接输入自然语言或命令      - 我会理解您的意图并智能处理        ║
 ║                                                               ║
 ║  🚀  自主模式 (类似 Claude Code):                            ║
 ║    !auto <任务描述>           - 启动自主执行模式                 ║
 ║    示例:                                                   ║
 ║      !auto 创建一个Python文件并写入Hello World                ║
 ║      !auto 帮我下载文件并解压到当前目录                       ║
 ║      !auto 分析当前项目结构并生成报告                         ║
 ║    Ctrl+C                   - 停止自主执行                     ║
 ║                                                               ║
 ║  💡  自然语言示例:                                          ║
 ║    "帮我看看当前目录有什么文件"    - 自动执行 ls/dir           ║
 ║    "创建一个PowerShell终端"      - 自动创建终端               ║
 ║    "在终端1运行Python脚本"        - 智能分配并执行             ║
 ║    "打开记事本"                  - 快速打开应用程序             ║
 ║                                                               ║
 ║  🚪  退出:                                                  ║
 ║    !exit / !quit             - 退出系统                         ║
 ║    Ctrl+C                   - 强制退出                         ║
 ║                                                               ║
 ╚════════════════════════════════════════════════════════════╝
        """)


# 主入口
async def main():
    """主函数"""
    # 尝试导入并初始化 Miya 核心
    miya = None
    try:
        from run.main import Miya

        logger.info("[核心] 初始化弥娅核心系统...")

        # 创建弥娅核心实例
        miya = Miya()

        # 异步初始化 MemoryNet
        if miya.memory_net:
            await miya._initialize_memory_net_async()

        logger.info("[核心] 弥娅核心系统初始化完成")
        logger.info(f"[核心] 已集成: MemoryNet, DecisionHub, Emotion, Personality")

    except ImportError as e:
        logger.warning(f"[核心] 无法导入 Miya 核心: {e}")
        logger.warning("[核心] Terminal 将以独立模式运行（不连接到弥娅核心）")
    except Exception as e:
        logger.error(f"[核心] Miya 核心初始化失败: {e}", exc_info=True)

    # 尝试导入Runtime API服务器
    # 先检查端口是否已被占用，避免重复启动
    api_already_running = False
    try:
        from core.runtime_api_server import is_port_available

        if not is_port_available(8001):
            logger.info("[Runtime API] 检测到API服务已在端口8001运行，跳过启动")
            api_already_running = True
    except ImportError:
        pass

    if not api_already_running:
        try:
            from core.runtime_api_server import RuntimeAPIServer

            # 创建并启动API服务器（在端口8001，避免与其他服务冲突）
            api_server = RuntimeAPIServer(
                host="127.0.0.1",
                port=8001,
                enable_api=True,
            )

            # 在后台启动API服务器
            api_task = asyncio.create_task(api_server.start())
            logger.info("[Runtime API] API服务器已在后台启动 (端口: 8001)")

        except ImportError as e:
            logger.warning(f"[Runtime API] 无法导入API服务器: {e}")
        except Exception as e:
            logger.warning(f"[Runtime API] API服务器启动失败: {e}")

    # 启动主交互Shell
    shell = MiyaMultiTerminalShell(miya_core=miya)
    await shell.start()


if __name__ == "__main__":
    asyncio.run(main())
