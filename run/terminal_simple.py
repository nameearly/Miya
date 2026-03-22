#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版终端模式 - 避免API服务器启动问题
"""

import asyncio
import sys
import os
import platform
import random
import json
import logging
from pathlib import Path
from typing import Optional, Any, Literal
from dataclasses import dataclass, field

# 跨平台控制台编码设置 - 支持中文输入
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Windows 下设置控制台编码
if sys.platform == 'win32':
    import subprocess
    try:
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

    # 设置标准输入输出编码
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(
            sys.stdin.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )

def chinese_input(prompt: str) -> str:
    """
    跨平台中文输入函数
    """
    if sys.platform == 'win32':
        import io
        if hasattr(sys.stdin, 'buffer') and not isinstance(sys.stdin, io.TextIOWrapper):
            sys.stdin = io.TextIOWrapper(
                sys.stdin.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )

    try:
        if prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()

        line = sys.stdin.readline()

        if line.endswith('\n'):
            line = line[:-1]
        elif line.endswith('\r\n'):
            line = line[:-2]

        return line
    except Exception:
        return input(prompt) if prompt else input()

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.terminal_orchestrator import IntelligentTerminalOrchestrator
from core.terminal_types import TerminalType

class SimpleTerminalShell:
    """简化版终端Shell"""

    def __init__(self):
        self.orchestrator = IntelligentTerminalOrchestrator()
        self.running = True

    async def start(self):
        """启动终端Shell"""
        self._show_banner()

        # 创建默认终端
        await self._init_default_terminal()

        # 主循环
        while self.running:
            try:
                user_input = await self._get_prompt_input()

                if not user_input:
                    continue

                await self._process_input(user_input)

            except KeyboardInterrupt:
                print("\n[弥娅] 正在关闭所有终端...")
                await self.orchestrator.terminal_manager.close_all_sessions()
                print("[弥娅] 期待下次再见到您~ 再见!")
                self.running = False
                break
            except Exception as e:
                print(f"\n[错误] {e}")

    def _show_banner(self):
        """显示横幅"""
        print("""
╔════════════════════════════════════════════════════════════╗
║                  弥娅 V4.0 - 简化终端模式                  ║
╠════════════════════════════════════════════════════════════╣
║  🖥️  单机多终端  │  🤖  智能编排  │  🔄  协同执行        ║
║  📊  实时监控    │  🧠  命令理解  │  🎯  智能路由        ║
╚════════════════════════════════════════════════════════════╝

输入 'help' 查看命令帮助
输入 'exit' 退出系统
        """)

    async def _init_default_terminal(self):
        """初始化默认终端"""
        system = platform.system()

        if system == "Windows":
            # Windows: 创建CMD
            cmd_id = await self.orchestrator.terminal_manager.create_terminal(
                name="CMD主终端",
                terminal_type=TerminalType.CMD
            )
            await self.orchestrator.terminal_manager.switch_session(cmd_id)
            print(f"[弥娅] 已创建默认CMD终端 (ID: {cmd_id})")

        elif system == "Linux":
            # Linux: 创建Bash
            bash_id = await self.orchestrator.terminal_manager.create_terminal(
                name="Bash主终端",
                terminal_type=TerminalType.BASH
            )
            await self.orchestrator.terminal_manager.switch_session(bash_id)
            print(f"[弥娅] 已创建默认Bash终端 (ID: {bash_id})")

        elif system == "Darwin":
            # macOS: 创建Zsh
            zsh_id = await self.orchestrator.terminal_manager.create_terminal(
                name="Zsh主终端",
                terminal_type=TerminalType.ZSH
            )
            await self.orchestrator.terminal_manager.switch_session(zsh_id)
            print(f"[弥娅] 已创建默认Zsh终端 (ID: {zsh_id})")

    async def _get_prompt_input(self) -> str:
        """获取用户输入"""
        active_session = self.orchestrator.terminal_manager.active_session_id
        session_info = None

        if active_session:
            session_info = self.orchestrator.terminal_manager.get_session_status(active_session)

        if session_info:
            active_mark = "★" if session_info['is_active'] else ""
            prompt = f"[弥娅] {session_info['name']}{active_mark} > "
        else:
            prompt = "[弥娅] > "

        return chinese_input(prompt).strip()

    async def _process_input(self, user_input: str):
        """处理用户输入"""
        if not user_input:
            return

        # 系统命令
        if user_input.startswith('!'):
            await self._handle_system_command(user_input)
        elif user_input.lower() in ['help', '帮助']:
            self._show_help()
        elif user_input.lower() in ['exit', 'quit', '退出']:
            print("[弥娅] 期待下次再见到您~ 再见!")
            self.running = False
        else:
            # 直接执行命令
            await self._execute_direct_command(user_input)

    async def _execute_direct_command(self, command: str):
        """直接执行命令"""
        if self.orchestrator.terminal_manager.active_session_id:
            print(f"\n[执行命令] {command}")

            try:
                result = await self.orchestrator.terminal_manager.execute_command(
                    self.orchestrator.terminal_manager.active_session_id,
                    command
                )

                if result.output and result.output.strip():
                    print(f"{result.output}")

                if result.error and result.error.strip():
                    print(f"[错误] {result.error}")

                if not result.success:
                    print(f"[状态] 命令执行失败 (退出码: {result.exit_code})")

            except Exception as e:
                print(f"[错误] 执行命令时出错: {e}")
        else:
            print("\n[弥娅] 还没有创建终端呢~ 使用 !create <name> 创建一个吧!")

    async def _handle_system_command(self, command: str):
        """处理系统命令"""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == '!help' or cmd == '!h':
            self._show_help()

        elif cmd == '!create' or cmd == '!new':
            # 创建新终端
            await self._create_terminal(parts)

        elif cmd == '!list' or cmd == '!ls':
            # 列出所有终端
            await self._list_terminals()

        elif cmd == '!switch' or cmd == '!use':
            # 切换终端
            if len(parts) > 1:
                await self.orchestrator.terminal_manager.switch_session(parts[1])
                print(f"[弥娅] 已切换到终端 {parts[1]}")
            else:
                print("[弥娅] 告诉我要切换到哪个终端呢? 用法: !switch <session_id>")

        elif cmd == '!close' or cmd == '!del':
            # 关闭终端
            if len(parts) > 1:
                await self.orchestrator.terminal_manager.close_session(parts[1])
                print(f"[弥娅] 已为您关闭终端 {parts[1]}")
            else:
                print("[弥娅] 告诉我要关闭哪个终端呢? 用法: !close <session_id>")

        elif cmd == '!status' or cmd == '!info':
            # 详细状态
            await self._show_detailed_status()

        else:
            print(f"[弥娅] 我不太理解 '{cmd}' 这个命令呢...")
            print("输入 '!help' 查看所有可用命令")

    async def _create_terminal(self, parts: list[str]) -> None:
        """创建新终端"""
        name = None
        term_type = TerminalType.CMD

        # 解析参数
        i = 1
        while i < len(parts):
            if parts[i] == '-t' or parts[i] == '--type':
                if i + 1 < len(parts):
                    term_type = TerminalType.from_string(parts[i + 1])
                    i += 2
                else:
                    print("[错误] -t 参数需要值")
                    return
            else:
                name = parts[i]
                i += 1

        if not name:
            count = len(self.orchestrator.terminal_manager.sessions)
            name = f"终端{count+1}"

        session_id = await self.orchestrator.terminal_manager.create_terminal(
            name=name,
            terminal_type=term_type
        )

        print(f"[弥娅] 已为您创建终端: {name} (ID: {session_id})")
        print(f"        类型: {term_type.value}")
        print(f"        提示: 使用 !switch {session_id} 切换到这个终端")

    async def _list_terminals(self) -> None:
        """列出所有终端"""
        all_status = self.orchestrator.terminal_manager.get_all_status()

        if not all_status:
            print("\n[弥娅] 当前还没有创建任何终端呢~")
            print("提示: 使用 !create <name> 来创建一个新终端吧!")
            return

        print(f"\n{'='*70}")
        print(f"{'终端列表':<20} {'类型':<15} {'状态':<10} {'目录':<20}")
        print(f"{'='*70}")

        for session_id, status in all_status.items():
            active_mark = "★" if status['is_active'] else " "
            print(f"{active_mark} {status['name']:<18} {status['type']:<15} "
                  f"{status['status']:<10} {status['directory'][:20]:<20}")

        print(f"{'='*70}")

    async def _show_detailed_status(self) -> None:
        """显示详细状态"""
        all_status = self.orchestrator.terminal_manager.get_all_status()

        if not all_status:
            print("\n[弥娅] 当前还没有创建任何终端呢~")
            return

        print(f"\n{'='*70}")
        print("                弥娅多终端系统状态")
        print(f"{'='*70}")

        for session_id, status in all_status.items():
            active_str = " (活动中)" if status['is_active'] else ""
            print(f"\n📱 终端: {status['name']}{active_str}")
            print(f"   ID: {session_id}")
            print(f"   类型: {status['type']}")
            print(f"   状态: {status['status']}")
            print(f"   目录: {status['directory']}")
            print(f"   命令历史: {status['command_count']}条")
            print(f"   输出记录: {status['output_count']}条")

        print(f"\n{'='*70}")

    def _show_help(self):
        """显示帮助"""
        print("""
╔════════════════════════════════════════════════════════════╗
║                    弥娅终端管理系统 - 帮助                  ║
╠════════════════════════════════════════════════════════════╣
║                                                               ║
║  🖥️  终端管理:                                              ║
║    !create <name> [-t type]  - 创建新终端                       ║
║    !list                     - 列出所有终端                     ║
║    !switch <session_id>      - 切换活动终端                     ║
║    !close <session_id>       - 关闭指定终端                     ║
║    !status                   - 显示详细状态                     ║
║                                                               ║
║  ⚡  执行模式:                                              ║
║    直接输入命令              - 在当前终端执行命令               ║
║                                                               ║
║  💡  示例:                                                  ║
║    dir / ls                 - 查看当前目录文件                 ║
║    cd <目录>                - 切换目录                        ║
║    echo Hello               - 输出文本                        ║
║                                                               ║
║  🚪  退出:                                                  ║
║    exit / quit              - 退出系统                         ║
║    Ctrl+C                   - 强制退出                         ║
║                                                               ║
╚════════════════════════════════════════════════════════════╝
        """)


async def main():
    """主函数"""
    print("[启动] 弥娅简化终端模式...")
    
    shell = SimpleTerminalShell()
    await shell.start()
    
    print("[结束] 弥娅终端模式已关闭")


if __name__ == "__main__":
    asyncio.run(main())