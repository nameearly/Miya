#!/usr/bin/env python3
"""
弥娅超级终端控制系统 - 完全终端掌控
让弥娅拥有类似 opencode 的完整终端能力

功能:
- terminal_exec: 执行任意shell命令
- file_read: 读取文件
- file_edit: 编辑文件
- file_write: 写入文件
- file_delete: 删除文件
- directory_tree: 目录树
- code_execute: 代码执行
- project_analyze: 项目分析
"""

import os
import sys
import subprocess
import shlex
import asyncio
import json
import re
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import platform

logger = logging.getLogger("Miya.TerminalUltra")


class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    warnings: List[str] = field(default_factory=list)


class TerminalUltra:
    """弥娅超级终端控制系统"""

    def __init__(self, workspace_root: str = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.current_dir = self.workspace_root
        self.safe_mode = True
        self.command_history: List[Dict] = []

        # 危险命令模式
        self._dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"rm\s+-rf\s+\.",
            r"format\s+",
            r"dd\s+if=",
            r"mkfs\.",
            r":\(\)\{",  # Fork bomb
            r">\s*/dev/sd",
            r"chmod\s+-R\s+777\s+/",
            r"chown\s+-R",
        ]

    # ==================== 终端执行 ====================

    async def terminal_exec(
        self,
        command: str,
        timeout: int = 60,
        cwd: str = None,
        env: Dict[str, str] = None,
        shell: bool = True,
    ) -> ExecutionResult:
        """
        执行终端命令

        Args:
            command: 要执行的命令
            timeout: 超时时间(秒)
            cwd: 工作目录
            env: 环境变量
            shell: 是否使用shell

        Returns:
            ExecutionResult: 执行结果
        """
        import time

        start_time = time.time()

        # 安全检查
        risk = self._check_command_risk(command)
        if risk == RiskLevel.BLOCKED:
            return ExecutionResult(
                success=False,
                output="",
                error="命令被安全系统拦截",
                exit_code=-1,
                execution_time=0,
                warnings=["危险命令已被阻止"],
            )

        warnings = []
        if risk == RiskLevel.DANGEROUS:
            warnings.append(f"警告: 命令 '{command[:30]}...' 具有危险性")

        # 确定工作目录
        work_dir = Path(cwd) if cwd else self.current_dir
        if not work_dir.exists():
            work_dir = self.workspace_root

        # 合并环境变量
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
            process = subprocess.Popen(
                command if shell else shlex.split(command),
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(work_dir),
                env=exec_env,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return ExecutionResult(
                    success=False,
                    output=stdout,
                    error="命令执行超时",
                    exit_code=-1,
                    execution_time=time.time() - start_time,
                    warnings=warnings + ["执行超时"],
                )

            execution_time = time.time() - start_time

            # 记录命令历史
            self.command_history.append(
                {
                    "command": command,
                    "exit_code": process.returncode,
                    "execution_time": execution_time,
                    "cwd": str(work_dir),
                }
            )

            # 保持工作目录同步
            if "cd " in command.lower():
                self._update_current_dir(command, stdout)

            return ExecutionResult(
                success=process.returncode == 0,
                output=stdout,
                error=stderr,
                exit_code=process.returncode,
                execution_time=execution_time,
                warnings=warnings,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time,
                warnings=warnings,
            )

    def _check_command_risk(self, command: str) -> RiskLevel:
        """检查命令危险等级"""
        cmd_lower = command.lower().strip()

        # 直接阻止的危险命令
        blocked = [
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
            ":(){ :|:& };:",
            "fork()",
            "> /dev/sd",
            "chmod -R 777 /",
        ]

        for pattern in blocked:
            if pattern in cmd_lower:
                return RiskLevel.BLOCKED

        # 危险命令需要确认
        dangerous = ["rm -rf", "rm -r", "del /", "format", "chmod 777"]
        for pattern in dangerous:
            if pattern in cmd_lower:
                return RiskLevel.DANGEROUS

        # 需要注意的命令
        caution = ["rm ", "del ", "mv ", "cp -r"]
        for pattern in caution:
            if cmd_lower.startswith(pattern):
                return RiskLevel.CAUTION

        return RiskLevel.SAFE

    def _update_current_dir(self, command: str, output: str):
        """更新当前目录"""
        cmd_lower = command.lower()

        # 提取 cd 目标目录
        if cmd_lower.startswith("cd "):
            parts = command.split(None, 1)
            if len(parts) > 1:
                new_dir = parts[1].strip("'\"")
                # 处理 ~ 和相对路径
                if new_dir.startswith("~"):
                    new_dir = str(Path.home() / new_dir[1:])
                elif not Path(new_dir).is_absolute():
                    new_dir = str(self.current_dir / new_dir)

                if Path(new_dir).exists():
                    self.current_dir = Path(new_dir)

    # ==================== 文件读取 ====================

    async def file_read(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = None,
        encoding: str = "utf-8",
    ) -> ExecutionResult:
        """
        读取文件内容

        Args:
            file_path: 文件路径
            offset: 起始行号
            limit: 读取行数
            encoding: 文件编码

        Returns:
            ExecutionResult: 包含文件内容
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"文件不存在: {file_path}"
                )

            if path.is_dir():
                return ExecutionResult(
                    success=False, output="", error=f"是目录不是文件: {file_path}"
                )

            # 检查文件大小
            size = path.stat().st_size
            if size > 10 * 1024 * 1024:  # 10MB
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"文件太大: {size / 1024 / 1024:.1f}MB",
                )

            with open(path, "r", encoding=encoding, errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # 应用 offset 和 limit
            if offset > 0:
                lines = lines[offset:]
            if limit:
                lines = lines[:limit]

            content = "".join(lines)

            # 添加位置信息
            header = f"=== {path} ===\n"
            header += f"Lines: {offset + 1}-{offset + len(lines)} / {total_lines}\n"
            header += f"Size: {size} bytes\n"
            header += "=" * 40 + "\n"

            return ExecutionResult(success=True, output=header + content)

        except UnicodeDecodeError:
            return ExecutionResult(
                success=False, output="", error="文件编码不支持，请尝试 binary 模式"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, output="", error=f"读取文件失败: {str(e)}"
            )

    # ==================== 文件写入 ====================

    async def file_write(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> ExecutionResult:
        """
        写入文件

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码
            create_dirs: 是否创建目录
        """
        try:
            path = self._resolve_path(file_path)

            # 创建父目录
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                f.write(content)

            size = path.stat().st_size
            lines = len(content.split("\n"))

            return ExecutionResult(
                success=True,
                output=f"文件已写入: {path}\n大小: {size} bytes\n行数: {lines}",
            )

        except Exception as e:
            return ExecutionResult(
                success=False, output="", error=f"写入文件失败: {str(e)}"
            )

    # ==================== 文件编辑 ====================

    async def file_edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> ExecutionResult:
        """
        编辑文件

        Args:
            file_path: 文件路径
            old_string: 要替换的内容
            new_string: 替换后的内容
            replace_all: 是否替换所有
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"文件不存在: {file_path}"
                )

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查旧字符串是否存在
            if old_string not in content:
                return ExecutionResult(
                    success=False, output="", error=f"未找到要替换的内容"
                )

            # 执行替换
            if replace_all:
                new_content = content.replace(old_string, new_string)
                count = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                count = 1

            # 写入文件
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ExecutionResult(
                success=True, output=f"已替换 {count} 处\n文件: {path}"
            )

        except Exception as e:
            return ExecutionResult(
                success=False, output="", error=f"编辑文件失败: {str(e)}"
            )

    # ==================== 文件删除 ====================

    async def file_delete(
        self, file_path: str, recursive: bool = False
    ) -> ExecutionResult:
        """
        删除文件或目录

        Args:
            file_path: 路径
            recursive: 是否递归删除目录
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"路径不存在: {file_path}"
                )

            # 安全检查
            if path.is_dir() and not recursive:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"是目录，请使用 recursive=True 删除目录",
                )

            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

            return ExecutionResult(success=True, output=f"已删除: {path}")

        except Exception as e:
            return ExecutionResult(
                success=False, output="", error=f"删除失败: {str(e)}"
            )

    # ==================== 目录树 ====================

    async def directory_tree(
        self, dir_path: str = ".", max_depth: int = 3, include_hidden: bool = False
    ) -> ExecutionResult:
        """
        显示目录树

        Args:
            dir_path: 目录路径
            max_depth: 最大深度
            include_hidden: 是否包含隐藏文件
        """
        try:
            path = self._resolve_path(dir_path)

            if not path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"目录不存在: {dir_path}"
                )

            if not path.is_dir():
                return ExecutionResult(
                    success=False, output="", error=f"不是目录: {dir_path}"
                )

            lines = []
            self._build_tree(path, "", lines, max_depth, 0, include_hidden)

            tree = "\n".join(lines)
            return ExecutionResult(success=True, output=f"=== {path} ===\n{tree}")

        except Exception as e:
            return ExecutionResult(
                success=False, output="", error=f"获取目录树失败: {str(e)}"
            )

    def _build_tree(
        self,
        path: Path,
        prefix: str,
        lines: List[str],
        max_depth: int,
        current_depth: int,
        include_hidden: bool,
    ):
        if current_depth >= max_depth:
            return

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            for i, item in enumerate(items):
                # 跳过隐藏文件
                if not include_hidden and item.name.startswith("."):
                    continue

                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "

                if item.is_dir():
                    lines.append(f"{prefix}{current_prefix}{item.name}/")
                    if current_depth < max_depth - 1:
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        self._build_tree(
                            item,
                            new_prefix,
                            lines,
                            max_depth,
                            current_depth + 1,
                            include_hidden,
                        )
                else:
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    lines.append(f"{prefix}{current_prefix}{item.name} ({size_str})")

        except PermissionError:
            lines.append(f"{prefix}[权限拒绝]")

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    # ==================== 代码执行 ====================

    async def code_execute(
        self, code: str, language: str = "python", timeout: int = 30
    ) -> ExecutionResult:
        """
        执行代码

        Args:
            code: 代码内容
            language: 语言 (python/javascript)
            timeout: 超时时间
        """
        if language.lower() == "python":
            return await self._execute_python(code, timeout)
        elif language.lower() in ["javascript", "js", "node"]:
            return await self._execute_javascript(code, timeout)
        else:
            return ExecutionResult(
                success=False, output="", error=f"不支持的语言: {language}"
            )

    async def _execute_python(self, code: str, timeout: int) -> ExecutionResult:
        """执行 Python 代码"""
        import time

        start_time = time.time()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = await self.terminal_exec(f'python "{temp_file}"', timeout=timeout)

            # 添加执行信息
            exec_time = time.time() - start_time
            info = f"\n[执行时间: {exec_time:.3f}s]"

            if result.success:
                result.output += info
            else:
                result.error += info

            return result

        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    async def _execute_javascript(self, code: str, timeout: int) -> ExecutionResult:
        """执行 JavaScript 代码"""
        import time

        start_time = time.time()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # 尝试使用 node
            result = await self.terminal_exec(f'node "{temp_file}"', timeout=timeout)

            exec_time = time.time() - start_time
            info = f"\n[执行时间: {exec_time:.3f}s]"

            if result.success:
                result.output += info
            else:
                result.error += info

            return result

        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    # ==================== 项目分析 ====================

    async def project_analyze(self, path: str = None) -> ExecutionResult:
        """
        分析项目结构

        Args:
            path: 项目路径
        """
        try:
            project_path = self._resolve_path(path) if path else self.workspace_root

            if not project_path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"路径不存在: {path}"
                )

            analysis = {
                "project_root": str(project_path),
                "files": {},
                "languages": {},
                "total_files": 0,
                "total_size": 0,
            }

            # 文件扩展名映射
            ext_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".jsx": "React",
                ".tsx": "React",
                ".java": "Java",
                ".go": "Go",
                ".rs": "Rust",
                ".cpp": "C++",
                ".c": "C",
                ".cs": "C#",
                ".rb": "Ruby",
                ".php": "PHP",
                ".swift": "Swift",
                ".kt": "Kotlin",
                ".html": "HTML",
                ".css": "CSS",
                ".scss": "SCSS",
                ".json": "JSON",
                ".yaml": "YAML",
                ".yml": "YAML",
                ".md": "Markdown",
                ".txt": "Text",
                ".sql": "SQL",
                ".sh": "Shell",
                ".bat": "Batch",
                ".ps1": "PowerShell",
            }

            ignored_dirs = {
                ".git",
                "__pycache__",
                "node_modules",
                ".venv",
                "venv",
                "dist",
                "build",
                ".idea",
                ".vscode",
                "data",
                "logs",
                ".pytest_cache",
            }

            # 使用 os.walk 代替 rglob，避免符号链接问题
            for root, dirs, files in os.walk(str(project_path)):
                # 跳过忽略的目录
                dirs[:] = [d for d in dirs if d not in ignored_dirs]

                for filename in files:
                    try:
                        filepath = Path(root) / filename
                        ext = filepath.suffix.lower()
                        lang = ext_map.get(ext, "Other")

                        size = filepath.stat().st_size
                        analysis["total_files"] += 1
                        analysis["total_size"] += size

                        if lang not in analysis["languages"]:
                            analysis["languages"][lang] = {"files": 0, "size": 0}
                        analysis["languages"][lang]["files"] += 1
                        analysis["languages"][lang]["size"] += size
                    except (OSError, PermissionError):
                        continue

            # 格式化输出
            lines = []
            lines.append(f"=== 项目分析: {project_path.name} ===")
            lines.append(f"总文件数: {analysis['total_files']}")
            lines.append(f"总大小: {self._format_size(analysis['total_size'])}")
            lines.append("")
            lines.append("语言分布:")

            for lang, info in sorted(
                analysis["languages"].items(), key=lambda x: x[1]["size"], reverse=True
            ):
                lines.append(
                    f"  {lang}: {info['files']} 文件, {self._format_size(info['size'])}"
                )

            # 列出根目录文件
            lines.append("")
            lines.append("根目录结构:")
            for item in sorted(project_path.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    lines.append(f"  📁 {item.name}/")
                else:
                    lines.append(f"  📄 {item.name}")

            return ExecutionResult(success=True, output="\n".join(lines))

        except Exception as e:
            return ExecutionResult(
                success=False, output="", error=f"项目分析失败: {str(e)}"
            )

    # ==================== 工具函数 ====================

    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        if not path:
            return self.current_dir

        path = path.strip()

        # 绝对路径
        if Path(path).is_absolute():
            return Path(path)

        # ~ 展开
        if path.startswith("~"):
            return Path.home() / path[1:]

        # 相对路径
        return self.current_dir / path

    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        result = await self.terminal_exec("uname -a" if os.name != "nt" else "ver")

        return {
            "platform": platform.system(),
            "platform_detail": platform.platform(),
            "python_version": sys.version,
            "current_dir": str(self.current_dir),
            "workspace_root": str(self.workspace_root),
            "hostname": platform.node(),
        }

    def get_command_history(self) -> List[Dict]:
        """获取命令历史"""
        return self.command_history


# 全局实例
_terminal_ultra_instance = None


def get_terminal_ultra(workspace_root: str = None) -> TerminalUltra:
    """获取全局 TerminalUltra 实例"""
    global _terminal_ultra_instance
    if _terminal_ultra_instance is None:
        _terminal_ultra_instance = TerminalUltra(workspace_root)
    return _terminal_ultra_instance
