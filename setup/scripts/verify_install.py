#!/usr/bin/env python3
"""
Miya 安装验证脚本
验证所有依赖是否正确安装并可用
"""

import sys
import importlib
from typing import List, Tuple


def check_import(package_name: str, import_name: str = None) -> bool:
    """检查包是否可以导入"""
    if import_name is None:
        import_name = package_name.replace('-', '_')

    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def verify_installation() -> Tuple[List[str], List[str], List[str]]:
    """验证安装

    Returns:
        (success, failed, optional_missing)
    """
    # 核心依赖
    core_deps = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("aiohttp", "aiohttp"),
        ("dotenv", "python_dotenv"),
        ("yaml", "yaml"),
        ("psutil", "psutil"),
        ("watchdog", "watchdog"),
    ]

    # AI 依赖
    ai_deps = [
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("sentence_transformers", "sentence_transformers"),
        ("torch", "torch"),
    ]

    # 数据库依赖
    db_deps = [
        ("redis", "redis"),
        ("chromadb", "chromadb"),
        ("pymilvus", "pymilvus"),
        ("neo4j", "neo4j"),
    ]

    # 数据处理
    data_deps = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scipy", "scipy"),
        ("sklearn", "sklearn"),
    ]

    # 可视化
    viz_deps = [
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
    ]

    # TTS
    tts_deps = [
        ("edge_tts", "edge_tts"),
    ]

    success = []
    failed = []
    optional_missing = []

    # 检查核心依赖
    for name, import_name in core_deps:
        if check_import(name, import_name):
            success.append(f"{name}")
        else:
            failed.append(f"{name}")

    # 检查 AI 依赖
    for name, import_name in ai_deps:
        if check_import(name, import_name):
            success.append(f"{name}")
        else:
            optional_missing.append(f"{name}")

    # 检查数据库依赖
    for name, import_name in db_deps:
        if check_import(name, import_name):
            success.append(f"{name}")
        else:
            optional_missing.append(f"{name}")

    # 检查数据处理
    for name, import_name in data_deps:
        if check_import(name, import_name):
            success.append(f"{name}")
        else:
            optional_missing.append(f"{name}")

    # 检查可视化
    for name, import_name in viz_deps:
        if check_import(name, import_name):
            success.append(f"{name}")
        else:
            optional_missing.append(f"{name}")

    # 检查 TTS
    for name, import_name in tts_deps:
        if check_import(name, import_name):
            success.append(f"{name}")
        else:
            optional_missing.append(f"{name}")

    return success, failed, optional_missing


def print_results(success: List[str], failed: List[str],
                  optional_missing: List[str]):
    """打印验证结果"""

    print("\n" + "=" * 60)
    print("Miya 安装验证结果")
    print("=" * 60)

    # 成功
    if success:
        print("\n✓ 成功导入的模块:")
        for module in success:
            print(f"  ✓ {module}")

    # 失败
    if failed:
        print("\n✗ 导入失败的核心模块:")
        for module in failed:
            print(f"  ✗ {module}")

    # 可选缺失
    if optional_missing:
        print("\n⚠ 缺失的可选模块 (不影响基础运行):")
        for module in optional_missing:
            print(f"  ⚠ {module}")

    # 统计
    print("\n" + "-" * 60)
    print(f"统计: {len(success)} 个成功, {len(failed)} 个失败, {len(optional_missing)} 个可选缺失")
    print("-" * 60)

    # 结果
    if failed:
        print("\n✗ 安装验证失败！请检查核心依赖是否正确安装。")
        print(f"\n建议运行: pip install -r setup/dependencies/base.txt")
        return False
    else:
        print("\n✓ 核心依赖验证通过！")

        if optional_missing:
            print("\n注意: 部分可选模块未安装，可能影响某些高级功能。")
            print(f"\n如需完整功能，运行: pip install -r setup/requirements/full.txt")

        print("\n✓ 安装验证成功！")
        return True

    print("=" * 60 + "\n")


def main():
    """主函数"""
    try:
        success, failed, optional_missing = verify_installation()
        result = print_results(success, failed, optional_missing)

        if not result:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
