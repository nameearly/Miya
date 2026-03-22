
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弥娅终端系统全面修复脚本

目标：修复所有终端功能问题，使其达到Claude Code级别能力
"""

import os
import sys
import json
import asyncio
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Any

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("弥娅终端系统全面修复")
print("=" * 80)


def check_system() -> Dict[str, Any]:
    """检查系统环境"""
    print("\n1. 检查系统环境...")
    
    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "current_dir": os.getcwd(),
        "encoding": sys.getdefaultencoding(),
        "filesystem_encoding": sys.getfilesystemencoding()
    }
    
    print(f"   操作系统: {system_info['platform']} {system_info['platform_version']}")
    print(f"   Python版本: {system_info['python_version']}")
    print(f"   当前目录: {system_info['current_dir']}")
    print(f"   默认编码: {system_info['encoding']}")
    print(f"   文件系统编码: {system_info['filesystem_encoding']}")
    
    return system_info


def check_dependencies() -> Dict[str, bool]:
    """检查依赖包"""
    print("\n2. 检查依赖包...")
    
    dependencies = {
        "psutil": False,
        "aiohttp": False,
        "asyncssh": False,
        "watchdog": False,
        "pywin32": False,
        "fastapi": False,
        "uvicorn": False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            print(f"   [OK] {dep}")
        except ImportError:
            print(f"   [MISSING] {dep} (未安装)")
    
    return dependencies


def check_terminal_files() -> Dict[str, bool]:
    """检查终端相关文件"""
    print("\n3. 检查终端相关文件...")
    
    files_to_check = [
        "core/local_terminal_manager.py",
        "core/terminal_types.py",
        "core/terminal_orchestrator.py",
        "core/terminal_agent.py",
        "core/web_api/terminal.py",
        "core/terminal/base/interfaces.py",
        "core/terminal/base/types.py",
        "core/terminal/enhanced_terminal_manager.py",
        "run/terminal_simple.py",
        "test_terminal_simple.py",
        "test_terminal_functional.py"
    ]
    
    file_status = {}
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            file_status[file_path] = True
            print(f"   [OK] {file_path} ({size} bytes)")
        else:
            file_status[file_path] = False
            print(f"   [MISSING] {file_path} (不存在)")
    
    return file_status


def test_basic_terminal() -> bool:
    """测试基本终端功能"""
    print("\n4. 测试基本终端功能...")
    
    try:
        # 测试导入
        from core.local_terminal_manager import LocalTerminalManager
        from core.terminal_types import TerminalType
        print("   [OK] 核心模块导入成功")
        
        # 测试创建管理器
        manager = LocalTerminalManager()
        print("   [OK] 终端管理器创建成功")
        
        # 测试创建终端（异步）
        async def create_test_terminal():
            session_id = await manager.create_terminal(
                name="修复测试终端",
                terminal_type=TerminalType.CMD
            )
            return session_id
        
        session_id = asyncio.run(create_test_terminal())
        print(f"   [OK] 终端创建成功 (ID: {session_id})")
        
        # 测试获取状态
        status = manager.get_session_status(session_id)
        if status:
            print(f"   [OK] 终端状态获取成功: {status['name']}")
        else:
            print("   [FAIL] 终端状态获取失败")
            return False
        
        # 测试命令执行
        async def test_command():
            result = await manager.execute_command(session_id, "echo 修复测试")
            return result
        
        result = asyncio.run(test_command())
        if result.success:
            print(f"   [OK] 命令执行成功: {result.output[:50]}")
        else:
            print(f"   [WARN] 命令执行可能有问题: {result.error}")
        
        # 清理
        async def cleanup():
            await manager.close_session(session_id)
        
        asyncio.run(cleanup())
        print("   [OK] 终端清理成功")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 基本终端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_server() -> bool:
    """测试API服务器"""
    print("\n5. 测试API服务器...")
    
    try:
        import requests
        import time
        
        # 检查端口是否在监听
        if platform.system() == "Windows":
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", ":8000"],
                capture_output=True,
                text=True,
                shell=True
            )
            port_in_use = ":8000" in result.stdout
        else:
            result = subprocess.run(
                ["netstat", "-tln", "|", "grep", ":8000"],
                capture_output=True,
                text=True,
                shell=True
            )
            port_in_use = result.returncode == 0
        
        if port_in_use:
            print("   [OK] 端口8000正在监听")
            
            # 测试API
            try:
                response = requests.get("http://localhost:8000/api/status", timeout=5)
                if response.status_code == 200:
                    print(f"   [OK] API服务器响应正常")
                    
                    # 测试终端API
                    data = {
                        "message": "测试",
                        "session_id": "test_api",
                        "from_terminal": "test"
                    }
                    
                    response = requests.post(
                        "http://localhost:8000/api/terminal/chat",
                        json=data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"   [OK] 终端API响应正常")
                        return True
                    else:
                        print(f"   [FAIL] 终端API响应失败: {response.status_code}")
                        return False
                else:
                    print(f"   [FAIL] API服务器响应失败: {response.status_code}")
                    return False
                    
            except requests.exceptions.ConnectionError:
                print("   [FAIL] 无法连接到API服务器")
                return False
            except Exception as e:
                print(f"   [FAIL] API测试异常: {e}")
                return False
        else:
            print("   [WARN] 端口8000未在监听（主系统可能未运行）")
            return False
            
    except Exception as e:
        print(f"   [FAIL] API服务器测试失败: {e}")
        return False


def create_fix_plan() -> Dict[str, List[str]]:
    """创建修复计划"""
    print("\n6. 创建修复计划...")
    
    fix_plan = {
        "critical": [
            "修复编码问题：确保Windows上的GBK/UTF-8正确处理",
            "修复命令执行：实现真正的终端交互而非模拟",
            "修复终端代理：确保能正确连接到主系统",
            "修复进程管理：实现完整的进程监控和控制"
        ],
        "important": [
            "增强命令解析：实现智能命令理解和分类",
            "增强安全检查：添加危险命令检测和阻止",
            "增强知识学习：从历史中学习用户习惯",
            "增强多终端协同：实现真正的多终端并行控制"
        ],
        "enhancement": [
            "添加流式输出：实现逐字输出效果",
            "添加自动完成：智能命令建议和补全",
            "添加脚本支持：支持执行复杂脚本",
            "添加性能监控：实时监控系统资源使用"
        ]
    }
    
    for category, items in fix_plan.items():
        print(f"   {category.upper()}:")
        for item in items:
            print(f"     • {item}")
    
    return fix_plan


def main():
    """主函数"""
    print("开始全面诊断弥娅终端系统...\n")
    
    # 执行检查
    system_info = check_system()
    dependencies = check_dependencies()
    file_status = check_terminal_files()
    
    # 执行测试
    basic_ok = test_basic_terminal()
    api_ok = test_api_server()
    
    # 创建修复计划
    fix_plan = create_fix_plan()
    
    # 总结
    print("\n" + "=" * 80)
    print("诊断结果总结")
    print("=" * 80)
    
    issues = []
    
    # 检查依赖
    missing_deps = [dep for dep, installed in dependencies.items() if not installed]
    if missing_deps:
        issues.append(f"缺少依赖包: {', '.join(missing_deps)}")
    
    # 检查文件
    missing_files = [f for f, exists in file_status.items() if not exists]
    if missing_files:
        issues.append(f"缺少文件: {', '.join(missing_files[:3])}...")
    
    # 检查功能
    if not basic_ok:
        issues.append("基本终端功能测试失败")
    
    if not api_ok:
        issues.append("API服务器测试失败")
    
    # 输出结果
    if issues:
        print("[FAIL] 发现以下问题:")
        for issue in issues:
            print(f"   • {issue}")
        
        print("\n[PLAN] 修复计划已创建，请按优先级执行修复。")
        print("       建议先修复CRITICAL级别的问题。")
    else:
        print("[OK] 所有检查通过！终端系统基本功能正常。")
        print("     可以继续执行增强功能修复。")
    
    print("\n下一步:")
    print("1. 执行修复脚本修复编码问题")
    print("2. 增强命令执行器实现真正交互")
    print("3. 测试修复后的完整功能")
    
    return len(issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
