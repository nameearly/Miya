#!/usr/bin/env python3
"""
智能执行器

统一整合智能命令执行功能
"""

import logging
import subprocess
import shlex
import os
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from ..base.types import (
    ExecutionMode, CommandCategory, CommandResult,
    ProcessInfo, RiskLevel, SafetyReport, CommandAnalysis
)
from ..base.interfaces import IExecutor
from ..safety import SafetyChecker

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """执行上下文"""
    working_directory: str = field(default_factory=lambda: os.getcwd())
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[int] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class IntelligentExecutor(IExecutor):
    """智能执行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.safety_checker = SafetyChecker()
        
        # 进程管理
        self.running_processes: Dict[int, subprocess.Popen] = {}
        self.process_lock = threading.Lock()
        
        # 执行统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        self.logger.info("智能执行器初始化完成")
    
    def execute(self, 
                command: str, 
                context: ExecutionContext, 
                analysis: Optional[CommandAnalysis] = None) -> CommandResult:
        """
        执行命令
        
        Args:
            command: 命令字符串
            context: 执行上下文
            analysis: 可选命令分析结果
            
        Returns:
            执行结果
        """
        start_time = time.time()
        self.execution_stats["total_executions"] += 1
        
        try:
            # 安全检查
            safety_report = self.safety_checker.check(command, analysis)
            
            if safety_report.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.logger.warning(f"高风险命令被阻止: {command}")
                return CommandResult(
                    success=False,
                    output=f"命令被安全系统阻止: {safety_report.reasons}",
                    error_code=403,
                    process_id=None,
                    safety_report=safety_report
                )
            
            # 准备环境
            env = os.environ.copy()
            if context.environment:
                env.update(context.environment)
            
            # 设置工作目录
            cwd = context.working_directory if context.working_directory else os.getcwd()
            
            # 解析命令
            if isinstance(command, list):
                args = command
            else:
                args = shlex.split(command)
            
            # 执行命令
            self.logger.info(f"执行命令: {command}")
            self.logger.info(f"工作目录: {cwd}")
            
            # 设置超时
            timeout = context.timeout
            
            process = subprocess.Popen(
                args,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False
            )
            
            # 注册进程
            with self.process_lock:
                self.running_processes[process.pid] = process
            
            # 等待完成
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
                
            except subprocess.TimeoutExpired:
                # 超时处理
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                # 移除进程
                with self.process_lock:
                    if process.pid in self.running_processes:
                        del self.running_processes[process.pid]
                
                elapsed_time = time.time() - start_time
                self.execution_stats["failed_executions"] += 1
                
                return CommandResult(
                    success=False,
                    output="",
                    error=f"命令执行超时 (超时时间: {timeout}秒)",
                    error_code=408,
                    process_id=process.pid,
                    execution_time=elapsed_time,
                    safety_report=safety_report
                )
            
            # 移除完成的进程
            with self.process_lock:
                if process.pid in self.running_processes:
                    del self.running_processes[process.pid]
            
            # 计算执行时间
            elapsed_time = time.time() - start_time
            self.execution_stats["total_execution_time"] += elapsed_time
            
            # 更新平均执行时间
            if self.execution_stats["successful_executions"] > 0:
                total_success = self.execution_stats["successful_executions"]
                self.execution_stats["avg_execution_time"] = \
                    self.execution_stats["total_execution_time"] / total_success
            
            # 判断是否成功
            success = return_code == 0
            
            if success:
                self.execution_stats["successful_executions"] += 1
                self.logger.info(f"命令执行成功: {command}")
            else:
                self.execution_stats["failed_executions"] += 1
                self.logger.warning(f"命令执行失败 (返回码: {return_code}): {command}")
            
            # 返回结果
            return CommandResult(
                success=success,
                output=stdout,
                error=stderr if stderr else None,
                error_code=return_code,
                process_id=process.pid,
                execution_time=elapsed_time,
                safety_report=safety_report
            )
            
        except Exception as e:
            self.logger.error(f"执行命令时发生异常: {e}", exc_info=True)
            elapsed_time = time.time() - start_time
            self.execution_stats["failed_executions"] += 1
            
            return CommandResult(
                success=False,
                output="",
                error=f"执行异常: {str(e)}",
                error_code=500,
                process_id=None,
                execution_time=elapsed_time
            )
    
    def execute_async(self, 
                      command: str, 
                      context: ExecutionContext, 
                      analysis: Optional[CommandAnalysis] = None) -> int:
        """
        异步执行命令
        
        Args:
            command: 命令字符串
            context: 执行上下文
            analysis: 可选命令分析结果
            
        Returns:
            进程ID
        """
        try:
            # 安全检查
            safety_report = self.safety_checker.check(command, analysis)
            
            if safety_report.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.logger.warning(f"高风险异步命令被阻止: {command}")
                raise PermissionError(f"命令被安全系统阻止: {safety_report.reasons}")
            
            # 准备环境
            env = os.environ.copy()
            if context.environment:
                env.update(context.environment)
            
            # 设置工作目录
            cwd = context.working_directory if context.working_directory else os.getcwd()
            
            # 解析命令
            if isinstance(command, list):
                args = command
            else:
                args = shlex.split(command)
            
            # 执行异步命令
            self.logger.info(f"异步执行命令: {command}")
            
            process = subprocess.Popen(
                args,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False
            )
            
            # 注册进程
            with self.process_lock:
                self.running_processes[process.pid] = process
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=self._monitor_async_process,
                args=(process.pid, command),
                daemon=True
            )
            monitor_thread.start()
            
            self.logger.info(f"异步进程已启动 PID: {process.pid}")
            return process.pid
            
        except Exception as e:
            self.logger.error(f"异步执行命令失败: {e}")
            raise
    
    def _monitor_async_process(self, pid: int, command: str):
        """监控异步进程"""
        try:
            with self.process_lock:
                if pid not in self.running_processes:
                    return
                
                process = self.running_processes[pid]
            
            # 等待进程完成
            process.wait()
            
            # 移除进程
            with self.process_lock:
                if pid in self.running_processes:
                    del self.running_processes[pid]
            
            # 记录结果
            if process.returncode == 0:
                self.logger.info(f"异步进程完成 PID: {pid} - 命令: {command}")
            else:
                self.logger.warning(
                    f"异步进程失败 PID: {pid} - 命令: {command} - 返回码: {process.returncode}"
                )
                
        except Exception as e:
            self.logger.error(f"监控异步进程时发生异常 PID: {pid}: {e}")
    
    def get_process_info(self, process_id: int) -> Optional[ProcessInfo]:
        """
        获取进程信息
        
        Args:
            process_id: 进程ID
            
        Returns:
            进程信息，如果进程不存在则返回None
        """
        with self.process_lock:
            if process_id not in self.running_processes:
                return None
            
            process = self.running_processes[process_id]
        
        try:
            # 获取进程状态
            status = "running" if process.poll() is None else "completed"
            
            return ProcessInfo(
                pid=process_id,
                command=str(process.args),
                status=status,
                return_code=process.returncode
            )
            
        except Exception as e:
            self.logger.error(f"获取进程信息失败 PID: {process_id}: {e}")
            return None
    
    def stop_process(self, process_id: int, force: bool = False) -> bool:
        """
        停止进程
        
        Args:
            process_id: 进程ID
            force: 是否强制停止
            
        Returns:
            是否成功停止
        """
        with self.process_lock:
            if process_id not in self.running_processes:
                self.logger.warning(f"进程不存在 PID: {process_id}")
                return False
            
            process = self.running_processes[process_id]
            
            try:
                if force:
                    process.kill()
                    self.logger.info(f"强制停止进程 PID: {process_id}")
                else:
                    process.terminate()
                    self.logger.info(f"终止进程 PID: {process_id}")
                
                # 等待进程结束
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if force:
                        self.logger.warning(f"进程无法强制停止 PID: {process_id}")
                        return False
                    else:
                        # 如果普通终止失败，尝试强制停止
                        process.kill()
                        process.wait(timeout=2)
                
                # 移除进程
                del self.running_processes[process_id]
                return True
                
            except Exception as e:
                self.logger.error(f"停止进程失败 PID: {process_id}: {e}")
                return False
    
    def get_running_processes(self) -> List[ProcessInfo]:
        """获取所有运行中的进程"""
        with self.process_lock:
            process_infos = []
            
            for pid, process in self.running_processes.items():
                try:
                    status = "running" if process.poll() is None else "completed"
                    
                    info = ProcessInfo(
                        pid=pid,
                        command=str(process.args) if process.args else "unknown",
                        status=status,
                        return_code=process.returncode
                    )
                    
                    process_infos.append(info)
                    
                except Exception as e:
                    self.logger.error(f"获取进程信息失败 PID: {pid}: {e}")
            
            return process_infos
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return self.execution_stats.copy()
    
    def reset_stats(self):
        """重置执行统计"""
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        self.logger.info("执行统计已重置")


# 单例实例
_global_executor: Optional[IntelligentExecutor] = None

def get_intelligent_executor() -> IntelligentExecutor:
    """获取全局执行器实例"""
    global _global_executor
    
    if _global_executor is None:
        _global_executor = IntelligentExecutor()
    
    return _global_executor