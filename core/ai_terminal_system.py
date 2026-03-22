#!/usr/bin/env python3
"""
AI终端控制系统 - 让弥娅完全掌控终端
具备智能命令解析、任务规划、自动执行等完整能力
"""

import asyncio
import os
import sys
import json
import logging
import subprocess
import shlex
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
import queue
import platform

from core.terminal.base.types import (
    CommandIntent, CommandComplexity, CommandAnalysis,
    CommandResult, ExecutionContext, RiskLevel
)
from core.terminal.base.interfaces import (
    ICommandParser, ISafetyChecker, IExecutor, IKnowledgeBase
)

logger = logging.getLogger(__name__)

class AITerminalSystem:
    """AI终端控制系统"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"term_{int(time.time())}"
        self.working_directory = os.getcwd()
        self.command_history: List[Dict[str, Any]] = []
        self.system_info = self._collect_system_info()
        self.safe_mode = True  # 安全模式，危险命令需要确认
        self.learning_mode = True  # 学习模式，记录用户习惯
        
        # 初始化组件
        self.command_analyzer = CommandAnalyzer()
        self.task_planner = TaskPlanner()
        self.execution_engine = ExecutionEngine()
        self.knowledge_base = KnowledgeBase()
        
        logger.info(f"AI终端系统初始化完成 - 会话ID: {self.session_id}")
        logger.info(f"系统信息: {self.system_info['os']} {self.system_info['platform']}")
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        info = {
            "os": sys.platform,
            "python_version": sys.version,
            "current_dir": os.getcwd(),
            "user": os.getenv("USERNAME") or os.getenv("USER"),
            "home_dir": str(Path.home()),
            "platform": platform.platform() if hasattr(platform, 'platform') else "unknown"
        }
        return info
    
    async def process_command(self, command: str) -> CommandResult:
        """处理用户命令 - 完整的AI处理流程"""
        logger.info(f"处理命令: {command}")
        
        # 1. 分析命令意图和复杂度
        analysis = self.command_analyzer.analyze(command)
        
        # 2. 检查安全性
        if analysis.confirmation_needed and self.safe_mode:
            return CommandResult(
                success=False,
                output="",
                error=f"命令需要确认: {command} (风险等级: {analysis.risk_level})",
                exit_code=-1,
                execution_time=0,
                command=command,
                warnings=[f"危险命令需要用户确认: {analysis.intent.value}"]
            )
        
        # 3. 如果是复杂任务，创建执行计划
        if analysis.intent in [CommandIntent.AUTOMATE, CommandIntent.COMPLEX]:
            execution_plan = self.task_planner.create_plan(analysis)
            analysis.execution_plan = execution_plan
        
        # 4. 执行命令
        result = await self.execution_engine.execute(
            analysis, 
            self.working_directory,
            self.system_info
        )
        
        # 5. 更新工作目录（如果命令改变了目录）
        if result.success and "cd" in command.lower():
            new_dir = self._extract_new_directory(command, result.output)
            if new_dir and os.path.exists(new_dir):
                self.working_directory = new_dir
                logger.info(f"工作目录已更新: {self.working_directory}")
        
        # 6. 记录到历史
        self.command_history.append({
            "timestamp": time.time(),
            "command": command,
            "analysis": analysis.__dict__,
            "result": {
                "success": result.success,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time
            }
        })
        
        # 7. 学习用户习惯
        if self.learning_mode:
            self.knowledge_base.learn_from_execution(command, analysis, result)
        
        return result
    
    def _extract_new_directory(self, command: str, output: str) -> Optional[str]:
        """从cd命令中提取新目录"""
        try:
            # 简单的cd命令解析
            if command.lower().startswith("cd "):
                target = command[3:].strip()
                
                # 处理特殊符号
                if target == "~":
                    return str(Path.home())
                elif target == "-":
                    # 回到上一个目录（需要历史记录）
                    if len(self.command_history) > 1:
                        prev_cmd = self.command_history[-2]
                        if "cd" in prev_cmd.get("command", "").lower():
                            # 这里可以更智能地处理
                            pass
                
                # 解析路径
                if os.path.isabs(target):
                    return target
                else:
                    new_path = os.path.join(self.working_directory, target)
                    if os.path.exists(new_path):
                        return os.path.abspath(new_path)
        
        except Exception as e:
            logger.error(f"提取目录失败: {e}")
        
        return None
    
    async def intelligent_assist(self, user_request: str) -> Dict[str, Any]:
        """智能助手 - 理解用户意图并提供帮助"""
        logger.info(f"智能助手请求: {user_request}")
        
        # 分析用户请求
        analysis = self.command_analyzer.analyze(user_request)
        
        # 根据意图提供帮助
        response = {
            "request": user_request,
            "intent": analysis.intent.value,
            "suggestions": [],
            "examples": [],
            "warnings": []
        }
        
        # 根据意图提供建议
        if analysis.intent == CommandIntent.QUERY:
            response["suggestions"] = [
                "使用 'ls' 查看文件",
                "使用 'pwd' 查看当前目录",
                "使用 'whoami' 查看当前用户",
                "使用 'systeminfo' 查看系统信息"
            ]
        elif analysis.intent == CommandIntent.FILE_OPS:
            response["suggestions"] = [
                "使用 'cp <源文件> <目标文件>' 复制文件",
                "使用 'mv <源文件> <目标文件>' 移动文件",
                "使用 'rm <文件>' 删除文件（谨慎使用）",
                "使用 'find <目录> -name <文件名>' 查找文件"
            ]
        elif analysis.intent == CommandIntent.NETWORK:
            response["suggestions"] = [
                "使用 'ping <主机>' 测试网络连接",
                "使用 'curl <URL>' 获取网页内容",
                "使用 'netstat -an' 查看网络连接",
                "使用 'ipconfig /all' 查看网络配置"
            ]
        
        # 添加警告
        if analysis.risk_level > 5:
            response["warnings"].append(f"此操作风险较高 ({analysis.risk_level}/10)，请确认后再执行")
        
        return response
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "session_id": self.session_id,
            "working_directory": self.working_directory,
            "system_info": self.system_info,
            "command_history_count": len(self.command_history),
            "safe_mode": self.safe_mode,
            "learning_mode": self.learning_mode,
            "recent_commands": self.command_history[-5:] if self.command_history else []
        }
        return status
    
    def toggle_safe_mode(self, enabled: bool = None) -> bool:
        """切换安全模式"""
        if enabled is not None:
            self.safe_mode = enabled
        else:
            self.safe_mode = not self.safe_mode
        
        logger.info(f"安全模式: {'启用' if self.safe_mode else '禁用'}")
        return self.safe_mode
    
    def export_history(self, format: str = "json") -> Optional[str]:
        """导出命令历史"""
        if format == "json":
            return json.dumps(self.command_history, indent=2, ensure_ascii=False)
        elif format == "text":
            lines = []
            for i, entry in enumerate(self.command_history, 1):
                cmd = entry.get("command", "")
                success = entry.get("result", {}).get("success", False)
                lines.append(f"{i}. [{'✓' if success else '✗'}] {cmd}")
            return "\n".join(lines)
        return None

class CommandAnalyzer:
    """命令分析器"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
        self.dangerous_commands = [
            "rm -rf", "format", "del /f", "shutdown", 
            "reboot", "chmod 777", "dd if=", "mkfs"
        ]
    
    def _load_patterns(self) -> Dict[CommandIntent, List[str]]:
        """加载命令模式"""
        return {
            CommandIntent.EXECUTE: [
                r"^(运行|执行|启动|打开)\s+.+",
                r"^\./.+",  # 执行脚本
                r"^[a-zA-Z0-9_\-]+(\s+.+)*$"  # 一般命令
            ],
            CommandIntent.QUERY: [
                r"^(查看|显示|列出|查询|搜索)\s+.+",
                r"^.+(\?|？)$",  # 以问号结尾
                r"^(怎么|如何|怎样).+",
                r"^ls\b", r"^dir\b", r"^pwd\b", r"^whoami\b"
            ],
            CommandIntent.FILE_OPS: [
                r"^(复制|移动|删除|创建|编辑|重命名)\s+.+",
                r"^cp\b", r"^mv\b", r"^rm\b", r"^touch\b",
                r"^vim\b", r"^nano\b", r"^cat\b"
            ],
            CommandIntent.NETWORK: [
                r"^(连接|下载|上传|访问|ping|curl)\s+.+",
                r"^ping\b", r"^curl\b", r"^wget\b",
                r"^ssh\b", r"^scp\b"
            ],
            CommandIntent.INSTALL: [
                r"^(安装|更新|升级|卸载)\s+.+",
                r"^pip install\b", r"^apt install\b",
                r"^yum install\b", r"^brew install\b"
            ]
        }
    
    def analyze(self, command: str) -> CommandAnalysis:
        """分析命令"""
        # 清理命令
        clean_cmd = command.strip()
        
        # 确定意图
        intent = self._detect_intent(clean_cmd)
        
        # 确定复杂度
        complexity = self._detect_complexity(clean_cmd)
        
        # 检查安全性
        risk_level, confirmation_needed = self._assess_risk(clean_cmd)
        
        # 提取参数
        parameters = self._extract_parameters(clean_cmd)
        
        # 生成建议命令
        suggested_commands = self._suggest_commands(clean_cmd, intent)
        
        return CommandAnalysis(
            raw_command=clean_cmd,
            intent=intent,
            complexity=complexity,
            parameters=parameters,
            safe_to_execute=risk_level < 5,
            confirmation_needed=confirmation_needed,
            suggested_commands=suggested_commands,
            risk_level=risk_level
        )
    
    def _detect_intent(self, command: str) -> CommandIntent:
        """检测命令意图"""
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.match(pattern, command, re.IGNORECASE):
                    return intent
        
        # 默认检查
        if any(cmd in command.lower() for cmd in ["?", "？", "怎么", "如何"]):
            return CommandIntent.QUERY
        
        return CommandIntent.UNKNOWN
    
    def _detect_complexity(self, command: str) -> CommandComplexity:
        """检测命令复杂度"""
        # 检查是否包含管道、重定向等
        if any(char in command for char in ['|', '>', '<', '&&', '||']):
            return CommandComplexity.COMPLEX
        
        # 检查是否危险命令
        if any(danger in command.lower() for danger in self.dangerous_commands):
            return CommandComplexity.DANGEROUS
        
        # 检查是否系统命令
        system_cmds = ["sudo", "chmod", "chown", "systemctl", "service"]
        if any(cmd in command.lower() for cmd in system_cmds):
            return CommandComplexity.SYSTEM
        
        return CommandComplexity.SIMPLE
    
    def _assess_risk(self, command: str) -> Tuple[int, bool]:
        """评估风险等级"""
        risk_level = 1
        confirmation_needed = False
        
        # 危险命令
        for dangerous in self.dangerous_commands:
            if dangerous in command.lower():
                risk_level = 9
                confirmation_needed = True
                break
        
        # 删除操作
        if any(cmd in command.lower() for cmd in ["rm ", "del ", "删除"]):
            risk_level = max(risk_level, 7)
            confirmation_needed = True
        
        # 系统级操作
        if any(cmd in command.lower() for cmd in ["sudo ", "chmod ", "chown "]):
            risk_level = max(risk_level, 6)
            confirmation_needed = True
        
        # 网络操作
        if any(cmd in command.lower() for cmd in ["curl ", "wget ", "ssh "]):
            risk_level = max(risk_level, 4)
        
        return risk_level, confirmation_needed
    
    def _extract_parameters(self, command: str) -> Dict[str, Any]:
        """提取命令参数"""
        params = {"raw": command}
        
        try:
            # 简单的参数解析
            parts = shlex.split(command)
            if parts:
                params["command"] = parts[0]
                params["args"] = parts[1:] if len(parts) > 1 else []
                
                # 解析常见选项
                flags = [arg for arg in parts[1:] if arg.startswith('-')]
                non_flags = [arg for arg in parts[1:] if not arg.startswith('-')]
                
                params["flags"] = flags
                params["arguments"] = non_flags
        except:
            pass
        
        return params
    
    def _suggest_commands(self, command: str, intent: CommandIntent) -> List[str]:
        """根据意图建议命令"""
        suggestions = []
        
        if intent == CommandIntent.QUERY:
            # 根据查询内容建议
            if "文件" in command or "目录" in command:
                suggestions.extend(["ls -la", "find . -type f", "tree"])
            elif "系统" in command or "信息" in command:
                suggestions.extend(["uname -a", "df -h", "free -h"])
            elif "网络" in command:
                suggestions.extend(["ifconfig", "netstat -tulpn", "ping localhost"])
        
        elif intent == CommandIntent.FILE_OPS:
            suggestions.extend(["cp -r", "mv -i", "rm -i", "mkdir -p"])
        
        return suggestions[:3]  # 返回前3个建议

class TaskPlanner:
    """任务规划器"""
    
    def create_plan(self, analysis: CommandAnalysis) -> str:
        """创建执行计划"""
        if analysis.intent == CommandIntent.AUTOMATE:
            return self._create_automation_plan(analysis)
        elif analysis.complexity == CommandComplexity.COMPLEX:
            return self._create_complex_plan(analysis)
        else:
            return "直接执行命令"
    
    def _create_automation_plan(self, analysis: CommandAnalysis) -> str:
        """创建自动化任务计划"""
        plan = []
        
        # 根据命令内容创建计划
        command = analysis.raw_command.lower()
        
        if "备份" in command or "backup" in command:
            plan = [
                "1. 检查备份目录是否存在",
                "2. 创建时间戳目录",
                "3. 复制文件到备份目录",
                "4. 验证备份完整性",
                "5. 清理旧备份"
            ]
        elif "部署" in command or "deploy" in command:
            plan = [
                "1. 检查代码更新",
                "2. 运行测试",
                "3. 构建项目",
                "4. 停止旧服务",
                "5. 部署新版本",
                "6. 启动服务",
                "7. 验证部署"
            ]
        elif "监控" in command or "monitor" in command:
            plan = [
                "1. 设置监控指标",
                "2. 启动监控服务",
                "3. 配置告警规则",
                "4. 生成监控报告"
            ]
        else:
            plan = ["执行自动化任务"]
        
        return "\n".join(plan)
    
    def _create_complex_plan(self, analysis: CommandAnalysis) -> str:
        """创建复杂命令执行计划"""
        plan = [
            "复杂命令执行计划:",
            "1. 解析命令结构和参数",
            "2. 验证命令语法正确性",
            "3. 检查执行权限和环境",
            "4. 分步执行命令",
            "5. 监控执行过程",
            "6. 收集和分析结果"
        ]
        
        # 添加特定检查
        if "|" in analysis.raw_command:
            plan.insert(2, "2.1 检查管道命令的输入输出")
        
        if ">" in analysis.raw_command or ">>" in analysis.raw_command:
            plan.insert(2, "2.2 检查文件重定向目标")
        
        return "\n".join(plan)

class ExecutionEngine:
    """执行引擎"""
    
    async def execute(self, analysis: CommandAnalysis, 
                     working_dir: str, 
                     system_info: Dict[str, Any]) -> CommandResult:
        """执行命令"""
        start_time = time.time()
        
        try:
            # 准备执行环境
            env = self._prepare_environment(system_info)
            
            # 根据复杂度选择执行方式
            if analysis.complexity == CommandComplexity.SIMPLE:
                result = await self._execute_simple(analysis.raw_command, working_dir, env)
            else:
                result = await self._execute_complex(analysis, working_dir, env)
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=result["success"],
                output=result.get("output", ""),
                error=result.get("error", ""),
                exit_code=result.get("exit_code", 0),
                execution_time=execution_time,
                command=analysis.raw_command,
                warnings=result.get("warnings", [])
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行命令失败: {e}")
            
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=execution_time,
                command=analysis.raw_command,
                warnings=["执行过程中发生异常"]
            )
    
    def _prepare_environment(self, system_info: Dict[str, Any]) -> Dict[str, str]:
        """准备执行环境"""
        env = os.environ.copy()
        
        # 添加系统信息到环境变量
        env["MIYA_TERMINAL_SESSION"] = "active"
        env["MIYA_SYSTEM_OS"] = system_info.get("os", "")
        env["MIYA_CURRENT_DIR"] = system_info.get("current_dir", "")
        
        return env
    
    async def _execute_simple(self, command: str, 
                            working_dir: str, 
                            env: Dict[str, str]) -> Dict[str, Any]:
        """执行简单命令"""
        try:
            # 使用subprocess执行
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=working_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='ignore'),
                "error": stderr.decode('utf-8', errors='ignore'),
                "exit_code": process.returncode,
                "warnings": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "warnings": [f"执行异常: {e}"]
            }
    
    async def _execute_complex(self, analysis: CommandAnalysis,
                              working_dir: str,
                              env: Dict[str, str]) -> Dict[str, Any]:
        """执行复杂命令"""
        # 这里可以实现更复杂的执行逻辑
        # 例如：分步执行、监控、重试等
        
        # 暂时使用简单执行
        return await self._execute_simple(analysis.raw_command, working_dir, env)

class KnowledgeBase:
    """知识库 - 学习用户习惯和命令模式"""
    
    def __init__(self):
        self.user_patterns = {}
        self.common_commands = self._load_common_commands()
        self.learning_data = []
    
    def _load_common_commands(self) -> Dict[str, List[str]]:
        """加载常见命令"""
        return {
            "file_operations": ["ls", "cd", "cp", "mv", "rm", "mkdir", "touch"],
            "text_processing": ["cat", "grep", "sed", "awk", "head", "tail"],
            "system_info": ["pwd", "whoami", "uname", "df", "free", "top"],
            "network": ["ping", "curl", "wget", "ssh", "scp", "netstat"]
        }
    
    def learn_from_execution(self, command: str, 
                            analysis: CommandAnalysis,
                            result: CommandResult):
        """从执行中学习"""
        learning_entry = {
            "timestamp": time.time(),
            "command": command,
            "intent": analysis.intent.value,
            "success": result.success,
            "execution_time": result.execution_time,
            "working_directory": os.getcwd()
        }
        
        self.learning_data.append(learning_entry)
        
        # 限制学习数据大小
        if len(self.learning_data) > 1000:
            self.learning_data = self.learning_data[-500:]
        
        # 分析用户模式
        self._analyze_user_patterns(learning_entry)
    
    def _analyze_user_patterns(self, entry: Dict[str, Any]):
        """分析用户模式"""
        command = entry["command"].split()[0] if entry["command"] else ""
        
        if command:
            if command not in self.user_patterns:
                self.user_patterns[command] = {
                    "count": 0,
                    "success_count": 0,
                    "avg_time": 0,
                    "last_used": 0
                }
            
            pattern = self.user_patterns[command]
            pattern["count"] += 1
            pattern["success_count"] += 1 if entry["success"] else 0
            pattern["avg_time"] = (pattern["avg_time"] * (pattern["count"] - 1) + 
                                 entry["execution_time"]) / pattern["count"]
            pattern["last_used"] = entry["timestamp"]
    
    def get_suggestions(self, context: str = "") -> List[str]:
        """根据上下文获取建议"""
        suggestions = []
        
        # 根据上下文提供建议
        if "文件" in context or "file" in context.lower():
            suggestions.extend(self.common_commands["file_operations"])
        
        if "文本" in context or "text" in context.lower():
            suggestions.extend(self.common_commands["text_processing"])
        
        if "系统" in context or "system" in context.lower():
            suggestions.extend(self.common_commands["system_info"])
        
        if "网络" in context or "network" in context.lower():
            suggestions.extend(self.common_commands["network"])
        
        # 添加用户常用命令
        user_favorites = sorted(
            self.user_patterns.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]
        
        suggestions.extend([cmd for cmd, _ in user_favorites])
        
        return list(dict.fromkeys(suggestions))[:10]  # 去重并限制数量

# 使用示例
async def example_usage():
    """使用示例"""
    # 创建AI终端系统
    terminal = AITerminalSystem(session_id="example_session")
    
    print(f"系统状态: {terminal.get_system_status()}")
    
    # 处理命令
    commands = [
        "ls -la",
        "查看系统信息",
        "备份当前目录",
        "rm -rf /tmp/test"  # 危险命令
    ]
    
    for cmd in commands:
        print(f"\n处理命令: {cmd}")
        result = await terminal.process_command(cmd)
        print(f"结果: {'成功' if result.success else '失败'}")
        print(f"输出: {result.output[:100]}...")
        print(f"错误: {result.error}")
        print(f"执行时间: {result.execution_time:.2f}秒")
    
    # 智能助手
    print("\n智能助手示例:")
    assistance = await terminal.intelligent_assist("如何查看网络连接?")
    print(f"建议: {assistance.get('suggestions', [])}")

if __name__ == "__main__":
    import platform
    # 运行示例
    asyncio.run(example_usage())