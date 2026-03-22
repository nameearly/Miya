"""
统一的终端主控制器

整合terminal_master.py、ai_terminal_system.py和intelligent_executor.py的核心功能
提供统一的接口供外部调用
"""

import asyncio
import os
import sys
import json
import logging
import time
import signal
from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path
import readline  # 用于命令历史

from ..base.types import (
    CommandIntent, CommandCategory, ExecutionMode, 
    TerminalStatus, CommandResult, ExecutionContext, RiskLevel
)
from ..base.interfaces import ITerminalController
from ..parser import CommandParser
from ..safety import SafetyChecker
from ..executor import IntelligentExecutor
from ..knowledge import KnowledgeBase
from ..monitor import ProcessMonitor

logger = logging.getLogger(__name__)

class TerminalMaster(ITerminalController):
    """统一的终端主控制器"""
    
    def __init__(self, session_id: str = None, config: Optional[Dict[str, Any]] = None):
        self.session_id = session_id or f"master_{int(time.time())}"
        self.config = config or self._default_config()
        
        # 初始化所有组件
        self.command_parser = CommandParser(use_learning=self.config.get("learning_enabled", True))
        self.safety_checker = SafetyChecker()
        self.executor = IntelligentExecutor(
            session_id=self.session_id,
            safety_level=self.config.get("safety_level", 5)
        )
        self.knowledge_base = KnowledgeBase()
        self.process_monitor = ProcessMonitor()
        self.context_manager = self._create_context_manager()
        
        # 状态跟踪
        self.status = TerminalStatus.IDLE
        self.command_count = 0
        self.start_time = time.time()
        self.working_directory = os.getcwd()
        self.is_running = True
        
        # 命令历史
        self.command_history = []
        self.max_history_size = self.config.get("max_history_size", 100)
        
        # 用户习惯
        self.user_patterns = {}
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        logger.info(f"终端主控制器初始化完成 - 会话ID: {self.session_id}")
        logger.info(f"配置: {json.dumps(self.config, indent=2, default=str)}")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "learning_enabled": True,
            "safety_level": 5,  # 1-10
            "execution_mode": "direct",
            "max_history_size": 100,
            "cache_enabled": True,
            "stream_output": True,
            "confirm_dangerous": True,
            "log_level": "INFO",
            "auto_save_context": True,
            "save_interval_seconds": 300,
            "performance_monitoring": True
        }
    
    def _create_context_manager(self) -> Any:
        """创建上下文管理器（简化版本）"""
        class SimpleContextManager:
            def __init__(self, master):
                self.master = master
                self.context_cache = {}
            
            def get_context(self, session_id: Optional[str] = None) -> ExecutionContext:
                session = session_id or self.master.session_id
                
                if session in self.context_cache:
                    return self.context_cache[session]
                
                context = ExecutionContext(
                    working_directory=self.master.working_directory,
                    user=os.getenv("USER") or os.getenv("USERNAME") or "unknown",
                    home_directory=str(Path.home()),
                    system_platform=sys.platform,
                    python_version=sys.version.split()[0],
                    environment_vars=dict(os.environ),
                    sudo_required=False,
                    writable=self._check_writable(),
                    terminal_type="local",
                    session_id=session
                )
                
                self.context_cache[session] = context
                return context
            
            def _check_writable(self) -> bool:
                """检查当前目录是否可写"""
                try:
                    test_file = os.path.join(self.master.working_directory, ".miya_test")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    return True
                except:
                    return False
            
            def update_context(self, result: CommandResult, analysis: Any):
                """更新上下文（基于执行结果）"""
                # 如果命令改变了目录，更新工作目录
                if "cd" in analysis.normalized_command.lower() and result.success:
                    try:
                        new_dir = os.getcwd()
                        if new_dir != self.master.working_directory:
                            self.master.working_directory = new_dir
                            logger.info(f"工作目录更新: {self.master.working_directory}")
                    except:
                        pass
                
                # 更新上下文缓存
                session = analysis.session_id or self.master.session_id
                if session in self.context_cache:
                    self.context_cache[session].working_directory = self.master.working_directory
        
        return SimpleContextManager(self)
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，优雅关闭...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def process_user_input(self, user_input: str, session_id: Optional[str] = None) -> CommandResult:
        """处理用户输入（完整流程）"""
        session = session_id or self.session_id
        self.status = TerminalStatus.EXECUTING
        
        logger.info(f"[{session}] 处理用户输入: {user_input}")
        
        try:
            # 1. 解析命令
            analysis = await self.command_parser.parse(user_input)
            analysis.session_id = session
            
            # 2. 获取上下文
            context = self.context_manager.get_context(session)
            
            # 3. 安全检查（详细检查）
            safety_report = await self.safety_checker.check_command(user_input, context)
            
            # 4. 如果命令危险且需要确认，返回需要确认的结果
            if safety_report.requires_confirmation and self.config.get("confirm_dangerous", True):
                return CommandResult(
                    success=False,
                    output="",
                    error=f"危险命令需要确认: {user_input} (风险等级: {safety_report.risk_level.name})",
                    exit_code=-1,
                    execution_time=0,
                    command=user_input,
                    warnings=safety_report.warnings
                )
            
            # 5. 确定执行模式
            execution_mode = self._determine_execution_mode(analysis, safety_report)
            
            # 6. 执行命令
            start_time = time.time()
            result = await self.executor.execute(analysis, context, execution_mode)
            execution_time = time.time() - start_time
            
            # 7. 更新执行时间
            result.execution_time = execution_time
            
            # 8. 更新上下文
            self.context_manager.update_context(result, analysis)
            
            # 9. 记录到历史
            self._record_to_history(user_input, analysis, result, session)
            
            # 10. 学习用户习惯
            if self.config.get("learning_enabled", True):
                self.knowledge_base.learn_from_execution(user_input, analysis, result)
                self._update_user_patterns(user_input, result.success, execution_time)
            
            # 11. 更新状态
            self.command_count += 1
            self.status = TerminalStatus.IDLE
            
            logger.info(f"[{session}] 命令处理完成: {result.success}, 耗时: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"[{session}] 处理命令时出错: {e}", exc_info=True)
            
            self.status = TerminalStatus.ERROR
            
            return CommandResult(
                success=False,
                output="",
                error=f"处理命令时出错: {str(e)}",
                exit_code=-1,
                execution_time=0,
                command=user_input,
                warnings=["系统内部错误，请检查日志"]
            )
    
    def _determine_execution_mode(self, analysis: Any, safety_report: Any) -> ExecutionMode:
        """确定执行模式"""
        # 从配置获取默认模式
        config_mode = self.config.get("execution_mode", "direct")
        
        if config_mode == "simulate":
            return ExecutionMode.SIMULATE
        elif config_mode == "safe":
            return ExecutionMode.SAFE
        elif config_mode == "step_by_step":
            return ExecutionMode.STEP_BY_STEP
        elif config_mode == "validate_only":
            return ExecutionMode.VALIDATE_ONLY
        
        # 根据安全性自动选择
        if safety_report.risk_level.value >= RiskLevel.HIGH.value:
            return ExecutionMode.SAFE
        
        if analysis.complexity.name == "COMPLEX":
            return ExecutionMode.STEP_BY_STEP
        
        return ExecutionMode.DIRECT
    
    def _record_to_history(self, user_input: str, analysis: Any, 
                          result: CommandResult, session_id: str):
        """记录到历史"""
        history_entry = {
            "timestamp": time.time(),
            "session_id": session_id,
            "user_input": user_input,
            "normalized_command": analysis.normalized_command,
            "intent": analysis.intent.value,
            "category": analysis.category.value,
            "complexity": analysis.complexity.name,
            "result": {
                "success": result.success,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "process_id": result.process_id
            },
            "working_directory": self.working_directory,
            "risk_level": analysis.risk_level.name
        }
        
        self.command_history.append(history_entry)
        
        # 限制历史记录大小
        if len(self.command_history) > self.max_history_size:
            self.command_history = self.command_history[-self.max_history_size:]
    
    def _update_user_patterns(self, command: str, success: bool, execution_time: float):
        """更新用户模式"""
        command_key = command.strip().lower()
        
        if command_key not in self.user_patterns:
            self.user_patterns[command_key] = {
                "count": 0,
                "success_count": 0,
                "total_time": 0,
                "last_used": time.time()
            }
        
        pattern = self.user_patterns[command_key]
        pattern["count"] += 1
        pattern["success_count"] += 1 if success else 0
        pattern["total_time"] += execution_time
        pattern["last_used"] = time.time()
        pattern["avg_time"] = pattern["total_time"] / pattern["count"]
    
    async def intelligent_assist(self, user_request: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """智能助手"""
        session = session_id or self.session_id
        
        logger.info(f"[{session}] 智能助手请求: {user_request}")
        
        # 解析请求
        analysis = await self.command_parser.parse(user_request)
        
        # 获取上下文
        context = self.context_manager.get_context(session)
        
        # 安全检查
        safety_report = await self.safety_checker.check_command(user_request, context)
        
        # 获取建议
        suggestions = self.knowledge_base.get_suggestions(user_request, limit=5)
        
        # 获取常用命令
        if analysis.category != CommandCategory.CUSTOM:
            common_commands = self.knowledge_base.get_common_commands(analysis.category)
        else:
            common_commands = []
        
        # 构建响应
        response = {
            "request": user_request,
            "intent": analysis.intent.value,
            "category": analysis.category.value,
            "complexity": analysis.complexity.name,
            "risk_level": analysis.risk_level.name,
            "safety_report": {
                "safe": safety_report.safe,
                "risk_level": safety_report.risk_level.name,
                "warnings": safety_report.warnings,
                "requires_confirmation": safety_report.requires_confirmation
            },
            "suggestions": suggestions,
            "common_commands": common_commands,
            "user_patterns": self._get_relevant_user_patterns(user_request),
            "context": {
                "working_directory": context.working_directory,
                "platform": context.system_platform,
                "writable": context.writable
            }
        }
        
        return response
    
    def _get_relevant_user_patterns(self, context: str) -> List[Dict[str, Any]]:
        """获取相关的用户模式"""
        relevant_patterns = []
        context_lower = context.lower()
        
        for command, pattern in self.user_patterns.items():
            # 简单的相关性检查
            if any(word in command for word in context_lower.split()):
                relevant_patterns.append({
                    "command": command,
                    "usage_count": pattern["count"],
                    "success_rate": pattern["success_count"] / pattern["count"] if pattern["count"] > 0 else 0,
                    "avg_time": pattern.get("avg_time", 0),
                    "last_used": pattern["last_used"]
                })
        
        # 按使用频率排序
        relevant_patterns.sort(key=lambda x: x["usage_count"], reverse=True)
        return relevant_patterns[:5]
    
    def get_system_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取系统状态"""
        session = session_id or self.session_id
        uptime = time.time() - self.start_time
        
        # 获取监控中的进程
        monitored_processes = self.process_monitor.get_monitored_processes()
        
        # 获取性能指标
        performance_metrics = {}
        if self.config.get("performance_monitoring", True):
            performance_metrics = self.process_monitor.get_performance_report()
        
        status = {
            "session_id": session,
            "status": self.status.name,
            "uptime_seconds": uptime,
            "command_count": self.command_count,
            "working_directory": self.working_directory,
            "config": {
                "safety_level": self.config.get("safety_level", 5),
                "learning_enabled": self.config.get("learning_enabled", True),
                "execution_mode": self.config.get("execution_mode", "direct")
            },
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version.split()[0],
                "current_user": os.getenv("USER") or os.getenv("USERNAME") or "unknown"
            },
            "monitoring": {
                "monitored_processes": len(monitored_processes),
                "active_sessions": 1,  # 简化版本
                "performance_metrics": performance_metrics
            },
            "knowledge_base": {
                "command_patterns": len(self.user_patterns),
                "history_size": len(self.command_history),
                "suggestions_count": len(self.knowledge_base.get_common_commands())
            }
        }
        
        return status
    
    def set_execution_mode(self, mode: ExecutionMode, session_id: Optional[str] = None):
        """设置执行模式"""
        session = session_id or self.session_id
        
        if isinstance(mode, str):
            try:
                mode = ExecutionMode[mode.upper()]
            except KeyError:
                logger.warning(f"[{session}] 无效的执行模式: {mode}")
                return
        
        self.config["execution_mode"] = mode.value
        self.executor.set_execution_mode(mode)
        
        logger.info(f"[{session}] 执行模式设置为: {mode.value}")
    
    def set_safety_level(self, level: int, session_id: Optional[str] = None):
        """设置安全级别"""
        session = session_id or self.session_id
        
        if 1 <= level <= 10:
            self.config["safety_level"] = level
            self.executor.set_safety_level(level)
            logger.info(f"[{session}] 安全级别设置为: {level}")
        else:
            logger.warning(f"[{session}] 无效的安全级别: {level}，必须为1-10")
    
    def get_command_history(self, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取命令历史"""
        session = session_id or self.session_id
        
        # 过滤指定会话的历史
        session_history = [
            entry for entry in self.command_history 
            if entry.get("session_id") == session
        ]
        
        return session_history[-limit:] if session_history else []
    
    async def run_interactive(self, welcome_message: bool = True):
        """运行交互模式"""
        if welcome_message:
            self._print_welcome_message()
        
        while self.is_running:
            try:
                # 显示提示符
                prompt = self._create_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                result = await self.process_user_input(user_input)
                
                # 显示结果
                self._display_result(result)
                
            except EOFError:
                # Ctrl+D 退出
                print("\n检测到EOF，退出...")
                break
            except KeyboardInterrupt:
                # Ctrl+C 处理
                print("\n输入 'exit' 退出系统")
                continue
            except Exception as e:
                logger.error(f"处理输入时出错: {e}")
                print(f"错误: {e}")
    
    def _print_welcome_message(self):
        """打印欢迎消息"""
        print("\n" + "=" * 70)
        print("🎯 弥娅终端主控制系统 - 统一架构")
        print("=" * 70)
        print(f"会话ID: {self.session_id}")
        print(f"工作目录: {self.working_directory}")
        print(f"系统时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n特性:")
        print("  ✓ 统一架构，消除代码冗余")
        print("  ✓ 智能命令解析和理解")
        print("  ✓ 多层安全检查")
        print("  ✓ 任务规划和自动化")
        print("  ✓ 用户习惯学习")
        print("\n输入 'help' 查看帮助，'exit' 退出系统")
        print("=" * 70 + "\n")
    
    def _create_prompt(self) -> str:
        """创建提示符"""
        try:
            cwd = self.working_directory
            home = str(Path.home())
            
            if cwd.startswith(home):
                cwd_display = "~" + cwd[len(home):]
            else:
                cwd_display = cwd
            
            # 限制长度
            if len(cwd_display) > 30:
                cwd_display = "..." + cwd_display[-27:]
        except:
            cwd_display = "?"
        
        # Windows处理
        if sys.platform == "win32":
            prompt = f"\n[{cwd_display}] 弥娅★ > "
        else:
            # Linux/Mac可以使用颜色
            prompt = f"\n\033[1;32m{cwd_display}\033[0m \033[1;34m弥娅★\033[0m > "
        
        return prompt
    
    def _display_result(self, result: CommandResult):
        """显示执行结果"""
        print(f"\n{'='*50}")
        
        if result.success:
            print(f"✅ 执行成功 ({result.execution_time:.2f}秒)")
            
            if result.output:
                output = result.output.strip()
                if output:
                    print(f"📤 输出:\n{output}")
            
        else:
            print(f"❌ 执行失败 ({result.execution_time:.2f}秒)")
            
            if result.error:
                error = result.error.strip()
                if error:
                    print(f"💥 错误:\n{error}")
        
        # 显示建议
        if result.suggestions:
            print(f"💡 建议:")
            for suggestion in result.suggestions:
                print(f"  • {suggestion}")
        
        # 显示警告
        if result.warnings:
            print(f"⚠️  警告:")
            for warning in result.warnings:
                print(f"  • {warning}")
        
        print(f"{'='*50}\n")
    
    def cleanup(self):
        """清理资源"""
        logger.info(f"[{self.session_id}] 清理终端控制器资源...")
        
        # 停止所有监控
        self.process_monitor.stop_all_monitoring()
        
        # 保存上下文
        if self.config.get("auto_save_context", True):
            self._save_context()
        
        # 保存知识库
        self.knowledge_base.save_knowledge(f"knowledge_{self.session_id}.json")
        
        # 清空缓存
        self.command_parser.clear_cache()
        
        logger.info(f"[{self.session_id}] 资源清理完成")

def create_terminal_master(session_id: Optional[str] = None, 
                          config: Optional[Dict[str, Any]] = None) -> TerminalMaster:
    """创建终端主控制器实例"""
    return TerminalMaster(session_id=session_id, config=config)