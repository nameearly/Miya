"""
Docker命令执行沙箱 - 安全加固模块
================================

该模块提供基于Docker的隔离命令执行环境，用于安全执行不信任的命令。
通过容器隔离、资源限制、网络限制和安全检查，防止命令执行导致的系统安全问题。

设计目标:
1. 完全隔离的命令执行环境
2. 严格的资源限制（CPU、内存、磁盘、网络）
3. 安全的命令白名单和黑名单
4. 执行结果审计和日志记录
5. 自动清理和超时控制
"""

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SandboxStatus(Enum):
    """沙箱状态"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


class SecurityLevel(Enum):
    """安全级别"""
    LOW = "low"      # 限制较少，适合可信命令
    MEDIUM = "medium" # 中等限制
    HIGH = "high"    # 严格限制，适合不信任命令
    PARANOID = "paranoid"  # 偏执级别，最大限制


@dataclass
class ResourceLimits:
    """资源限制配置"""
    cpu_percent: float = 50.0  # CPU使用率限制
    memory_mb: int = 512       # 内存限制（MB）
    disk_mb: int = 100         # 磁盘空间限制（MB）
    network_enabled: bool = False  # 是否允许网络访问
    read_only: bool = True     # 是否只读文件系统
    max_processes: int = 100   # 最大进程数
    max_execution_time: int = 300  # 最大执行时间（秒）
    
    @classmethod
    def from_security_level(cls, level: SecurityLevel) -> "ResourceLimits":
        """根据安全级别创建资源限制"""
        if level == SecurityLevel.LOW:
            return cls(
                cpu_percent=100.0,
                memory_mb=2048,
                disk_mb=500,
                network_enabled=True,
                read_only=False,
                max_processes=500,
                max_execution_time=600
            )
        elif level == SecurityLevel.MEDIUM:
            return cls(
                cpu_percent=75.0,
                memory_mb=1024,
                disk_mb=200,
                network_enabled=True,
                read_only=True,
                max_processes=200,
                max_execution_time=300
            )
        elif level == SecurityLevel.HIGH:
            return cls(
                cpu_percent=50.0,
                memory_mb=512,
                disk_mb=100,
                network_enabled=False,
                read_only=True,
                max_processes=100,
                max_execution_time=180
            )
        else:  # PARANOID
            return cls(
                cpu_percent=25.0,
                memory_mb=256,
                disk_mb=50,
                network_enabled=False,
                read_only=True,
                max_processes=50,
                max_execution_time=60
            )


@dataclass
class CommandResult:
    """命令执行结果"""
    status: SandboxStatus
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float  # 执行时间（秒）
    resource_usage: Dict[str, Any]  # 资源使用情况
    container_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SandboxConfig:
    """沙箱配置"""
    base_image: str = "alpine:latest"  # 基础镜像
    security_level: SecurityLevel = SecurityLevel.HIGH
    resource_limits: Optional[ResourceLimits] = None
    allowed_commands: List[str] = field(default_factory=list)  # 允许的命令白名单
    denied_commands: List[str] = field(default_factory=list)   # 拒绝的命令黑名单
    allowed_networks: List[str] = field(default_factory=lambda: ["127.0.0.1"])  # 允许的网络
    volume_mounts: Dict[str, str] = field(default_factory=dict)  # 卷挂载（主机:容器）
    environment_vars: Dict[str, str] = field(default_factory=dict)  # 环境变量
    working_directory: str = "/workspace"  # 工作目录
    cleanup: bool = True  # 执行后是否清理容器
    log_level: str = "INFO"


class CommandValidator:
    """命令验证器"""
    
    DANGEROUS_COMMANDS = [
        "rm -rf /", "rm -rf /*", "rm -rf .",  # 危险删除命令
        "dd if=/dev/zero", "dd of=/dev/sda",  # 磁盘操作
        "mkfs", "fdisk", "parted",            # 分区命令
        "chmod 777 /", "chmod -R 777 /",      # 危险权限命令
        "shutdown", "reboot", "poweroff",     # 系统控制命令
        "init", "telinit",                    # 系统初始化
        "mount", "umount",                    # 挂载命令
        "insmod", "rmmod",                    # 内核模块
        "iptables", "firewall-cmd",           # 防火墙
        "useradd", "userdel", "groupadd",     # 用户管理
        "passwd",                             # 密码修改
        "crontab",                            # 定时任务
        "systemctl", "service",               # 服务管理
        "docker", "podman", "containerd",     # 容器管理
        "kubectl", "helm",                    # Kubernetes
    ]
    
    def __init__(self, allowed_commands: Optional[List[str]] = None, denied_commands: Optional[List[str]] = None):
        self.allowed_commands = allowed_commands or []
        self.denied_commands = denied_commands or []
        
        # 构建危险命令模式
        self.dangerous_patterns = [
            re.compile(r'rm\s+-rf\s+/.*', re.IGNORECASE),
            re.compile(r'chmod\s+[0-7]{3,4}\s+/.*', re.IGNORECASE),
            re.compile(r'dd\s+.*(/dev/[a-z]+)', re.IGNORECASE),
        ]
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """验证命令是否安全"""
        command = command.strip()
        
        # 检查空命令
        if not command:
            return False, "命令不能为空"
        
        # 检查白名单（如果有）
        if self.allowed_commands:
            command_base = command.split()[0]
            if command_base not in self.allowed_commands:
                return False, f"命令不在白名单中: {command_base}"
        
        # 检查黑名单
        for denied in self.denied_commands:
            if command.startswith(denied):
                return False, f"命令在黑名单中: {denied}"
        
        # 检查危险命令列表
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command.lower():
                return False, f"检测到危险命令: {dangerous}"
        
        # 检查危险模式
        for pattern in self.dangerous_patterns:
            if pattern.search(command):
                return False, f"检测到危险命令模式: {pattern.pattern}"
        
        # 检查命令注入尝试
        injection_patterns = [
            r';\s*', r'&&\s*', r'\|\|\s*', r'`.*`', r'\$\(.*\)',  # 命令分隔符
            r'>\s*/dev/', r'>>\s*/dev/',                          # 设备重定向
            r'cat\s+>/etc/', r'echo\s+.*>>\s*/etc/',              # 系统文件写入
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, command):
                return False, f"检测到命令注入尝试: {pattern}"
        
        return True, "命令验证通过"


class DockerSandbox(ABC):
    """Docker沙箱抽象基类"""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.resource_limits = config.resource_limits or ResourceLimits.from_security_level(config.security_level)
        self.validator = CommandValidator(config.allowed_commands, config.denied_commands)
        self.container_id: Optional[str] = None
        
    @abstractmethod
    async def execute_command(self, command: str, input_data: Optional[str] = None) -> CommandResult:
        """执行命令"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """清理沙箱"""
        pass
    
    def validate_and_sanitize_command(self, command: str) -> Tuple[str, str]:
        """验证和清理命令"""
        # 验证命令
        is_valid, message = self.validator.validate_command(command)
        if not is_valid:
            raise ValueError(f"命令验证失败: {message}")
        
        # 清理命令：移除危险字符和多余空格
        command = command.strip()
        
        # 移除多个连续空格
        command = re.sub(r'\s+', ' ', command)
        
        # 限制命令长度
        if len(command) > 4096:
            raise ValueError(f"命令过长: {len(command)} 字符")
        
        return command, message


class DockerCLISandbox(DockerSandbox):
    """基于Docker CLI的沙箱实现"""
    
    def __init__(self, config: SandboxConfig):
        super().__init__(config)
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        
    async def _check_docker_available(self) -> bool:
        """检查Docker是否可用"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"检查Docker可用性失败: {e}")
            return False
    
    async def _pull_image_if_needed(self):
        """如果需要，拉取基础镜像"""
        # 检查镜像是否已存在
        check_cmd = ["docker", "images", "-q", self.config.base_image]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            if not stdout.strip():  # 镜像不存在
                logger.info(f"拉取Docker镜像: {self.config.base_image}")
                
                proc = await asyncio.create_subprocess_exec(
                    "docker", "pull", self.config.base_image,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    raise RuntimeError(f"拉取镜像失败: {stderr.decode()}")
        except Exception as e:
            logger.error(f"检查/拉取镜像失败: {e}")
            raise
    
    async def _create_container(self) -> str:
        """创建Docker容器"""
        # 创建临时目录用于卷挂载
        self._temp_dir = tempfile.TemporaryDirectory(prefix="docker_sandbox_")
        temp_path = self._temp_dir.name
        
        # 构建Docker命令
        cmd = ["docker", "run", "-d", "--rm"]
        
        # 添加资源限制
        cmd.extend(["--cpus", str(self.resource_limits.cpu_percent / 100.0)])
        cmd.extend(["--memory", f"{self.resource_limits.memory_mb}m"])
        cmd.extend(["--memory-swap", f"{self.resource_limits.memory_mb}m"])  # 禁用swap
        
        # 添加进程限制
        cmd.extend(["--pids-limit", str(self.resource_limits.max_processes)])
        
        # 添加网络限制
        if not self.resource_limits.network_enabled:
            cmd.append("--network=none")
        
        # 添加只读文件系统
        if self.resource_limits.read_only:
            cmd.append("--read-only")
        
        # 添加安全选项
        cmd.extend([
            "--security-opt", "no-new-privileges:true",
            "--cap-drop", "ALL",
            "--cap-add", "CHOWN",
            "--cap-add", "DAC_OVERRIDE",
            "--cap-add", "FOWNER",
            "--cap-add", "FSETID",
            "--cap-add", "SETGID",
            "--cap-add", "SETUID",
            "--cap-add", "SETFCAP",
        ])
        
        # 添加卷挂载
        for host_path, container_path in self.config.volume_mounts.items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # 添加临时工作目录
        cmd.extend(["-v", f"{temp_path}:{self.config.working_directory}"])
        
        # 添加环境变量
        for key, value in self.config.environment_vars.items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # 添加基础镜像和工作目录
        cmd.extend([self.config.base_image, "sleep", "infinity"])
        
        logger.debug(f"创建容器命令: {' '.join(cmd)}")
        
        # 执行命令
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"创建容器失败: {stderr.decode()}")
        
        container_id = stdout.decode().strip()
        logger.info(f"创建容器成功: {container_id[:12]}")
        
        return container_id
    
    async def execute_command(self, command: str, input_data: Optional[str] = None) -> CommandResult:
        """执行命令"""
        start_time = time.time()
        
        try:
            # 验证命令
            sanitized_command, validation_message = self.validate_and_sanitize_command(command)
            
            # 检查Docker可用性
            if not await self._check_docker_available():
                return CommandResult(
                    status=SandboxStatus.FAILED,
                    exit_code=-1,
                    stdout="",
                    stderr="Docker不可用",
                    execution_time=time.time() - start_time,
                    resource_usage={},
                    error_message="Docker不可用"
                )
            
            # 拉取镜像（如果需要）
            await self._pull_image_if_needed()
            
            # 创建容器
            if not self.container_id:
                self.container_id = await self._create_container()
            
            # 准备命令执行
            exec_cmd = ["docker", "exec"]
            
            # 添加工作目录
            exec_cmd.extend(["-w", self.config.working_directory])
            
            # 添加环境变量
            for key, value in self.config.environment_vars.items():
                exec_cmd.extend(["-e", f"{key}={value}"])
            
            # 添加容器ID和命令
            exec_cmd.extend([self.container_id, "sh", "-c", sanitized_command])
            
            logger.debug(f"执行命令: {' '.join(exec_cmd)}")
            
            # 执行命令（带超时）
            try:
                proc = await asyncio.create_subprocess_exec(
                    *exec_cmd,
                    stdin=asyncio.subprocess.PIPE if input_data else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # 设置超时
                timeout = self.resource_limits.max_execution_time
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(input_data.encode() if input_data else None),
                        timeout=timeout
                    )
                    exit_code = proc.returncode
                    status = SandboxStatus.COMPLETED if exit_code == 0 else SandboxStatus.FAILED
                    
                except asyncio.TimeoutError:
                    # 超时，杀死进程
                    proc.kill()
                    await proc.wait()
                    
                    # 停止容器
                    await self._stop_container()
                    
                    return CommandResult(
                        status=SandboxStatus.TIMEOUT,
                        exit_code=-1,
                        stdout="",
                        stderr=f"命令执行超时 ({timeout}秒)",
                        execution_time=time.time() - start_time,
                        resource_usage={},
                        container_id=self.container_id,
                        error_message="执行超时"
                    )
                
                # 获取资源使用情况
                resource_usage = await self._get_container_stats()
                
                execution_time = time.time() - start_time
                
                return CommandResult(
                    status=status,
                    exit_code=exit_code,
                    stdout=stdout.decode(errors='ignore'),
                    stderr=stderr.decode(errors='ignore'),
                    execution_time=execution_time,
                    resource_usage=resource_usage,
                    container_id=self.container_id
                )
                
            except Exception as e:
                logger.error(f"命令执行异常: {e}")
                return CommandResult(
                    status=SandboxStatus.FAILED,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    execution_time=time.time() - start_time,
                    resource_usage={},
                    container_id=self.container_id,
                    error_message=f"执行异常: {e}"
                )
            
        except ValueError as e:
            # 命令验证失败
            return CommandResult(
                status=SandboxStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                resource_usage={},
                error_message=f"命令验证失败: {e}"
            )
        except Exception as e:
            logger.error(f"沙箱执行失败: {e}")
            return CommandResult(
                status=SandboxStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                resource_usage={},
                error_message=f"沙箱执行失败: {e}"
            )
    
    async def _get_container_stats(self) -> Dict[str, Any]:
        """获取容器资源使用情况"""
        if not self.container_id:
            return {}
        
        try:
            cmd = ["docker", "stats", self.container_id, "--no-stream", "--format", "json"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0 and stdout:
                stats = json.loads(stdout.decode())
                
                # 解析资源使用情况
                cpu_percent = float(stats.get("CPUPerc", "0%").rstrip('%'))
                memory_usage = stats.get("MemUsage", "0B / 0B").split('/')[0]
                
                # 转换内存使用量
                def parse_size(size_str):
                    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
                    for unit, multiplier in units.items():
                        if size_str.endswith(unit):
                            return float(size_str.rstrip(unit)) * multiplier
                    return float(size_str)
                
                memory_bytes = parse_size(memory_usage.strip())
                
                return {
                    "cpu_percent": cpu_percent,
                    "memory_bytes": memory_bytes,
                    "memory_mb": memory_bytes / (1024**2),
                    "network_io": stats.get("NetIO", "0B / 0B"),
                    "block_io": stats.get("BlockIO", "0B / 0B"),
                    "pids": int(stats.get("PIDs", "0")),
                }
            
        except Exception as e:
            logger.error(f"获取容器统计失败: {e}")
        
        return {}
    
    async def _stop_container(self):
        """停止容器"""
        if not self.container_id:
            return
        
        try:
            cmd = ["docker", "stop", "-t", "1", self.container_id]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            logger.info(f"停止容器: {self.container_id[:12]}")
            
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
        finally:
            self.container_id = None
    
    async def cleanup(self):
        """清理沙箱"""
        try:
            # 停止容器
            if self.container_id:
                await self._stop_container()
            
            # 清理临时目录
            if self._temp_dir:
                self._temp_dir.cleanup()
                self._temp_dir = None
            
            logger.info("沙箱清理完成")
            
        except Exception as e:
            logger.error(f"沙箱清理失败: {e}")


class SandboxManager:
    """沙箱管理器"""
    
    _instance = None
    _sandboxes: Dict[str, DockerSandbox] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def create_sandbox(
        cls,
        sandbox_id: str,
        config: Optional[SandboxConfig] = None
    ) -> DockerSandbox:
        """创建沙箱"""
        if sandbox_id in cls._sandboxes:
            logger.warning(f"沙箱已存在: {sandbox_id}")
            return cls._sandboxes[sandbox_id]
        
        config = config or SandboxConfig()
        sandbox = DockerCLISandbox(config)
        
        cls._sandboxes[sandbox_id] = sandbox
        logger.info(f"创建沙箱: {sandbox_id}")
        
        return sandbox
    
    @classmethod
    async def execute_in_sandbox(
        cls,
        sandbox_id: str,
        command: str,
        config: Optional[SandboxConfig] = None,
        input_data: Optional[str] = None
    ) -> CommandResult:
        """在沙箱中执行命令"""
        sandbox = await cls.create_sandbox(sandbox_id, config)
        
        try:
            result = await sandbox.execute_command(command, input_data)
            
            # 如果需要清理，执行后清理沙箱
            if sandbox.config.cleanup:
                await sandbox.cleanup()
                if sandbox_id in cls._sandboxes:
                    del cls._sandboxes[sandbox_id]
            
            return result
            
        except Exception as e:
            logger.error(f"沙箱执行失败: {e}")
            
            # 确保清理
            if sandbox_id in cls._sandboxes:
                sandbox = cls._sandboxes.pop(sandbox_id)
                await sandbox.cleanup()
            
            return CommandResult(
                status=SandboxStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                resource_usage={},
                error_message=f"沙箱执行失败: {e}"
            )
    
    @classmethod
    async def cleanup_sandbox(cls, sandbox_id: str):
        """清理特定沙箱"""
        if sandbox_id in cls._sandboxes:
            sandbox = cls._sandboxes.pop(sandbox_id)
            await sandbox.cleanup()
            logger.info(f"清理沙箱: {sandbox_id}")
    
    @classmethod
    async def cleanup_all(cls):
        """清理所有沙箱"""
        logger.info(f"清理所有沙箱，数量={len(cls._sandboxes)}")
        
        for sandbox_id in list(cls._sandboxes.keys()):
            await cls.cleanup_sandbox(sandbox_id)


# 便捷函数
async def execute_command_safely(
    command: str,
    security_level: SecurityLevel = SecurityLevel.HIGH,
    sandbox_id: Optional[str] = None,
    **kwargs
) -> CommandResult:
    """便捷函数：安全执行命令"""
    sandbox_id = sandbox_id or f"sandbox_{int(time.time())}"
    
    # 创建配置
    config = SandboxConfig(
        security_level=security_level,
        **kwargs
    )
    
    return await SandboxManager.execute_in_sandbox(
        sandbox_id=sandbox_id,
        command=command,
        config=config
    )


async def test_sandbox():
    """测试沙箱功能"""
    print("=== Docker沙箱测试 ===")
    
    # 测试安全命令
    safe_command = "echo 'Hello, Sandbox!' && ls -la /"
    
    print(f"执行安全命令: {safe_command}")
    result = await execute_command_safely(
        command=safe_command,
        security_level=SecurityLevel.HIGH,
        sandbox_id="test_safe"
    )
    
    print(f"状态: {result.status.value}")
    print(f"退出码: {result.exit_code}")
    print(f"执行时间: {result.execution_time:.2f}秒")
    print(f"标准输出:\n{result.stdout}")
    if result.stderr:
        print(f"标准错误:\n{result.stderr}")
    
    # 测试危险命令（应该被阻止）
    dangerous_command = "rm -rf /tmp/*"
    
    print(f"\n尝试执行危险命令: {dangerous_command}")
    try:
        result = await execute_command_safely(
            command=dangerous_command,
            security_level=SecurityLevel.HIGH,
            sandbox_id="test_dangerous"
        )
        
        print(f"结果: {result.status.value}")
        print(f"错误消息: {result.error_message}")
        
    except ValueError as e:
        print(f"命令验证失败（预期）: {e}")
    
    # 清理
    await SandboxManager.cleanup_all()
    print("\n测试完成，所有沙箱已清理")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_sandbox())