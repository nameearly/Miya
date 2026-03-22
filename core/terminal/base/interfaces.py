"""
统一的终端系统接口定义

定义所有终端组件的接口，确保一致性和可替换性
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from .types import (
    CommandAnalysis, CommandResult, ExecutionContext, 
    SafetyReport, ProcessInfo, UserPattern, CommandIntent,
    CommandCategory, ExecutionMode, RiskLevel
)

class ICommandParser(ABC):
    """命令解析器接口"""
    
    @abstractmethod
    async def parse(self, user_input: str) -> CommandAnalysis:
        """解析用户输入为命令分析结果"""
        pass
    
    @abstractmethod
    def categorize(self, command: str) -> CommandCategory:
        """分类命令"""
        pass
    
    @abstractmethod
    def extract_parameters(self, command: str) -> Dict[str, Any]:
        """提取命令参数"""
        pass
    
    @abstractmethod
    def normalize_command(self, command: str) -> str:
        """规范化命令（处理别名、缩写等）"""
        pass

class ISafetyChecker(ABC):
    """安全检查器接口"""
    
    @abstractmethod
    async def check_command(self, command: str, context: ExecutionContext) -> SafetyReport:
        """检查命令安全性"""
        pass
    
    @abstractmethod
    def add_dangerous_pattern(self, pattern: str, risk_level: RiskLevel, description: str):
        """添加危险模式"""
        pass
    
    @abstractmethod
    def get_dangerous_patterns(self) -> List[Dict[str, Any]]:
        """获取所有危险模式"""
        pass
    
    @abstractmethod
    def should_confirm(self, report: SafetyReport) -> bool:
        """判断是否需要用户确认"""
        pass

class IExecutor(ABC):
    """命令执行器接口"""
    
    @abstractmethod
    async def execute(self, analysis: CommandAnalysis, context: ExecutionContext, 
                     mode: ExecutionMode = ExecutionMode.DIRECT) -> CommandResult:
        """执行命令"""
        pass
    
    @abstractmethod
    async def execute_script(self, script_content: str, script_type: str, 
                           context: ExecutionContext) -> CommandResult:
        """执行脚本"""
        pass
    
    @abstractmethod
    async def execute_streaming(self, analysis: CommandAnalysis, context: ExecutionContext) -> AsyncGenerator[str, None]:
        """流式执行命令（逐行输出）"""
        pass
    
    @abstractmethod
    def cancel_execution(self, process_id: int) -> bool:
        """取消正在执行的命令"""
        pass
    
    @abstractmethod
    def get_running_processes(self) -> List[ProcessInfo]:
        """获取正在运行的进程"""
        pass

class IContextManager(ABC):
    """上下文管理器接口"""
    
    @abstractmethod
    def get_context(self, session_id: Optional[str] = None) -> ExecutionContext:
        """获取执行上下文"""
        pass
    
    @abstractmethod
    def update_context(self, result: CommandResult, analysis: CommandAnalysis):
        """更新上下文（基于执行结果）"""
        pass
    
    @abstractmethod
    def save_context(self, session_id: str):
        """保存上下文到持久化存储"""
        pass
    
    @abstractmethod
    def load_context(self, session_id: str) -> Optional[ExecutionContext]:
        """从持久化存储加载上下文"""
        pass
    
    @abstractmethod
    def clear_context(self, session_id: str):
        """清理上下文"""
        pass

class IMonitor(ABC):
    """进程监控器接口"""
    
    @abstractmethod
    def start_monitoring(self, process_id: int, command: str, session_id: str):
        """开始监控进程"""
        pass
    
    @abstractmethod
    def stop_monitoring(self, process_id: int):
        """停止监控进程"""
        pass
    
    @abstractmethod
    def get_monitored_processes(self) -> Dict[int, ProcessInfo]:
        """获取所有监控中的进程"""
        pass
    
    @abstractmethod
    def get_process_metrics(self, process_id: int) -> Dict[str, Any]:
        """获取进程指标"""
        pass
    
    @abstractmethod
    def get_performance_report(self, time_window_seconds: int = 300) -> Dict[str, Any]:
        """获取性能报告"""
        pass

class IKnowledgeBase(ABC):
    """知识库接口"""
    
    @abstractmethod
    def learn_from_execution(self, command: str, analysis: CommandAnalysis, 
                           result: CommandResult):
        """从执行中学习"""
        pass
    
    @abstractmethod
    def get_user_patterns(self, user_id: Optional[str] = None) -> Dict[str, UserPattern]:
        """获取用户模式"""
        pass
    
    @abstractmethod
    def get_suggestions(self, context: str, limit: int = 5) -> List[str]:
        """获取智能建议"""
        pass
    
    @abstractmethod
    def get_common_commands(self, category: Optional[CommandCategory] = None) -> List[str]:
        """获取常用命令"""
        pass
    
    @abstractmethod
    def save_knowledge(self, filepath: str):
        """保存知识库到文件"""
        pass
    
    @abstractmethod
    def load_knowledge(self, filepath: str):
        """从文件加载知识库"""
        pass

class ITerminalController(ABC):
    """终端控制器接口（高层接口）"""
    
    @abstractmethod
    async def process_user_input(self, user_input: str, session_id: Optional[str] = None) -> CommandResult:
        """处理用户输入（完整流程）"""
        pass
    
    @abstractmethod
    async def intelligent_assist(self, user_request: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """智能助手"""
        pass
    
    @abstractmethod
    def get_system_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取系统状态"""
        pass
    
    @abstractmethod
    def set_execution_mode(self, mode: ExecutionMode, session_id: Optional[str] = None):
        """设置执行模式"""
        pass
    
    @abstractmethod
    def set_safety_level(self, level: int, session_id: Optional[str] = None):
        """设置安全级别"""
        pass
    
    @abstractmethod
    def get_command_history(self, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取命令历史"""
        pass