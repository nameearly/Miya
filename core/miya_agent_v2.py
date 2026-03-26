#!/usr/bin/env python3
"""
弥亚智能代理系统 V2 - 真正的 ReAct 循环
具备:
- 真正的思考-执行-观察-推理循环
- 任务完成感知
- 自我纠错能力
- 适应性执行
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class AgentThought:
    """思考"""

    reasoning: str  # 推理过程
    action: str  # 执行的动作
    observation: str  # 观察结果
    evaluation: str  # 评估结果 (成功/失败/需要重试)
    is_complete: bool  # 任务是否完成


class MiyaAgentV2:
    """
    弥亚智能代理 V2 - 真正的 ReAct 循环

    与 Claude Code / opencode 类似的架构:
    1. Reasoning - 深度思考当前状态
    2. Acting - 执行动作
    3. Observing - 观察结果
    4. Evaluating - 评估是否完成
    5. 如需继续,回到步骤1
    """

    def __init__(self):
        self.max_iterations = 10
        self.thoughts: List[AgentThought] = []
        self.task_history: List[str] = []  # 执行过的动作历史

    async def run(self, user_request: str) -> str:
        """
        运行 ReAct 循环处理用户请求
        """
        self.thoughts = []
        self.task_history = []

        current_request = user_request
        is_complete = False
        iteration = 0

        # ReAct 循环
        while not is_complete and iteration < self.max_iterations:
            iteration += 1

            # 1. Reasoning - 深度思考
            thought = await self._reason(current_request, iteration)
            self.thoughts.append(thought)

            # 2. Acting - 执行动作
            if thought.action:
                result = await self._act(thought.action, current_request)
                thought.observation = result
                self.task_history.append(thought.action)

            # 3. Evaluating - 评估结果
            evaluation = await self._evaluate(
                current_request, thought.observation, thought.action
            )
            thought.evaluation = evaluation

            # 4. 检查是否完成
            if evaluation.get("is_complete", False):
                is_complete = True
                thought.is_complete = True
            elif evaluation.get("needs_retry", False):
                # 需要重试，调整策略
                current_request = evaluation.get("next_action", current_request)
            else:
                # 任务可能失败或无法完成
                is_complete = True

        # 生成最终响应
        return self._format_response(user_request)

    async def _reason(self, request: str, iteration: int) -> AgentThought:
        """推理步骤 - 分析当前状态和下一步"""

        # 上下文信息
        history_str = ", ".join(self.task_history[-3:]) if self.task_history else "无"

        # 分析当前状态
        analysis = self._analyze_request(request)

        # 决定下一步动作
        action = self._decide_action(request, analysis, iteration)

        reasoning = f"[迭代 {iteration}] 任务: '{request}' | 历史: {history_str}"
        reasoning += f"\n分析: {analysis['summary']}"
        reasoning += f"\n决定: {action['type']} - {action['detail']}"

        return AgentThought(
            reasoning=reasoning,
            action=action["command"],
            observation="",
            evaluation="",
            is_complete=False,
        )

    def _analyze_request(self, request: str) -> Dict:
        """分析用户请求"""
        r = request.lower()

        # 检测任务类型
        task_types = []

        if any(kw in r for kw in ["ip", "ip地址", "网络"]):
            task_types.append("network")
        if any(kw in r for kw in ["打开", "启动", "开", "运行"]):
            task_types.append("launch")
        if any(kw in r for kw in ["看看", "查看", "显示", "分析"]):
            task_types.append("view")
        if any(kw in r for kw in ["创建", "新建", "写"]):
            task_types.append("create")
        if any(kw in r for kw in ["删除", "remove"]):
            task_types.append("delete")
        if any(kw in r for kw in ["代码", "python", "执行"]):
            task_types.append("execute")

        # 检测目标
        target = self._extract_target(request)

        return {
            "types": task_types,
            "target": target,
            "summary": f"任务类型: {task_types}, 目标: {target}",
        }

    def _extract_target(self, request: str) -> str:
        """提取目标"""
        r = request.lower()

        # 应用
        apps = [
            "火狐",
            "firefox",
            "chrome",
            "浏览器",
            "微信",
            "wechat",
            "qq",
            "notepad",
            "记事本",
        ]
        for app in apps:
            if app in r:
                return app

        # 文件
        if ".py" in r or ".txt" in r or ".md" in r:
            # 尝试提取文件名
            words = request.split()
            for word in words:
                if "." in word:
                    return word

        return "unknown"

    def _decide_action(self, request: str, analysis: Dict, iteration: int) -> Dict:
        """决定下一步动作"""
        r = request.lower()
        target = analysis.get("target", "unknown")
        task_types = analysis.get("types", [])

        # 网络查询
        if "network" in task_types:
            return {"type": "execute", "detail": "查询网络配置", "command": "ipconfig"}

        # 启动应用
        if "launch" in task_types:
            if "firefox" in r or "火狐" in r:
                return {
                    "type": "launch",
                    "detail": "启动火狐",
                    "command": "start firefox",
                }
            if "chrome" in r or "浏览器" in r:
                return {
                    "type": "launch",
                    "detail": "启动浏览器",
                    "command": "start chrome",
                }
            if "微信" in r or "wechat" in r:
                return {
                    "type": "launch",
                    "detail": "启动微信",
                    "command": "start wechat",
                }
            if "qq" in r:
                return {"type": "launch", "detail": "启动QQ", "command": "start qq"}
            if "记事本" in r or "notepad" in r:
                return {"type": "launch", "detail": "启动记事本", "command": "notepad"}

        # 查看/分析
        if "view" in task_types:
            if "项目" in request or "程序" in request:
                return {
                    "type": "analyze",
                    "detail": "分析项目",
                    "command": "project_analyze",
                }
            if "目录" in request or "结构" in request:
                return {
                    "type": "view",
                    "detail": "查看目录",
                    "command": "directory_tree",
                }
            # 尝试作为文件读取
            current_target = analysis.get("target", "unknown")
            if current_target != "unknown" and "." in current_target:
                return {
                    "type": "read",
                    "detail": f"读取{current_target}",
                    "command": f"file_read:{current_target}",
                }

        # 执行代码
        if "execute" in task_types:
            code = self._extract_code(request)
            return {
                "type": "execute",
                "detail": "执行代码",
                "command": f"code_execute:{code}",
            }

        # 默认: 尝试作为shell命令执行
        return {"type": "execute", "detail": "执行命令", "command": f"shell:{request}"}

    def _extract_code(self, text: str) -> str:
        """提取代码"""
        if "```" in text:
            match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 提取 print(...)
        match = re.search(r"print\([^)]+\)", text)
        if match:
            return match.group(0)

        # 移除关键词
        for kw in ["运行", "执行", "python", "代码"]:
            text = text.replace(kw, "")
        return text.strip() or 'print("hello")'

    async def _act(self, action: str, original_request: str) -> str:
        """执行动作"""
        from core.terminal_ultra import get_terminal_ultra

        terminal = get_terminal_ultra()

        try:
            # 解析动作
            if action.startswith("file_read:"):
                path = action.split(":", 1)[1]
                result = await terminal.file_read(path)
                return result.output if result.success else f"失败: {result.error}"

            elif action.startswith("code_execute:"):
                code = action.split(":", 1)[1]
                result = await terminal.code_execute(code, "python")
                return result.output if result.success else f"失败: {result.error}"

            elif action.startswith("shell:"):
                cmd = action.split(":", 1)[1]
                result = await terminal.terminal_exec(cmd)
                return result.output if result.success else f"失败: {result.error}"

            elif action == "project_analyze":
                result = await terminal.project_analyze(".")
                return result.output if result.success else f"失败: {result.error}"

            elif action == "directory_tree":
                result = await terminal.directory_tree(".", max_depth=2)
                return result.output if result.success else f"失败: {result.error}"

            else:
                # 直接执行
                result = await terminal.terminal_exec(action)
                return result.output if result.success else f"失败: {result.error}"

        except Exception as e:
            return f"执行出错: {str(e)}"

    async def _evaluate(self, request: str, observation: str, action: str) -> Dict:
        """评估执行结果 - 关键！判断任务是否完成"""

        r = request.lower()

        # 成功的关键词
        success_indicators = [
            "已启动",
            "已打开",
            "启动",
            "打开",
            "success",
            "completed",
            "ipv4",
            "address",
            "ip地址",
            "config",
        ]

        # 失败的关键词
        failure_indicators = [
            "失败",
            "错误",
            "error",
            "not found",
            "找不到",
            "无法",
            "不是内部命令",
            "is not recognized",
            "exception",
            "Exception",
        ]

        obs_lower = observation.lower()

        # 检查是否失败
        is_failure = any(kw in obs_lower for kw in failure_indicators)

        # 检查是否成功
        is_success = any(kw in obs_lower for kw in success_indicators)

        # 特殊判断
        if "ip" in r or "地址" in r:
            # IP查询: 输出包含IP就算成功
            if "ipv4" in obs_lower or "." in observation:
                return {"is_complete": True, "result": "success"}
            elif is_failure:
                return {
                    "is_complete": False,
                    "needs_retry": True,
                    "next_action": "ipconfig /all",
                }

        if any(kw in r for kw in ["打开", "启动", "开"]):
            # 启动应用: 没有报错就算成功
            if is_failure:
                # 尝试其他方式
                return {"is_complete": False, "needs_retry": True}
            return {"is_complete": True, "result": "success"}

        if "看看" in r or "查看" in r or "分析" in r:
            # 查看任务: 有输出就算成功
            if len(observation) > 10:
                return {"is_complete": True, "result": "success"}
            elif is_failure:
                return {"is_complete": False, "needs_retry": True}

        if "执行" in r or "运行" in r:
            # 执行任务: 有输出或无错误就算成功
            if is_failure:
                return {
                    "is_complete": True,
                    "result": "completed_with_error",
                    "output": observation,
                }
            return {"is_complete": True, "result": "success"}

        # 默认: 有输出且没有明显错误就算成功
        if len(observation) > 5 and not is_failure:
            return {"is_complete": True, "result": "success"}
        elif is_failure:
            return {"is_complete": False, "needs_retry": True}

        return {"is_complete": True, "result": "unknown"}

    def _format_response(self, request: str) -> str:
        """格式化响应"""
        output = []

        output.append("=" * 60)
        output.append("【弥亚智能代理 V2 - ReAct 循环】")
        output.append("=" * 60)
        output.append(f"\n任务: {request}")
        output.append(f"迭代次数: {len(self.thoughts)}")

        output.append("\n" + "-" * 60)
        output.append("【思考 - 执行 - 观察 - 评估】")
        output.append("-" * 60)

        for i, thought in enumerate(self.thoughts, 1):
            output.append(f"\n▶ 第 {i} 轮:")
            output.append(f"  推理: {thought.reasoning[:100]}...")
            output.append(f"  动作: {thought.action}")
            output.append(
                f"  观察: {thought.observation[:150] if thought.observation else '(无)'}..."
            )
            output.append(
                f"  评估: {thought.evaluation.get('result', thought.evaluation) if isinstance(thought.evaluation, dict) else thought.evaluation}"
            )

        # 最终结果
        last_thought = self.thoughts[-1] if self.thoughts else None
        if last_thought:
            output.append("\n" + "=" * 60)
            output.append("【执行结果】")
            output.append("=" * 60)

            obs = last_thought.observation
            if len(obs) > 800:
                output.append(obs[:800] + "\n... (结果已截断)")
            else:
                output.append(obs)

        return "\n".join(output)


# 全局实例
_agent_v2_instance = None


def get_miya_agent_v2() -> MiyaAgentV2:
    """获取弥亚代理V2实例"""
    global _agent_v2_instance
    if _agent_v2_instance is None:
        _agent_v2_instance = MiyaAgentV2()
    return _agent_v2_instance
