"""
弥娅系统信息工具

提供全面的系统信息查询和管理能力：
- 进程管理
- 端口和网络连接
- 服务管理（Windows sc/Linux systemctl）
- 系统日志
- 性能监控
"""

import subprocess
import psutil
import platform
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from webnet.ToolNet.base import BaseTool, ToolContext

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """进程信息"""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    create_time: float
    cmdline: List[str]


class SystemInfoTool(BaseTool):
    """
    系统信息工具

    功能：
    - list_processes: 列出运行中的进程
    - find_process: 查找指定进程
    - kill_process: 终止进程
    - list_ports: 列出端口和连接
    - find_port: 查找占用指定端口的进程
    - system_info: 获取系统基本信息
    - disk_usage: 磁盘使用情况
    - memory_usage: 内存使用情况
    """

    def __init__(self):
        super().__init__()
        self.name = "system_info"

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "system_info",
            "description": """【系统信息管理工具】

提供全面的系统信息查询和管理能力。

【功能列表】
1. list_processes - 列出运行中的进程
2. find_process - 查找指定进程（按名称）
3. kill_process - 终止指定进程（按PID或名称）
4. list_ports - 列出所有端口和网络连接
5. find_port - 查找占用指定端口的进程
6. system_info - 获取系统基本信息
7. disk_usage - 磁盘使用情况
8. memory_usage - 内存使用情况
9. network_connections - 网络连接列表

【使用方式】
直接调用对应操作，传入参数即可。

【注意】
- kill_process 需要谨慎使用，会终止进程
- 列出进程可能会有较多输出
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": """操作类型，可选值：
- list_processes: 列出所有进程（可指定数量）
- find_process: 查找进程（按名称关键词）
- kill_process: 终止进程（PID或名称）
- list_ports: 列出端口和连接
- find_port: 查找占用端口的进程
- system_info: 系统基本信息
- disk_usage: 磁盘使用
- memory_usage: 内存使用
- network_connections: 网络连接""",
                    },
                    "params": {
                        "type": "object",
                        "description": "操作参数，根据operation不同而不同",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "限制返回数量（list_processes）",
                            },
                            "name": {
                                "type": "string",
                                "description": "进程名称关键词（find_process）",
                            },
                            "pid": {
                                "type": "integer",
                                "description": "进程PID（kill_process）",
                            },
                            "port": {
                                "type": "integer",
                                "description": "端口号（find_port）",
                            },
                            "force": {
                                "type": "boolean",
                                "description": "是否强制终止（kill_process）",
                            },
                        },
                    },
                },
                "required": ["operation"],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        operation = args.get("operation", "")
        params = args.get("params", {})

        try:
            if operation == "list_processes":
                return await self._list_processes(params)
            elif operation == "find_process":
                return await self._find_process(params)
            elif operation == "kill_process":
                return await self._kill_process(params)
            elif operation == "list_ports":
                return await self._list_ports(params)
            elif operation == "find_port":
                return await self._find_port(params)
            elif operation == "system_info":
                return await self._system_info(params)
            elif operation == "disk_usage":
                return await self._disk_usage(params)
            elif operation == "memory_usage":
                return await self._memory_usage(params)
            elif operation == "network_connections":
                return await self._network_connections(params)
            else:
                return f"❌ 未知操作: {operation}\n\n可用操作: list_processes, find_process, kill_process, list_ports, find_port, system_info, disk_usage, memory_usage, network_connections"
        except Exception as e:
            logger.error(f"系统信息操作失败: {e}", exc_info=True)
            return f"❌ 操作失败: {str(e)}"

    async def _list_processes(self, params: Dict) -> str:
        limit = params.get("limit", 50)

        try:
            processes = []
            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cpu_percent",
                    "memory_percent",
                    "status",
                    "create_time",
                    "cmdline",
                ]
            ):
                try:
                    info = proc.info
                    processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"],
                            "cpu": info["cpu_percent"],
                            "mem": info["memory_percent"],
                            "status": info["status"],
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            processes.sort(key=lambda x: x["cpu"], reverse=True)

            header = f"{'PID':>8} {'名称':<30} {'CPU%':>8} {'内存%':>8} {'状态':<10}"
            lines = [header, "-" * 70]

            for p in processes[:limit]:
                lines.append(
                    f"{p['pid']:>8} {p['name']:<30} {p['cpu']:>8.1f} {p['mem']:>8.1f} {p['status']:<10}"
                )

            return (
                f"📊 运行中的进程（按CPU使用率排序，显示前{limit}个）：\n\n"
                + "\n".join(lines)
            )
        except Exception as e:
            return f"❌ 获取进程列表失败: {e}"

    async def _find_process(self, params: Dict) -> str:
        name = params.get("name", "").lower()
        if not name:
            return "❌ 请提供进程名称（name参数）"

        try:
            matches = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent", "cmdline"]
            ):
                try:
                    info = proc.info
                    if name in info["name"].lower():
                        matches.append(
                            {
                                "pid": info["pid"],
                                "name": info["name"],
                                "cpu": info["cpu_percent"],
                                "mem": info["memory_percent"],
                                "cmdline": " ".join(info["cmdline"])
                                if info["cmdline"]
                                else "",
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if not matches:
                return f"🔍 未找到包含 '{name}' 的进程"

            lines = [f"🔍 找到 {len(matches)} 个匹配进程:\n"]
            for m in matches[:20]:
                lines.append(
                    f"PID: {m['pid']} | CPU: {m['cpu']:.1f}% | 内存: {m['mem']:.1f}%"
                )
                lines.append(f"  名称: {m['name']}")
                if m["cmdline"]:
                    lines.append(f"  命令: {m['cmdline'][:100]}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            return f"❌ 查找进程失败: {e}"

    async def _kill_process(self, params: Dict) -> str:
        pid = params.get("pid")
        name = params.get("name", "").lower()
        force = params.get("force", False)

        try:
            if pid:
                proc = psutil.Process(pid)
                proc_name = proc.name()
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                return f"✅ 已终止进程 PID={pid} ({proc_name})"
            elif name:
                killed = []
                for proc in psutil.process_iter():
                    try:
                        if name in proc.name().lower():
                            if force:
                                proc.kill()
                            else:
                                proc.terminate()
                            killed.append(f"{proc.pid}:{proc.name()}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                if killed:
                    return f"✅ 已终止 {len(killed)} 个进程:\n" + "\n".join(killed)
                else:
                    return f"🔍 未找到进程: {name}"
            else:
                return "❌ 请提供 PID 或进程名称"
        except Exception as e:
            return f"❌ 终止进程失败: {e}"

    async def _list_ports(self, params: Dict) -> str:
        try:
            connections = psutil.net_connections(kind="inet")

            lines = [
                f"{'协议':<6} {'本地地址':<25} {'远程地址':<25} {'状态':<15} {'PID':<8}"
            ]
            lines.append("-" * 90)

            for conn in connections[:100]:
                if conn.laddr:
                    local = f"{conn.laddr.ip}:{conn.laddr.port}"
                else:
                    local = "-"

                if conn.raddr:
                    remote = f"{conn.raddr.ip}:{conn.raddr.port}"
                else:
                    remote = "-"

                pid = str(conn.pid) if conn.pid else "-"
                lines.append(
                    f"{conn.type.name:<6} {local:<25} {remote:<25} {conn.status:<15} {pid:<8}"
                )

            return f"🔌 网络连接（显示前100个）：\n\n" + "\n".join(lines)
        except Exception as e:
            return f"❌ 获取端口列表失败: {e}"

    async def _find_port(self, params: Dict) -> str:
        port = params.get("port")
        if not port:
            return "❌ 请提供端口号（port参数）"

        try:
            matches = []
            for conn in psutil.net_connections(kind="inet"):
                if conn.laddr and conn.laddr.port == port:
                    try:
                        proc = psutil.Process(conn.pid) if conn.pid else None
                        matches.append(
                            {
                                "protocol": conn.type.name,
                                "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                                "remote": f"{conn.raddr.ip}:{conn.raddr.port}"
                                if conn.raddr
                                else "-",
                                "status": conn.status,
                                "pid": conn.pid,
                                "name": proc.name() if proc else "-",
                            }
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            if not matches:
                return f"🔌 端口 {port} 未被占用"

            lines = [f"🔌 端口 {port} 被以下进程占用:\n"]
            for m in matches:
                lines.append(
                    f"协议: {m['protocol']} | 状态: {m['status']} | PID: {m['pid']}"
                )
                lines.append(f"  进程: {m['name']}")
                lines.append(f"  本地: {m['local']} -> {m['remote']}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            return f"❌ 查找端口失败: {e}"

    async def _system_info(self, params: Dict) -> str:
        try:
            uname = platform.uname()
            cpu_count = psutil.cpu_count()
            boot_time = psutil.boot_time()
            uptime = (psutil.time.time() - boot_time) / 3600

            info = f"""🖥️ 系统信息

【基本信息】
操作系统: {uname.system} {uname.release}
主机名: {uname.node}
架构: {uname.machine}
处理器: {uname.processor}

【CPU】
核心数: {cpu_count} (物理: {psutil.cpu_count(logical=False)})
当前使用率: {psutil.cpu_percent(interval=0.1):.1f}%

【运行时间】
已运行: {uptime:.1f} 小时

【Python】
版本: {platform.python_version()}
实现: {platform.python_implementation()}
"""
            return info
        except Exception as e:
            return f"❌ 获取系统信息失败: {e}"

    async def _disk_usage(self, params: Dict) -> str:
        try:
            partitions = psutil.disk_partitions()
            lines = ["💾 磁盘使用情况\n"]

            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    lines.append(f"📁 {p.mountpoint} ({p.fstype})")
                    lines.append(f"   总容量: {usage.total / (1024**3):.2f} GB")
                    lines.append(
                        f"   已使用: {usage.used / (1024**3):.2f} GB ({usage.percent:.1f}%)"
                    )
                    lines.append(f"   可用: {usage.free / (1024**3):.2f} GB")
                    lines.append("")
                except PermissionError:
                    pass

            return "\n".join(lines)
        except Exception as e:
            return f"❌ 获取磁盘使用情况失败: {e}"

    async def _memory_usage(self, params: Dict) -> str:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            info = f"""🧠 内存使用情况

【物理内存】
总容量: {mem.total / (1024**3):.2f} GB
已使用: {mem.used / (1024**3):.2f} GB ({mem.percent:.1f}%)
可用: {mem.available / (1024**3):.2f} GB

【交换内存】
总容量: {swap.total / (1024**3):.2f} GB
已使用: {swap.used / (1024**3):.2f} GB ({swap.percent:.1f}%)
"""
            return info
        except Exception as e:
            return f"❌ 获取内存使用情况失败: {e}"

    async def _network_connections(self, params: Dict) -> str:
        try:
            stats = psutil.net_io_counters()

            info = f"""🌐 网络统计

发送: {stats.bytes_sent / (1024**2):.2f} MB
接收: {stats.bytes_recv / (1024**2):.2f} MB
数据包: 发送 {stats.packets_sent}, 接收 {stats.packets_recv}
错误: 发送 {stats.errout}, 接收 {stats.errin}
丢弃: 发送 {stats.dropout}, 接收 {stats.dropin}
"""
            return info
        except Exception as e:
            return f"❌ 获取网络统计失败: {e}"


_system_info_tool_instance: Optional[SystemInfoTool] = None


def get_system_info_tool() -> SystemInfoTool:
    """获取系统信息工具单例"""
    global _system_info_tool_instance
    if _system_info_tool_instance is None:
        _system_info_tool_instance = SystemInfoTool()
    return _system_info_tool_instance
