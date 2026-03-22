#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整终端系统测试

测试修复后的终端系统所有功能
"""

import asyncio
import sys
import os
import time
import json
import platform
from pathlib import Path

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("完整终端系统测试")
print("=" * 80)


class TerminalSystemTester:
    """终端系统测试器"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {test_name}: {message}")
        
        return success
    
    async def test_module_imports(self):
        """测试模块导入"""
        print("\n1. 测试模块导入...")
        
        modules = [
            ("core.local_terminal_manager", "LocalTerminalManager"),
            ("core.terminal_types", "TerminalType"),
            ("core.terminal_orchestrator", "IntelligentTerminalOrchestrator"),
            ("core.terminal_agent", "MiyaTerminalAgent"),
            ("core.conpty_terminal_manager", "ConPTYTerminalManager"),
        ]
        
        all_success = True
        for module_path, class_name in modules:
            try:
                module = __import__(module_path, fromlist=[class_name])
                if hasattr(module, class_name):
                    self.log_result(f"导入 {class_name}", True, f"{module_path}.{class_name}")
                else:
                    self.log_result(f"导入 {class_name}", False, f"类 {class_name} 不存在")
                    all_success = False
            except ImportError as e:
                self.log_result(f"导入 {class_name}", False, f"导入失败: {e}")
                all_success = False
            except Exception as e:
                self.log_result(f"导入 {class_name}", False, f"异常: {e}")
                all_success = False
        
        return all_success
    
    async def test_terminal_creation(self):
        """测试终端创建"""
        print("\n2. 测试终端创建...")
        
        try:
            from core.local_terminal_manager import LocalTerminalManager
            from core.terminal_types import TerminalType
            
            manager = LocalTerminalManager(use_conpty=False)  # 暂时禁用ConPTY
            
            # 测试创建CMD终端
            session_id = await manager.create_terminal(
                name="测试终端-CMD",
                terminal_type=TerminalType.CMD
            )
            
            if session_id:
                self.log_result("创建CMD终端", True, f"会话ID: {session_id}")
                
                # 测试获取状态
                status = manager.get_session_status(session_id)
                if status:
                    self.log_result("获取终端状态", True, f"状态: {status['status']}")
                else:
                    self.log_result("获取终端状态", False, "状态获取失败")
                
                # 测试命令执行
                result = await manager.execute_command(session_id, "echo 终端测试成功")
                if result.success:
                    self.log_result("执行命令", True, f"输出: {result.output[:50]}...")
                else:
                    self.log_result("执行命令", False, f"错误: {result.error}")
                
                # 测试终端切换
                try:
                    await manager.switch_session(session_id)
                    self.log_result("切换终端", True, f"活动终端: {manager.active_session_id}")
                except Exception as e:
                    self.log_result("切换终端", False, f"切换失败: {e}")
                
                # 清理
                await manager.close_session(session_id)
                self.log_result("关闭终端", True, "终端已关闭")
                
                return True
            else:
                self.log_result("创建CMD终端", False, "会话ID为空")
                return False
                
        except Exception as e:
            self.log_result("终端创建测试", False, f"异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_multiple_terminals(self):
        """测试多终端"""
        print("\n3. 测试多终端...")
        
        try:
            from core.local_terminal_manager import LocalTerminalManager
            from core.terminal_types import TerminalType
            
            manager = LocalTerminalManager(use_conpty=False)
            
            # 创建多个终端
            terminals = []
            for i in range(2):
                session_id = await manager.create_terminal(
                    name=f"多终端测试-{i+1}",
                    terminal_type=TerminalType.CMD
                )
                if session_id:
                    terminals.append(session_id)
                    self.log_result(f"创建终端{i+1}", True, f"ID: {session_id}")
                else:
                    self.log_result(f"创建终端{i+1}", False, "创建失败")
            
            if len(terminals) >= 2:
                self.log_result("多终端创建", True, f"创建了 {len(terminals)} 个终端")
                
                # 测试获取所有状态
                all_status = manager.get_all_status()
                if len(all_status) >= 2:
                    self.log_result("获取所有状态", True, f"共 {len(all_status)} 个终端")
                else:
                    self.log_result("获取所有状态", False, f"只有 {len(all_status)} 个终端")
                
                # 测试并行执行
                commands = {terminals[0]: "echo 终端1", terminals[1]: "echo 终端2"}
                results = await manager.execute_parallel(commands)
                
                success_count = sum(1 for r in results.values() if r.success)
                if success_count >= 2:
                    self.log_result("并行执行", True, f"{success_count}/2 个命令成功")
                else:
                    self.log_result("并行执行", False, f"只有 {success_count}/2 个命令成功")
                
                # 清理
                for session_id in terminals:
                    await manager.close_session(session_id)
                self.log_result("清理多终端", True, "所有终端已关闭")
                
                return True
            else:
                self.log_result("多终端测试", False, "终端数量不足")
                return False
                
        except Exception as e:
            self.log_result("多终端测试", False, f"异常: {e}")
            return False
    
    async def test_orchestrator(self):
        """测试终端编排器"""
        print("\n4. 测试终端编排器...")
        
        try:
            from core.terminal_orchestrator import IntelligentTerminalOrchestrator
            
            orchestrator = IntelligentTerminalOrchestrator()
            self.log_result("创建编排器", True, "IntelligentTerminalOrchestrator")
            
            # 测试智能执行
            result = await orchestrator.smart_execute("显示当前目录")
            
            if "error" not in result:
                self.log_result("智能执行", True, f"策略: {result.get('strategy', 'unknown')}")
                return True
            else:
                self.log_result("智能执行", False, f"错误: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            self.log_result("编排器测试", False, f"异常: {e}")
            return False
    
    async def test_terminal_agent(self):
        """测试终端代理"""
        print("\n5. 测试终端代理...")
        
        try:
            from core.terminal_agent import MiyaTerminalAgent
            
            agent = MiyaTerminalAgent("test_session_123")
            self.log_result("创建终端代理", True, "MiyaTerminalAgent")
            
            # 测试连接（不实际连接，只测试对象创建）
            if hasattr(agent, 'connect_to_miya'):
                self.log_result("代理方法检查", True, "connect_to_miya 方法存在")
            else:
                self.log_result("代理方法检查", False, "connect_to_miya 方法不存在")
            
            if hasattr(agent, 'send_message'):
                self.log_result("代理方法检查", True, "send_message 方法存在")
            else:
                self.log_result("代理方法检查", False, "send_message 方法不存在")
            
            return True
            
        except Exception as e:
            self.log_result("终端代理测试", False, f"异常: {e}")
            return False
    
    async def test_api_integration(self):
        """测试API集成"""
        print("\n6. 测试API集成...")
        
        try:
            import requests
            import time
            
            # 检查API服务器是否运行
            try:
                response = requests.get("http://localhost:8000/api/status", timeout=3)
                if response.status_code == 200:
                    self.log_result("API服务器状态", True, "服务器运行正常")
                    
                    # 测试终端API
                    data = {
                        "message": "API集成测试",
                        "session_id": "api_test_123",
                        "from_terminal": "test_terminal"
                    }
                    
                    response = requests.post(
                        "http://localhost:8000/api/terminal/chat",
                        json=data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log_result("终端API", True, f"响应: {result.get('response', '')[:50]}...")
                        return True
                    else:
                        self.log_result("终端API", False, f"状态码: {response.status_code}")
                        return False
                else:
                    self.log_result("API服务器状态", False, f"状态码: {response.status_code}")
                    return False
                    
            except requests.exceptions.ConnectionError:
                self.log_result("API服务器状态", False, "无法连接，服务器可能未运行")
                return False
            except Exception as e:
                self.log_result("API集成测试", False, f"异常: {e}")
                return False
                
        except ImportError:
            self.log_result("API集成测试", False, "requests模块未安装")
            return False
        except Exception as e:
            self.log_result("API集成测试", False, f"异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始运行完整终端系统测试...\n")
        
        tests = [
            self.test_module_imports,
            self.test_terminal_creation,
            self.test_multiple_terminals,
            self.test_orchestrator,
            self.test_terminal_agent,
            self.test_api_integration
        ]
        
        test_names = [
            "模块导入",
            "终端创建",
            "多终端",
            "终端编排器",
            "终端代理",
            "API集成"
        ]
        
        test_results = []
        
        for i, (test_func, test_name) in enumerate(zip(tests, test_names), 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = await test_func()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"测试异常: {e}")
                import traceback
                traceback.print_exc()
                test_results.append((test_name, False))
        
        # 总结
        print("\n" + "=" * 80)
        print("测试结果总结")
        print("=" * 80)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for _, passed in test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, passed in test_results:
            status = "✅" if passed else "❌"
            print(f"  {status} {test_name}")
        
        # 输出JSON报告
        report = {
            "timestamp": time.time(),
            "duration": time.time() - self.start_time,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": [
                {
                    "test": test_name,
                    "passed": passed
                }
                for test_name, passed in test_results
            ],
            "detailed_results": self.results
        }
        
        # 保存报告
        report_file = "terminal_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        return passed_tests == total_tests


async def main():
    """主函数"""
    tester = TerminalSystemTester()
    success = await tester.run_all_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 所有测试通过！终端系统功能正常。")
    else:
        print("⚠️  部分测试失败，请检查上述输出。")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
