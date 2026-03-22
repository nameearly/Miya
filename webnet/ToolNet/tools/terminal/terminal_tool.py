"""
终端工具 - 弥娅核心模块
支持终端命令执行、系统操作等
"""
import subprocess
import shlex
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from webnet.ToolNet.base import BaseTool, ToolContext

logger = logging.getLogger(__name__)


class TerminalTool(BaseTool):
    """终端命令工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "terminal",
            "description": "执行终端命令。当用户请求执行系统命令时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间（秒）",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行命令（异步）"""
        command = args.get("command", "")
        timeout = args.get("timeout", 30)

        if not command:
            return "❌ 缺少命令"

        try:
            # 异步执行命令
            result = await self._execute_command(command, timeout)
            return result
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return f"❌ 执行命令失败: {str(e)}"

    async def _execute_command(self, command: str, timeout: int = 30) -> str:
        """异步执行命令并返回结果"""
        try:
            # 在线程池中执行同步命令（因为subprocess不支持async）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._sync_execute_command(command, timeout)
            )
            return result

        except asyncio.TimeoutError:
            return "❌ 命令执行超时"
        except Exception as e:
            return f"❌ 执行命令时出错: {str(e)}"

    def _sync_execute_command(self, command: str, timeout: int = 30) -> str:
        """同步执行命令（在线程池中运行）"""
        try:
            # Windows 和 Unix 系统的处理
            import platform
            is_windows = platform.system() == 'Windows'

            # 执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            stdout, stderr = process.communicate(timeout=timeout)

            if process.returncode != 0:
                return f"❌ 命令执行失败（退出码: {process.returncode}）\n错误输出: {stderr}"
            else:
                return stdout or "命令执行成功（无输出）"

        except subprocess.TimeoutExpired:
            process.kill()
            return "❌ 命令执行超时"
        except Exception as e:
            return f"❌ 执行命令时出错: {str(e)}"

    def format_result(self, result: Any) -> str:
        """格式化命令执行结果"""
        if isinstance(result, str):
            return result
        elif isinstance(result, tuple):
            # 处理 (returncode, stdout, stderr) 格式
            code, stdout, stderr = result
            if code == 0:
                return stdout or "命令执行成功"
            else:
                return f"❌ 命令执行失败（退出码: {code}）\n{stderr}"
        else:
            return str(result)
