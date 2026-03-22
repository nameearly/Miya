#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真正的终端窗口打开
"""

import subprocess
import time
import os
import sys

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("测试真正的终端窗口打开")
print("=" * 60)

print("1. 测试直接使用 start 命令打开 CMD 窗口...")
try:
    # 直接使用 start 命令打开 CMD 窗口
    cmd = 'start cmd /k "echo 这是一个测试窗口 && pause"'
    print(f"   执行命令: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("   [OK] 命令已执行")
    print("   等待5秒查看窗口是否打开...")
    
    for i in range(5, 0, -1):
        print(f"   等待 {i} 秒...")
        time.sleep(1)
    
    print("   [OK] 测试完成")
    
except Exception as e:
    print(f"   [ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n2. 测试打开 PowerShell 窗口...")
try:
    cmd = 'start powershell -NoExit -Command "Write-Host \"这是一个PowerShell测试窗口\""'
    print(f"   执行命令: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("   [OK] 命令已执行")
    print("   等待3秒查看窗口是否打开...")
    
    for i in range(3, 0, -1):
        print(f"   等待 {i} 秒...")
        time.sleep(1)
    
    print("   [OK] 测试完成")
    
except Exception as e:
    print(f"   [ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("[OK] 所有测试完成！")
print("=" * 60)
print("\n检查：您应该看到了两个新打开的终端窗口：")
print("1. 一个CMD窗口显示'这是一个测试窗口'")
print("2. 一个PowerShell窗口显示'这是一个PowerShell测试窗口'")
print("\n如果窗口没有打开，可能是权限或系统配置问题。")