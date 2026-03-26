#!/usr/bin/env python3
"""
弥亚智能代理系统 (Miya Agent)
真正的 ReAct (Reasoning + Acting) 循环
让弥亚像人类一样思考-执行-观察-修正
"""

import asyncio
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AgentStep:
    """代理步骤"""

    step: int
    thought: str  # 思考
    action: str  # 执行的动作
    observation: str  # 观察结果
    is_final: bool = False


class MiyaAgent:
    """
    弥亚智能代理

    ReAct 循环:
    1. Thought - 思考当前情况
    2. Action - 执行动作
    3. Observation - 观察结果
    4. 重复直到完成任务
    """

    def __init__(self):
        self.max_iterations = 5
        self.history: List[AgentStep] = []

    async def run(self, user_request: str) -> str:
        """
        运行代理处理用户请求

        Args:
            user_request: 用户请求

        Returns:
            最终结果
        """
        self.history = []
        current_step = 0

        # 步骤1: 理解任务
        current_step += 1
        thought = f"用户说: '{user_request}'。我需要理解这个任务并执行它。"

        # 步骤2: 分析意图
        intent_analysis = self._analyze_intent(user_request)
        thought += f"\n分析: 这是一个'{intent_analysis['type']}'任务，需要执行'{intent_analysis['action']}'"

        self.history.append(
            AgentStep(
                step=current_step,
                thought=thought,
                action="分析用户意图",
                observation=f"意图类型: {intent_analysis['type']}, 执行动作: {intent_analysis['action']}",
            )
        )

        # 步骤3: 执行
        result = await self._execute_intent(user_request, intent_analysis)

        current_step += 1
        self.history.append(
            AgentStep(
                step=current_step,
                thought="执行完成，观察结果",
                action=intent_analysis["action"],
                observation=result[:500] if len(result) > 500 else result,
                is_final=True,
            )
        )

        # 返回结果
        return self._format_response(user_request, intent_analysis, result)

    def _analyze_intent(self, request: str) -> Dict:
        """分析用户意图"""
        r = request.lower()

        # IP地址
        if any(kw in r for kw in ["ip", "ip地址", "网络地址"]):
            return {"type": "查询", "action": "ipconfig", "detail": "查看IP配置"}

        # 打开应用
        if any(kw in r for kw in ["打开", "启动", "运行", "开"]):
            if "火狐" in request or "firefox" in r:
                return {"type": "打开应用", "action": "firefox", "detail": "启动火狐"}
            if "浏览器" in request:
                return {
                    "type": "打开应用",
                    "action": "start chrome",
                    "detail": "启动浏览器",
                }
            if "微信" in request:
                return {"type": "打开应用", "action": "wechat", "detail": "启动微信"}
            if "qq" in r:
                return {"type": "打开应用", "action": "qq", "detail": "启动QQ"}

        # 文件操作
        if any(kw in r for kw in ["看看", "查看", "显示"]):
            if "项目" in request or "程序" in request:
                return {"type": "分析", "action": "analyze", "detail": "分析项目"}
            if "目录" in request:
                return {"type": "查看", "action": "tree", "detail": "查看目录"}
            return {"type": "读取", "action": "read", "detail": "读取文件"}

        # 代码执行
        if any(kw in r for kw in ["运行代码", "执行代码", "python"]):
            return {"type": "执行", "action": "python", "detail": "运行Python代码"}

        # 帮助
        if any(kw in r for kw in ["帮助", "help", "你能做什么"]):
            return {"type": "帮助", "action": "help", "detail": "显示帮助"}

        # 默认: 尝试作为命令执行
        return {"type": "执行", "action": "exec", "detail": request}

    async def _execute_intent(self, request: str, intent: Dict) -> str:
        """执行意图"""
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()

        action = intent["action"]

        try:
            if action == "ipconfig":
                result = await terminal.terminal_exec("ipconfig")
                return result.output if result.success else f"错误: {result.error}"

            elif action == "firefox":
                result = await terminal.terminal_exec("start firefox")
                if result.success:
                    return "火狐浏览器已启动"
                # 尝试其他方式
                result = await terminal.terminal_exec(
                    '"C:\\Program Files\\Mozilla Firefox\\firefox.exe"'
                )
                return (
                    result.output if result.success else f"已尝试启动: {result.error}"
                )

            elif action == "chrome":
                result = await terminal.terminal_exec("start chrome")
                return result.output if result.success else f"错误: {result.error}"

            elif action == "wechat":
                result = await terminal.terminal_exec("start wechat")
                return result.output if result.success else f"错误: {result.error}"

            elif action == "qq":
                result = await terminal.terminal_exec("start qq")
                return result.output if result.success else f"错误: {result.error}"

            elif action == "analyze":
                result = await terminal.project_analyze(".")
                return result.output if result.success else f"错误: {result.error}"

            elif action == "tree":
                result = await terminal.directory_tree(".", max_depth=2)
                return result.output if result.success else f"错误: {result.error}"

            elif action == "python":
                # 提取代码
                code = self._extract_code(request)
                result = await terminal.code_execute(code, "python")
                return result.output if result.success else f"错误: {result.error}"

            elif action == "help":
                return self._get_help()

            else:
                # 直接执行命令
                cmd = action if action != "exec" else request
                result = await terminal.terminal_exec(cmd)
                return result.output if result.success else f"错误: {result.error}"

        except Exception as e:
            return f"执行失败: {str(e)}"

    def _extract_code(self, text: str) -> str:
        """提取代码"""
        if "```" in text:
            match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 尝试提取 print
        match = re.search(r"print\([^)]+\)", text)
        if match:
            return match.group(0)

        # 移除关键词
        for kw in ["运行", "执行", "python", "代码"]:
            text = text.replace(kw, "")
        return text.strip() or 'print("hello")'

    def _format_response(self, request: str, intent: Dict, result: str) -> str:
        """格式化响应"""
        output = []

        output.append("=" * 50)
        output.append("【思考】")
        output.append("=" * 50)

        for step in self.history:
            output.append(f"\n步骤 {step.step}: {step.thought}")
            output.append(f"  → 执行: {step.action}")
            output.append(f"  → 观察: {step.observation[:100]}...")

        output.append("\n" + "=" * 50)
        output.append("【执行结果】")
        output.append("=" * 50)

        # 简化结果展示
        if intent["action"] == "ipconfig":
            # 提取关键IP
            lines = result.split("\n")
            for line in lines:
                if "IPv4" in line and "192.168" in line:
                    output.append(f"\n{line.strip()}")
                elif "IPv4" in line and "10." in line:
                    output.append(f"\n{line.strip()}")
                elif "IPv4" in line and "172." in line:
                    output.append(f"\n{line.strip()}")
        else:
            # 截断过长输出
            if len(result) > 1000:
                output.append(f"\n{result[:1000]}\n... (结果已截断)")
            else:
                output.append(f"\n{result}")

        return "\n".join(output)

    def _get_help(self) -> str:
        """帮助信息"""
        return """
╔════════════════════════════════════════════════════════════╗
║              弥娅智能代理 - 可执行操作              ║
╠════════════════════════════════════════════════════════════╣
║ 功能:                                                    ║
║   • 查看IP地址: "我的IP是多少"                       ║
║   • 打开应用: "打开微信" "打开火狐"                  ║
║   • 查看项目: "看看项目结构"                         ║
║   • 执行代码: "运行 print('hello')"                ║
║   • 目录操作: "查看当前目录"                         ║
╚════════════════════════════════════════════════════════════╝
"""


# 全局实例
_agent_instance = None


def get_miya_agent() -> MiyaAgent:
    """获取弥亚代理实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MiyaAgent()
    return _agent_instance
