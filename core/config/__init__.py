"""
配置模块
提供配置验证和管理功能
"""

from .validator import (
    AppConfig, DatabaseConfig, AIConfig, TerminalConfig,
    MemoryConfig, EmotionConfig, WebConfig, ConfigManager,
    get_config_manager, get_config, reload_config,
    get_default_config, create_minimal_config, validate_config_file
)

__all__ = [
    'AppConfig',
    'DatabaseConfig',
    'AIConfig',
    'TerminalConfig',
    'MemoryConfig',
    'EmotionConfig',
    'WebConfig',
    'ConfigManager',
    'get_config_manager',
    'get_config',
    'reload_config',
    'get_default_config',
    'create_minimal_config',
    'validate_config_file'
]