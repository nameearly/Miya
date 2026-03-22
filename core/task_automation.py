#!/usr/bin/env python3
"""
任务规划和自动化系统
让弥娅能够理解复杂任务并自动执行
"""

import asyncio
import os
import sys
import json
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import queue

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型"""
    FILE_MANAGEMENT = "file_management"      # 文件管理
    PROCESS_AUTOMATION = "process_automation"  # 进程自动化
    SYSTEM_MAINTENANCE = "system_maintenance"  # 系统维护
    DEVELOPMENT_WORKFLOW = "development_workflow"  # 开发工作流
    NETWORK_OPERATION = "network_operation"  # 网络操作
    CUSTOM_SCRIPT = "custom_script"          # 自定义脚本

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"          # 等待执行
    RUNNING = "running"          # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
    PAUSED = "paused"            # 已暂停

@dataclass
class TaskStep:
    """任务步骤"""
    name: str
    command: str
    description: str
    expected_outcome: str
    timeout: int = 60  # 超时时间（秒）
    retry_count: int = 3  # 重试次数
    critical: bool = True  # 是否为关键步骤

@dataclass
class TaskPlan:
    """任务计划"""
    id: str
    name: str
    description: str
    type: TaskType
    steps: List[TaskStep]
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    estimated_duration: int = 300  # 预计持续时间（秒）
    priority: int = 5  # 优先级 1-10

@dataclass
class TaskExecution:
    """任务执行"""
    task_id: str
    plan: TaskPlan
    status: TaskStatus
    current_step: int = 0
    results: List[Dict] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

class TaskAutomationSystem:
    """任务自动化系统"""
    
    def __init__(self, executor=None):
        self.executor = executor  # 智能执行器
        self.task_queue = queue.Queue()
        self.running_tasks: Dict[str, TaskExecution] = {}
        self.task_history: List[TaskExecution] = []
        self.task_templates = self._load_templates()
        
        # 启动任务处理线程
        self.task_thread = threading.Thread(
            target=self._process_tasks,
            daemon=True
        )
        self.task_thread.start()
        
        logger.info("任务自动化系统初始化完成")
    
    def _load_templates(self) -> Dict[str, TaskPlan]:
        """加载任务模板"""
        templates = {}
        
        # 文件管理模板
        templates["file_backup"] = TaskPlan(
            id="file_backup",
            name="文件备份",
            description="自动备份指定目录",
            type=TaskType.FILE_MANAGEMENT,
            steps=[
                TaskStep(
                    name="检查备份目录",
                    command="mkdir -p ~/backups/$(date +%Y%m%d)",
                    description="创建备份目录",
                    expected_outcome="备份目录创建成功"
                ),
                TaskStep(
                    name="备份文件",
                    command="cp -r {source_dir} ~/backups/$(date +%Y%m%d)/",
                    description="复制文件到备份目录",
                    expected_outcome="文件复制完成"
                ),
                TaskStep(
                    name="验证备份",
                    command="ls -la ~/backups/$(date +%Y%m%d)/ | wc -l",
                    description="检查备份文件数量",
                    expected_outcome="备份文件验证通过"
                )
            ]
        )
        
        # 系统维护模板
        templates["system_cleanup"] = TaskPlan(
            id="system_cleanup",
            name="系统清理",
            description="清理系统临时文件和日志",
            type=TaskType.SYSTEM_MAINTENANCE,
            steps=[
                TaskStep(
                    name="清理临时文件",
                    command="rm -rf /tmp/*",
                    description="删除临时文件",
                    expected_outcome="临时文件清理完成",
                    critical=False
                ),
                TaskStep(
                    name="清理日志文件",
                    command="find /var/log -name \"*.log\" -mtime +7 -delete",
                    description="删除7天前的日志文件",
                    expected_outcome="旧日志文件清理完成"
                ),
                TaskStep(
                    name="检查磁盘空间",
                    command="df -h",
                    description="查看磁盘使用情况",
                    expected_outcome="磁盘空间报告生成"
                )
            ]
        )
        
        # 开发工作流模板
        templates["development_setup"] = TaskPlan(
            id="development_setup",
            name="开发环境设置",
            description="设置Python开发环境",
            type=TaskType.DEVELOPMENT_WORKFLOW,
            steps=[
                TaskStep(
                    name="创建虚拟环境",
                    command="python -m venv venv",
                    description="创建Python虚拟环境",
                    expected_outcome="虚拟环境创建成功"
                ),
                TaskStep(
                    name="激活虚拟环境",
                    command="source venv/bin/activate",
                    description="激活虚拟环境",
                    expected_outcome="虚拟环境已激活"
                ),
                TaskStep(
                    name="安装依赖",
                    command="pip install -r requirements.txt",
                    description="安装项目依赖",
                    expected_outcome="依赖安装完成"
                )
            ]
        )
        
        return templates
    
    def create_task_from_natural_language(self, user_request: str) -> Optional[TaskPlan]:
        """从自然语言创建任务"""
        logger.info(f"从自然语言创建任务: {user_request}")
        
        # 分析用户请求
        task_type = self._analyze_request_type(user_request)
        
        if not task_type:
            logger.warning(f"无法识别任务类型: {user_request}")
            return None
        
        # 根据类型创建任务
        if task_type == TaskType.FILE_MANAGEMENT:
            return self._create_file_management_task(user_request)
        elif task_type == TaskType.SYSTEM_MAINTENANCE:
            return self._create_system_maintenance_task(user_request)
        elif task_type == TaskType.DEVELOPMENT_WORKFLOW:
            return self._create_development_task(user_request)
        else:
            return self._create_custom_task(user_request)
    
    def _analyze_request_type(self, request: str) -> Optional[TaskType]:
        """分析请求类型"""
        request_lower = request.lower()
        
        # 文件管理关键词
        file_keywords = ["备份", "复制", "移动", "整理", "清理", "归档", "backup", "copy", "move", "organize"]
        if any(keyword in request_lower for keyword in file_keywords):
            return TaskType.FILE_MANAGEMENT
        
        # 系统维护关键词
        system_keywords = ["清理", "优化", "维护", "更新", "升级", "clean", "optimize", "maintain", "update"]
        if any(keyword in request_lower for keyword in system_keywords):
            return TaskType.SYSTEM_MAINTENANCE
        
        # 开发工作流关键词
        dev_keywords = ["开发", "部署", "测试", "构建", "环境", "develop", "deploy", "test", "build", "environment"]
        if any(keyword in request_lower for keyword in dev_keywords):
            return TaskType.DEVELOPMENT_WORKFLOW
        
        # 进程自动化关键词
        process_keywords = ["自动", "计划", "定时", "监控", "auto", "schedule", "monitor"]
        if any(keyword in request_lower for keyword in process_keywords):
            return TaskType.PROCESS_AUTOMATION
        
        return None
    
    def _create_file_management_task(self, request: str) -> TaskPlan:
        """创建文件管理任务"""
        # 提取源目录和目标目录
        source_match = re.search(r"从\s*(.+?)\s*(备份|复制|移动)", request)
        target_match = re.search(r"(到|至)\s*(.+)", request)
        
        source_dir = source_match.group(1) if source_match else "."
        target_dir = target_match.group(2) if target_match else f"~/backups/{datetime.now().strftime('%Y%m%d')}"
        
        task_id = f"file_mgmt_{int(time.time())}"
        
        return TaskPlan(
            id=task_id,
            name="文件管理任务",
            description=request,
            type=TaskType.FILE_MANAGEMENT,
            steps=[
                TaskStep(
                    name="检查目录",
                    command=f"ls -la {source_dir}",
                    description=f"检查源目录 {source_dir}",
                    expected_outcome="源目录存在且可访问"
                ),
                TaskStep(
                    name="创建目标目录",
                    command=f"mkdir -p {target_dir}",
                    description=f"创建目标目录 {target_dir}",
                    expected_outcome="目标目录创建成功"
                ),
                TaskStep(
                    name="执行操作",
                    command=f"cp -r {source_dir}/* {target_dir}/",
                    description=f"从 {source_dir} 复制到 {target_dir}",
                    expected_outcome="文件操作完成"
                ),
                TaskStep(
                    name="验证结果",
                    command=f"ls -la {target_dir} | wc -l",
                    description="验证操作结果",
                    expected_outcome="操作验证通过"
                )
            ]
        )
    
    def _create_system_maintenance_task(self, request: str) -> TaskPlan:
        """创建系统维护任务"""
        task_id = f"sys_maint_{int(time.time())}"
        
        return TaskPlan(
            id=task_id,
            name="系统维护",
            description=request,
            type=TaskType.SYSTEM_MAINTENANCE,
            steps=[
                TaskStep(
                    name="检查系统状态",
                    command="top -bn1 | head -5",
                    description="检查系统负载",
                    expected_outcome="系统状态报告"
                ),
                TaskStep(
                    name="清理临时文件",
                    command="rm -rf /tmp/* 2>/dev/null || true",
                    description="清理系统临时文件",
                    expected_outcome="临时文件清理完成"
                ),
                TaskStep(
                    name="检查磁盘空间",
                    command="df -h",
                    description="检查磁盘使用情况",
                    expected_outcome="磁盘空间报告"
                ),
                TaskStep(
                    name="更新软件包",
                    command="apt update && apt upgrade -y",
                    description="更新系统软件包",
                    expected_outcome="软件包更新完成"
                )
            ]
        )
    
    def _create_development_task(self, request: str) -> TaskPlan:
        """创建开发任务"""
        task_id = f"dev_{int(time.time())}"
        
        return TaskPlan(
            id=task_id,
            name="开发任务",
            description=request,
            type=TaskType.DEVELOPMENT_WORKFLOW,
            steps=[
                TaskStep(
                    name="检查项目结构",
                    command="ls -la",
                    description="检查当前项目结构",
                    expected_outcome="项目结构清晰"
                ),
                TaskStep(
                    name="检查依赖",
                    command="pip list",
                    description="检查已安装的依赖",
                    expected_outcome="依赖列表显示"
                ),
                TaskStep(
                    name="运行测试",
                    command="python -m pytest",
                    description="运行项目测试",
                    expected_outcome="测试通过"
                ),
                TaskStep(
                    name="构建项目",
                    command="python setup.py build",
                    description="构建项目",
                    expected_outcome="构建成功"
                )
            ]
        )
    
    def _create_custom_task(self, request: str) -> TaskPlan:
        """创建自定义任务"""
        task_id = f"custom_{int(time.time())}"
        
        return TaskPlan(
            id=task_id,
            name="自定义任务",
            description=request,
            type=TaskType.CUSTOM_SCRIPT,
            steps=[
                TaskStep(
                    name="分析请求",
                    command=f"echo '分析请求: {request}'",
                    description="分析用户请求",
                    expected_outcome="请求分析完成"
                ),
                TaskStep(
                    name="执行任务",
                    command=f"echo '执行任务: {request}'",
                    description="执行用户请求的任务",
                    expected_outcome="任务执行完成"
                ),
                TaskStep(
                    name="验证结果",
                    command="echo '任务完成'",
                    description="验证任务执行结果",
                    expected_outcome="任务验证通过"
                )
            ]
        )
    
    def schedule_task(self, task_plan: TaskPlan, delay_seconds: int = 0) -> str:
        """调度任务"""
        if delay_seconds > 0:
            # 延迟执行
            threading.Timer(
                delay_seconds,
                lambda: self.task_queue.put(task_plan)
            ).start()
            logger.info(f"任务 {task_plan.id} 将在 {delay_seconds} 秒后执行")
        else:
            # 立即执行
            self.task_queue.put(task_plan)
            logger.info(f"任务 {task_plan.id} 已加入队列")
        
        return task_plan.id
    
    def _process_tasks(self):
        """处理任务队列"""
        while True:
            try:
                task_plan = self.task_queue.get(timeout=1)
                self._execute_task(task_plan)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"任务处理异常: {e}")
    
    def _execute_task(self, task_plan: TaskPlan):
        """执行任务"""
        execution = TaskExecution(
            task_id=task_plan.id,
            plan=task_plan,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.running_tasks[task_plan.id] = execution
        
        logger.info(f"开始执行任务: {task_plan.name}")
        
        try:
            # 执行每个步骤
            for step_index, step in enumerate(task_plan.steps):
                execution.current_step = step_index
                
                logger.info(f"执行步骤 {step_index + 1}: {step.name}")
                
                # 执行命令
                result = self._execute_step(step)
                execution.results.append(result)
                
                # 检查步骤结果
                if not result["success"] and step.critical:
                    logger.error(f"关键步骤失败: {step.name}")
                    execution.status = TaskStatus.FAILED
                    execution.error_message = f"步骤失败: {step.name}"
                    break
            
            # 更新任务状态
            if execution.status == TaskStatus.RUNNING:
                execution.status = TaskStatus.COMPLETED
                logger.info(f"任务完成: {task_plan.name}")
            
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            execution.status = TaskStatus.FAILED
            execution.error_message = str(e)
        
        finally:
            execution.end_time = datetime.now()
            self.task_history.append(execution)
            
            if task_plan.id in self.running_tasks:
                del self.running_tasks[task_plan.id]
    
    def _execute_step(self, step: TaskStep) -> Dict[str, Any]:
        """执行步骤"""
        max_retries = step.retry_count
        last_error = None
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # 使用执行器或直接执行
                if self.executor:
                    result = asyncio.run(
                        self.executor.execute_intelligent(step.command)
                    )
                else:
                    # 直接执行
                    import subprocess
                    process = subprocess.run(
                        step.command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=step.timeout
                    )
                    
                    result = {
                        "success": process.returncode == 0,
                        "output": process.stdout,
                        "error": process.stderr,
                        "exit_code": process.returncode
                    }
                
                execution_time = time.time() - start_time
                
                result.update({
                    "step_name": step.name,
                    "attempt": attempt + 1,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
                
                if result["success"]:
                    logger.info(f"步骤 {step.name} 执行成功 (尝试 {attempt + 1})")
                    return result
                else:
                    last_error = result["error"]
                    logger.warning(f"步骤 {step.name} 执行失败 (尝试 {attempt + 1}): {last_error}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(2)  # 等待后重试
            
            except subprocess.TimeoutExpired:
                last_error = f"步骤超时 ({step.timeout}秒)"
                logger.warning(f"步骤 {step.name} 超时 (尝试 {attempt + 1})")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"步骤 {step.name} 异常 (尝试 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        # 所有重试都失败
        return {
            "step_name": step.name,
            "success": False,
            "output": "",
            "error": f"所有重试失败: {last_error}",
            "exit_code": -1,
            "attempt": max_retries,
            "execution_time": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            execution = self.running_tasks[task_id]
            return self._format_execution_status(execution)
        
        # 检查历史任务
        for execution in reversed(self.task_history):
            if execution.task_id == task_id:
                return self._format_execution_status(execution)
        
        return None
    
    def _format_execution_status(self, execution: TaskExecution) -> Dict[str, Any]:
        """格式化执行状态"""
        status = {
            "task_id": execution.task_id,
            "name": execution.plan.name,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "total_steps": len(execution.plan.steps),
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "error_message": execution.error_message,
            "results": execution.results
        }
        
        # 计算进度
        if execution.status == TaskStatus.RUNNING:
            status["progress"] = (execution.current_step / len(execution.plan.steps)) * 100
        elif execution.status == TaskStatus.COMPLETED:
            status["progress"] = 100
        else:
            status["progress"] = 0
        
        # 计算持续时间
        if execution.start_time:
            if execution.end_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
            else:
                duration = (datetime.now() - execution.start_time).total_seconds()
            status["duration_seconds"] = duration
        
        return status
    
    def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = []
        
        # 运行中的任务
        for execution in self.running_tasks.values():
            if status_filter is None or execution.status == status_filter:
                tasks.append(self._format_execution_status(execution))
        
        # 历史任务
        for execution in self.task_history:
            if status_filter is None or execution.status == status_filter:
                tasks.append(self._format_execution_status(execution))
        
        return tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.running_tasks:
            execution = self.running_tasks[task_id]
            execution.status = TaskStatus.CANCELLED
            execution.end_time = datetime.now()
            execution.error_message = "任务被用户取消"
            
            # 移动到历史
            self.task_history.append(execution)
            del self.running_tasks[task_id]
            
            logger.info(f"任务已取消: {task_id}")
            return True
        
        return False

# 自然语言任务创建器
class NaturalLanguageTaskCreator:
    """自然语言任务创建器"""
    
    def __init__(self, automation_system: TaskAutomationSystem):
        self.automation_system = automation_system
        self.task_patterns = self._load_patterns()
    
    def _load_patterns(self) -> List[Tuple[str, Callable]]:
        """加载任务模式"""
        patterns = [
            (r"(备份|backup)\s+(.+?)\s+(到|to)\s+(.+)", self._create_backup_task),
            (r"(清理|clean)\s+(.+?)\s+(的|of)?\s*(文件|files)?", self._create_cleanup_task),
            (r"(设置|setup)\s+(.+?)\s+(环境|environment)", self._create_setup_task),
            (r"(部署|deploy)\s+(.+?)\s+(项目|project)?", self._create_deploy_task),
            (r"(监控|monitor)\s+(.+?)\s+(进程|process)", self._create_monitor_task)
        ]
        return patterns
    
    def create_task(self, user_input: str) -> Optional[TaskPlan]:
        """从自然语言创建任务"""
        for pattern, creator in self.task_patterns:
            match = re.match(pattern, user_input, re.IGNORECASE)
            if match:
                return creator(match.groups())
        
        # 使用通用分析
        return self.automation_system.create_task_from_natural_language(user_input)
    
    def _create_backup_task(self, groups: Tuple) -> TaskPlan:
        """创建备份任务"""
        _, source, _, target = groups
        task_id = f"backup_{int(time.time())}"
        
        return TaskPlan(
            id=task_id,
            name=f"备份 {source} 到 {target}",
            description=f"备份 {source} 到 {target}",
            type=TaskType.FILE_MANAGEMENT,
            steps=[
                TaskStep(
                    name="检查源目录",
                    command=f"ls -la {source}",
                    description=f"检查源目录 {source}",
                    expected_outcome="源目录存在"
                ),
                TaskStep(
                    name="创建备份目录",
                    command=f"mkdir -p {target}",
                    description=f"创建备份目录 {target}",
                    expected_outcome="备份目录创建成功"
                ),
                TaskStep(
                    name="执行备份",
                    command=f"cp -r {source}/* {target}/",
                    description="复制文件到备份目录",
                    expected_outcome="备份完成"
                )
            ]
        )
    
    def _create_cleanup_task(self, groups: Tuple) -> TaskPlan:
        """创建清理任务"""
        _, target, *_ = groups
        task_id = f"cleanup_{int(time.time())}"
        
        return TaskPlan(
            id=task_id,
            name=f"清理 {target}",
            description=f"清理 {target} 中的文件",
            type=TaskType.SYSTEM_MAINTENANCE,
            steps=[
                TaskStep(
                    name="检查目录",
                    command=f"ls -la {target}",
                    description=f"检查 {target} 目录",
                    expected_outcome="目录检查完成"
                ),
                TaskStep(
                    name="清理临时文件",
                    command=f"find {target} -name \"*.tmp\" -o -name \"*.temp\" -delete",
                    description="清理临时文件",
                    expected_outcome="临时文件清理完成"
                ),
                TaskStep(
                    name="清理日志文件",
                    command=f"find {target} -name \"*.log\" -mtime +7 -delete",
                    description="清理旧日志文件",
                    expected_outcome="日志文件清理完成"
                )
            ]
        )

# 使用示例
def example_usage():
    """使用示例"""
    # 创建自动化系统
    automation = TaskAutomationSystem()
    
    # 创建自然语言任务创建器
    task_creator = NaturalLanguageTaskCreator(automation)
    
    # 从自然语言创建任务
    user_requests = [
        "备份当前目录到 ~/backups",
        "清理系统临时文件",
        "设置Python开发环境"
    ]
    
    for request in user_requests:
        print(f"\n处理请求: {request}")
        
        # 创建任务
        task_plan = task_creator.create_task(request)
        if task_plan:
            print(f"创建任务: {task_plan.name}")
            print(f"任务描述: {task_plan.description}")
            print(f"任务步骤: {len(task_plan.steps)} 个")
            
            # 调度任务
            task_id = automation.schedule_task(task_plan)
            print(f"任务ID: {task_id}")
            
            # 等待一会儿查看状态
            time.sleep(2)
            status = automation.get_task_status(task_id)
            if status:
                print(f"任务状态: {status['status']}")
                print(f"任务进度: {status.get('progress', 0):.1f}%")
        else:
            print("无法创建任务")
    
    # 列出所有任务
    print("\n所有任务:")
    tasks = automation.list_tasks()
    for task in tasks:
        print(f"  - {task['name']}: {task['status']} ({task.get('progress', 0):.1f}%)")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行示例
    example_usage()