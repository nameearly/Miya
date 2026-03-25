"""
Skills 热重载模块

功能：
1. 监控 skills 目录文件变化
2. 自动重载修改的工具/智能体
3. 支持配置变更热更新

参考 Undefined 项目的实现
"""

import asyncio
import logging
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime

# 可选依赖：文件监控
try:
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler,
        FileModifiedEvent,
        FileCreatedEvent,
    )

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("[SkillsHotReload] watchdog 模块未安装，将使用轮询模式")

logger = logging.getLogger(__name__)


@dataclass
class SkillInfo:
    """技能信息"""

    name: str
    path: Path
    type: str  # tool, agent, toolset, command
    hash: str = ""
    last_modified: float = 0
    loaded_at: float = field(default_factory=time.time)
    reload_count: int = 0


class SkillFileHandler:
    """技能文件事件处理器（兼容有无watchdog）"""

    # 需要监控的文件
    WATCHED_FILES = {"config.json", "handler.py", "prompt.md", "intro.md"}
    # 忽略的目录
    IGNORE_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv"}

    def __init__(self, hot_reloader: "SkillsHotReloader"):
        self.hot_reloader = hot_reloader
        self.pending_reload: Dict[str, float] = {}  # 待重载的文件路径 -> 时间
        self.debounce_seconds = 2.0  # 防抖时间

        # 如果有watchdog，使用它
        if WATCHDOG_AVAILABLE:
            self._handler = _WatchdogHandler(self)

    @property
    def handler(self):
        """获取实际的watchdog处理器"""
        if WATCHDOG_AVAILABLE:
            return self._handler
        return None

    def should_process(self, path: str) -> bool:
        """判断是否处理该文件"""
        path_obj = Path(path)

        # 忽略目录
        for ignore_dir in self.IGNORE_DIRS:
            if ignore_dir in path_obj.parts:
                return False

        # 只处理指定文件
        return path_obj.name in self.WATCHED_FILES

    def _schedule_reload(self, file_path: str):
        """安排重载（带防抖）"""
        now = time.time()

        # 检查是否在防抖期内
        if file_path in self.pending_reload:
            if now - self.pending_reload[file_path] < self.debounce_seconds:
                return

        self.pending_reload[file_path] = now
        logger.info(f"[SkillsHotReload] 检测到文件变更: {file_path}")

        # 安排延迟执行
        asyncio.create_task(self._delayed_reload(file_path))

    async def _delayed_reload(self, file_path: str):
        """延迟执行重载"""
        await asyncio.sleep(self.debounce_seconds)

        # 再次检查是否需要重载
        if file_path in self.pending_reload:
            del self.pending_reload[file_path]
            await self.hot_reloader.reload_skill(file_path)


# 如果有watchdog，定义实际的处理器
if WATCHDOG_AVAILABLE:

    class _WatchdogHandler(FileSystemEventHandler):
        """实际的watchdog处理器"""

        def __init__(self, wrapper: SkillFileHandler):
            self.wrapper = wrapper

        def on_modified(self, event: FileModifiedEvent):
            if not event.is_directory and self.wrapper.should_process(event.src_path):
                self.wrapper._schedule_reload(event.src_path)

        def on_created(self, event: FileCreatedEvent):
            if not event.is_directory and self.wrapper.should_process(event.src_path):
                self.wrapper._schedule_reload(event.src_path)


class SkillsHotReloader:
    """Skills 热重载管理器"""

    def __init__(
        self,
        skills_dir: Optional[Path] = None,
        watch_subdirs: Optional[List[str]] = None,
        on_reload_callback: Optional[Callable] = None,
    ):
        """
        初始化热重载管理器

        Args:
            skills_dir: Skills 目录路径
            watch_subdirs: 要监控的子目录列表
            on_reload_callback: 重载回调函数
        """
        # 默认路径
        if skills_dir is None:
            self.skills_dir = (
                Path(__file__).parent.parent / "webnet" / "ToolNet" / "tools"
            )
        else:
            self.skills_dir = Path(skills_dir)

        # 默认监控子目录
        if watch_subdirs is None:
            self.watch_subdirs = [
                "basic",
                "terminal",
                "message",
                "group",
                "memory",
                "knowledge",
                "cognitive",
                "bilibili",
                "scheduler",
                "entertainment",
                "qq",
                "life",
                "network",
                "visualization",
            ]
        else:
            self.watch_subdirs = watch_subdirs

        self.on_reload_callback = on_reload_callback

        # 技能信息缓存
        self.skills_cache: Dict[str, SkillInfo] = {}

        # 统计信息
        self.stats = {
            "total_reloads": 0,
            "successful_reloads": 0,
            "failed_reloads": 0,
            "last_reload_time": None,
        }

        # 文件监控
        self.observer: Optional[Observer] = None
        self.is_running = False

        # 初始化文件哈希
        self._init_hashes()

    def _init_hashes(self):
        """初始化文件哈希"""
        if not self.skills_dir.exists():
            logger.warning(f"[SkillsHotReload] Skills目录不存在: {self.skills_dir}")
            return

        # 扫描所有技能文件
        for subdir in self.watch_subdirs:
            subdir_path = self.skills_dir / subdir
            if not subdir_path.exists():
                continue

            self._scan_directory(subdir_path)

        logger.info(f"[SkillsHotReload] 已初始化 {len(self.skills_cache)} 个技能文件")

    def _scan_directory(self, directory: Path):
        """扫描目录下的技能文件"""
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    # 检查是否是技能目录
                    config_file = item / "config.json"
                    if config_file.exists():
                        skill_name = item.name
                        skill_type = directory.name

                        self.skills_cache[f"{skill_type}/{skill_name}"] = SkillInfo(
                            name=skill_name,
                            path=item,
                            type=skill_type,
                            hash=self._calculate_hash(config_file),
                            last_modified=config_file.stat().st_mtime,
                        )
        except Exception as e:
            logger.error(f"[SkillsHotReload] 扫描目录失败 {directory}: {e}")

    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"[SkillsHotReload] 计算哈希失败 {file_path}: {e}")
            return ""

    async def reload_skill(self, file_path: str):
        """重载技能"""
        path_obj = Path(file_path)
        skill_dir = path_obj.parent

        # 查找对应的技能
        skill_key = None
        for key, info in self.skills_cache.items():
            if info.path == skill_dir:
                skill_key = key
                break

        if not skill_key:
            # 新文件，添加到缓存
            skill_key = f"unknown/{skill_dir.name}"
            self.skills_cache[skill_key] = SkillInfo(
                name=skill_dir.name,
                path=skill_dir,
                type="unknown",
            )

        skill_info = self.skills_cache[skill_key]

        # 检查文件是否真的改变了
        config_file = skill_dir / "config.json"
        if config_file.exists():
            new_hash = self._calculate_hash(config_file)
            if new_hash == skill_info.hash:
                logger.debug(f"[SkillsHotReload] 文件未变更，跳过: {file_path}")
                return

        logger.info(f"[SkillsHotReload] 开始重载技能: {skill_key}")
        self.stats["total_reloads"] += 1

        try:
            # 执行回调
            if self.on_reload_callback:
                result = self.on_reload_callback(skill_key, skill_dir)
                if asyncio.iscoroutine(result):
                    await result

            # 更新哈希
            if config_file.exists():
                skill_info.hash = self._calculate_hash(config_file)
                skill_info.last_modified = config_file.stat().st_mtime

            skill_info.reload_count += 1
            self.stats["successful_reloads"] += 1
            self.stats["last_reload_time"] = datetime.now().isoformat()

            logger.info(
                f"[SkillsHotReload] 技能重载成功: {skill_key} (重载次数: {skill_info.reload_count})"
            )

        except Exception as e:
            self.stats["failed_reloads"] += 1
            logger.error(
                f"[SkillsHotReload] 技能重载失败 {skill_key}: {e}", exc_info=True
            )

    def start(self):
        """启动文件监控"""
        if self.is_running:
            logger.warning("[SkillsHotReload] 已在运行中")
            return

        if not self.skills_dir.exists():
            logger.error(f"[SkillsHotReload] Skills目录不存在: {self.skills_dir}")
            return

        if WATCHDOG_AVAILABLE:
            # 使用 watchdog
            self.observer = Observer()
            event_handler = SkillFileHandler(self)

            for subdir in self.watch_subdirs:
                subdir_path = self.skills_dir / subdir
                if subdir_path.exists():
                    self.observer.schedule(
                        event_handler, str(subdir_path), recursive=True
                    )
                    logger.info(f"[SkillsHotReload] 监控目录: {subdir_path}")

            self.observer.start()
        else:
            # 使用轮询模式（备选方案）
            logger.warning("[SkillsHotReload] 使用轮询模式（每30秒检查一次）")
            asyncio.create_task(self._poll_loop())

        self.is_running = True
        logger.info("[SkillsHotReload] 文件监控已启动")

    async def _poll_loop(self):
        """轮询检查文件变化（备选方案）"""
        import asyncio

        poll_interval = 30  # 每30秒检查一次

        while self.is_running:
            try:
                # 检查所有技能文件是否有变化
                for skill_key, skill_info in list(self.skills_cache.items()):
                    config_file = skill_info.path / "config.json"
                    if config_file.exists():
                        current_mtime = config_file.stat().st_mtime
                        if current_mtime > skill_info.last_modified:
                            new_hash = self._calculate_hash(config_file)
                            if new_hash != skill_info.hash:
                                await self.reload_skill(str(config_file))
            except Exception as e:
                logger.error(f"[SkillsHotReload] 轮询检查失败: {e}")

            await asyncio.sleep(poll_interval)

    def stop(self):
        """停止文件监控"""
        if not self.is_running:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.is_running = False
        logger.info("[SkillsHotReload] 文件监控已停止")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "cached_skills": len(self.skills_cache),
            "is_running": self.is_running,
        }


# 全局热重载管理器实例
_global_hot_reloader: Optional[SkillsHotReloader] = None


def get_global_hot_reloader(
    skills_dir: Optional[Path] = None,
    watch_subdirs: Optional[List[str]] = None,
    on_reload_callback: Optional[Callable] = None,
) -> SkillsHotReloader:
    """获取全局热重载管理器实例"""
    global _global_hot_reloader

    if _global_hot_reloader is None:
        _global_hot_reloader = SkillsHotReloader(
            skills_dir=skills_dir,
            watch_subdirs=watch_subdirs,
            on_reload_callback=on_reload_callback,
        )

    return _global_hot_reloader


def start_skills_hot_reload(
    skills_dir: Optional[Path] = None,
    watch_subdirs: Optional[List[str]] = None,
    on_reload_callback: Optional[Callable] = None,
) -> SkillsHotReloader:
    """启动Skills热重载（便捷函数）"""
    reloader = get_global_hot_reloader(skills_dir, watch_subdirs, on_reload_callback)
    reloader.start()
    return reloader


def stop_skills_hot_reload():
    """停止Skills热重载（便捷函数）"""
    global _global_hot_reloader

    if _global_hot_reloader:
        _global_hot_reloader.stop()
        _global_hot_reloader = None
