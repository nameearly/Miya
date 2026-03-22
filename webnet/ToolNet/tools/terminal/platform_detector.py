"""
平台检测模块
检测当前运行平台并返回平台信息
"""
import platform
import os
from enum import Enum
from typing import Optional


class Platform(Enum):
    """平台枚举"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    WSL = "wsl"
    ANDROID = "android"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    """
    检测当前运行平台

    Returns:
        Platform: 检测到的平台
    """
    system = platform.system().lower()

    # 检测 WSL
    if system == "linux":
        # 检查 /proc/version 是否包含 Microsoft
        try:
            with open("/proc/version", "r") as f:
                version = f.read().lower()
                if "microsoft" in version or "wsl" in version:
                    return Platform.WSL
        except (FileNotFoundError, IOError):
            pass
        return Platform.LINUX

    elif system == "windows":
        return Platform.WINDOWS

    elif system == "darwin":
        return Platform.MACOS

    # 检测 Android
    elif "android" in os.environ.get("TERM", "").lower():
        return Platform.ANDROID

    else:
        return Platform.UNKNOWN


def get_platform_info() -> dict:
    """
    获取详细的平台信息

    Returns:
        dict: 平台信息字典
    """
    detected_platform = detect_platform()

    return {
        "platform": detected_platform.value,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def is_windows() -> bool:
    """是否为 Windows 平台"""
    return detect_platform() == Platform.WINDOWS


def is_linux() -> bool:
    """是否为 Linux 平台"""
    return detect_platform() == Platform.LINUX


def is_macos() -> bool:
    """是否为 macOS 平台"""
    return detect_platform() == Platform.MACOS


def is_wsl() -> bool:
    """是否为 WSL 平台"""
    return detect_platform() == Platform.WSL


def is_unix_like() -> bool:
    """是否为类 Unix 平台（Linux、macOS、WSL）"""
    platform_type = detect_platform()
    return platform_type in [Platform.LINUX, Platform.MACOS, Platform.WSL]
