#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试终端窗口是否能正常打开
"""

import asyncio
import sys
import os
import time

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试弥娅终端窗口打开功能")
print("=" * 60)

async def test_terminal_window():
    try:
        from core.local_terminal_manager import LocalTerminalManager
        from core.terminal_types import TerminalType
        
        print("1. 创建终端管理器...")
        manager = LocalTerminalManager()
        print("   [OK] 终端管理器创建成功")
        
        print("2. 创建CMD终端窗口...")
        session_id = await manager.create_terminal(
            name="测试CMD窗口",
            terminal_type=TerminalType.CMD
        )
        print(f"   [OK] CMD终端创建成功，会话ID: {session_id}")
        
        print("3. 等待5秒查看窗口是否打开...")
        for i in range(5, 0, -1):
            print(f"   等待 {i} 秒...")
            await asyncio.sleep(1)
        
        print("4. 测试命令执行...")
        result = await manager.execute_command(session_id, "echo 测试终端窗口")
        if result.success:
            print(f"   [OK] 命令执行成功")
            print(f"     输出: {result.output}")
        else:
            print(f"   [ERROR] 命令执行失败: {result.error}")
        
        print("5. 关闭终端...")
        await manager.close_session(session_id)
        print("   [OK] 终端已关闭")
        
        print("\n" + "=" * 60)
        print("[OK] 终端窗口测试完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_terminal_window())