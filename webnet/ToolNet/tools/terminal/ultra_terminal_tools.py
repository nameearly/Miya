"""
弥娅超级终端工具集成
将 TerminalUltra 的能力集成到 ToolNet 系统中
"""

import asyncio
from typing import Dict, Any, Optional
from webnet.ToolNet.base import BaseTool, ToolContext


class TerminalExecTool(BaseTool):
    """终端命令执行工具 - 完全终端掌控"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "terminal_exec",
            "description": """执行终端命令。这是弥娅完全掌控终端的核心工具。
            
当用户请求执行系统命令、安装包、运行脚本等操作时使用此工具。
支持 Windows、Linux、MacOS 等平台。
            
示例:
- 执行 Python 脚本: python script.py
- 查看文件列表: ls -la
- 安装 npm 包: npm install
- 启动服务: npm run dev""",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的终端命令"},
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间(秒)，默认60",
                        "default": 60,
                    },
                    "cwd": {"type": "string", "description": "工作目录（可选）"},
                },
                "required": ["command"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        command = args.get("command", "")
        timeout = args.get("timeout", 60)
        cwd = args.get("cwd")

        if not command:
            return "❌ 缺少命令参数"

        result = await terminal.terminal_exec(command, timeout=timeout, cwd=cwd)

        if result.success:
            output = result.output or "命令执行成功（无输出）"
            if result.warnings:
                output += f"\n⚠️ {'; '.join(result.warnings)}"
            return output
        else:
            error_msg = result.error or f"命令执行失败（退出码: {result.exit_code}）"
            return f"❌ {error_msg}"


class FileReadTool(BaseTool):
    """文件读取工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "file_read",
            "description": """读取文件内容。

当用户请求查看文件内容、代码、配置等时使用此工具。
支持大文件分块读取，可以指定起始行和读取行数。

示例:
- 读取 Python 文件: 查看 src/main.py
- 分块读取: 读取 file.txt 从第100行开始共50行
- 查看配置文件: 读取 config/app.json""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径（绝对路径或相对于当前工作目录）",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "起始行号（从0开始），默认0",
                        "default": 0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "读取行数，默认读取全部",
                        "default": 100,
                    },
                },
                "required": ["file_path"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        file_path = args.get("file_path", "")
        offset = args.get("offset", 0)
        limit = args.get("limit", 100)

        if not file_path:
            return "❌ 缺少文件路径参数"

        result = await terminal.file_read(file_path, offset=offset, limit=limit)

        if result.success:
            return result.output
        else:
            return f"❌ {result.error}"


class FileWriteTool(BaseTool):
    """文件写入工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "file_write",
            "description": """创建或写入文件。

当用户请求创建新文件、写代码、保存配置等操作时使用此工具。
会自动创建父目录。

示例:
- 创建 Python 文件: 写入 src/utils.py 内容为...
- 创建配置文件: 写入 config.json 内容为...
- 写入 HTML: 写入 index.html 内容为...""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
                },
                "required": ["file_path", "content"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        file_path = args.get("file_path", "")
        content = args.get("content", "")

        if not file_path:
            return "❌ 缺少文件路径参数"

        if not content:
            return "❌ 缺少文件内容参数"

        result = await terminal.file_write(file_path, content)

        if result.success:
            return f"✅ {result.output}"
        else:
            return f"❌ {result.error}"


class FileEditTool(BaseTool):
    """文件编辑工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "file_edit",
            "description": """编辑现有文件。

当用户请求修改文件内容时使用此工具。
使用旧字符串匹配来定位要修改的内容。

示例:
- 修改函数名: 修改 src/main.py 中的 "def old_func" 为 "def new_func"
- 修改配置: 修改 config.json 中的 "old_value" 为 "new_value"
- 替换所有: 替换所有 "foo" 为 "bar" """,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "old_string": {
                        "type": "string",
                        "description": "要替换的旧内容（必须精确匹配）",
                    },
                    "new_string": {"type": "string", "description": "替换后的新内容"},
                    "replace_all": {
                        "type": "boolean",
                        "description": "是否替换所有匹配项，默认false只替换第一个",
                        "default": False,
                    },
                },
                "required": ["file_path", "old_string", "new_string"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        file_path = args.get("file_path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")
        replace_all = args.get("replace_all", False)

        if not file_path or not old_string:
            return "❌ 缺少必要参数"

        result = await terminal.file_edit(
            file_path, old_string, new_string, replace_all
        )

        if result.success:
            return f"✅ {result.output}"
        else:
            return f"❌ {result.error}"


class DirectoryTreeTool(BaseTool):
    """目录树工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "directory_tree",
            "description": """查看目录树结构。

当用户请求查看项目结构、目录布局等时使用此工具。
可以设置最大显示深度。

示例:
- 查看项目结构: 查看当前目录
- 查看源码目录: 查看 src 目录
- 浅层查看: 查看 . 深度 2""",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "目录路径，默认当前目录",
                        "default": ".",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "最大显示深度，默认3",
                        "default": 3,
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "是否包含隐藏文件",
                        "default": False,
                    },
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        dir_path = args.get("dir_path", ".")
        max_depth = args.get("max_depth", 3)
        include_hidden = args.get("include_hidden", False)

        result = await terminal.directory_tree(dir_path, max_depth, include_hidden)

        if result.success:
            return result.output
        else:
            return f"❌ {result.error}"


class CodeExecuteTool(BaseTool):
    """代码执行工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "code_execute",
            "description": """执行代码。

当用户请求运行代码、测试脚本、执行算法等时使用此工具。
支持 Python 和 JavaScript。

示例:
- 运行 Python: 执行 python 代码 print('Hello')
- 运行 JS: 执行 javascript 代码 console.log('Hello')
- 执行脚本: 运行 python 代码 import sys; print(sys.version)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的代码"},
                    "language": {
                        "type": "string",
                        "description": "语言: python 或 javascript，默认 python",
                        "default": "python",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间(秒)，默认30",
                        "default": 30,
                    },
                },
                "required": ["code"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        code = args.get("code", "")
        language = args.get("language", "python")
        timeout = args.get("timeout", 30)

        if not code:
            return "❌ 缺少代码参数"

        result = await terminal.code_execute(code, language, timeout)

        if result.success:
            output = result.output or "代码执行成功（无输出）"
            return f"✅ {output}"
        else:
            return f"❌ {result.error}"


class ProjectAnalyzeTool(BaseTool):
    """项目分析工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "project_analyze",
            "description": """分析项目结构。

当用户请求了解项目概况、查看语言分布、统计文件等时使用此工具。
会分析项目的文件类型、语言分布、大小等信息。

示例:
- 分析当前项目: 分析项目
- 分析指定目录: 分析 src
- 查看项目统计: 分析""",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "项目路径，默认当前目录",
                        "default": ".",
                    }
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        path = args.get("path", ".")

        result = await terminal.project_analyze(path)

        if result.success:
            return result.output
        else:
            return f"❌ {result.error}"


class FileDeleteTool(BaseTool):
    """文件删除工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "file_delete",
            "description": """删除文件或目录。

当用户请求删除文件时使用此工具。
目录删除需要设置 recursive=true。

示例:
- 删除文件: 删除 temp.txt
- 删除目录: 删除 temp_dir recursive=true""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要删除的文件或目录路径",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归删除目录",
                        "default": False,
                    },
                },
                "required": ["file_path"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        file_path = args.get("file_path", "")
        recursive = args.get("recursive", False)

        if not file_path:
            return "❌ 缺少文件路径参数"

        result = await terminal.file_delete(file_path, recursive)

        if result.success:
            return f"✅ {result.output}"
        else:
            return f"❌ {result.error}"


# ==================== Git 工具 ====================


class GitStatusTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_status",
            "description": "查看 Git 仓库状态",
            "parameters": {
                "type": "object",
                "properties": {"short": {"type": "boolean", "default": False}},
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_status(short=args.get("short", False))
        return result.output if result.success else f"❌ {result.error}"


class GitDiffTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_diff",
            "description": "查看文件差异",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "staged": {"type": "boolean", "default": False},
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_diff(
            args.get("file_path"), args.get("staged", False)
        )
        return result.output if result.success else f"❌ {result.error}"


class GitLogTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_log",
            "description": "查看提交历史",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "default": 10},
                    "file_path": {"type": "string"},
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_log(args.get("count", 10), args.get("file_path"))
        return result.output if result.success else f"❌ {result.error}"


class GitBranchTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_branch",
            "description": "查看 Git 分支",
            "parameters": {
                "type": "object",
                "properties": {"all": {"type": "boolean", "default": False}},
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_branch(args.get("all", False))
        return result.output if result.success else f"❌ {result.error}"


class GitCommitTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_commit",
            "description": "提交更改",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "amend": {"type": "boolean", "default": False},
                },
                "required": ["message"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_commit(
            args.get("message", ""), args.get("amend", False)
        )
        return f"✅ {result.output}" if result.success else f"❌ {result.error}"


class GitAddTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_add",
            "description": "添加文件到暂存区",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}},
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_add(args.get("path", "."))
        return f"✅ {result.output}" if result.success else f"❌ {result.error}"


class GitPushTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_push",
            "description": "推送到远程",
            "parameters": {
                "type": "object",
                "properties": {
                    "remote": {"type": "string", "default": "origin"},
                    "branch": {"type": "string"},
                    "force": {"type": "boolean", "default": False},
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_push(
            args.get("remote", "origin"), args.get("branch"), args.get("force", False)
        )
        return f"✅ {result.output}" if result.success else f"❌ {result.error}"


class GitPullTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_pull",
            "description": "从远程拉取",
            "parameters": {
                "type": "object",
                "properties": {
                    "remote": {"type": "string", "default": "origin"},
                    "branch": {"type": "string"},
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_pull(
            args.get("remote", "origin"), args.get("branch")
        )
        return f"✅ {result.output}" if result.success else f"❌ {result.error}"


class GitCheckoutTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_checkout",
            "description": "切换分支",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {"type": "string"},
                    "create": {"type": "boolean", "default": False},
                },
                "required": ["branch"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.git_checkout(
            args.get("branch", ""), args.get("create", False)
        )
        return f"✅ {result.output}" if result.success else f"❌ {result.error}"


class GitStashTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "git_stash",
            "description": "暂存工作区",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["push", "pop", "list", "clear"],
                    },
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        action = args.get("action", "push")
        if action == "pop":
            result = await terminal.git_stash(pop=True)
        elif action == "list":
            result = await terminal.git_stash(list=True)
        elif action == "clear":
            result = await terminal.git_stash(clear=True)
        else:
            result = await terminal.git_stash()
        return f"✅ {result.output}" if result.success else f"❌ {result.error}"


# ==================== 搜索工具 ====================


class FileGrepTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "file_grep",
            "description": "搜索文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                    "include": {"type": "string"},
                    "recursive": {"type": "boolean", "default": True},
                },
                "required": ["pattern"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.file_grep(
            args.get("pattern", ""),
            args.get("path", "."),
            args.get("recursive", True),
            include=args.get("include"),
        )
        return result.output if result.success else f"❌ {result.error}"


class FileGlobTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "file_glob",
            "description": "查找文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                    "recursive": {"type": "boolean", "default": True},
                },
                "required": ["pattern"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.file_glob(
            args.get("pattern", ""), args.get("path", "."), args.get("recursive", True)
        )
        return result.output if result.success else f"❌ {result.error}"


# ==================== 代码理解工具 ====================


class CodeExplainTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "code_explain",
            "description": "分析解释代码",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "code": {"type": "string"},
                },
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.code_explain(args.get("code"), args.get("file_path"))
        return result.output if result.success else f"❌ {result.error}"


class CodeSearchSymbolTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "code_search_symbol",
            "description": "搜索代码符号定义和引用",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                },
                "required": ["symbol"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.code_search_symbol(
            args.get("symbol", ""), args.get("path", ".")
        )
        return result.output if result.success else f"❌ {result.error}"


# ==================== 智能工具 ====================


class ProjectContextTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "project_context",
            "description": "加载项目上下文 (CLAUDE.md 类似)",
            "parameters": {"type": "object", "properties": {}},
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.load_project_context()
        lines = ["=== 项目上下文 ==="]
        if result.get("context_file"):
            lines.append(f"上下文文件: {result['context_file']}")
            lines.append(f"\n{result.get('instructions', '')[:500]}")
        lines.append(f"\nGit 仓库: {'是' if result.get('is_git_repo') else '否'}")
        if result.get("config_file"):
            lines.append(f"配置文件: {result['config_file']}")
        return "\n".join(lines)


class TaskPlanTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "task_plan",
            "description": "分析复杂任务并生成执行计划",
            "parameters": {
                "type": "object",
                "properties": {"task": {"type": "string"}},
                "required": ["task"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        result = await terminal.plan_complex_task(args.get("task", ""))
        lines = [
            f"=== 任务计划: {result['task']} ===",
            f"预估步骤: {result['estimated_steps']}",
        ]
        for i, step in enumerate(result["steps"], 1):
            lines.append(f"{i}. {step['action']} (工具: {step['tool']})")
        return "\n".join(lines)


class SuggestionsTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "suggestions",
            "description": "根据当前上下文提供智能建议",
            "parameters": {"type": "object", "properties": {}},
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()
        suggestions = await terminal.get_suggestions()
        if not suggestions:
            return "暂无建议"
        return "💡 智能建议:\n" + "\n".join(f"- {s}" for s in suggestions)


# ==================== Agent 工具 ====================


class CodeExplorerAgentTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "code_explorer_agent",
            "description": "代码探索Agent - 分析项目结构、搜索符号定义和引用",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "explore",
                            "find_symbol",
                            "find_definitions",
                            "find_references",
                            "analyze_structure",
                        ],
                    },
                    "target": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                },
                "required": ["action", "target"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import call_agent

        result = await call_agent("code_explorer", args)
        return result.output if result.success else f"❌ {result.error}"


class CodeReviewerAgentTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "code_reviewer_agent",
            "description": "代码审查Agent - 代码质量、bug检测、安全扫描",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "review",
                            "find_bugs",
                            "check_errors",
                            "analyze_quality",
                            "security_scan",
                        ],
                    },
                    "target": {"type": "string"},
                },
                "required": ["action", "target"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import call_agent

        result = await call_agent("code_reviewer", args)
        return result.output if result.success else f"❌ {result.error}"


class CodeArchitectAgentTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "code_architect_agent",
            "description": "代码架构Agent - 架构设计、模块规划、重构指导",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "design",
                            "plan_modules",
                            "refactor",
                            "analyze_dependencies",
                            "structure",
                        ],
                    },
                    "target": {"type": "string"},
                    "requirements": {"type": "string"},
                },
                "required": ["action", "target"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import call_agent

        result = await call_agent("code_architect", args)
        return result.output if result.success else f"❌ {result.error}"


class TerminalAgentTool(BaseTool):
    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "terminal_agent",
            "description": "终端Agent - 根据任务自动选择合适的子Agent执行",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "任务描述"},
                },
                "required": ["task"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        from core.terminal_ultra import execute_terminal_agent

        result = await execute_terminal_agent(args.get("task", ""))
        return result.output if result.success else f"❌ {result.error}"


# 导出所有工具
__all__ = [
    "TerminalExecTool",
    "FileReadTool",
    "FileWriteTool",
    "FileEditTool",
    "FileDeleteTool",
    "DirectoryTreeTool",
    "CodeExecuteTool",
    "ProjectAnalyzeTool",
    # Git 工具
    "GitStatusTool",
    "GitDiffTool",
    "GitLogTool",
    "GitBranchTool",
    "GitCommitTool",
    "GitAddTool",
    "GitPushTool",
    "GitPullTool",
    "GitCheckoutTool",
    "GitStashTool",
    # 搜索工具
    "FileGrepTool",
    "FileGlobTool",
    # 代码理解工具
    "CodeExplainTool",
    "CodeSearchSymbolTool",
    # 智能工具
    "ProjectContextTool",
    "TaskPlanTool",
    "SuggestionsTool",
    # Agent 工具
    "CodeExplorerAgentTool",
    "CodeReviewerAgentTool",
    "CodeArchitectAgentTool",
    "TerminalAgentTool",
]
