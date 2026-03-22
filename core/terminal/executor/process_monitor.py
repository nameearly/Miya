#!/usr/bin/env python3
"""
进程监控器

监控和管理运行中的进程
"""

import logging
import time
import threading
import psutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..base.types import ProcessInfo

logger = logging.getLogger(__name__)


@dataclass
class ProcessMetrics:
    """进程指标"""
    pid: int
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_rss: int = 0  # RSS内存 (字节)
    memory_vms: int = 0  # VMS内存 (字节)
    num_threads: int = 0
    create_time: float = 0.0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    connections: List[Any] = field(default_factory=list)
    open_files: List[str] = field(default_factory=list)


class ProcessMonitor:
    """进程监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 监控的进程
        self.monitored_processes: Dict[int, Dict[str, Any]] = {}
        
        # 监控锁
        self.monitor_lock = threading.Lock()
        
        # 监控线程
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_running = False
        
        # 监控统计
        self.monitor_stats = {
            "total_monitored": 0,
            "currently_monitoring": 0,
            "cpu_alerts": 0,
            "memory_alerts": 0,
            "io_alerts": 0
        }
        
        # 警报配置
        self.alert_config = {
            "cpu_threshold": 90.0,      # CPU使用率阈值 (%)
            "memory_threshold": 80.0,   # 内存使用率阈值 (%)
            "io_threshold_mb": 100,     # IO阈值 (MB)
            "check_interval": 5.0,      # 检查间隔 (秒)
            "max_log_entries": 100      # 最大日志条目数
        }
        
        # 进程历史记录
        self.process_history: Dict[int, List[Dict[str, Any]]] = {}
        
        self.logger.info("进程监控器初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        with self.monitor_lock:
            if self.monitor_running:
                self.logger.warning("监控器已在运行")
                return
            
            self.monitor_running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="ProcessMonitor"
            )
            self.monitor_thread.start()
            
            self.logger.info("进程监控器已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        with self.monitor_lock:
            if not self.monitor_running:
                self.logger.warning("监控器未在运行")
                return
            
            self.monitor_running = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=10)
                self.monitor_thread = None
            
            self.logger.info("进程监控器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        self.logger.info("监控循环开始")
        
        while self.monitor_running:
            try:
                self._check_processes()
                time.sleep(self.alert_config["check_interval"])
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(10)  # 异常时等待更长时间
    
    def _check_processes(self):
        """检查进程"""
        with self.monitor_lock:
            pids_to_remove = []
            
            for pid, process_info in self.monitored_processes.items():
                try:
                    # 检查进程是否存在
                    if not psutil.pid_exists(pid):
                        pids_to_remove.append(pid)
                        self.logger.info(f"进程已结束 PID: {pid}")
                        continue
                    
                    # 获取进程对象
                    proc = psutil.Process(pid)
                    
                    # 收集指标
                    metrics = self._collect_metrics(proc)
                    
                    # 更新进程信息
                    process_info["metrics"] = metrics
                    process_info["last_check"] = time.time()
                    
                    # 检查警报
                    self._check_alerts(pid, process_info, metrics)
                    
                    # 记录历史
                    self._record_history(pid, metrics)
                    
                except psutil.NoSuchProcess:
                    pids_to_remove.append(pid)
                    self.logger.info(f"进程不存在 PID: {pid}")
                except Exception as e:
                    self.logger.error(f"检查进程失败 PID: {pid}: {e}")
            
            # 移除已结束的进程
            for pid in pids_to_remove:
                self._remove_process(pid)
    
    def _collect_metrics(self, proc: psutil.Process) -> ProcessMetrics:
        """收集进程指标"""
        try:
            with proc.oneshot():
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_info = proc.memory_info()
                memory_percent = proc.memory_percent()
                
                # IO统计
                io_counters = proc.io_counters()
                io_read_bytes = io_counters.read_bytes if io_counters else 0
                io_write_bytes = io_counters.write_bytes if io_counters else 0
                
                # 连接信息
                connections = []
                try:
                    connections = proc.connections()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                
                # 打开的文件
                open_files = []
                try:
                    open_files = [f.path for f in proc.open_files()]
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                
                return ProcessMetrics(
                    pid=proc.pid,
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_rss=memory_info.rss,
                    memory_vms=memory_info.vms,
                    num_threads=proc.num_threads(),
                    create_time=proc.create_time(),
                    io_read_bytes=io_read_bytes,
                    io_write_bytes=io_write_bytes,
                    connections=connections,
                    open_files=open_files
                )
        
        except Exception as e:
            self.logger.error(f"收集指标失败 PID: {proc.pid}: {e}")
            return ProcessMetrics(pid=proc.pid)
    
    def _check_alerts(self, pid: int, process_info: Dict[str, Any], metrics: ProcessMetrics):
        """检查警报条件"""
        alerts = []
        
        # CPU警报
        if metrics.cpu_percent > self.alert_config["cpu_threshold"]:
            alerts.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
            self.monitor_stats["cpu_alerts"] += 1
        
        # 内存警报
        if metrics.memory_percent > self.alert_config["memory_threshold"]:
            alerts.append(f"内存使用率过高: {metrics.memory_percent:.1f}%")
            self.monitor_stats["memory_alerts"] += 1
        
        # IO警报
        io_total_mb = (metrics.io_read_bytes + metrics.io_write_bytes) / (1024 * 1024)
        if io_total_mb > self.alert_config["io_threshold_mb"]:
            alerts.append(f"IO使用量过大: {io_total_mb:.1f}MB")
            self.monitor_stats["io_alerts"] += 1
        
        # 记录警报
        if alerts:
            alert_msg = f"进程警报 PID: {pid} - " + "; ".join(alerts)
            self.logger.warning(alert_msg)
            
            # 添加到进程信息
            process_info.setdefault("alerts", []).extend(alerts)
            
            # 触发警报回调
            if "alert_callback" in process_info:
                try:
                    process_info["alert_callback"](pid, alerts, metrics)
                except Exception as e:
                    self.logger.error(f"警报回调失败 PID: {pid}: {e}")
    
    def _record_history(self, pid: int, metrics: ProcessMetrics):
        """记录历史数据"""
        if pid not in self.process_history:
            self.process_history[pid] = []
        
        history_entry = {
            "timestamp": time.time(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "memory_rss_mb": metrics.memory_rss / (1024 * 1024),
            "io_read_mb": metrics.io_read_bytes / (1024 * 1024),
            "io_write_mb": metrics.io_write_bytes / (1024 * 1024)
        }
        
        self.process_history[pid].append(history_entry)
        
        # 限制历史记录数量
        if len(self.process_history[pid]) > self.alert_config["max_log_entries"]:
            self.process_history[pid] = self.process_history[pid][-self.alert_config["max_log_entries"]:]
    
    def _remove_process(self, pid: int):
        """移除进程"""
        if pid in self.monitored_processes:
            del self.monitored_processes[pid]
            self.monitor_stats["currently_monitoring"] -= 1
            
            # 保留历史记录一段时间
            if pid in self.process_history:
                # 可以在这里保存历史记录到文件
                pass
    
    def add_process(self, pid: int, command: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加进程到监控
        
        Args:
            pid: 进程ID
            command: 命令字符串
            metadata: 额外元数据
        """
        with self.monitor_lock:
            if pid in self.monitored_processes:
                self.logger.warning(f"进程已在监控中 PID: {pid}")
                return
            
            self.monitored_processes[pid] = {
                "pid": pid,
                "command": command,
                "metadata": metadata or {},
                "added_time": time.time(),
                "last_check": None,
                "metrics": None,
                "alerts": []
            }
            
            self.monitor_stats["total_monitored"] += 1
            self.monitor_stats["currently_monitoring"] += 1
            
            self.logger.info(f"开始监控进程 PID: {pid} - 命令: {command}")
            
            # 如果监控器未运行，启动它
            if not self.monitor_running:
                self.start_monitoring()
    
    def remove_process(self, pid: int):
        """从监控中移除进程"""
        with self.monitor_lock:
            self._remove_process(pid)
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """获取进程信息"""
        with self.monitor_lock:
            return self.monitored_processes.get(pid)
    
    def get_all_processes(self) -> List[Dict[str, Any]]:
        """获取所有监控的进程"""
        with self.monitor_lock:
            return list(self.monitored_processes.values())
    
    def get_process_metrics(self, pid: int) -> Optional[ProcessMetrics]:
        """获取进程指标"""
        process_info = self.get_process_info(pid)
        if process_info and "metrics" in process_info:
            return process_info["metrics"]
        return None
    
    def get_process_history(self, pid: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取进程历史记录"""
        if pid in self.process_history:
            history = self.process_history[pid]
            if limit:
                return history[-limit:]
            return history
        return []
    
    def set_alert_callback(self, pid: int, callback):
        """设置警报回调函数"""
        with self.monitor_lock:
            if pid in self.monitored_processes:
                self.monitored_processes[pid]["alert_callback"] = callback
                return True
            return False
    
    def update_alert_config(self, config: Dict[str, Any]):
        """更新警报配置"""
        with self.monitor_lock:
            self.alert_config.update(config)
            self.logger.info(f"警报配置已更新: {config}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        with self.monitor_lock:
            stats = self.monitor_stats.copy()
            stats["alert_config"] = self.alert_config.copy()
            stats["monitor_running"] = self.monitor_running
            stats["monitored_count"] = len(self.monitored_processes)
            return stats
    
    def clear_history(self, pid: Optional[int] = None):
        """清除历史记录"""
        with self.monitor_lock:
            if pid:
                if pid in self.process_history:
                    del self.process_history[pid]
                    self.logger.info(f"已清除进程历史 PID: {pid}")
            else:
                self.process_history.clear()
                self.logger.info("已清除所有历史记录")


# 单例实例
_global_process_monitor: Optional[ProcessMonitor] = None

def get_process_monitor() -> ProcessMonitor:
    """获取全局进程监控器实例"""
    global _global_process_monitor
    
    if _global_process_monitor is None:
        _global_process_monitor = ProcessMonitor()
    
    return _global_process_monitor