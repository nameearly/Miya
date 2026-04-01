#!/usr/bin/env python3
"""
弥娅终端工具系统 - 完全对齐 Claude Code
整合 BashTool、FileTool、SearchTool 等所有工具
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
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from core.system_config import get_constant

logger = logging.getLogger("Miya.Tools")


# ==================== 基础类型 ====================


class ToolResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str = ""
    status: ToolResultStatus = ToolResultStatus.SUCCESS
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, output: str = "", metadata: Dict = None) -> "ToolResult":
        return cls(
            success=True,
            output=output,
            status=ToolResultStatus.SUCCESS,
            metadata=metadata or {},
        )

    @classmethod
    def err(cls, error: str, metadata: Dict = None) -> "ToolResult":
        return cls(
            success=False,
            error=error,
            status=ToolResultStatus.ERROR,
            metadata=metadata or {},
        )


@dataclass
class ToolContext:
    workspace_root: str
    current_dir: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    abort_signal: Optional[Any] = None


class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


# ==================== BashTool ====================


class BashTool:
    """弥娅 BashTool - 完全对齐 Claude Code BashTool"""

    SEARCH_COMMANDS = {"find", "grep", "rg", "ag", "ack", "locate", "which", "whereis"}
    READ_COMMANDS = {
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "wc",
        "stat",
        "file",
        "strings",
        "jq",
        "awk",
        "cut",
        "sort",
        "uniq",
        "tr",
    }
    LIST_COMMANDS = {"ls", "tree", "du"}
    SILENT_COMMANDS = {
        "mv",
        "cp",
        "rm",
        "mkdir",
        "rmdir",
        "chmod",
        "chown",
        "chgrp",
        "touch",
        "ln",
        "cd",
        "export",
        "unset",
        "wait",
    }
    SEMANTIC_NEUTRAL = {"echo", "printf", "true", "false", ":"}
    COMMON_BACKGROUND = {
        "npm",
        "yarn",
        "pnpm",
        "node",
        "python",
        "python3",
        "go",
        "cargo",
        "make",
        "docker",
        "terraform",
        "webpack",
        "vite",
        "jest",
        "pytest",
        "curl",
        "wget",
    }
    DISALLOWED_AUTO_BACKGROUND = {"sleep"}

    DEFAULT_TIMEOUT_MS = get_constant("terminal", "default_timeout_ms", 120000)
    MAX_TIMEOUT_MS = get_constant("terminal", "max_timeout_ms", 600000)
    PROGRESS_THRESHOLD_MS = get_constant("terminal", "progress_threshold_ms", 2000)

    def __init__(self):
        self._background_tasks: Dict[str, Dict] = {}
        self._blocked_patterns = get_constant(
            "terminal",
            "blocked_commands",
            [
                "rm -rf /",
                "rm -rf /*",
                "mkfs",
                "dd if=/dev/zero",
                ":(){ :|:& };:",
                "fork()",
                "> /dev/sd",
                "chmod -R 777 /",
            ],
        )
        self._dangerous_patterns = get_constant(
            "terminal",
            "dangerous_patterns",
            ["rm -rf", "rm -r", "del /", "format", "chmod 777"],
        )
        self._caution_patterns = get_constant(
            "terminal", "caution_patterns", ["rm ", "del ", "mv ", "cp -r"]
        )
        self._whitelist = get_constant("terminal", "whitelist", {})

    @property
    def name(self) -> str:
        return "bash"

    def _check_command_risk(self, command: str) -> RiskLevel:
        cmd_lower = command.lower().strip()
        for p in self._blocked_patterns:
            if p in cmd_lower:
                return RiskLevel.BLOCKED
        for p in self._dangerous_patterns:
            if p in cmd_lower:
                return RiskLevel.DANGEROUS
        for p in self._caution_patterns:
            if cmd_lower.startswith(p):
                return RiskLevel.CAUTION
        return RiskLevel.SAFE

    def _detect_blocked_sleep_pattern(self, command: str) -> Optional[str]:
        parts = command.strip().split()
        if not parts:
            return None
        match = re.match(r"^sleep\s+(\d+)\s*$", parts[0].strip().lower())
        if not match:
            return None
        secs = int(match.group(1))
        if secs < 2:
            return None
        rest = " ".join(parts[1:]).strip()
        return f"sleep {secs}" + (f" followed by: {rest}" if rest else " standalone")

    def _is_read_only(self, command: str) -> bool:
        try:
            parts = self._split_command_with_operators(command)
        except:
            return False
        has_non_neutral = False
        for part in parts:
            if part in {">", ">>", ">&", "||", "&&", "|", ";"}:
                continue
            base = part.strip().split()[0] if part.strip() else ""
            if base in self.SEMANTIC_NEUTRAL:
                continue
            has_non_neutral = True
        return not has_non_neutral

    def _split_command_with_operators(self, command: str) -> List[str]:
        result, current, in_quote = [], "", None
        for char in command:
            if in_quote:
                if char == in_quote:
                    in_quote = None
                current += char
            elif char in ('"', "'"):
                in_quote, current = char, current + char
            elif char in ("|", "&", ";", ">"):
                if current.strip():
                    result.append(current.strip())
                result.append(char)
                current = ""
            else:
                current += char
        if current.strip():
            result.append(current.strip())
        return result if result else [command]

    def _interpret_exit_code(self, code: int, stdout: str) -> Dict:
        if code == 0:
            return {"is_error": False}
        if "nothing to commit" in stdout.lower():
            return {"is_error": False, "message": "Nothing to commit"}
        return {"is_error": True, "message": f"Exit code {code}"}

    def _is_silent_command(self, command: str) -> bool:
        try:
            parts = self._split_command_with_operators(command)
        except:
            return False
        for part in parts:
            if part in {"||", "&&", "|", ";", ">", ">>", ">&"}:
                continue
            base = part.strip().split()[0] if part.strip() else ""
            if base in self.SILENT_COMMANDS:
                return True
        return False

    async def execute(
        self,
        command: str,
        timeout: int = None,
        cwd: str = None,
        env: Dict = None,
        run_in_background: bool = False,
        context: ToolContext = None,
    ) -> ToolResult:
        start_time = time.time()
        timeout_ms = timeout or self.DEFAULT_TIMEOUT_MS
        timeout_ms = min(timeout_ms, self.MAX_TIMEOUT_MS)

        # 安全检查
        risk = self._check_command_risk(command)
        if risk == RiskLevel.BLOCKED:
            return ToolResult.err("Command blocked by security system")

        # 检查 sleep 模式
        blocked_sleep = self._detect_blocked_sleep_pattern(command)
        if blocked_sleep:
            return ToolResult.err(
                f"Blocked: {blocked_sleep}. Use run_in_background or Monitor tool"
            )

        # 权限检查
        if (
            context
            and context.permissions.get("read_only")
            and not self._is_read_only(command)
        ):
            return ToolResult.err("Read-only mode: write operations not allowed")

        # 执行环境
        work_dir = cwd or (context.current_dir if context else os.getcwd())
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        if context and context.environment:
            exec_env.update(context.environment)

        if run_in_background:
            task_id = str(uuid.uuid4())[:8]
            self._background_tasks[task_id] = {
                "command": command,
                "status": "running",
                "start_time": time.time(),
            }
            asyncio.create_task(
                self._run_background(command, work_dir, exec_env, timeout_ms, task_id)
            )
            return ToolResult.ok(
                f"Command running in background with ID: {task_id}",
                {"background_task_id": task_id},
            )

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=work_dir,
                env=exec_env,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout_ms / 1000)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                elapsed = time.time() - start_time
                return ToolResult.ok(
                    stdout,
                    {"interrupted": True, "timeout": True, "execution_time": elapsed},
                )

            elapsed = time.time() - start_time
            interpretation = self._interpret_exit_code(process.returncode, stdout)

            output = stdout
            if stderr:
                output += "\n" + stderr
            if interpretation.get("is_error") and process.returncode != 0:
                output += f"\nExit code {process.returncode}"

            return ToolResult.ok(
                output,
                {
                    "exit_code": process.returncode,
                    "execution_time": elapsed,
                    "return_code_interpretation": interpretation.get("message"),
                    "no_output_expected": self._is_silent_command(command),
                },
            )
        except Exception as e:
            return ToolResult.err(str(e))

    async def _run_background(
        self, command: str, cwd: str, env: Dict, timeout_ms: int, task_id: str
    ):
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                text=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout_ms / 1000)
                self._background_tasks[task_id].update(
                    {
                        "status": "completed",
                        "exit_code": process.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                    }
                )
            except subprocess.TimeoutExpired:
                process.kill()
                self._background_tasks[task_id].update({"status": "timeout"})
            self._background_tasks[task_id]["end_time"] = time.time()
        except Exception as e:
            self._background_tasks[task_id].update({"status": "error", "error": str(e)})

    def get_background_status(self, task_id: str) -> Optional[Dict]:
        return self._background_tasks.get(task_id)


# ==================== FileTool ====================


class FileReadTool:
    DEFAULT_MAX_SIZE = get_constant("terminal", "default_max_size", 10485760)
    DEFAULT_LIMIT = get_constant("terminal", "default_limit", 2000)

    @property
    def name(self) -> str:
        return "read"

    def _resolve_path(self, path: str, context: ToolContext) -> str:
        path = path.strip()
        if os.path.isabs(path):
            return os.path.normpath(path)
        if path.startswith("~"):
            return os.path.normpath(os.path.expanduser(path))
        return os.path.normpath(os.path.join(context.current_dir, path))

    def _detect_encoding(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            first_bytes = f.read(4)
            if first_bytes.startswith(b"\xff\xfe"):
                return "utf-16-le"
            if first_bytes.startswith(b"\xfe\xff"):
                return "utf-16-be"
            if first_bytes.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig"
        return "utf-8"

    async def execute(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = None,
        force: bool = False,
        context: ToolContext = None,
    ) -> ToolResult:
        if not context:
            return ToolResult.err("ToolContext required")

        abs_path = self._resolve_path(file_path, context)

        if not os.path.exists(abs_path):
            return ToolResult.err(f"File not found: {file_path}")

        if os.path.isdir(abs_path):
            return ToolResult.err(f"Is a directory: {file_path}")

        size = os.path.getsize(abs_path)
        if size > self.DEFAULT_MAX_SIZE and not force:
            return ToolResult.err(
                f"File too large: {size / 1024 / 1024:.1f}MB. Use force: true to read anyway."
            )

        encoding = self._detect_encoding(abs_path)

        try:
            with open(abs_path, "r", encoding=encoding, errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return ToolResult.err(f"Failed to read: {str(e)}")

        total_lines = len(lines)
        if offset > 0:
            lines = lines[offset:]
        if limit:
            lines = lines[:limit]

        content = "".join(lines)
        truncated = offset + (limit or total_lines) < total_lines

        header = f"=== {abs_path} ===\nLines: {offset + 1}-{offset + len(lines)} / {total_lines}\nSize: {size} bytes\n"
        if truncated:
            header += f"Truncated: {total_lines - (offset + (limit or total_lines))} lines remaining\n"
        header += "=" * 40 + "\n"

        return ToolResult.ok(
            header + content,
            {"num_lines": len(lines), "truncated": truncated, "size": size},
        )


class FileEditTool:
    @property
    def name(self) -> str:
        return "edit"

    def _resolve_path(self, path: str, context: ToolContext) -> str:
        path = path.strip()
        if os.path.isabs(path):
            return os.path.normpath(path)
        if path.startswith("~"):
            return os.path.normpath(os.path.expanduser(path))
        return os.path.normpath(os.path.join(context.current_dir, path))

    def _detect_encoding(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            first_bytes = f.read(4)
            if first_bytes.startswith(b"\xff\xfe"):
                return "utf-16-le"
            if first_bytes.startswith(b"\xfe\xff"):
                return "utf-16-be"
            if first_bytes.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig"
        return "utf-8"

    async def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        force: bool = False,
        context: ToolContext = None,
    ) -> ToolResult:
        if not context:
            return ToolResult.err("ToolContext required")

        abs_path = self._resolve_path(file_path, context)

        if not os.path.exists(abs_path):
            return ToolResult.err(f"File not found: {file_path}")

        encoding = self._detect_encoding(abs_path)

        try:
            with open(abs_path, "r", encoding=encoding, errors="replace") as f:
                content = f.read()
        except Exception as e:
            return ToolResult.err(f"Failed to read: {str(e)}")

        if not force and old_string not in content:
            return ToolResult.err("old_string not found in file")

        if replace_all:
            new_content = content.replace(old_string, new_string)
            count = content.count(old_string)
        else:
            new_content = content.replace(old_string, new_string, 1)
            count = 1

        try:
            with open(abs_path, "w", encoding=encoding) as f:
                f.write(new_content)
        except Exception as e:
            return ToolResult.err(f"Failed to write: {str(e)}")

        return ToolResult.ok(
            f"Replaced {count} occurrence(s) in {abs_path}", {"replacements": count}
        )


class FileWriteTool:
    @property
    def name(self) -> str:
        return "write"

    def _resolve_path(self, path: str, context: ToolContext) -> str:
        path = path.strip()
        if os.path.isabs(path):
            return os.path.normpath(path)
        if path.startswith("~"):
            return os.path.normpath(os.path.expanduser(path))
        return os.path.normpath(os.path.join(context.current_dir, path))

    async def execute(
        self,
        file_path: str,
        content: str,
        create_dirs: bool = True,
        context: ToolContext = None,
    ) -> ToolResult:
        if not context:
            return ToolResult.err("ToolContext required")

        abs_path = self._resolve_path(file_path, context)

        if create_dirs:
            parent = os.path.dirname(abs_path)
            if parent and not os.path.exists(parent):
                try:
                    os.makedirs(parent, exist_ok=True)
                except Exception as e:
                    return ToolResult.err(f"Failed to create directory: {str(e)}")

        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            return ToolResult.err(f"Failed to write: {str(e)}")

        size = os.path.getsize(abs_path)
        return ToolResult.ok(
            f"File written: {abs_path}",
            {"size": size, "lines": len(content.split("\n"))},
        )


class FileDeleteTool:
    @property
    def name(self) -> str:
        return "delete"

    def _resolve_path(self, path: str, context: ToolContext) -> str:
        path = path.strip()
        if os.path.isabs(path):
            return os.path.normpath(path)
        return os.path.normpath(os.path.join(context.current_dir, path))

    async def execute(
        self, file_path: str, recursive: bool = False, context: ToolContext = None
    ) -> ToolResult:
        if not context:
            return ToolResult.err("ToolContext required")

        abs_path = self._resolve_path(file_path, context)

        if not os.path.exists(abs_path):
            return ToolResult.err(f"Path does not exist: {file_path}")

        try:
            if os.path.isdir(abs_path):
                if not recursive:
                    return ToolResult.err("Use recursive: true to delete directories")
                shutil.rmtree(abs_path)
            else:
                os.unlink(abs_path)
        except Exception as e:
            return ToolResult.err(f"Failed to delete: {str(e)}")

        return ToolResult.ok(f"Deleted: {abs_path}")


# ==================== SearchTool ====================


class GlobTool:
    DEFAULT_MAX_RESULTS = get_constant("terminal", "default_max_results", 1000)

    @property
    def name(self) -> str:
        return "glob"

    def _resolve_path(self, path: str, context: ToolContext) -> str:
        if not path or path == ".":
            return context.current_dir
        if os.path.isabs(path):
            return os.path.normpath(path)
        return os.path.normpath(os.path.join(context.current_dir, path))

    async def execute(
        self,
        pattern: str,
        path: str = None,
        include_hidden: bool = False,
        max_results: int = None,
        context: ToolContext = None,
    ) -> ToolResult:
        if not context:
            return ToolResult.err("ToolContext required")

        search_path = self._resolve_path(path or context.current_dir, context)

        if not os.path.isdir(search_path):
            return ToolResult.err(f"Directory not found: {path}")

        max_results = max_results or self.DEFAULT_MAX_RESULTS
        base_path = Path(search_path)

        files = []
        try:
            for p in base_path.glob(pattern):
                if p.is_file():
                    if not include_hidden and any(
                        part.startswith(".") for part in p.parts
                    ):
                        continue
                    files.append(str(p))
        except Exception as e:
            return ToolResult.err(f"Glob failed: {str(e)}")

        truncated = len(files) > max_results
        files = files[:max_results]

        rel_files = [os.path.relpath(f, context.workspace_root) for f in files]
        output = f"Found {len(files)} files:\n" + "\n".join(rel_files)
        if truncated:
            output += f"\n... (truncated, showing first {max_results})"

        return ToolResult.ok(
            output,
            {"files": rel_files, "num_files": len(files), "truncated": truncated},
        )


class GrepTool:
    DEFAULT_HEAD_LIMIT = get_constant("terminal", "default_head_limit", 250)
    VCS_EXCLUDE_DIRS = [".git", ".svn", ".hg", ".bzr", ".jj"]

    @property
    def name(self) -> str:
        return "grep"

    def _resolve_path(self, path: str, context: ToolContext) -> str:
        if not path or path == ".":
            return context.current_dir
        if os.path.isabs(path):
            return os.path.normpath(path)
        return os.path.normpath(os.path.join(context.current_dir, path))

    async def execute(
        self,
        pattern: str,
        path: str = None,
        glob: str = None,
        output_mode: str = "files_with_matches",
        context_lines: int = 2,
        show_line_numbers: bool = True,
        case_insensitive: bool = False,
        head_limit: int = None,
        offset: int = 0,
        context: ToolContext = None,
    ) -> ToolResult:
        if not context:
            return ToolResult.err("ToolContext required")

        search_path = self._resolve_path(path or context.current_dir, context)
        head_limit = head_limit or self.DEFAULT_HEAD_LIMIT

        # 检查 ripgrep 是否可用
        rg_available = True
        try:
            subprocess.run(["rg", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            rg_available = False

        if not rg_available:
            return await self._execute_python_grep(
                pattern,
                search_path,
                glob,
                output_mode,
                context_lines,
                show_line_numbers,
                case_insensitive,
                head_limit,
                offset,
                context,
            )

        cmd = ["rg", "--no-heading"]

        if output_mode == "content":
            cmd.extend(["--line-number", "--context", str(context_lines)])
        elif output_mode == "count":
            cmd.append("--count-matches")
        else:
            cmd.append("--files-with-matches")

        if case_insensitive:
            cmd.append("-i")

        if glob:
            cmd.extend(["--glob", glob])

        for vcs_dir in self.VCS_EXCLUDE_DIRS:
            cmd.extend(["--glob", f"!.{vcs_dir}/**"])

        if head_limit > 0:
            cmd.extend(["--max-count", str(head_limit + offset)])

        cmd.extend([pattern, search_path])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            stdout = result.stdout
            stderr = result.stderr

            if head_limit > 0 and offset > 0 and stdout:
                lines = stdout.split("\n")
                stdout = "\n".join(lines[offset : offset + head_limit])

            files = set()
            num_lines = 0
            if output_mode == "files_with_matches":
                files = set(line for line in stdout.split("\n") if line.strip())
                num_files = len(files)
            elif output_mode == "content":
                for line in stdout.split("\n"):
                    if line.strip():
                        match = re.match(r"^(.+?):", line)
                        if match:
                            files.add(match.group(1))
                num_lines = len([l for l in stdout.split("\n") if l.strip()])
                num_files = len(files)
            else:
                num_files = len([l for l in stdout.split("\n") if l.strip()])

            output = stdout or "No matches found"
            if stderr and not stdout:
                output = stderr

            return ToolResult.ok(
                output,
                {"mode": output_mode, "num_files": num_files, "filenames": list(files)},
            )
        except FileNotFoundError:
            return await self._execute_python_grep(
                pattern,
                search_path,
                glob,
                output_mode,
                context_lines,
                show_line_numbers,
                case_insensitive,
                head_limit,
                offset,
                context,
            )
        except Exception as e:
            return ToolResult.err(f"Grep failed: {str(e)}")

    async def _execute_python_grep(
        self,
        pattern: str,
        search_path: str,
        glob: str,
        output_mode: str,
        context_lines: int,
        show_line_numbers: bool,
        case_insensitive: bool,
        head_limit: int,
        offset: int,
        context: ToolContext,
    ) -> ToolResult:
        """Python 回退 grep 实现"""
        try:
            import fnmatch

            flags = re.IGNORECASE if case_insensitive else 0
            compiled_pattern = re.compile(pattern, flags)

            matches = []
            file_matches = set()

            # 处理路径：可能是文件或目录
            search_paths = []
            if os.path.isfile(search_path):
                search_paths = [search_path]
            elif os.path.isdir(search_path):
                search_paths = [search_path]
            else:
                return ToolResult.err(f"Path not found: {search_path}")

            for base_path in search_paths:
                if os.path.isfile(base_path):
                    # 单个文件
                    files_to_search = [os.path.basename(base_path)]
                    base_dir = os.path.dirname(base_path)
                else:
                    # 目录
                    files_to_search = None
                    base_dir = base_path

                if files_to_search:
                    # 搜索单个文件
                    for filepath in files_to_search:
                        full_path = (
                            os.path.join(base_dir, filepath) if base_dir else filepath
                        )
                        if os.path.isfile(full_path):
                            try:
                                with open(
                                    full_path, "r", encoding="utf-8", errors="ignore"
                                ) as f:
                                    lines = f.readlines()

                                for i, line in enumerate(lines):
                                    if compiled_pattern.search(line):
                                        file_matches.add(full_path)

                                        if output_mode == "content":
                                            line_num = (
                                                f":{i + 1}" if show_line_numbers else ""
                                            )
                                            matches.append(
                                                f"{full_path}{line_num}:{line.rstrip()}"
                                            )

                                        if output_mode == "count":
                                            matches.append(
                                                f"{full_path}: {sum(1 for l in lines if compiled_pattern.search(l))}"
                                            )

                                        if len(matches) >= head_limit:
                                            break
                            except:
                                continue

                    if len(matches) >= head_limit:
                        break
                else:
                    # 目录搜索
                    for root, dirs, files in os.walk(base_dir):
                        dirs[:] = [d for d in dirs if d not in self.VCS_EXCLUDE_DIRS]

                        for filename in files:
                            if glob and not fnmatch.fnmatch(filename, glob):
                                continue

                            filepath = os.path.join(root, filename)

                            try:
                                with open(
                                    filepath, "r", encoding="utf-8", errors="ignore"
                                ) as f:
                                    lines = f.readlines()
                            except:
                                continue

                            for i, line in enumerate(lines):
                                if compiled_pattern.search(line):
                                    file_matches.add(filepath)

                                    if output_mode == "content":
                                        line_num = (
                                            f":{i + 1}" if show_line_numbers else ""
                                        )
                                        matches.append(
                                            f"{filepath}{line_num}:{line.rstrip()}"
                                        )

                                    if output_mode == "count":
                                        matches.append(
                                            f"{filepath}: {sum(1 for l in lines if compiled_pattern.search(l))}"
                                        )

                                    if len(matches) >= head_limit:
                                        break

                            if len(matches) >= head_limit:
                                break

                        if len(matches) >= head_limit:
                            break

            if output_mode == "files_with_matches":
                output = "\n".join(sorted(file_matches)) or "No matches found"
                num_files = len(file_matches)
            else:
                output = "\n".join(matches[:head_limit]) or "No matches found"
                num_files = len(file_matches)

            return ToolResult.ok(
                output,
                {
                    "mode": output_mode,
                    "num_files": num_files,
                    "filenames": list(file_matches),
                },
            )

        except Exception as e:
            return ToolResult.err(f"Python grep failed: {str(e)}")


# ==================== 工具注册表 ====================


class ToolRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict = {}
            cls._instance._init_default_tools()
        return cls._instance

    def _init_default_tools(self):
        self._tools = {
            "bash": BashTool(),
            "read": FileReadTool(),
            "edit": FileEditTool(),
            "write": FileWriteTool(),
            "delete": FileDeleteTool(),
            "glob": GlobTool(),
            "grep": GrepTool(),
        }

    def get(self, name: str):
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())


def get_tool_registry() -> ToolRegistry:
    return ToolRegistry()


# ==================== TerminalUltra 主类 ====================


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    warnings: List[str] = field(default_factory=list)


class TerminalUltra:
    """弥娅超级终端控制系统 - 完全对齐 Claude Code"""

    def __init__(self, workspace_root: str = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.current_dir = str(self.workspace_root)
        self.safe_mode = True
        self.command_history: List[Dict] = []
        self._tool_registry = get_tool_registry()

        # 初始化工具上下文
        self._context = ToolContext(
            workspace_root=str(self.workspace_root),
            current_dir=self.current_dir,
            permissions={"read_only": False},
            environment={},
        )

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self._tool_registry.get(tool_name)
        if not tool:
            return ToolResult.err(f"Tool not found: {tool_name}")

        # 更新上下文
        self._context.current_dir = self.current_dir

        # 执行工具
        if tool_name == "bash":
            return await tool.execute(
                command=kwargs.get("command"),
                timeout=kwargs.get("timeout"),
                cwd=kwargs.get("cwd"),
                env=kwargs.get("env"),
                run_in_background=kwargs.get("run_in_background", False),
                context=self._context,
            )
        elif tool_name == "read":
            return await tool.execute(
                file_path=kwargs.get("file_path"),
                offset=kwargs.get("offset", 0),
                limit=kwargs.get("limit"),
                force=kwargs.get("force", False),
                context=self._context,
            )
        elif tool_name == "edit":
            return await tool.execute(
                file_path=kwargs.get("file_path"),
                old_string=kwargs.get("old_string"),
                new_string=kwargs.get("new_string"),
                replace_all=kwargs.get("replace_all", False),
                force=kwargs.get("force", False),
                context=self._context,
            )
        elif tool_name == "write":
            return await tool.execute(
                file_path=kwargs.get("file_path"),
                content=kwargs.get("content"),
                create_dirs=kwargs.get("create_dirs", True),
                context=self._context,
            )
        elif tool_name == "delete":
            return await tool.execute(
                file_path=kwargs.get("file_path"),
                recursive=kwargs.get("recursive", False),
                context=self._context,
            )
        elif tool_name == "glob":
            return await tool.execute(
                pattern=kwargs.get("pattern"),
                path=kwargs.get("path"),
                include_hidden=kwargs.get("include_hidden", False),
                max_results=kwargs.get("max_results"),
                context=self._context,
            )
        elif tool_name == "grep":
            return await tool.execute(
                pattern=kwargs.get("pattern"),
                path=kwargs.get("path"),
                glob=kwargs.get("glob"),
                output_mode=kwargs.get("output_mode", "files_with_matches"),
                context_lines=kwargs.get("context", 2),
                show_line_numbers=kwargs.get("-n", True),
                case_insensitive=kwargs.get("-i", False),
                head_limit=kwargs.get("head_limit"),
                offset=kwargs.get("offset", 0),
                context=self._context,
            )

        return ToolResult.err(f"Tool {tool_name} not implemented")

    # ==================== 兼容旧API ====================

    async def terminal_exec(
        self,
        command: str,
        timeout: int = 60,
        cwd: str = None,
        env: Dict = None,
        shell: bool = True,
    ) -> ExecutionResult:
        """执行终端命令 - 兼容旧API"""
        result = await self.execute_tool(
            "bash", command=command, timeout=timeout * 1000, cwd=cwd, env=env
        )

        return ExecutionResult(
            success=result.success,
            output=result.output,
            error=result.error,
            exit_code=result.metadata.get("exit_code", 0),
            execution_time=result.metadata.get("execution_time", 0.0),
            warnings=[],
        )

    async def file_read(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = None,
        encoding: str = "utf-8",
    ) -> ExecutionResult:
        """读取文件 - 兼容旧API"""
        result = await self.execute_tool(
            "read", file_path=file_path, offset=offset, limit=limit
        )

        return ExecutionResult(
            success=result.success, output=result.output, error=result.error
        )

    async def file_write(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> ExecutionResult:
        """写入文件 - 兼容旧API"""
        result = await self.execute_tool(
            "write", file_path=file_path, content=content, create_dirs=create_dirs
        )

        return ExecutionResult(
            success=result.success, output=result.output, error=result.error
        )

    async def file_edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> ExecutionResult:
        """编辑文件 - 兼容旧API"""
        result = await self.execute_tool(
            "edit",
            file_path=file_path,
            old_string=old_string,
            new_string=new_string,
            replace_all=replace_all,
        )

        return ExecutionResult(
            success=result.success, output=result.output, error=result.error
        )

    async def file_delete(
        self, file_path: str, recursive: bool = False
    ) -> ExecutionResult:
        """删除文件 - 兼容旧API"""
        result = await self.execute_tool(
            "delete", file_path=file_path, recursive=recursive
        )

        return ExecutionResult(
            success=result.success, output=result.output, error=result.error
        )

    async def file_glob(
        self, pattern: str, path: str = ".", recursive: bool = True
    ) -> ExecutionResult:
        """查找文件 - 兼容旧API"""
        result = await self.execute_tool("glob", pattern=pattern, path=path)

        return ExecutionResult(
            success=result.success, output=result.output, error=result.error
        )

    async def file_grep(
        self,
        pattern: str,
        path: str = ".",
        recursive: bool = True,
        include: str = None,
        exclude: str = None,
        context: int = 2,
    ) -> ExecutionResult:
        """搜索文件内容 - 兼容旧API"""
        result = await self.execute_tool(
            "grep", pattern=pattern, path=path, glob=include, context=context
        )

        return ExecutionResult(
            success=result.success, output=result.output, error=result.error
        )

    async def directory_tree(
        self, dir_path: str = ".", max_depth: int = 3, include_hidden: bool = False
    ) -> ExecutionResult:
        """显示目录树 - 兼容旧API"""
        try:
            path = Path(dir_path)
            if not path.is_absolute():
                path = Path(self.current_dir) / path

            if not path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"Directory not found: {dir_path}"
                )

            lines = []
            self._build_tree(path, "", lines, max_depth, 0, include_hidden)

            return ExecutionResult(
                success=True, output=f"=== {path} ===\n" + "\n".join(lines)
            )
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    def _build_tree(
        self,
        path: Path,
        prefix: str,
        lines: List,
        max_depth: int,
        current_depth: int,
        include_hidden: bool,
    ):
        if current_depth >= max_depth:
            return

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            for i, item in enumerate(items):
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
            lines.append(f"{prefix}[Permission denied]")

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    async def code_execute(
        self, code: str, language: str = "python", timeout: int = 30
    ) -> ExecutionResult:
        """执行代码 - 兼容旧API"""
        if language.lower() == "python":
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                temp_file = f.name

            result = await self.terminal_exec(f'python "{temp_file}"', timeout=timeout)

            try:
                os.unlink(temp_file)
            except:
                pass

            return result
        elif language.lower() in ["javascript", "js", "node"]:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                temp_file = f.name

            result = await self.terminal_exec(f'node "{temp_file}"', timeout=timeout)

            try:
                os.unlink(temp_file)
            except:
                pass

            return result
        else:
            return ExecutionResult(
                success=False, output="", error=f"Unsupported language: {language}"
            )

    async def project_analyze(self, path: str = None) -> ExecutionResult:
        """分析项目结构 - 兼容旧API"""
        try:
            project_path = Path(path) if path else self.workspace_root

            if not project_path.exists():
                return ExecutionResult(
                    success=False, output="", error=f"Path not found: {path}"
                )

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
            }

            analysis = {"total_files": 0, "total_size": 0, "languages": {}}

            for root, dirs, files in os.walk(str(project_path)):
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
                    except:
                        continue

            lines = [
                f"=== Project: {project_path.name} ===",
                f"Total files: {analysis['total_files']}",
                f"Total size: {self._format_size(analysis['total_size'])}",
                "",
                "Languages:",
            ]

            for lang, info in sorted(
                analysis["languages"].items(), key=lambda x: x[1]["size"], reverse=True
            ):
                lines.append(
                    f"  {lang}: {info['files']} files, {self._format_size(info['size'])}"
                )

            lines.append("")
            lines.append("Root structure:")
            for item in sorted(project_path.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    lines.append(f"  📁 {item.name}/")
                else:
                    lines.append(f"  📄 {item.name}")

            return ExecutionResult(success=True, output="\n".join(lines))
        except Exception as e:
            return ExecutionResult(success=False, output="", error=str(e))

    # ==================== Git 工具 ====================

    async def git_status(self, short: bool = False) -> ExecutionResult:
        cmd = "git status" + (" -s" if short else "")
        return await self.terminal_exec(cmd)

    async def git_diff(
        self, file_path: str = None, staged: bool = False
    ) -> ExecutionResult:
        if staged:
            cmd = "git diff --cached" + (f" {file_path}" if file_path else "")
        else:
            cmd = "git diff" + (f" -- {file_path}" if file_path else "")
        return await self.terminal_exec(cmd)

    async def git_log(self, count: int = 10) -> ExecutionResult:
        return await self.terminal_exec(f"git log -{count} --oneline")

    async def git_branch(self, all: bool = False) -> ExecutionResult:
        cmd = "git branch" + (" -a" if all else "")
        return await self.terminal_exec(cmd)

    async def git_commit(self, message: str) -> ExecutionResult:
        if not message:
            return ExecutionResult(
                success=False, output="", error="Commit message required"
            )
        status = await self.git_status(short=True)
        if not status.output.strip():
            return ExecutionResult(success=False, output="", error="Nothing to commit")
        return await self.terminal_exec(f'git commit -m "{message}"')

    async def git_add(self, path: str = ".") -> ExecutionResult:
        return await self.terminal_exec(f"git add {path}")

    async def git_push(
        self, remote: str = "origin", branch: str = None, force: bool = False
    ) -> ExecutionResult:
        branch_part = f" {branch}" if branch else ""
        force_part = " -f" if force else ""
        return await self.terminal_exec(f"git push{force_part} {remote}{branch_part}")

    async def git_pull(
        self, remote: str = "origin", branch: str = None
    ) -> ExecutionResult:
        branch_part = f" {branch}" if branch else ""
        return await self.terminal_exec(f"git pull {remote}{branch_part}")

    async def git_checkout(
        self, branch_or_ref: str, create: bool = False
    ) -> ExecutionResult:
        """Git checkout/switch branch"""
        if create:
            return await self.terminal_exec(f"git checkout -b {branch_or_ref}")
        return await self.terminal_exec(f"git checkout {branch_or_ref}")

    async def git_stash(
        self, pop: bool = False, list: bool = False, clear: bool = False
    ) -> ExecutionResult:
        """Git stash operations"""
        if pop:
            return await self.terminal_exec("git stash pop")
        if list:
            return await self.terminal_exec("git stash list")
        if clear:
            return await self.terminal_exec("git stash clear")
        return await self.terminal_exec("git stash push")

    async def file_copy(
        self, source: str, destination: str, overwrite: bool = False
    ) -> ExecutionResult:
        """Copy file or directory"""
        flag = "/Y" if os.name == "nt" else "-f" if overwrite else ""
        return await self.terminal_exec(
            f'copy {flag} "{source}" "{destination}"'
            if os.name == "nt"
            else f"cp {'-f' if overwrite else ''} '{source}' '{destination}'"
        )

    async def file_move(
        self, source: str, destination: str, overwrite: bool = False
    ) -> ExecutionResult:
        """Move file or directory"""
        return await self.terminal_exec(
            f'move /Y "{source}" "{destination}"'
            if os.name == "nt"
            else f"mv {'-f' if overwrite else ''} '{source}' '{destination}'"
        )

    async def code_explain(
        self, code: str = None, file_path: str = None
    ) -> ExecutionResult:
        """Explain code - returns code content for AI analysis"""
        if file_path:
            return await self.file_read(file_path)
        return ExecutionResult(success=True, output=code or "")

    async def code_search_symbol(
        self, symbol: str, path: str = None
    ) -> ExecutionResult:
        """Search for symbol in codebase"""
        search_path = path or str(self.workspace_root)
        return await self.file_grep(pattern=symbol, path=search_path)

    async def plan_complex_task(self, task: str) -> ExecutionResult:
        """Plan a complex task - returns task description for AI planning"""
        return ExecutionResult(
            success=True,
            output=f"Task: {task}\n\nUse terminal tools to execute step by step.",
        )

    async def get_suggestions(self, context: str = None) -> ExecutionResult:
        """Get command suggestions based on context"""
        suggestions = [
            "ls -la - 列出目录内容",
            "git status - 查看Git状态",
            "cat <file> - 查看文件内容",
            "grep -r 'pattern' . - 搜索文件内容",
        ]
        return ExecutionResult(success=True, output="\n".join(suggestions))

    # ==================== 上下文和工具 ====================

    async def load_project_context(self) -> Dict:
        """加载项目上下文"""
        context = {"files": [], "instructions": "", "commands": {}}

        for cf in ["CLAUDE.md", "claude.md", ".claude.md", "PROJECT.md"]:
            path = self.workspace_root / cf
            if path.exists():
                result = await self.file_read(str(path))
                if result.success:
                    context["instructions"] = result.output
                    context["context_file"] = cf
                    break

        git_dir = self.workspace_root / ".git"
        context["is_git_repo"] = git_dir.exists()

        return context

    def get_tools_list(self) -> List[str]:
        """获取工具列表"""
        return self._tool_registry.list_tools()


# 全局实例
_terminal_ultra_instance = None


def get_terminal_ultra(workspace_root: str = None) -> TerminalUltra:
    global _terminal_ultra_instance
    if _terminal_ultra_instance is None:
        _terminal_ultra_instance = TerminalUltra(workspace_root)
    return _terminal_ultra_instance
