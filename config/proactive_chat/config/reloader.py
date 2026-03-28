# 配置重载器
# Config Reloader

import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# 尝试导入 watchdog，如果不存在则设置标志
WATCHDOG_AVAILABLE = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
    logger.info("watchdog 模块已加载，文件监控功能可用")
except ImportError:
    logger.warning("watchdog 模块不可用，文件监控功能将被禁用")

    # 创建一个空的基类
    class FileSystemEventHandler:
        pass


class ConfigChangeHandler(FileSystemEventHandler):
    def __init__(self, reloader):
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.reloader = reloader

    def on_modified(self, event):
        if hasattr(event, "src_path") and event.src_path.endswith("_base.yaml"):
            logger.info(f"检测到配置文件变化: {event.src_path}")
            asyncio.create_task(self.reloader.reload_config())


class ProactiveChatConfigReloader:
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.observer = None
        self.check_interval = 300  # 5分钟
        self.is_running = False
        self.last_check_time = 0

    async def start(self):
        if self.is_running:
            return

        try:
            # 文件监控（如果 watchdog 可用）
            if WATCHDOG_AVAILABLE:
                try:
                    event_handler = ConfigChangeHandler(self)
                    self.observer = Observer()
                    config_dir = Path(self.config_loader.config_path).parent
                    self.observer.schedule(
                        event_handler, str(config_dir), recursive=False
                    )
                    self.observer.start()
                    logger.info("配置重载器文件监控已启动")
                except Exception as e:
                    logger.warning(f"文件监控启动失败: {e}")
            else:
                logger.info("配置重载器文件监控已禁用 (watchdog 不可用)")

            # 启动定时检查
            asyncio.create_task(self._periodic_check())

            self.is_running = True
            logger.info("配置重载器启动成功")

        except Exception as e:
            logger.error(f"配置重载器启动失败: {e}")

    async def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.is_running = False
        logger.info("配置重载器已停止")

    async def reload_config(self):
        try:
            await self.config_loader.reload_config()
            logger.info("配置重载成功")
            return True
        except Exception as e:
            logger.error(f"配置重载失败: {e}")
            return False

    async def _periodic_check(self):
        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_check_time >= self.check_interval:
                    await self.reload_config()
                    self.last_check_time = current_time
            except Exception as e:
                logger.error(f"定时检查失败: {e}")

            await asyncio.sleep(60)  # 每分钟检查一次

    def get_stats(self) -> Dict:
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "last_check_time": self.last_check_time,
            "watchdog_available": WATCHDOG_AVAILABLE,
        }
