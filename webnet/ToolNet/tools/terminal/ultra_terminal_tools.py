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
]
