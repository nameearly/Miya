"""
统一的终端系统类型定义

整合所有重复的枚举和数据类定义
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

class CommandIntent(Enum):
    """命令意图分类 - 整合ai_terminal_system.py和intelligent_executor.py"""
    EXECUTE = "execute"           # 执行命令
    QUERY = "query"              # 查询信息
    CONFIGURE = "configure"      # 配置系统
    AUTOMATE = "automate"        # 自动化任务
    DEBUG = "debug"              # 调试问题
    INSTALL = "install"          # 安装软件
    MANAGE = "manage"            # 管理服务
    FILE_OPS = "file_ops"        # 文件操作
    NETWORK = "network"          # 网络操作
    HELP = "help"                # 帮助请求
    UNKNOWN = "unknown"          # 未知意图

class CommandCategory(Enum):
    """命令分类 - 整合intelligent_executor.py的分类"""
    FILE_SYSTEM = "file_system"      # 文件系统操作
    PROCESS_MANAGEMENT = "process_management"  # 进程管理
    NETWORK = "network"              # 网络操作
    SYSTEM_INFO = "system_info"      # 系统信息
    DEVELOPMENT = "development"      # 开发工具
    AUTOMATION = "automation"        # 自动化任务
    SECURITY = "security"            # 安全操作
    UTILITY = "utility"              # 工具命令
    CUSTOM = "custom"                # 自定义命令

class ExecutionMode(Enum):
    """执行模式 - 整合intelligent_executor.py"""
    DIRECT = "direct"           # 直接执行
    SAFE = "safe"               # 安全模式（需要确认）
    SIMULATE = "simulate"       # 模拟执行（不实际运行）
    STEP_BY_STEP = "step_by_step"  # 分步执行
    VALIDATE_ONLY = "validate_only"  # 仅验证

class CommandComplexity(Enum):
    """命令复杂度 - 整合ai_terminal_system.py"""
    SIMPLE = "simple"         # 简单命令，直接执行
    COMPLEX = "complex"       # 复杂命令，需要分析
    DANGEROUS = "dangerous"   # 危险命令，需要确认
    SYSTEM = "system"         # 系统级命令，需要权限

class TerminalStatus(Enum):
    """终端状态"""
    IDLE = "idle"            # 空闲
    BUSY = "busy"            # 忙碌
    EXECUTING = "executing"  # 执行中
    ERROR = "error"          # 错误
    DISCONNECTED = "disconnected"  # 断开连接

class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = 1     # 极低风险
    LOW = 2          # 低风险
    MEDIUM = 3       # 中等风险
    HIGH = 4         # 高风险
    VERY_HIGH = 5    # 极高风险
    CRITICAL = 6     # 关键风险
    DANGEROUS = 7    # 危险
    VERY_DANGEROUS = 8  # 非常危险
    EXTREME = 9      # 极端危险
    CATASTROPHIC = 10 # 灾难性风险

@dataclass
class CommandAnalysis:
    """命令分析结果 - 整合ai_terminal_system.py和intelligent_executor.py的解析结果"""
    raw_command: str                    # 原始命令
    normalized_command: str             # 规范化后的命令
    intent: CommandIntent               # 命令意图
    category: CommandCategory           # 命令类别
    complexity: CommandComplexity       # 复杂度
    parameters: Dict[str, Any]          # 参数
    safe_to_execute: bool               # 是否安全可执行
    confirmation_needed: bool           # 是否需要确认
    suggested_commands: List[str]       # 建议命令
    risk_level: RiskLevel               # 风险等级
    execution_plan: Optional[str] = None  # 执行计划
    session_id: Optional[str] = None    # 会话ID
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

@dataclass
class CommandResult:
    """命令执行结果 - 统一执行结果格式"""
    success: bool                       # 是否成功
    output: str                         # 输出内容
    error: str                          # 错误信息
    exit_code: int                      # 退出代码
    execution_time: float               # 执行时间
    command: str                        # 执行的命令
    process_id: Optional[int] = None    # 进程ID
    warnings: List[str] = field(default_factory=list)  # 警告信息
    suggestions: List[str] = field(default_factory=list)  # 后续建议
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据

@dataclass
class ExecutionContext:
    """执行上下文 - 统一上下文信息"""
    working_directory: str              # 工作目录
    user: str                           # 用户
    home_directory: str                 # 家目录
    system_platform: str                # 系统平台
    python_version: str                 # Python版本
    environment_vars: Dict[str, str]    # 环境变量
    sudo_required: bool = False         # 是否需要sudo
    writable: bool = True               # 当前目录是否可写
    terminal_type: str = "local"        # 终端类型
    session_id: Optional[str] = None    # 会话ID

@dataclass
class ProcessInfo:
    """进程信息 - 用于进程监控"""
    process_id: int                     # 进程ID
    command: str                        # 命令
    start_time: float                   # 启动时间
    end_time: Optional[float] = None    # 结束时间
    status: str = "running"             # 状态
    cpu_percent: float = 0.0            # CPU使用率
    memory_mb: float = 0.0              # 内存使用(MB)
    exit_code: Optional[int] = None     # 退出代码
    session_id: Optional[str] = None    # 会话ID
    monitored: bool = False             # 是否被监控

@dataclass
class SafetyReport:
    """安全检查报告"""
    safe: bool                          # 是否安全
    risk_level: RiskLevel               # 风险等级
    requires_confirmation: bool         # 是否需要确认
    warnings: List[str]                 # 警告信息
    blocked: bool = False               # 是否被阻止
    rationale: Optional[str] = None     # 风险评估理由
    suggested_alternative: Optional[str] = None  # 建议的替代命令

@dataclass
class UserPattern:
    """用户模式 - 用户习惯学习"""
    command_pattern: str                # 命令模式
    usage_count: int                    # 使用次数
    success_count: int                  # 成功次数
    avg_execution_time: float           # 平均执行时间
    last_used: float                    # 最后使用时间
    preferred_flags: List[str] = field(default_factory=list)  # 常用标志
    common_arguments: List[str] = field(default_factory=list)  # 常用参数


@dataclass
class KnowledgeItem:
    """知识项 - 用于知识库存储"""
    title: str                              # 标题
    content: str                            # 内容
    id: Optional[int] = None                 # 知识项ID
    category: Optional[str] = None          # 分类
    tags: List[str] = field(default_factory=list)  # 标签
    source: str = "system"                  # 来源
    priority: int = 1                       # 优先级 (1-10)
    created_at: Optional[str] = None        # 创建时间
    updated_at: Optional[str] = None        # 更新时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class KnowledgeQuery:
    """知识查询条件"""
    keywords: List[str] = field(default_factory=list)  # 关键词列表
    category: Optional[str] = None          # 分类
    tags: List[str] = field(default_factory=list)  # 标签
    limit: Optional[int] = 10               # 结果限制
    offset: Optional[int] = 0               # 偏移量