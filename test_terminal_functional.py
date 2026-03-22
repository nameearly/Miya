#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能测试终端模式
"""

import sys
import os
import asyncio

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("功能测试弥娅终端模式")
print("=" * 60)

async def test_terminal_creation():
    """测试终端创建"""
    print("\n1. 测试终端创建...")
    
    try:
        from core.local_terminal_manager import LocalTerminalManager
        from core.terminal_types import TerminalType
        
        manager = LocalTerminalManager()
        
        # 创建CMD终端
        print("   创建CMD终端...")
        cmd_session_id = await manager.create_terminal(
            name="测试CMD终端",
            terminal_type=TerminalType.CMD
        )
        print(f"   ✅ CMD终端创建成功，会话ID: {cmd_session_id}")
        
        # 获取状态
        status = manager.get_session_status(cmd_session_id)
        print(f"   终端状态: {status}")
        
        # 创建PowerShell终端
        print("   创建PowerShell终端...")
        ps_session_id = await manager.create_terminal(
            name="测试PowerShell终端",
            terminal_type=TerminalType.POWERSHELL
        )
        print(f"   ✅ PowerShell终端创建成功，会话ID: {ps_session_id}")
        
        # 获取所有终端状态
        all_status = manager.get_all_status()
        print(f"   总终端数: {len(all_status)}")
        
        return manager, cmd_session_id, ps_session_id
        
    except Exception as e:
        print(f"   ❌ 终端创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

async def test_command_execution(manager, session_id):
    """测试命令执行"""
    print(f"\n2. 在会话 {session_id} 测试命令执行...")
    
    try:
        # 执行简单命令
        print("   执行 'echo Hello World'...")
        result = await manager.execute_command(session_id, "echo Hello World")
        
        if result.success:
            print(f"   ✅ 命令执行成功")
            print(f"     输出: {result.output[:100] if result.output else '无输出'}")
            print(f"     执行时间: {result.execution_time:.2f}秒")
        else:
            print(f"   ❌ 命令执行失败")
            print(f"     错误: {result.error}")
        
        return result.success
        
    except Exception as e:
        print(f"   ❌ 命令执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_terminal_switching(manager, session_id):
    """测试终端切换"""
    print(f"\n3. 测试切换到会话 {session_id}...")
    
    try:
        await manager.switch_session(session_id)
        print(f"   ✅ 终端切换成功")
        print(f"     活动终端: {manager.active_session_id}")
        return True
    except Exception as e:
        print(f"   ❌ 终端切换失败: {e}")
        return False

async def test_orchestrator():
    """测试终端编排器"""
    print("\n4. 测试终端编排器...")
    
    try:
        from core.terminal_orchestrator import IntelligentTerminalOrchestrator
        
        orchestrator = IntelligentTerminalOrchestrator()
        print("   ✅ 终端编排器创建成功")
        
        # 测试智能执行
        print("   测试智能执行任务...")
        result = await orchestrator.smart_execute("显示当前目录")
        
        if "error" not in result:
            print(f"   ✅ 智能执行成功")
            print(f"     策略: {result.get('strategy', 'unknown')}")
            return True
        else:
            print(f"   ❌ 智能执行失败: {result.get('error', '未知错误')}")
            return False
        
    except Exception as e:
        print(f"   ❌ 终端编排器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    
    # 测试终端创建
    manager, cmd_session_id, ps_session_id = await test_terminal_creation()
    
    if not manager:
        print("\n❌ 终端创建测试失败，终止测试")
        return
    
    # 测试命令执行
    if cmd_session_id:
        await test_command_execution(manager, cmd_session_id)
    
    # 测试终端切换
    if cmd_session_id:
        await test_terminal_switching(manager, cmd_session_id)
    
    # 测试终端编排器
    await test_orchestrator()
    
    # 清理
    print("\n5. 清理测试终端...")
    try:
        await manager.close_all_sessions()
        print("   ✅ 所有终端已关闭")
    except Exception as e:
        print(f"   ❌ 清理失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 功能测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())