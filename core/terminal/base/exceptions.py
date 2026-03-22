"""
统一的终端系统异常定义

定义所有终端相关的异常类型
"""

class TerminalError(Exception):
    """终端系统基础异常"""
    pass

class CommandExecutionError(TerminalError):
    """命令执行错误"""
    def __init__(self, command: str, error: str, exit_code: int = -1):
        self.command = command
        self.error = error
        self.exit_code = exit_code
        super().__init__(f"命令执行失败: {command} (退出码: {exit_code}) - {error}")

class SafetyViolationError(TerminalError):
    """安全违规错误"""
    def __init__(self, command: str, risk_level: str, reason: str):
        self.command = command
        self.risk_level = risk_level
        self.reason = reason
        super().__init__(f"安全违规: {command} (风险等级: {risk_level}) - {reason}")

class TerminalConnectionError(TerminalError):
    """终端连接错误"""
    def __init__(self, target: str, reason: str):
        self.target = target
        self.reason = reason
        super().__init__(f"终端连接失败: {target} - {reason}")

class InvalidCommandError(TerminalError):
    """无效命令错误"""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        super().__init__(f"无效命令: {command} - {reason}")

class CommandTimeoutError(TerminalError):
    """命令超时错误"""
    def __init__(self, command: str, timeout_seconds: int):
        self.command = command
        self.timeout_seconds = timeout_seconds
        super().__init__(f"命令超时: {command} (超时时间: {timeout_seconds}秒)")

class PermissionDeniedError(TerminalError):
    """权限拒绝错误"""
    def __init__(self, command: str, required_permission: str):
        self.command = command
        self.required_permission = required_permission
        super().__init__(f"权限拒绝: {command} 需要 {required_permission} 权限")

class ResourceExhaustedError(TerminalError):
    """资源耗尽错误"""
    def __init__(self, resource_type: str, limit: str):
        self.resource_type = resource_type
        self.limit = limit
        super().__init__(f"资源耗尽: {resource_type} 达到限制 {limit}")

class ConfigurationError(TerminalError):
    """配置错误"""
    def __init__(self, config_key: str, error: str):
        self.config_key = config_key
        self.error = error
        super().__init__(f"配置错误: {config_key} - {error}")

class KnowledgeBaseError(TerminalError):
    """知识库错误"""
    def __init__(self, operation: str, error: str):
        self.operation = operation
        self.error = error
        super().__init__(f"知识库错误: {operation} - {error}")

class MonitoringError(TerminalError):
    """监控错误"""
    def __init__(self, process_id: int, error: str):
        self.process_id = process_id
        self.error = error
        super().__init__(f"监控错误: 进程 {process_id} - {error}")

class SessionError(TerminalError):
    """会话错误"""
    def __init__(self, session_id: str, error: str):
        self.session_id = session_id
        self.error = error
        super().__init__(f"会话错误: {session_id} - {error}")