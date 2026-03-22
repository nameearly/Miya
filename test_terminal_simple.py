#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试终端模式
"""

import sys
import os

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试弥娅终端模式")
print("=" * 60)

try:
    # 测试导入终端管理器
    print("1. 测试导入终端管理器...")
    from core.local_terminal_manager import LocalTerminalManager
    print("   ✅ 终端管理器导入成功")
    
    print("2. 测试导入终端编排器...")
    from core.terminal_orchestrator import IntelligentTerminalOrchestrator
    print("   ✅ 终端编排器导入成功")
    
    print("3. 测试导入终端类型...")
    from core.terminal_types import TerminalType
    print("   ✅ 终端类型导入成功")
    
    print("4. 测试创建终端管理器实例...")
    manager = LocalTerminalManager()
    print("   ✅ 终端管理器实例创建成功")
    
    print("5. 测试创建终端编排器实例...")
    orchestrator = IntelligentTerminalOrchestrator()
    print("   ✅ 终端编排器实例创建成功")
    
    print("\n" + "=" * 60)
    print("✅ 终端模式核心组件测试通过！")
    print("=" * 60)
    
    # 显示系统信息
    import platform
    print(f"\n系统信息:")
    print(f"  操作系统: {platform.system()} {platform.release()}")
    print(f"  Python版本: {platform.python_version()}")
    print(f"  当前目录: {os.getcwd()}")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)