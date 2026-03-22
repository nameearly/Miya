#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式终端测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run.terminal_simple import SimpleTerminalShell

async def test_interactive():
    """交互式测试"""
    print("=" * 60)
    print("交互式终端测试")
    print("=" * 60)
    
    shell = SimpleTerminalShell()
    
    # 模拟用户输入
    test_commands = [
        "!list",
        "dir",
        "echo 测试终端功能",
        "!status",
        "exit"
    ]
    
    print("\n模拟测试命令:")
    for cmd in test_commands:
        print(f"  {cmd}")
    
    print("\n注意: 由于终端需要真实交互，这里只显示启动状态。")
    print("要完整测试，请直接运行: python run/terminal_simple.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_interactive())