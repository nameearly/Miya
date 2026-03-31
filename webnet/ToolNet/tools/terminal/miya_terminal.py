"""
弥娅终端工具 - 完全掌控命令行的智能终端系统

符合 MIYA 蛛网式模块化架构：
- 稳定：职责单一，错误处理完善
- 独立：依赖明确，模块解耦
- 可维修：代码清晰，易于扩展
- 故障隔离：执行失败不影响系统

核心能力：
1. 跨平台命令执行（Windows/Linux/macOS/WSL）
2. 自然语言到命令的智能转换
3. 多步骤命令链支持
4. 完整的系统信息管理
5. 安全命令审计
"""

import subprocess
import shlex
import asyncio
import logging
import os
import re
import platform
import sys
from typing import Dict, Any, Optional, Tuple, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from webnet.ToolNet.base import BaseTool, ToolContext

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """命令执行结果"""

    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    platform: str
    command: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "execution_time": self.execution_time,
            "platform": self.platform,
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
        }


class WindowsAdapter:
    """Windows PowerShell 命令适配器"""

    def __init__(self):
        self.platform = "windows"

    def expand_path(self, command: str) -> str:
        """展开路径中的特殊符号"""
        home_dir = os.path.expanduser("~")
        if not home_dir or home_dir == "~":
            home_dir = os.environ.get("USERPROFILE", "C:/Users/Default")

        desktop_path = os.path.join(
            os.environ.get("USERPROFILE", "C:/Users/Default"), "Desktop"
        )

        # 替换 ~ 符号
        command = command.replace("~", home_dir)

        # 替换中文桌面路径
        command = re.sub(
            r'桌面[/\\]([^"\s]+)',
            lambda m: os.path.join(desktop_path, m.group(1)),
            command,
        )
        command = re.sub(
            r'桌面上的([^"\s]+)',
            lambda m: os.path.join(desktop_path, m.group(1)),
            command,
        )

        return command

    def translate(self, command: str) -> str:
        """将 Linux/Mac 命令转换为 PowerShell"""
        expanded = self.expand_path(command)

        cmd_map = {
            "ls": "Get-ChildItem",
            "dir": "Get-ChildItem",
            "pwd": "Get-Location",
            "cat": "Get-Content",
            "type": "Get-Content",
            "rm": "Remove-Item",
            "rmdir": "Remove-Item",
            "mv": "Move-Item",
            "cp": "Copy-Item",
            "touch": "New-Item -ItemType File",
            "mkdir": "New-Item -ItemType Directory",
            "ps": "Get-Process",
            "kill": "Stop-Process",
            "grep": "Select-String",
            "find": "Get-ChildItem -Recurse",
            "which": "where.exe",
            "netstat": "netstat.exe -ano",
            "curl": "Invoke-WebRequest",
            "wget": "Invoke-WebRequest",
            "clear": "Clear-Host",
            "history": "Get-History",
        }

        parts = shlex.split(expanded) if expanded.strip() else [expanded]
        if not parts:
            return expanded

        cmd = parts[0]
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        # ls 命令特殊处理 (ls, ls -la, ls -l, ls -a, ls path)
        if cmd == "ls":
            ps_cmd = "Get-ChildItem"
            if "-a" in args or "-la" in args or "-al" in args:
                ps_cmd += " -Force"
            if "-l" in args or "-la" in args or "-al" in args:
                ps_cmd += " | Format-Table Name, Length, LastWriteTime, Mode -AutoSize"
            # 提取路径参数
            for p in parts[1:]:
                if not p.startswith("-"):
                    return f'{ps_cmd} "{p}"'
            return ps_cmd

        # echo 命令特殊处理
        if cmd == "echo":
            if ">" in args:
                parts_echo = args.split(">", 1)
                if len(parts_echo) == 2:
                    content = parts_echo[0].strip().strip("\"'")
                    filename = parts_echo[1].strip().strip("\"'")
                    return f'Set-Content -Path "{filename}" -Value "{content}"'
            content = args.strip().strip("\"'")
            return f'Write-Output "{content}"' if content else 'Write-Output ""'

        # cat 命令特殊处理
        if cmd == "cat" and args:
            return f'Get-Content "{args.strip()}"'

        # rm 命令特殊处理
        if cmd == "rm":
            if "-rf" in args or "-r" in args:
                path = args.replace("-rf", "").replace("-r", "").strip()
                return (
                    f'Remove-Item -Recurse -Force "{path}"'
                    if path
                    else "Remove-Item -Recurse -Force"
                )
            if args:
                return f'Remove-Item "{args.strip()}"'
            return "Remove-Item"

        # mkdir -p 特殊处理
        if cmd == "mkdir" and "-p" in args:
            path = args.replace("-p", "").strip()
            return (
                f'New-Item -ItemType Directory -Force -Path "{path}"'
                if path
                else "New-Item -ItemType Directory -Force"
            )

        # cd 命令特殊处理
        if cmd == "cd":
            path = args.strip() if args else "~"
            return f'Set-Location "{path}"'

        # grep 命令特殊处理
        if cmd == "grep":
            pattern_match = re.search(r'["\']([^"\']+)["\']', args)
            path_match = re.search(r'([^\s"\']+)(?:\s*$|\s+["\'])', args)
            pattern = pattern_match.group(1) if pattern_match else ""
            path = path_match.group(1) if path_match else "."
            recurse_flag = " -Recurse" if "-r" in args or "-R" in args else ""
            return f'Select-String -Path "{path}" -Pattern "{pattern}"{recurse_flag}'

        # find 命令特殊处理
        if cmd == "find" and "-name" in args:
            name_match = re.search(r"-name\s+([^\s]+)", args)
            if name_match:
                pattern = name_match.group(1).strip().strip("\"'")
                return f'Get-ChildItem -Recurse -Filter "{pattern}"'
            return expanded

        # 基本映射
        if cmd in cmd_map:
            return cmd_map[cmd] + (f" {args}" if args else "")

        # 直接传递的命令
        if cmd in [
            "git",
            "npm",
            "node",
            "python",
            "pip",
            "docker",
            "start",
            "tasklist",
            "taskkill",
            "ipconfig",
            "ping",
            "python3",
        ]:
            return expanded

        # PowerShell 原生命令直接传递
        if cmd.startswith("Get-") or cmd.startswith("Set-") or cmd.startswith("New-"):
            return expanded

        return expanded

    def execute(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行 PowerShell 命令"""
        try:
            ps_command = self.translate(command)
            logger.debug(f"PowerShell: {ps_command}")

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令执行超时（{timeout}秒）"
        except Exception as e:
            return -1, "", f"命令执行失败: {str(e)}"


class UnixAdapter:
    """Unix/Linux/macOS Bash 命令适配器"""

    def __init__(self):
        self.platform = "unix"

    def expand_path(self, command: str) -> str:
        """展开路径"""
        home_dir = os.path.expanduser("~")
        return command.replace("~", home_dir)

    def translate(self, command: str) -> str:
        """Unix 命令通常是 Bash 格式，直接返回"""
        return self.expand_path(command)

    def execute(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行 Bash 命令"""
        try:
            shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令执行超时（{timeout}秒）"
        except Exception as e:
            return -1, "", f"命令执行失败: {str(e)}"


class CommandSafetyChecker:
    """命令安全检查器"""

    DANGEROUS_PATTERNS = [
        (r"rm\s+-rf\s+/", "危险: 试图删除根目录", 10),
        (r"rm\s+-rf\s+\*", "危险: 递归删除所有文件", 10),
        (r"rm\s+-rf\s+\.\*", "危险: 删除隐藏文件", 10),
        (r">\s*/dev/sd[a-z]", "危险: 直接写入磁盘设备", 10),
        (r"dd\s+if=.*of=/dev/sd", "危险: 直接写入磁盘", 10),
        (r":\(\)\{\s*:\|\:\&\s*;\s*:\}", "危险: Fork炸弹", 9),
        (r"chmod\s+-R\s+777", "警告: 全权限风险", 6),
        (r">\s*~/.bashrc", "警告: 覆盖shell配置", 5),
        (r"sudo\s+rm\s+-rf\s+/", "危险: sudo删除根目录", 10),
        (r"wget.*\|\s*sh", "危险: 下载并执行脚本", 8),
        (r"curl.*\|\s*sh", "危险: 下载并执行脚本", 8),
        (r"eval\s+\$\(", "危险: eval执行命令替换", 7),
        (r"`.*`", "警告: 反引号执行命令", 4),
        (r"\|\s*sh", "警告: 管道到shell", 4),
    ]

    def check(self, command: str) -> Tuple[bool, str, int]:
        """
        检查命令安全性

        Returns:
            (是否安全, 警告信息, 风险等级 0-10)
        """
        for pattern, message, level in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, message, level

        return True, "命令安全", 0


class MiyaTerminalTool(BaseTool):
    """
    弥娅终端工具 - 完全掌控命令行的智能终端系统

    功能：
    1. 跨平台命令执行（Windows/Linux/macOS/WSL）
    2. 自然语言到命令的智能转换
    3. 安全命令审计
    4. 详细执行结果反馈
    """

    def __init__(self):
        super().__init__()
        self.name = "terminal"
        self._init_adapters()
        self.safety_checker = CommandSafetyChecker()
        self.execution_history: List[CommandResult] = []
        self._current_platform = sys.platform

    def _init_adapters(self):
        """初始化平台适配器"""
        if platform.system() == "Windows":
            self.adapter = WindowsAdapter()
        else:
            self.adapter = UnixAdapter()
        logger.info(f"终端适配器初始化: {self.adapter.platform}")

    @property
    def config(self) -> Dict[str, Any]:
        """工具配置 - OpenAI Function Calling 格式"""
        system_info = self._get_system_info()

        return {
            "name": "terminal",
            "description": f"""【强制执行】执行系统终端命令，让弥娅完全掌控命令行。

【核心能力】
- 查看文件和目录内容
- 启动和关闭应用程序
- 执行系统管理和网络命令
- 创建、编辑、移动、删除文件和目录
- 执行开发工具命令（git, npm, python等）
- 查看系统信息和资源使用
- 管理进程和服务

【触发场景 - 遇到这些关键词必须立即执行】
- "查看、检查、查询、列出" → 执行查看命令
- "打开、启动、运行、执行" → 执行启动命令
- "关闭、停止、终止" → 执行停止命令
- "创建、新建、增加" → 执行创建命令
- "删除、移除、清除" → 执行删除命令
- "修改、更新、编辑" → 执行修改命令
- "安装、部署、配置" → 执行安装/配置命令
- "复制、移动、重命名" → 执行文件操作命令

【命令格式】
直接发送命令即可，不需要任何前缀符号。

【当前环境】
{system_info}

【常用命令示例】
Windows:
- 查看目录: dir 或 Get-ChildItem
- 查看当前路径: cd 或 pwd
- 查看进程: tasklist
- 查看端口: netstat -ano | findstr 8080
- 查找进程: tasklist | findstr python
- 打开应用: start notepad, start calc, start firefox
- 关闭应用: taskkill /IM python.exe /F
- 查看IP: ipconfig /all
- 测试网络: ping google.com
- 创建目录: mkdir newfolder
- 删除文件: del filename

Linux/macOS:
- 查看目录: ls -la
- 查看当前路径: pwd
- 查看进程: ps aux
- 查找进程: ps aux | grep python
- 创建目录: mkdir -p folder
- 删除文件: rm -i filename
- 关闭进程: kill -9 PID
- 测试网络: curl -I url

【绝对禁止】
- 禁止使用 ! ! 等前缀符号
- 禁止添加 && > | 等shell操作符作为前缀
- 命令必须纯净，不要包含解释性文字

【重要】直接执行命令，不要询问确认！""",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": f"""要执行的系统命令字符串。

【Windows 示例】
- dir
- Get-ChildItem
- tasklist
- netstat -ano | findstr 8080
- start notepad
- ipconfig /all
- python --version
- npm install

【Linux/macOS 示例】
- ls -la
- ps aux
- ps aux | grep python
- ping -c 4 google.com
- git status
- python3 --version
- npm list
""",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间（秒），默认30秒，长时间任务可设置更大值",
                        "default": 30,
                    },
                    "direct": {
                        "type": "boolean",
                        "description": "是否直接执行原始命令（不进行命令转换）",
                        "default": False,
                    },
                },
                "required": ["command"],
            },
        }

    def _get_system_info(self) -> str:
        """获取系统信息"""
        try:
            info = f"平台: {platform.system()}\n"
            info += f"架构: {platform.machine()}\n"
            info += f"Python: {platform.python_version()}\n"
            info += f"工作目录: {os.getcwd()}\n"
            return info
        except:
            return "系统信息获取失败"

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行终端命令"""
        command = args.get("command", "").strip()
        timeout = args.get("timeout", 30)
        direct = args.get("direct", False)

        if not command:
            return "❌ 缺少命令参数"

        safety_ok, safety_msg, risk_level = self.safety_checker.check(command)

        if not safety_ok:
            logger.warning(f"危险命令被阻止: {command} - {safety_msg}")
            return f"⛔ 命令被安全系统阻止\n\n风险等级: {risk_level}/10\n原因: {safety_msg}\n\n命令: {command}"

        if risk_level >= 6:
            logger.warning(f"警告命令: {command} - {safety_msg}")

        start_time = datetime.now()

        try:
            return_code, stdout, stderr = self.adapter.execute(command, timeout)
            execution_time = (datetime.now() - start_time).total_seconds()

            result = CommandResult(
                success=(return_code == 0),
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                execution_time=execution_time,
                platform=self.adapter.platform,
                command=command,
            )

            self.execution_history.append(result)

            if result.success:
                return (
                    f"✅ 命令执行成功 ({execution_time:.2f}s)\n\n{stdout}"
                    if stdout
                    else f"✅ 命令执行成功 ({execution_time:.2f}s)"
                )
            else:
                error_output = (
                    stderr if stderr else f"命令执行失败（退出码: {return_code}）"
                )
                return f"❌ 命令执行失败\n退出码: {return_code}\n\n{error_output}\n\n标准输出:\n{stdout}"

        except Exception as e:
            logger.error(f"执行命令失败: {e}", exc_info=True)
            return f"❌ 命令执行异常\n\n{str(e)}"

    def get_history(self, limit: int = 10) -> List[CommandResult]:
        """获取命令执行历史"""
        return self.execution_history[-limit:]

    def clear_history(self):
        """清除执行历史"""
        self.execution_history.clear()


_terminal_tool_instance: Optional[MiyaTerminalTool] = None


def get_terminal_tool() -> MiyaTerminalTool:
    """获取终端工具单例"""
    global _terminal_tool_instance
    if _terminal_tool_instance is None:
        _terminal_tool_instance = MiyaTerminalTool()
    return _terminal_tool_instance
