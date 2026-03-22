#!/usr/bin/env python3
"""
程序启动助手
为弥娅系统提供智能的程序启动功能
"""

import subprocess
import os
import sys
import logging
from typing import List, Dict, Optional, Tuple
import shutil

logger = logging.getLogger(__name__)

class ProgramLauncher:
    """程序启动器"""
    
    def __init__(self):
        self.program_paths_cache = {}
        self.custom_config = self._load_custom_config()
    
    def _load_custom_config(self) -> Dict:
        """加载自定义配置"""
        config_paths = [
            "firefox_config.json",
            "program_paths.json",
            os.path.join(os.path.dirname(__file__), "..", "config", "programs.json")
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    import json
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    logger.info(f"加载自定义配置: {config_path}")
                    
                    # 处理自定义路径
                    if "custom_paths" in config:
                        for program, path in config["custom_paths"].items():
                            if os.path.exists(path):
                                self.program_paths_cache[program] = path
                                logger.info(f"自定义路径: {program} -> {path}")
                    
                    return config
                    
                except Exception as e:
                    logger.error(f"加载配置 {config_path} 失败: {e}")
        
        return {}
        
    def find_program(self, program_name: str) -> Optional[str]:
        """查找程序的可执行文件路径"""
        # 1. 检查缓存
        if program_name in self.program_paths_cache:
            return self.program_paths_cache[program_name]
        
        # 2. 检查自定义配置
        program_key = program_name.lower()
        if self.custom_config and "custom_paths" in self.custom_config:
            custom_paths = self.custom_config["custom_paths"]
            
            # 直接匹配
            if program_key in custom_paths:
                path = custom_paths[program_key]
                if os.path.exists(path):
                    self.program_paths_cache[program_name] = path
                    logger.info(f"使用自定义配置路径: {program_name} -> {path}")
                    return path
            
            # 别名匹配
            aliases = {
                "火狐": "firefox",
                "firefox": "firefox", 
                "谷歌": "chrome",
                "chrome": "chrome",
                "edge": "edge",
                "记事本": "notepad",
                "notepad": "notepad",
                "计算器": "calc",
                "calc": "calc"
            }
            
            if program_key in aliases:
                alias = aliases[program_key]
                if alias in custom_paths:
                    path = custom_paths[alias]
                    if os.path.exists(path):
                        self.program_paths_cache[program_name] = path
                        logger.info(f"使用别名自定义路径: {program_name} -> {path}")
                        return path
        
        program_path = None
        
        # Windows系统
        if sys.platform == "win32":
            # 常见的Windows程序路径
            common_paths = {
                "firefox": [
                    "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                    "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
                    os.path.expanduser("~\\AppData\\Local\\Mozilla Firefox\\firefox.exe")
                ],
                "chrome": [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                    os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
                ],
                "edge": [
                    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                    os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\Application\\msedge.exe")
                ],
                "notepad": [
                    "C:\\Windows\\System32\\notepad.exe"
                ],
                "calc": [
                    "C:\\Windows\\System32\\calc.exe"
                ],
                "cmd": [
                    "C:\\Windows\\System32\\cmd.exe"
                ],
                "powershell": [
                    "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                ]
            }
            
            # 查找特定程序
            if program_name in common_paths:
                for path in common_paths[program_name]:
                    if os.path.exists(path):
                        program_path = path
                        break
            
            # 如果没找到，尝试在PATH中查找
            if not program_path:
                path_extensions = ['.exe', '.bat', '.cmd']
                for ext in path_extensions:
                    found = shutil.which(f"{program_name}{ext}")
                    if found:
                        program_path = found
                        break
        
        # Linux/Mac系统
        else:
            # 在PATH中查找
            program_path = shutil.which(program_name)
            
            # Linux特定的程序路径
            if sys.platform == "linux" and not program_path:
                linux_paths = {
                    "firefox": ["/usr/bin/firefox", "/usr/local/bin/firefox"],
                    "chrome": ["/usr/bin/google-chrome", "/opt/google/chrome/google-chrome"],
                    "gedit": ["/usr/bin/gedit"],
                    "nautilus": ["/usr/bin/nautilus"]
                }
                if program_name in linux_paths:
                    for path in linux_paths[program_name]:
                        if os.path.exists(path):
                            program_path = path
                            break
            
            # Mac特定的程序路径
            elif sys.platform == "darwin" and not program_path:
                mac_paths = {
                    "firefox": ["/Applications/Firefox.app"],
                    "chrome": ["/Applications/Google Chrome.app"],
                    "safari": ["/Applications/Safari.app"]
                }
                if program_name in mac_paths:
                    for path in mac_paths[program_name]:
                        if os.path.exists(path):
                            program_path = path
                            break
        
        # 缓存结果
        if program_path:
            self.program_paths_cache[program_name] = program_path
            logger.info(f"找到程序 '{program_name}': {program_path}")
        else:
            logger.warning(f"未找到程序 '{program_name}'")
        
        return program_path
    
    def launch_program(self, program_name: str, arguments: List[str] = None) -> Tuple[bool, str]:
        """启动程序
        
        Args:
            program_name: 程序名或路径
            arguments: 启动参数
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 如果提供的是完整路径，直接使用
            if os.path.exists(program_name) and os.path.isfile(program_name):
                program_path = program_name
            else:
                # 查找程序
                program_path = self.find_program(program_name.lower())
                if not program_path:
                    return False, f"❌ 未找到程序 '{program_name}'。请确认是否已安装。"
            
            # 准备启动命令
            cmd = [program_path]
            if arguments:
                cmd.extend(arguments)
            
            # 启动程序
            logger.info(f"启动程序: {' '.join(cmd)}")
            
            if sys.platform == "win32":
                # Windows: 使用shell=True以便正确处理路径中的空格
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                # Linux/Mac
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            
            # 等待一会儿检查是否启动成功
            try:
                process.wait(timeout=2)
                # 如果进程很快结束，可能是错误
                if process.returncode != 0:
                    stderr = process.stderr.read() if process.stderr else ""
                    error_msg = stderr[:200] if stderr else f"退出码: {process.returncode}"
                    return False, f"❌ 程序启动失败: {error_msg}"
                else:
                    return True, f"✅ 程序 '{program_name}' 已启动"
            except subprocess.TimeoutExpired:
                # 进程仍在运行，说明启动成功
                return True, f"✅ 程序 '{program_name}' 已启动"
                
        except FileNotFoundError:
            return False, f"❌ 文件未找到: {program_name}"
        except PermissionError:
            return False, f"❌ 没有权限启动程序: {program_name}"
        except Exception as e:
            logger.error(f"启动程序 '{program_name}' 时出错: {e}", exc_info=True)
            return False, f"❌ 启动程序时遇到问题: {str(e)[:100]}"
    
    def launch_browser(self, browser_name: str, url: str = None) -> Tuple[bool, str]:
        """启动浏览器
        
        Args:
            browser_name: 浏览器名称 (firefox, chrome, edge等)
            url: 要打开的URL
            
        Returns:
            (成功标志, 消息)
        """
        browser_name = browser_name.lower()
        
        # 浏览器别名映射
        browser_aliases = {
            "火狐": "firefox",
            "firefox": "firefox",
            "谷歌": "chrome",
            "chrome": "chrome",
            "edge": "edge",
            "微软浏览器": "edge",
            "safari": "safari"
        }
        
        actual_browser = browser_aliases.get(browser_name, browser_name)
        
        # 准备启动参数
        arguments = []
        if url:
            arguments.append(url)
        
        return self.launch_program(actual_browser, arguments)
    
    def parse_launch_command(self, message: str) -> Tuple[Optional[str], List[str]]:
        """解析启动命令
        
        Args:
            message: 用户消息，如"打开火狐"或"启动记事本"
            
        Returns:
            (程序名, 参数列表) 或 (None, []) 如果无法解析
        """
        message = message.lower().strip()
        
        # 常见的中文启动命令
        launch_patterns = {
            r"打开\s*(火狐|firefox)": "firefox",
            r"启动\s*(火狐|firefox)": "firefox",
            r"运行\s*(火狐|firefox)": "firefox",
            r"打开\s*(谷歌|chrome)": "chrome",
            r"启动\s*(谷歌|chrome)": "chrome",
            r"打开\s*(edge|微软浏览器)": "edge",
            r"启动\s*(edge|微软浏览器)": "edge",
            r"打开\s*(记事本|notepad)": "notepad",
            r"启动\s*(记事本|notepad)": "notepad",
            r"打开\s*(计算器|calc)": "calc",
            r"启动\s*(计算器|calc)": "calc",
            r"打开\s*(cmd|命令行)": "cmd",
            r"启动\s*(cmd|命令行)": "cmd",
            r"打开\s*(powershell)": "powershell",
            r"启动\s*(powershell)": "powershell"
        }
        
        import re
        
        for pattern, program in launch_patterns.items():
            match = re.search(pattern, message)
            if match:
                return program, []
        
        # 通用格式: "打开 [程序名]"
        match = re.search(r"打开\s+(.+)", message)
        if match:
            program_name = match.group(1).strip()
            return program_name, []
        
        # 通用格式: "启动 [程序名]"
        match = re.search(r"启动\s+(.+)", message)
        if match:
            program_name = match.group(1).strip()
            return program_name, []
        
        return None, []
    
    def get_supported_programs(self) -> Dict[str, List[str]]:
        """获取支持的程序列表"""
        return {
            "浏览器": ["火狐 (firefox)", "谷歌浏览器 (chrome)", "微软Edge (edge)", "Safari"],
            "系统工具": ["记事本 (notepad)", "计算器 (calc)", "命令行 (cmd)", "PowerShell"],
            "办公软件": ["Word", "Excel", "PowerPoint", "记事本"],
            "媒体播放器": ["Windows Media Player", "VLC", "暴风影音"]
        }

def test_launcher():
    """测试启动器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="程序启动器测试")
    parser.add_argument("program", help="要启动的程序名")
    parser.add_argument("--url", help="要打开的URL (仅浏览器)")
    
    args = parser.parse_args()
    
    launcher = ProgramLauncher()
    
    print(f"测试启动程序: {args.program}")
    
    if args.url:
        print(f"URL: {args.url}")
        success, message = launcher.launch_browser(args.program, args.url)
    else:
        success, message = launcher.launch_program(args.program)
    
    print(f"结果: {message}")
    
    if not success:
        print("\n支持的程序:")
        supported = launcher.get_supported_programs()
        for category, programs in supported.items():
            print(f"  {category}:")
            for program in programs:
                print(f"    • {program}")

if __name__ == "__main__":
    test_launcher()