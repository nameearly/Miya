"""
统一日志配置
"""

import logging
import logging.config
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import datetime
from dataclasses import dataclass, field
from enum import Enum


class LogLevel(str, Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """日志格式"""

    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"


@dataclass
class LogConfig:
    """日志配置"""

    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.DETAILED
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_enabled: bool = True
    file_enabled: bool = True
    json_indent: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogConfig":
        """从字典创建配置"""
        return cls(
            level=LogLevel(data.get("level", "INFO")),
            format=LogFormat(data.get("format", "detailed")),
            file_path=data.get("file_path"),
            max_bytes=data.get("max_bytes", 10 * 1024 * 1024),
            backup_count=data.get("backup_count", 5),
            console_enabled=data.get("console_enabled", True),
            file_enabled=data.get("file_enabled", True),
            json_indent=data.get("json_indent"),
        )


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def __init__(self, indent: Optional[int] = None):
        super().__init__()
        self.indent = indent

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        # 添加额外字段
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加栈信息（如果是错误级别）
        if record.levelno >= logging.ERROR:
            log_data["stack_info"] = (
                self.formatStack(record.stack_info) if record.stack_info else None
            )

        return json.dumps(log_data, indent=self.indent, ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""

    COLORS = {
        "DEBUG": "\033[0;36m",  # 青色
        "INFO": "\033[0;32m",  # 绿色
        "WARNING": "\033[1;33m",  # 黄色
        "ERROR": "\033[1;31m",  # 红色
        "CRITICAL": "\033[1;41m",  # 红色背景
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # 简化日志格式
        fmt = f"{color}[%(asctime)s] [%(levelname)-8s] %(message)s{reset}"

        formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """
    设置日志配置

    Args:
        config: 日志配置，如果为None则使用默认配置
    """
    if config is None:
        config = LogConfig()

    # 确保日志目录存在
    if config.file_enabled and config.file_path:
        log_file = Path(config.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # 构建日志配置字典
    log_config_dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "json": {"()": JsonFormatter, "indent": config.json_indent},
            "color": {"()": ColorFormatter},
        },
        "handlers": {},
        "loggers": {
            "": {  # 根日志器
                "handlers": [],
                "level": config.level.value,
                "propagate": True,
            },
            "core": {"handlers": [], "level": config.level.value, "propagate": False},
            "hub": {"handlers": [], "level": config.level.value, "propagate": False},
            "run": {"handlers": [], "level": config.level.value, "propagate": False},
            "uvicorn": {"level": "WARNING", "propagate": False},
            "fastapi": {"level": "WARNING", "propagate": False},
        },
    }

    # 添加控制台处理器
    if config.console_enabled:
        handler_name = "console"
        if config.format == LogFormat.JSON:
            handler_name = "console_json"
            log_config_dict["formatters"]["console_json"] = {
                "()": JsonFormatter,
                "indent": config.json_indent,
            }

        log_config_dict["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": config.level.value,
            "formatter": "color"
            if sys.stderr.isatty() and config.format != LogFormat.JSON
            else config.format.value,
            "stream": sys.stderr,
        }
        log_config_dict["loggers"][""]["handlers"].append("console")
        for logger_name in ["core", "hub", "run"]:
            log_config_dict["loggers"][logger_name]["handlers"].append("console")

    # 添加文件处理器
    if config.file_enabled and config.file_path:
        log_config_dict["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": config.level.value,
            "formatter": config.format.value,
            "filename": config.file_path,
            "maxBytes": config.max_bytes,
            "backupCount": config.backup_count,
            "encoding": "utf-8",
        }
        log_config_dict["loggers"][""]["handlers"].append("file")
        for logger_name in ["core", "hub", "run"]:
            log_config_dict["loggers"][logger_name]["handlers"].append("file")

    # 应用配置
    logging.config.dictConfig(log_config_dict)

    # 记录日志系统启动
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已启动，级别: {config.level}, 格式: {config.format}")
    if config.file_enabled and config.file_path:
        logger.info(f"日志文件: {config.file_path}")


def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    获取日志器，支持额外字段

    Args:
        name: 日志器名称
        extra: 额外字段

    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)

    # 添加上下文信息
    if extra:
        old_factory = logger.makeRecord

        def make_record_wrapper(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.extra = extra
            return record

        logger.makeRecord = make_record_wrapper

    return logger


class LogContext:
    """日志上下文管理器，用于添加临时字段"""

    def __init__(self, logger: logging.Logger, **fields):
        self.logger = logger
        self.fields = fields
        self.old_make_record = logger.makeRecord

    def __enter__(self):
        def make_record_wrapper(*args, **kwargs):
            record = self.old_make_record(*args, **kwargs)
            record.extra = getattr(record, "extra", {})
            record.extra.update(self.fields)
            return record

        self.logger.makeRecord = make_record_wrapper
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.makeRecord = self.old_make_record


def log_execution_time(logger: logging.Logger, level: int = logging.INFO):
    """记录函数执行时间的装饰器"""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.log(level, f"函数 {func.__name__} 执行时间: {duration:.3f}s")

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.log(level, f"函数 {func.__name__} 执行时间: {duration:.3f}s")

            return sync_wrapper

    return decorator


def log_exceptions(logger: logging.Logger, level: int = logging.ERROR):
    """捕获并记录异常的装饰器"""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.log(level, f"函数 {func.__name__} 执行失败", exc_info=True)
                    raise

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.log(level, f"函数 {func.__name__} 执行失败", exc_info=True)
                    raise

            return sync_wrapper

    return decorator


# 导入time和asyncio用于装饰器
import time
import asyncio

# 默认配置
DEFAULT_CONFIG = LogConfig(
    level=LogLevel.INFO, format=LogFormat.DETAILED, file_path=None, console_enabled=True
)

# 初始化日志系统（使用默认配置）
setup_logging(DEFAULT_CONFIG)
