#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试弥娅终端系统的完整能力
"""

import asyncio
import sys
import os
import platform

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("弥娅终端系统能力测试")
print("=" * 70)

async def test_core_capabilities():
    """测试核心能力"""
    print("\n1. 测试核心模块导入...")
    
    try:
        # 测试终端管理器
        from core.local_terminal_manager import LocalTerminalManager
        print("   ✅ 终端管理器导入成功")
        
        # 测试终端编排器
        from core.terminal_orchestrator import IntelligentTerminalOrchestrator
        print("   ✅ 终端编排器导入成功")
        
        # 测试终端类型
        from core.terminal_types import TerminalType
        print("   ✅ 终端类型导入成功")
        
        # 测试终端基础类型
        from core.terminal.base.types import CommandIntent, CommandCategory, ExecutionMode
        print("   ✅ 终端基础类型导入成功")
        
        # 测试终端接口
        from core.terminal.base.interfaces import ICommandParser, IExecutor
        print("   ✅ 终端接口导入成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 核心模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_terminal_creation():
    """测试终端创建能力"""
    print("\n2. 测试终端创建能力...")
    
    try:
        from core.local_terminal_manager import LocalTerminalManager
        from core.terminal_types import TerminalType
        
        manager = LocalTerminalManager()
        
        # 测试创建CMD终端
        print("   创建CMD终端...")
        cmd_id = await manager.create_terminal(
            name="测试CMD终端",
            terminal_type=TerminalType.CMD
        )
        print(f"   ✅ CMD终端创建成功: {cmd_id}")
        
        # 测试创建PowerShell终端
        print("   创建PowerShell终端...")
        ps_id = await manager.create_terminal(
            name="测试PowerShell终端",
            terminal_type=TerminalType.POWERSHELL
        )
        print(f"   ✅ PowerShell终端创建成功: {ps_id}")
        
        # 获取终端状态
        status = manager.get_all_status()
        print(f"   总终端数: {len(status)}")
        
        # 清理
        await manager.close_all_sessions()
        print("   所有终端已清理")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 终端创建测试失败: {e}")
        return False

async def test_command_execution():
    """测试命令执行能力"""
    print("\n3. 测试命令执行能力...")
    
    try:
        from core.local_terminal_manager import LocalTerminalManager
        from core.terminal_types import TerminalType
        
        manager = LocalTerminalManager()
        
        # 创建测试终端
        session_id = await manager.create_terminal(
            name="命令执行测试终端",
            terminal_type=TerminalType.CMD
        )
        
        # 测试简单命令
        print("   执行简单命令: echo Hello World")
        result = await manager.execute_command(session_id, "echo Hello World")
        
        if result.success:
            print(f"   ✅ 命令执行成功")
            print(f"     输出: {result.output}")
        else:
            print(f"   ❌ 命令执行失败: {result.error}")
        
        # 测试目录命令
        print("   执行目录命令: dir")
        result = await manager.execute_command(session_id, "dir")
        
        if result.success:
            print(f"   ✅ 目录命令执行成功")
            print(f"     输出长度: {len(result.output)} 字符")
        else:
            print(f"   ❌ 目录命令执行失败: {result.error}")
        
        # 清理
        await manager.close_all_sessions()
        
        return result.success
        
    except Exception as e:
        print(f"   ❌ 命令执行测试失败: {e}")
        return False

async def test_orchestrator():
    """测试终端编排器"""
    print("\n4. 测试终端编排器...")
    
    try:
        from core.terminal_orchestrator import IntelligentTerminalOrchestrator
        
        orchestrator = IntelligentTerminalOrchestrator()
        
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
        return False

async def test_multi_terminal():
    """测试多终端能力"""
    print("\n5. 测试多终端能力...")
    
    try:
        from core.local_terminal_manager import LocalTerminalManager
        from core.terminal_types import TerminalType
        
        manager = LocalTerminalManager()
        
        # 创建多个终端
        terminals = []
        for i in range(3):
            session_id = await manager.create_terminal(
                name=f"多终端测试{i+1}",
                terminal_type=TerminalType.CMD
            )
            terminals.append(session_id)
            print(f"   创建终端 {i+1}: {session_id}")
        
        # 测试并行执行
        print("   测试并行执行...")
        commands = {session_id: f"echo 来自终端 {i+1}" for i, session_id in enumerate(terminals)}
        results = await manager.execute_parallel(commands)
        
        success_count = sum(1 for r in results.values() if r.success)
        print(f"   并行执行结果: {success_count}/{len(terminals)} 成功")
        
        # 测试顺序执行
        print("   测试顺序执行...")
        if terminals:
            sequence_results = await manager.execute_sequence(
                terminals[0],
                ["echo 第一步", "echo 第二步", "echo 第三步"]
            )
            print(f"   顺序执行结果: {len(sequence_results)} 个命令")
        
        # 清理
        await manager.close_all_sessions()
        
        return success_count > 0
        
    except Exception as e:
        print(f"   ❌ 多终端测试失败: {e}")
        return False

async def test_system_integration():
    """测试系统集成能力"""
    print("\n6. 测试系统集成能力...")
    
    try:
        # 测试系统信息
        print("   系统信息:")
        print(f"     操作系统: {platform.system()} {platform.release()}")
        print(f"     Python版本: {platform.python_version()}")
        print(f"     当前目录: {os.getcwd()}")
        
        # 测试环境变量
        print("   环境变量检查:")
        important_vars = ['PATH', 'PYTHONPATH', 'HOME', 'USERPROFILE']
        for var in important_vars:
            value = os.environ.get(var, '未设置')
            print(f"     {var}: {value[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 系统集成测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    
    print("\n开始测试弥娅终端系统...")
    
    # 运行所有测试
    tests = [
        ("核心模块", test_core_capabilities),
        ("终端创建", test_terminal_creation),
        ("命令执行", test_command_execution),
        ("终端编排", test_orchestrator),
        ("多终端", test_multi_terminal),
        ("系统集成", test_system_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试 {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 显示结果
    print("\n" + "=" * 70)
    print("测试结果汇总:")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！弥娅终端系统核心功能正常。")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 项测试失败，需要修复。")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())