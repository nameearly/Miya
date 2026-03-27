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

    # ==================== Git 工具 ====================

    async def git_status(self, short: bool = False) -> ExecutionResult:
        """查看 Git 状态"""
        cmd = "git status" + (" -s" if short else "")
        return await self.terminal_exec(cmd)

    async def git_diff(
        self, file_path: str = None, staged: bool = False
    ) -> ExecutionResult:
        """查看 Git 差异"""
        if staged:
            cmd = "git diff --cached" + (f" {file_path}" if file_path else "")
        else:
            cmd = "git diff" + (f" -- {file_path}" if file_path else "")
        return await self.terminal_exec(cmd)

    async def git_log(self, count: int = 10, file_path: str = None) -> ExecutionResult:
        """查看 Git 提交历史"""
        cmd = f"git log -{count}" + (f" -- {file_path}" if file_path else " --oneline")
        return await self.terminal_exec(cmd)

    async def git_branch(self, all: bool = False) -> ExecutionResult:
        """查看 Git 分支"""
        cmd = "git branch" + (" -a" if all else "")
        return await self.terminal_exec(cmd)

    async def git_commit(self, message: str, amend: bool = False) -> ExecutionResult:
        """提交更改"""
        if not message:
            return ExecutionResult(success=False, output="", error="提交信息不能为空")

        # 先检查是否有暂存的更改
        status_result = await self.git_status(short=True)
        if not status_result.output.strip():
            return ExecutionResult(success=False, output="", error="没有需要提交的内容")

        cmd = f'git commit -m "{message}"' + (" --amend" if amend else "")
        return await self.terminal_exec(cmd)

    async def git_add(self, path: str = ".") -> ExecutionResult:
        """添加文件到暂存区"""
        cmd = f"git add {path}"
        return await self.terminal_exec(cmd)

    async def git_push(
        self, remote: str = "origin", branch: str = None, force: bool = False
    ) -> ExecutionResult:
        """推送到远程"""
        branch_part = f" {branch}" if branch else ""
        force_part = " -f" if force else ""
        cmd = f"git push{force_part} {remote}{branch_part}"
        return await self.terminal_exec(cmd)

    async def git_pull(
        self, remote: str = "origin", branch: str = None
    ) -> ExecutionResult:
        """从远程拉取"""
        branch_part = f" {branch}" if branch else ""
        cmd = f"git pull {remote}{branch_part}"
        return await self.terminal_exec(cmd)

    async def git_checkout(self, branch: str, create: bool = False) -> ExecutionResult:
        """切换分支"""
        cmd = f"git checkout{' -b' if create else ''} {branch}"
        return await self.terminal_exec(cmd)

    async def git_stash(
        self, pop: bool = False, list: bool = False, clear: bool = False
    ) -> ExecutionResult:
        """Git 暂存操作"""
        if list:
            return await self.terminal_exec("git stash list")
        elif pop:
            return await self.terminal_exec("git stash pop")
        elif clear:
            return await self.terminal_exec("git stash clear")
        else:
            return await self.terminal_exec("git stash")

    async def git_merge(self, branch: str) -> ExecutionResult:
        """合并分支"""
        cmd = f"git merge {branch}"
        return await self.terminal_exec(cmd)

    async def git_rebase(self, branch: str = None) -> ExecutionResult:
        """变基操作"""
        cmd = f"git rebase {branch}" if branch else "git rebase -i HEAD~3"
        return await self.terminal_exec(cmd)

    # ==================== 文件搜索 ====================

    async def file_grep(
        self,
        pattern: str,
        path: str = ".",
        recursive: bool = True,
        include: str = None,
        exclude: str = None,
        context: int = 2,
    ) -> ExecutionResult:
        """搜索文件内容 (grep)"""
        if not pattern:
            return ExecutionResult(success=False, output="", error="搜索模式不能为空")

        cmd = f"grep -r -n" + (" -H" if recursive else "") + f" -C {context}"

        if include:
            cmd += f' --include="{include}"'
        if exclude:
            cmd += f' --exclude="{exclude}"'

        cmd += f' "{pattern}" {path}'

        result = await self.terminal_exec(cmd)

        if result.output and "matches" in result.output.lower():
            result.output += f"\n\n[搜索完成: {result.output.count(chr(10))} 行匹配]"

        return result

    async def file_glob(
        self,
        pattern: str,
        path: str = ".",
        recursive: bool = True,
    ) -> ExecutionResult:
        """查找文件 (glob/find)"""
        if os.name == "nt":
            cmd = f'Get-ChildItem -Path "{path}" -Recurse -Filter "{pattern}" -ErrorAction SilentlyContinue | Select-Object FullName'
            result = await self.terminal_exec(f'powershell -Command "{cmd}"')
        else:
            recurse = "-r" if recursive else ""
            cmd = f'find {path} {recurse} -name "{pattern}" 2>/dev/null'
            result = await self.terminal_exec(cmd)

        if result.success and result.output:
            files = [f for f in result.output.strip().split("\n") if f]
            result.output = f"找到 {len(files)} 个文件:\n" + "\n".join(files[:100])
            if len(files) > 100:
                result.output += f"\n... 还有 {len(files) - 100} 个文件"

        return result

    # ==================== 代码理解 ====================

    async def code_search_symbol(
        self,
        symbol: str,
        path: str = ".",
    ) -> ExecutionResult:
        """查找符号定义和引用"""
        # 尝试使用 ctags 或 ripgrep
        result = await self.file_grep(pattern=symbol, path=path, context=1)
        if result.success:
            result.output = f"符号 '{symbol}' 搜索结果:\n" + result.output
        return result

    async def code_find_definitions(
        self,
        symbol: str,
        path: str = ".",
    ) -> ExecutionResult:
        """查找定义"""
        return await self.code_search_symbol(symbol, path)

    async def code_find_references(
        self,
        symbol: str,
        path: str = ".",
    ) -> ExecutionResult:
        """查找引用"""
        return await self.code_search_symbol(symbol, path)

    async def code_explain(
        self,
        code: str = None,
        file_path: str = None,
    ) -> ExecutionResult:
        """解释代码"""
        if file_path:
            result = await self.file_read(file_path, limit=50)
            if not result.success:
                return result
            code = result.output

        if not code:
            return ExecutionResult(success=False, output="", error="没有提供代码")

        # 简单分析代码结构
        lines = code.split("\n")
        analysis = []

        # 统计信息
        total_lines = len([l for l in lines if l.strip()])
        blank_lines = len([l for l in lines if not l.strip()])
        comment_lines = len(
            [
                l
                for l in lines
                if l.strip().startswith("#") or l.strip().startswith("//")
            ]
        )

        analysis.append(
            f"总行数: {total_lines} | 空行: {blank_lines} | 注释: {comment_lines}"
        )

        # 检测函数/类
        import re

        functions = re.findall(r"def\s+(\w+)|class\s+(\w+)", code)
        if functions:
            analysis.append(f"\n函数/类定义: {len(functions)} 个")
            for f in functions[:10]:
                name = f[0] or f[1]
                analysis.append(f"  - {name}")

        # 检测 import
        imports = re.findall(r"^import\s+(\w+)|^from\s+(\w+)", code, re.MULTILINE)
        if imports:
            analysis.append(f"\n导入模块: {len(imports)} 个")
            for imp in imports[:10]:
                name = imp[0] or imp[1]
                analysis.append(f"  - {name}")

        return ExecutionResult(success=True, output="代码分析:\n" + "\n".join(analysis))

    # ==================== 项目上下文 ====================

    async def load_project_context(self) -> Dict[str, Any]:
        """加载项目上下文 (类似 CLAUDE.md)"""
        context = {
            "files": [],
            "instructions": "",
            "commands": {},
        }

        # 查找 CLAUDE.md 或 CLAUDE.md 类似文件
        context_files = [
            "CLAUDE.md",
            "claude.md",
            ".claude.md",
            "PROJECT.md",
            "project.md",
        ]

        for cf in context_files:
            path = self.workspace_root / cf
            if path.exists():
                result = await self.file_read(str(path))
                if result.success:
                    context["instructions"] = result.output
                    context["context_file"] = cf
                    break

        # 查找 .gitignore
        gitignore_path = self.workspace_root / ".gitignore"
        if gitignore_path.exists():
            result = await self.file_read(str(gitignore_path))
            if result.success:
                context["gitignore"] = [
                    l for l in result.output.split("\n") if l and not l.startswith("#")
                ]

        # 检查是否是 Git 仓库
        git_dir = self.workspace_root / ".git"
        context["is_git_repo"] = git_dir.exists()

        # 读取 package.json 或其他项目配置
        for config_file in [
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
        ]:
            config_path = self.workspace_root / config_file
            if config_path.exists():
                result = await self.file_read(str(config_path), limit=30)
                if result.success:
                    context["config_file"] = config_file
                    context["config_summary"] = result.output[:500]
                    break

        return context

    # ==================== 智能任务拆解 ====================

    async def plan_complex_task(self, task: str) -> Dict[str, Any]:
        """分析复杂任务并生成执行计划"""
        task_lower = task.lower()

        plan = {
            "task": task,
            "steps": [],
            "estimated_steps": 0,
        }

        # 检测任务类型并生成步骤
        if any(
            k in task_lower
            for k in ["开发", "实现", "创建", "写", "build", "create", "implement"]
        ):
            plan["steps"] = [
                {"action": "分析需求", "tool": "project_analyze"},
                {"action": "创建文件结构", "tool": "terminal_exec", "cmd": "mkdir -p"},
                {"action": "编写代码", "tool": "file_write"},
                {"action": "测试运行", "tool": "terminal_exec"},
            ]

        elif any(k in task_lower for k in ["修复", "debug", "bug", "错误"]):
            plan["steps"] = [
                {"action": "定位问题", "tool": "file_grep"},
                {"action": "分析代码", "tool": "code_explain"},
                {"action": "修复代码", "tool": "file_edit"},
                {"action": "验证修复", "tool": "terminal_exec"},
            ]

        elif any(k in task_lower for k in ["重构", "优化", "refactor"]):
            plan["steps"] = [
                {"action": "分析现有代码", "tool": "project_analyze"},
                {"action": "制定重构计划", "tool": "code_explain"},
                {"action": "执行重构", "tool": "file_edit"},
                {"action": "运行测试", "tool": "terminal_exec"},
            ]

        elif any(k in task_lower for k in ["提交", "commit", "推送", "push", "git"]):
            plan["steps"] = [
                {"action": "查看状态", "tool": "git_status"},
                {"action": "查看差异", "tool": "git_diff"},
                {"action": "添加文件", "tool": "git_add"},
                {"action": "提交", "tool": "git_commit"},
                {"action": "推送", "tool": "git_push"},
            ]

        elif any(k in task_lower for k in ["搜索", "查找", "search", "find"]):
            plan["steps"] = [
                {"action": "文件搜索", "tool": "file_glob"},
                {"action": "内容搜索", "tool": "file_grep"},
                {"action": "分析结果", "tool": "code_explain"},
            ]

        else:
            # 默认通用任务
            plan["steps"] = [
                {"action": "分析任务", "tool": "project_analyze"},
                {"action": "执行操作", "tool": "terminal_exec"},
            ]

        plan["estimated_steps"] = len(plan["steps"])

        return plan

    # ==================== 智能建议 ====================

    async def get_suggestions(self, context: str = None) -> List[str]:
        """根据上下文提供智能建议"""
        suggestions = []

        # 检查 Git 状态
        status_result = await self.git_status(short=True)
        if status_result.success and status_result.output.strip():
            suggestions.append("检测到未提交的更改 - 使用 git_commit 提交")

        # 检查是否有未安装的依赖
        if (self.workspace_root / "package.json").exists():
            if not (self.workspace_root / "node_modules").exists():
                suggestions.append(
                    "检测到 package.json 但 node_modules 不存在 - 运行 npm install"
                )

        if (self.workspace_root / "requirements.txt").exists():
            suggestions.append(
                "检测到 Python 项目 - 使用 pip install -r requirements.txt"
            )

        # 检查测试文件
        if (self.workspace_root / "tests").exists():
            suggestions.append("检测到 tests 目录 - 可以运行 pytest")

        # 检查 README
        if not (self.workspace_root / "README.md").exists():
            suggestions.append("项目缺少 README.md - 建议创建")

        return suggestions[:5]

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


def reset_terminal_ultra():
    """重置全局 TerminalUltra 实例"""
    global _terminal_ultra_instance
    _terminal_ultra_instance = None


# ==================== Agent 调用 ====================


# Agent handlers - 直接从文件导入
_agent_handlers = {}


async def _load_agent_handlers():
    """加载所有 agent handlers"""
    global _agent_handlers
    if _agent_handlers:
        return

    import importlib.util

    agents_dir = Path(__file__).parent / "skills" / "agents"

    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir() and not agent_dir.name.startswith("_"):
            handler_path = agent_dir / "handler.py"
            if handler_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"agent_{agent_dir.name}", handler_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    _agent_handlers[agent_dir.name] = module.handler
                except Exception as e:
                    logger.warning(f"[Agent] 加载 {agent_dir.name} 失败: {e}")


async def call_agent(
    agent_name: str, args: Dict[str, Any], context: Dict[str, Any] = None
) -> ExecutionResult:
    """调用 Agent 执行任务

    Args:
        agent_name: Agent名称 (code_explorer, code_reviewer, code_architect)
        args: Agent参数
        context: 上下文信息

    Returns:
        ExecutionResult: 执行结果
    """
    try:
        await _load_agent_handlers()

        handler = _agent_handlers.get(agent_name)
        if not handler:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Agent不存在: {agent_name}",
            )

        result = await handler(args, context or {})

        return ExecutionResult(
            success=True,
            output=result,
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output="",
            error=f"Agent执行失败: {str(e)}",
        )


async def execute_terminal_agent(
    task: str, context: Dict[str, Any] = None
) -> ExecutionResult:
    """根据任务自动选择合适的 Agent 执行

    Args:
        task: 任务描述
        context: 上下文

    Returns:
        ExecutionResult: 执行结果
    """
    task_lower = task.lower()

    # 根据关键词选择 Agent
    if any(
        k in task_lower
        for k in ["探索", "分析结构", "查找", "搜索", "explore", "find", "search"]
    ):
        target = _extract_target(task)
        return await call_agent(
            "code_explorer", {"action": "explore", "target": target}, context
        )

    elif any(
        k in task_lower
        for k in ["审查", "审查代码", "检查bug", "review", "bug", "检查"]
    ):
        target = _extract_target(task)
        return await call_agent(
            "code_reviewer", {"action": "review", "target": target}, context
        )

    elif any(
        k in task_lower
        for k in ["架构", "设计", "重构", "模块", "architecture", "design", "refactor"]
    ):
        target = _extract_target(task)
        return await call_agent(
            "code_architect", {"action": "design", "target": target}, context
        )

    else:
        return ExecutionResult(
            success=False,
            output="",
            error="未识别任务类型，请明确指定: 探索/审查/架构",
        )


def _extract_target(task: str) -> str:
    """从任务描述中提取目标路径"""
    import re

    # 提取文件或目录路径
    match = re.search(r"[.\/\\][\w\.\/\\]+", task)
    if match:
        return match.group()
    return "."
