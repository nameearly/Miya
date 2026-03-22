#!/usr/bin/env python3
"""
Miya 依赖检查脚本
检查所有依赖是否已安装
"""

import sys
import subprocess
from typing import Dict, List, Tuple


# 依赖清单（更新后）
DEPENDENCIES = {
    # 基础依赖
    "fastapi": {"required": True, "min_version": "0.100.0"},
    "uvicorn": {"required": True, "min_version": "0.22.0"},
    "pydantic": {"required": True, "min_version": "2.0.0"},
    "aiohttp": {"required": True, "min_version": "3.8.0"},
    "python-dotenv": {"required": True, "min_version": "1.0.0"},
    "pyyaml": {"required": True, "min_version": "6.0"},
    "psutil": {"required": True, "min_version": "5.9.0"},
    "watchdog": {"required": True, "min_version": "3.0.0"},
    "requests": {"required": True, "min_version": "2.31.0"},
    "aiofiles": {"required": True, "min_version": "23.0.0"},  # 新增
    "PyJWT": {"required": True, "min_version": "2.8.0"},  # 新增
    "cryptography": {"required": True, "min_version": "41.0.0"},  # 新增

    # AI 依赖
    "openai": {"required": True, "min_version": "1.3.0"},
    "tiktoken": {"required": True, "min_version": "0.5.0"},  # 新增
    "anthropic": {"required": False, "min_version": "0.7.0"},
    "sentence-transformers": {"required": False, "min_version": "2.2.0"},
    "torch": {"required": False, "min_version": "2.0.0"},

    # 数据库依赖
    "redis": {"required": False, "min_version": "4.5.0"},
    "chromadb": {"required": False, "min_version": "0.4.0"},
    "pymilvus": {"required": False, "min_version": "2.3.0"},
    "neo4j": {"required": False, "min_version": "5.0.0"},

    # 文档处理（新增）
    "PyPDF2": {"required": False, "min_version": "3.0.0"},
    "python-docx": {"required": False, "min_version": "1.1.0"},

    # 网络通信（新增）
    "httpx": {"required": False, "min_version": "0.24.0"},
    "websockets": {"required": False, "min_version": "12.0"},
    "paramiko": {"required": False, "min_version": "3.0.0"},

    # 数据处理
    "numpy": {"required": True, "min_version": "1.24.0"},
    "pandas": {"required": False, "min_version": "2.0.0"},
    "scipy": {"required": False, "min_version": "1.10.0"},
    "scikit-learn": {"required": False, "min_version": "1.3.0"},

    # 可视化
    "matplotlib": {"required": False, "min_version": "3.7.0"},
    "seaborn": {"required": False, "min_version": "0.12.0"},

    # TTS
    "edge-tts": {"required": False, "min_version": "6.1.0"},

    # 任务调度
    "apscheduler": {"required": False, "min_version": "3.10.0"},  # 新增
}


def get_version(package_name: str) -> str:
    """获取包的版本"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        for line in output.split('\n'):
            if line.startswith('Version:'):
                return line.split(':')[1].strip()
        return None
    except subprocess.CalledProcessError:
        return None


def compare_versions(version: str, min_version: str) -> int:
    """比较版本号，返回 1(>), 0(=), -1(<)"""
    def parse_version(v):
        return tuple(map(int, v.split('.')))

    v1 = parse_version(version)
    v2 = parse_version(min_version)

    # 补齐长度
    max_len = max(len(v1), len(v2))
    v1 = v1 + (0,) * (max_len - len(v1))
    v2 = v2 + (0,) * (max_len - len(v2))

    if v1 > v2:
        return 1
    elif v1 < v2:
        return -1
    else:
        return 0


def check_dependencies() -> Tuple[List[str], List[str], List[str]]:
    """检查依赖

    Returns:
        (installed, missing, version_mismatch)
    """
    installed = []
    missing = []
    version_mismatch = []

    for package, info in DEPENDENCIES.items():
        version = get_version(package)

        if version is None:
            if info['required']:
                missing.append(package)
            else:
                # 可选依赖不在检查中显示缺失
                pass
        else:
            # 检查版本
            min_version = info.get('min_version')
            if min_version and compare_versions(version, min_version) < 0:
                version_mismatch.append(f"{package} ({version} < {min_version})")
            else:
                installed.append(f"{package} {version}")

    return installed, missing, version_mismatch


def print_results(installed: List[str], missing: List[str],
                  version_mismatch: List[str]):
    """打印检查结果"""

    print("\n" + "=" * 60)
    print("Miya 依赖检查结果")
    print("=" * 60)

    # 已安装
    if installed:
        print("\n✓ 已安装的依赖:")
        for pkg in installed:
            print(f"  ✓ {pkg}")

    # 版本不匹配
    if version_mismatch:
        print("\n⚠ 版本不匹配:")
        for pkg in version_mismatch:
            print(f"  ⚠ {pkg}")

    # 缺失
    if missing:
        print("\n✗ 缺少的依赖:")
        for pkg in missing:
            print(f"  ✗ {pkg}")

    # 统计
    print("\n" + "-" * 60)
    print(f"统计: {len(installed)} 个已安装, {len(missing)} 个缺失, {len(version_mismatch)} 个版本不匹配")
    print("-" * 60)

    # 建议
    if missing or version_mismatch:
        print("\n建议操作:")

        if missing:
            print(f"\n  安装缺失的依赖:")
            print(f"  pip install {' '.join(missing)}")

        if version_mismatch:
            print(f"\n  升级版本不匹配的依赖:")
            print(f"  pip install -r setup/requirements/full.txt --upgrade")

    else:
        print("\n✓ 所有依赖检查通过！")

    print("=" * 60 + "\n")

    return len(missing) == 0 and len(version_mismatch) == 0


def main():
    """主函数"""
    try:
        installed, missing, version_mismatch = check_dependencies()
        success = print_results(installed, missing, version_mismatch)

        if not success:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
