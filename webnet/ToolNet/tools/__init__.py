"""
ToolNet 工具包 - 弥娅统一工具服务

> 符合模块化架构的工具系统
> - 所有工具集中在 ToolNet（服务层）
> - 各功能模块通过接口调用工具
> - AI 索引友好，易于发现和使用

功能域索引:
--------------

# 核心服务
- task_scheduler: 任务调度引擎
- backup_manager: 备份管理系统
- system_monitor: 系统监控
- workflow_engine: 工作流引擎
- file_classifier: 文件分类器

# 网络交互
- web_search: 网络搜索
- web_research: 深度网络调研
- api_client: API 客户端

# 社交平台（🌟 跨端共享）
- qq_tools: QQ点赞、消息（已迁移到 tools/qq/）
- wechat_tools: 微信交互（预留）
- discord_tools: Discord操作（预留）

# 办公文档
- excel_processor: Excel 处理
- pdf_docx_processor: PDF/Word 处理
- invoice_parser: 发票解析

# 可视化
- chart_generator: 图表生成
- data_analyzer: 数据分析

# 报表生成
- report_generator: 报表生成器

# 认证授权
- add_user: 添加用户
- remove_user: 移除用户
- check_permission: 检查权限
- grant_permission: 授予权限
- revoke_permission: 撤销权限
- list_permissions: 列出权限
- list_groups: 列出组

# 基础功能
- get_current_time: 获取当前时间
- get_user_info: 获取用户信息
- python_interpreter: Python解释器

# 生活记忆
- life_add_memory: 添加生活记忆
- life_delete_memory: 删除生活记忆
- life_list_nodes: 列出节点
- life_search_memory: 搜索生活记忆
- life_get_summary: 获取摘要
- life_get_mood: 获取心情
- life_set_mood: 设置心情
- life_get_health: 获取健康
- life_set_health: 设置健康
- life_get_state: 获取状态

# 记忆管理
- memory_add: 添加记忆
- memory_delete: 删除记忆
- memory_update: 更新记忆
- memory_list: 列出记忆
- auto_extract_memory: 自动提取记忆

# 消息工具
- send_message: 发送消息
- send_text_file: 发送文本文件
- send_url_file: 发送URL文件
- get_recent_messages: 获取最近消息

# 任务调度
- create_schedule_task: 创建定时任务
- delete_schedule_task: 删除定时任务
- list_schedule_tasks: 列出定时任务

# 娱乐功能
- get_leaderboard: 获取排行榜
- get_stats: 获取统计
- get_achievements: 获取成就
- check_balance: 检查余额
- transfer_currency: 转账

# 群组管理
- list_members: 列出成员
- add_member: 添加成员
- remove_member: 移除成员
- set_group_name: 设置群名称
- get_group_info: 获取群信息

# 知识库
- add_knowledge: 添加知识
- search_knowledge: 搜索知识
- delete_knowledge: 删除知识

# 认知系统
- get_profile: 获取认知档案
- search_profiles: 搜索档案
- search_events: 搜索事件

# 媒体工具
- bilibili_video: B站视频处理

# 跨终端
- cross_terminal: 跨终端操作

# 注意：终端命令模块由 terminal/ 和 terminal_net/ 提供
"""

from .core import *
from .network import *
from .office import *
from .terminal import *
from .visualization import *
from .social import *
from .reporting import *
from .auth import *
from .basic import *
from .life import *
from .memory import *
from .message import *
from .scheduler import *
from .terminal_net import *
from .entertainment import *
from .group import *
from .knowledge import *
from .cognitive import *
from .bilibili import *
from .cross_terminal import *
from .web_search import *

__all__ = [
    # 核心服务
    "TaskScheduler",
    "BackupManager",
    "SystemMonitor",
    "WorkflowEngine",
    "FileClassifier",
    # 网络交互
    "WebSearch",
    "WebResearch",
    "APIClient",
    # 社交平台
    "SocialBase",
    # 办公文档
    "ExcelProcessor",
    "PDFDocxProcessor",
    "InvoiceParser",
    # 可视化
    "ChartGenerator",
    "DataAnalyzer",
    # 报表生成
    "ReportGenerator",
]
