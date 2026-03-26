#!/usr/bin/env python3
"""
弥亚终端思考链系统
让弥亚能够自主多步骤思考和执行任务
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ThinkStep:
    """思考步骤"""

    step: int
    thought: str  # 思考内容
    action: str = ""  # 执行的动作
    tool_call: str = ""  # 工具调用
    result: str = ""  # 执行结果
    is_final: bool = False


class TerminalThinkChain:
    """
    终端思考链系统

    类似于 opencode 的思考-执行循环：
    1. 理解用户意图
    2. 制定执行计划
    3. 逐步执行
    4. 汇总结果
    """

    def __init__(self, terminal_instance=None):
        self.terminal = terminal_instance
        self.steps: List[ThinkStep] = []
        self.max_steps = 10  # 最大思考步骤

    async def think_and_execute(self, user_input: str) -> str:
        """
        思考并执行用户请求

        Args:
            user_input: 用户输入

        Returns:
            最终结果
        """
        self.steps = []

        # 步骤1: 理解意图
        step1 = ThinkStep(
            step=1, thought=f"用户说: '{user_input}'。我需要理解用户的真实意图。"
        )
        self.steps.append(step1)

        # 步骤2: 分析任务类型
        task_analysis = self._analyze_task(user_input)
        step2 = ThinkStep(
            step=2,
            thought=f"这是一个{task_analysis['type']}任务，需要{task_analysis['action_count']}个步骤。",
            action=f"任务类型: {task_analysis['type']}",
        )
        self.steps.append(step2)

        # 步骤3: 执行计划
        actions = task_analysis["actions"]

        results = []
        for i, action in enumerate(actions):
            step_num = i + 3

            # 思考
            thought = f"步骤{step_num}: {action['description']}"

            # 执行
            result = await self._execute_action(action)

            step = ThinkStep(
                step=step_num,
                thought=thought,
                action=action["description"],
                tool_call=action.get("tool_call", ""),
                result=result,
                is_final=(i == len(actions) - 1),
            )
            self.steps.append(step)

            results.append(f"【{action['name']}】\n{result}")

            # 检查是否需要终止
            if "error" in result.lower() or "失败" in result:
                break

        # 最终总结
        final_result = self._format_results(user_input, results)

        return final_result

    def _analyze_task(self, user_input: str) -> Dict[str, Any]:
        """分析任务类型和需要的动作"""
        input_lower = user_input.lower()

        actions = []

        # 项目分析类
        if any(
            kw in input_lower
            for kw in ["项目", "程序", "项目结构", "程序结构", "analyze", "分析"]
        ):
            if any(kw in input_lower for kw in ["看看", "查看", "显示", "看看"]):
                actions.append(
                    {
                        "name": "project_analyze",
                        "description": "分析项目结构",
                        "tool": "project_analyze",
                        "params": {"path": "."},
                    }
                )
            else:
                # 默认用项目分析
                actions.append(
                    {
                        "name": "project_analyze",
                        "description": "分析项目",
                        "tool": "project_analyze",
                        "params": {"path": "."},
                    }
                )

        # 目录树类
        elif any(
            kw in input_lower for kw in ["目录", "文件夹", "结构", "tree", "dir", "ls"]
        ):
            actions.append(
                {
                    "name": "directory_tree",
                    "description": "查看目录树",
                    "tool": "directory_tree",
                    "params": {"dir_path": ".", "max_depth": 3},
                }
            )

        # 执行命令类
        elif any(kw in input_lower for kw in ["运行", "执行", "跑", "启动", "run"]):
            actions.append(
                {
                    "name": "terminal_exec",
                    "description": "执行终端命令",
                    "tool": "terminal_exec",
                    "params": {"command": self._extract_command(user_input)},
                }
            )

        # 代码执行类
        elif any(
            kw in input_lower for kw in ["代码", "python", "script", "code_execute"]
        ):
            code = self._extract_code(user_input)
            actions.append(
                {
                    "name": "code_execute",
                    "description": "执行代码",
                    "tool": "code_execute",
                    "params": {"code": code, "language": "python"},
                }
            )

        # 创建文件类
        elif any(kw in input_lower for kw in ["创建", "新建", "写一个", "write"]):
            actions.append(
                {
                    "name": "file_write",
                    "description": "创建文件",
                    "tool": "file_write",
                    "params": self._extract_file_info(user_input),
                }
            )

        # 帮助类
        elif any(kw in input_lower for kw in ["帮助", "help", "你能做什么", "功能"]):
            actions.append(
                {
                    "name": "help",
                    "description": "显示帮助信息",
                    "tool": "help",
                    "params": {},
                }
            )

        # 未知任务 - 尝试执行命令
        if not actions:
            actions.append(
                {
                    "name": "terminal_exec",
                    "description": "执行用户命令",
                    "tool": "terminal_exec",
                    "params": {"command": user_input},
                }
            )

        return {
            "type": self._get_task_type(actions),
            "actions": actions,
            "action_count": len(actions),
        }

    def _get_task_type(self, actions: List[Dict]) -> str:
        """获取任务类型"""
        if len(actions) > 1:
            return "复合"
        tool = actions[0]["tool"] if actions else "unknown"
        types = {
            "terminal_exec": "命令执行",
            "file_read": "文件读取",
            "file_write": "文件写入",
            "directory_tree": "目录查看",
            "project_analyze": "项目分析",
            "code_execute": "代码执行",
            "help": "帮助查询",
        }
        return types.get(tool, "通用")

    async def _execute_action(self, action: Dict) -> str:
        """执行单个动作"""
        from core.terminal_ultra import get_terminal_ultra

        tool_name = action.get("tool", "")
        params = action.get("params", {})

        try:
            terminal = get_terminal_ultra()

            if tool_name == "terminal_exec":
                result = await terminal.terminal_exec(
                    params.get("command", ""), timeout=params.get("timeout", 60)
                )
                return result.output if result.success else f"错误: {result.error}"

            elif tool_name == "file_read":
                result = await terminal.file_read(
                    params.get("file_path", ""),
                    offset=params.get("offset", 0),
                    limit=params.get("limit", 100),
                )
                return result.output if result.success else f"错误: {result.error}"

            elif tool_name == "file_write":
                result = await terminal.file_write(
                    params.get("file_path", ""), params.get("content", "")
                )
                return result.output if result.success else f"错误: {result.error}"

            elif tool_name == "directory_tree":
                result = await terminal.directory_tree(
                    params.get("dir_path", "."), params.get("max_depth", 3)
                )
                return result.output if result.success else f"错误: {result.error}"

            elif tool_name == "project_analyze":
                result = await terminal.project_analyze(params.get("path", "."))
                return result.output if result.success else f"错误: {result.error}"

            elif tool_name == "code_execute":
                result = await terminal.code_execute(
                    params.get("code", ""),
                    params.get("language", "python"),
                    params.get("timeout", 30),
                )
                return result.output if result.success else f"错误: {result.error}"

            elif tool_name == "help":
                return self._get_help_text()

            else:
                return f"未知工具: {tool_name}"

        except Exception as e:
            return f"执行失败: {str(e)}"

    def _extract_command(self, user_input: str) -> str:
        """提取命令"""
        # 移除常见的动词
        for prefix in ["运行 ", "执行 ", "跑 ", "启动 "]:
            if user_input.startswith(prefix):
                return user_input[len(prefix) :].strip()
        return user_input

    def _extract_code(self, user_input: str) -> str:
        """提取代码"""
        # 尝试提取代码块
        if "```" in user_input:
            match = re.search(r"```(?:\w+)?\n(.*?)```", user_input, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 尝试提取 print() 或其他代码
        match = re.search(r"print\([^)]+\)", user_input)
        if match:
            return match.group(0)

        # 默认返回整个输入
        return user_input

    def _extract_file_info(self, user_input: str) -> Dict:
        """提取文件信息"""
        # 简单实现 - 后续可以改进
        return {"file_path": "new_file.txt", "content": user_input}

    def _format_results(self, original_request: str, results: List[str]) -> str:
        """格式化结果"""
        output = []
        output.append("=" * 50)
        output.append(f"【思考过程】")
        output.append("=" * 50)

        for step in self.steps:
            output.append(f"\n📍 步骤 {step.step}: {step.thought}")
            if step.action:
                output.append(f"   执行: {step.action}")
            if step.result:
                # 限制结果长度
                result_preview = (
                    step.result[:500] + "..." if len(step.result) > 500 else step.result
                )
                output.append(f"   结果: {result_preview}")

        output.append("\n" + "=" * 50)
        output.append("【执行结果】")
        output.append("=" * 50)

        for i, result in enumerate(results, 1):
            output.append(f"\n{i}. {result}")

        return "\n".join(output)

    def _get_help_text(self) -> str:
        """获取帮助文本"""
        return """
╔════════════════════════════════════════════════════════════╗
║              弥娅超级终端 - 可用功能                      ║
╠════════════════════════════════════════════════════════════╣
║ 查看项目:                                                  ║
║   - "看看项目结构" → 分析整个项目                        ║
║   - "查看目录" → 显示目录树                              ║
║                                                            ║
║ 执行命令:                                                  ║
║   - "运行 python test.py" → 执行命令                    ║
║   - "安装 npm" → 执行安装命令                           ║
║                                                            ║
║ 代码执行:                                                  ║
║   - "运行代码 print('hello')" → 直接运行Python         ║
║                                                            ║
║ 文件操作:                                                  ║
║   - "查看 xxx.py" → 读取文件内容                        ║
║   - "创建 xxx.txt 内容是..." → 创建文件                 ║
║                                                            ║
║ 项目分析:                                                  ║
║   - "分析这个项目" → 显示项目统计                        ║
╚════════════════════════════════════════════════════════════╝
"""

    def get_thoughts_summary(self) -> str:
        """获取思考过程摘要"""
        if not self.steps:
            return ""

        lines = []
        for step in self.steps:
            lines.append(f"步骤{step.step}: {step.thought}")

        return "\n".join(lines)


# 全局实例
_think_chain_instance = None


def get_think_chain() -> TerminalThinkChain:
    """获取思考链实例"""
    global _think_chain_instance
    if _think_chain_instance is None:
        _think_chain_instance = TerminalThinkChain()
    return _think_chain_instance
