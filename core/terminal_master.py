#!/usr/bin/env python3
"""
终端主控制系统 - 让弥娅完全掌控终端
集成智能命令解析、任务规划、自动执行等所有功能
"""

import asyncio
import os
import sys
import json
import logging
import time
import readline  # 用于命令历史
from typing import Dict, List, Optional, Any
from pathlib import Path
import signal

# 导入自定义模块
from core.ai_terminal_system import AITerminalSystem
from core.terminal.base.types import CommandIntent
from core.intelligent_executor import IntelligentExecutor
from core.terminal.base.types import ExecutionMode
from core.task_automation import TaskAutomationSystem, NaturalLanguageTaskCreator

logger = logging.getLogger(__name__)

class TerminalMasterController:
    """终端主控制器"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"master_{int(time.time())}"
        self.working_directory = os.getcwd()
        
        # 初始化所有子系统
        self.ai_system = AITerminalSystem(self.session_id)
        self.executor = IntelligentExecutor(self.session_id)
        self.automation = TaskAutomationSystem(self.executor)
        self.task_creator = NaturalLanguageTaskCreator(self.automation)
        
        # 状态跟踪
        self.is_running = True
        self.command_count = 0
        self.start_time = time.time()
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        logger.info(f"终端主控制器初始化完成 - 会话ID: {self.session_id}")
        self._print_welcome_message()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，优雅关闭...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _print_welcome_message(self):
        """打印欢迎消息"""
        print("\n" + "=" * 70)
        print("🎯 弥娅终端主控制系统")
        print("=" * 70)
        print(f"会话ID: {self.session_id}")
        print(f"工作目录: {self.working_directory}")
        print(f"系统时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n特性:")
        print("  ✓ 智能命令解析和理解")
        print("  ✓ 任务规划和自动化")
        print("  ✓ 完整终端控制能力")
        print("  ✓ 实时监控和反馈")
        print("\n输入 'help' 查看帮助，'exit' 退出系统")
        print("=" * 70 + "\n")
    
    async def run_interactive(self):
        """运行交互模式"""
        print("🔄 启动交互模式...")
        
        while self.is_running:
            try:
                # 显示提示符
                prompt = self._create_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                await self._process_user_input(user_input)
                
                # 更新计数
                self.command_count += 1
                
            except EOFError:
                # Ctrl+D 退出
                print("\n检测到EOF，退出...")
                break
            except KeyboardInterrupt:
                # Ctrl+C 处理
                print("\n输入 'exit' 退出系统")
                continue
            except Exception as e:
                logger.error(f"处理输入时出错: {e}")
                print(f"❌ 错误: {e}")
    
    def _create_prompt(self) -> str:
        """创建提示符"""
        # 获取当前目录的短名称
        try:
            cwd = os.getcwd()
            home = str(Path.home())
            
            if cwd.startswith(home):
                cwd_display = "~" + cwd[len(home):]
            else:
                cwd_display = cwd
            
            # 限制长度
            if len(cwd_display) > 30:
                cwd_display = "..." + cwd_display[-27:]
        except:
            cwd_display = "?"
        
        # 创建彩色提示符（Windows可能需要特殊处理）
        if sys.platform == "win32":
            prompt = f"\n[{cwd_display}] 弥娅★ > "
        else:
            # Linux/Mac可以使用颜色
            prompt = f"\n\033[1;32m{cwd_display}\033[0m \033[1;34m弥娅★\033[0m > "
        
        return prompt
    
    async def _process_user_input(self, user_input: str):
        """处理用户输入"""
        start_time = time.time()
        
        # 检查是否为系统命令
        if await self._handle_system_command(user_input):
            return
        
        # 检查是否为任务请求
        if await self._handle_task_request(user_input):
            return
        
        # 使用智能执行器处理
        print(f"🤖 正在处理: {user_input}")
        
        result = await self.executor.execute_intelligent(user_input)
        
        # 显示结果
        self._display_execution_result(result, time.time() - start_time)
        
        # 更新工作目录
        self._update_working_directory(user_input, result)
    
    async def _handle_system_command(self, user_input: str) -> bool:
        """处理系统命令"""
        command = user_input.lower().strip()
        
        if command in ["exit", "quit", "退出"]:
            print("👋 再见！")
            self.is_running = False
            return True
        
        elif command in ["help", "帮助", "?"]:
            self._show_help()
            return True
        
        elif command in ["status", "状态"]:
            self._show_status()
            return True
        
        elif command in ["history", "历史"]:
            self._show_history()
            return True
        
        elif command in ["clear", "cls", "清屏"]:
            os.system("cls" if sys.platform == "win32" else "clear")
            return True
        
        elif command.startswith("cd "):
            # cd命令特殊处理
            target = command[3:].strip()
            try:
                if target == "~":
                    os.chdir(str(Path.home()))
                elif target == "-":
                    # 这里可以实现目录历史
                    pass
                else:
                    os.chdir(target)
                
                self.working_directory = os.getcwd()
                print(f"📁 目录已切换到: {self.working_directory}")
            except Exception as e:
                print(f"❌ 切换目录失败: {e}")
            return True
        
        return False
    
    async def _handle_task_request(self, user_input: str) -> bool:
        """处理任务请求"""
        # 检查是否为任务相关命令
        task_keywords = ["任务", "计划", "自动化", "备份", "清理", "部署", "task", "schedule", "automate"]
        
        if any(keyword in user_input.lower() for keyword in task_keywords):
            print(f"📋 识别为任务请求: {user_input}")
            
            # 创建任务
            task_plan = self.task_creator.create_task(user_input)
            if task_plan:
                print(f"✅ 创建任务: {task_plan.name}")
                print(f"📝 描述: {task_plan.description}")
                print(f"🔢 步骤: {len(task_plan.steps)} 个")
                
                # 确认执行
                confirm = input("是否立即执行? (y/n): ").strip().lower()
                if confirm == 'y':
                    task_id = self.automation.schedule_task(task_plan)
                    print(f"🚀 任务已调度，ID: {task_id}")
                    
                    # 监控任务执行
                    await self._monitor_task(task_id)
                else:
                    print("⏸️ 任务已保存但未执行")
            else:
                print("❌ 无法创建任务，请尝试其他描述")
            
            return True
        
        return False
    
    async def _monitor_task(self, task_id: str):
        """监控任务执行"""
        print(f"👀 监控任务 {task_id}...")
        
        for _ in range(30):  # 最多监控30秒
            status = self.automation.get_task_status(task_id)
            
            if status:
                print(f"进度: {status.get('progress', 0):.1f}% - {status['status']}")
                
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
            
            await asyncio.sleep(1)
        
        # 显示最终结果
        final_status = self.automation.get_task_status(task_id)
        if final_status:
            if final_status['status'] == 'completed':
                print(f"✅ 任务完成!")
            elif final_status['status'] == 'failed':
                print(f"❌ 任务失败: {final_status.get('error_message', '未知错误')}")
            elif final_status['status'] == 'cancelled':
                print(f"⏹️ 任务已取消")
    
    def _display_execution_result(self, result: Dict[str, Any], execution_time: float):
        """显示执行结果"""
        print(f"\n{'='*50}")
        
        if result.get("success"):
            print(f"✅ 执行成功 ({execution_time:.2f}秒)")
            
            if result.get("output"):
                output = result["output"].strip()
                if output:
                    print(f"📤 输出:\n{output}")
            
        else:
            print(f"❌ 执行失败 ({execution_time:.2f}秒)")
            
            if result.get("error"):
                error = result["error"].strip()
                if error:
                    print(f"💥 错误:\n{error}")
        
        # 显示建议
        if result.get("suggestions"):
            print(f"💡 建议:")
            for suggestion in result["suggestions"]:
                print(f"  • {suggestion}")
        
        print(f"{'='*50}\n")
    
    def _update_working_directory(self, command: str, result: Dict[str, Any]):
        """更新工作目录"""
        # 检查是否为cd命令或改变了目录的命令
        if "cd" in command.lower() and result.get("success"):
            try:
                new_dir = os.getcwd()
                if new_dir != self.working_directory:
                    self.working_directory = new_dir
                    logger.info(f"工作目录更新: {self.working_directory}")
            except:
                pass
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
📚 弥娅终端控制系统 - 帮助

基本命令:
  help / 帮助           - 显示此帮助信息
  exit / quit / 退出    - 退出系统
  status / 状态        - 显示系统状态
  history / 历史       - 显示命令历史
  clear / cls / 清屏   - 清空屏幕

智能功能:
  • 直接输入自然语言命令，如:
    - "查看当前目录的文件"
    - "备份项目到备份目录"
    - "清理系统临时文件"
    - "查看网络连接状态"
  
  • 任务自动化:
    - "创建一个备份任务"
    - "自动化系统清理"
    - "计划定时任务"

  • 系统管理:
    - "查看进程列表"
    - "监控系统资源"
    - "安装软件包"

安全特性:
  • 危险命令需要确认
  • 实时监控执行过程
  • 自动备份重要操作

输入示例:
  查看文件: ls -la
  网络测试: ping google.com
  进程管理: ps aux | grep python
  文件操作: cp file.txt backup/
"""
        print(help_text)
    
    def _show_status(self):
        """显示系统状态"""
        uptime = time.time() - self.start_time
        
        status = f"""
📊 系统状态报告

会话信息:
  • 会话ID: {self.session_id}
  • 运行时间: {uptime:.0f} 秒
  • 命令计数: {self.command_count}

系统信息:
  • 工作目录: {self.working_directory}
  • 操作系统: {sys.platform}
  • Python版本: {sys.version.split()[0]}

子系统状态:
  • AI终端系统: ✅ 运行中
  • 智能执行器: ✅ 运行中
  • 任务自动化: ✅ 运行中

任务状态:
  • 运行中任务: {len(self.automation.running_tasks)}
  • 历史任务: {len(self.automation.task_history)}
"""
        print(status)
    
    def _show_history(self):
        """显示命令历史"""
        history = self.executor.get_execution_history(10)
        
        if not history:
            print("📜 暂无命令历史")
            return
        
        print("📜 最近命令历史:")
        print("-" * 60)
        
        for i, entry in enumerate(reversed(history), 1):
            cmd = entry.get("user_input", "未知命令")
            result = entry.get("result", {})
            success = result.get("success", False)
            timestamp = entry.get("timestamp", 0)
            
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp)) if timestamp > 0 else "未知时间"
            
            status_icon = "✅" if success else "❌"
            print(f"{i:2d}. {time_str} {status_icon} {cmd}")
        
        print("-" * 60)

class TerminalMasterCLI:
    """终端主控制系统CLI"""
    
    @staticmethod
    def run():
        """运行CLI"""
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("🚀 启动弥娅终端主控制系统...")
        
        try:
            # 创建控制器
            controller = TerminalMasterController()
            
            # 运行交互模式
            asyncio.run(controller.run_interactive())
            
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断，正在退出...")
        except Exception as e:
            print(f"\n💥 系统错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("👋 弥娅终端系统已关闭")

# 命令行接口
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="弥娅终端主控制系统")
    parser.add_argument("--session", help="指定会话ID")
    parser.add_argument("--command", help="执行单个命令后退出")
    parser.add_argument("--script", help="执行脚本文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    if args.command:
        # 执行单个命令
        print(f"执行命令: {args.command}")
        
        controller = TerminalMasterController(args.session)
        
        # 执行命令
        import asyncio
        asyncio.run(controller._process_user_input(args.command))
        
    elif args.script:
        # 执行脚本
        print(f"执行脚本: {args.script}")
        
        if os.path.exists(args.script):
            with open(args.script, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            controller = TerminalMasterController(args.session)
            
            # 这里可以添加脚本执行逻辑
            print("脚本执行功能开发中...")
        else:
            print(f"错误: 脚本文件不存在 - {args.script}")
    
    else:
        # 启动交互模式
        TerminalMasterCLI.run()

if __name__ == "__main__":
    main()