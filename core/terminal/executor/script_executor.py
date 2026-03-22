#!/usr/bin/env python3
"""
脚本执行器

专门处理脚本文件的执行
"""

import logging
import os
import subprocess
import shlex
from typing import Optional, Dict, Any
from pathlib import Path

from ..base.types import CommandResult, ExecutionContext
from .intelligent_executor import IntelligentExecutor

logger = logging.getLogger(__name__)


class ScriptExecutor:
    """脚本执行器"""
    
    def __init__(self, executor: Optional[IntelligentExecutor] = None):
        self.logger = logging.getLogger(__name__)
        
        if executor:
            self.executor = executor
        else:
            self.executor = IntelligentExecutor()
        
        # 支持的脚本扩展名
        self.supported_extensions = {
            '.py': 'python',
            '.sh': 'bash',
            '.bat': 'cmd',
            '.ps1': 'powershell',
            '.js': 'node',
            '.ts': 'ts-node',
            '.rb': 'ruby',
            '.php': 'php',
            '.pl': 'perl',
            '.lua': 'lua'
        }
        
        # 脚本解释器映射
        self.interpreter_map = {
            'python': ['python', 'python3'],
            'bash': ['bash', 'sh'],
            'cmd': ['cmd', 'cmd.exe'],
            'powershell': ['powershell', 'pwsh'],
            'node': ['node', 'nodejs'],
            'ts-node': ['ts-node'],
            'ruby': ['ruby'],
            'php': ['php'],
            'perl': ['perl'],
            'lua': ['lua']
        }
        
        self.logger.info("脚本执行器初始化完成")
    
    def get_script_type(self, script_path: str) -> Optional[str]:
        """
        获取脚本类型
        
        Args:
            script_path: 脚本路径
            
        Returns:
            脚本类型，如果不支持则返回None
        """
        path = Path(script_path)
        
        if not path.exists():
            self.logger.warning(f"脚本文件不存在: {script_path}")
            return None
        
        ext = path.suffix.lower()
        
        if ext in self.supported_extensions:
            return self.supported_extensions[ext]
        
        # 检查文件头部
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                
                # 检查shebang
                if first_line.startswith('#!'):
                    shebang = first_line[2:]
                    
                    # 解析shebang
                    for script_type, interpreters in self.interpreter_map.items():
                        for interpreter in interpreters:
                            if interpreter in shebang:
                                return script_type
                
                # 检查.py文件没有shebang的情况
                if ext == '.py' or script_path.endswith('.py'):
                    return 'python'
                
                # 检查.sh文件
                if ext == '.sh' or script_path.endswith('.sh'):
                    return 'bash'
                
        except Exception as e:
            self.logger.error(f"读取脚本文件失败: {e}")
        
        return None
    
    def build_command(self, script_path: str, args: Optional[list] = None) -> str:
        """
        构建执行命令
        
        Args:
            script_path: 脚本路径
            args: 参数列表
            
        Returns:
            构建的命令字符串
        """
        script_type = self.get_script_type(script_path)
        
        if not script_type:
            self.logger.error(f"不支持的脚本类型: {script_path}")
            return f"echo '不支持的脚本类型: {script_path}'"
        
        # 获取解释器
        interpreters = self.interpreter_map.get(script_type, [])
        interpreter = interpreters[0] if interpreters else script_type
        
        # 构建命令
        command_parts = [interpreter, script_path]
        
        if args:
            # 转义参数
            escaped_args = []
            for arg in args:
                if ' ' in arg:
                    escaped_args.append(f'"{arg}"')
                else:
                    escaped_args.append(arg)
            
            command_parts.extend(escaped_args)
        
        return ' '.join(command_parts)
    
    def execute_script(self, 
                       script_path: str, 
                       args: Optional[list] = None, 
                       context: Optional[ExecutionContext] = None) -> CommandResult:
        """
        执行脚本
        
        Args:
            script_path: 脚本路径
            args: 参数列表
            context: 执行上下文
            
        Returns:
            执行结果
        """
        # 验证脚本文件
        script_file = Path(script_path)
        
        if not script_file.exists():
            self.logger.error(f"脚本文件不存在: {script_path}")
            return CommandResult(
                success=False,
                output="",
                error=f"脚本文件不存在: {script_path}",
                error_code=404
            )
        
        if not script_file.is_file():
            self.logger.error(f"不是有效的文件: {script_path}")
            return CommandResult(
                success=False,
                output="",
                error=f"不是有效的文件: {script_path}",
                error_code=400
            )
        
        # 检查脚本类型
        script_type = self.get_script_type(script_path)
        
        if not script_type:
            self.logger.error(f"不支持的脚本类型: {script_path}")
            return CommandResult(
                success=False,
                output="",
                error=f"不支持的脚本类型: {script_path}",
                error_code=415
            )
        
        # 构建命令
        command = self.build_command(script_path, args)
        
        # 设置上下文
        if context is None:
            context = ExecutionContext()
        
        # 确保工作目录是脚本所在目录
        if not context.working_directory:
            context.working_directory = str(script_file.parent)
        
        # 添加脚本环境变量
        if not context.environment:
            context.environment = {}
        
        context.environment.update({
            'SCRIPT_PATH': script_path,
            'SCRIPT_TYPE': script_type,
            'SCRIPT_DIR': str(script_file.parent)
        })
        
        # 设置合适的超时时间
        if context.timeout is None:
            context.timeout = 300  # 默认5分钟
        
        # 执行命令
        self.logger.info(f"执行脚本: {script_path} (类型: {script_type})")
        result = self.executor.execute(command, context)
        
        # 添加脚本相关信息
        result.metadata = result.metadata or {}
        result.metadata.update({
            'script_path': script_path,
            'script_type': script_type,
            'interpreter': self.interpreter_map.get(script_type, [script_type])[0]
        })
        
        return result
    
    def validate_script(self, script_path: str) -> Dict[str, Any]:
        """
        验证脚本
        
        Args:
            script_path: 脚本路径
            
        Returns:
            验证结果
        """
        result = {
            'valid': False,
            'script_type': None,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        # 检查文件是否存在
        script_file = Path(script_path)
        if not script_file.exists():
            result['errors'].append(f"文件不存在: {script_path}")
            return result
        
        if not script_file.is_file():
            result['errors'].append(f"不是有效的文件: {script_path}")
            return result
        
        # 检查文件权限
        if not os.access(script_path, os.R_OK):
            result['errors'].append(f"文件不可读: {script_path}")
        
        if not os.access(script_path, os.X_OK):
            result['warnings'].append(f"文件不可执行: {script_path}")
        
        # 检查文件大小
        file_size = script_file.stat().st_size
        result['info']['file_size'] = file_size
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            result['warnings'].append(f"文件过大: {file_size / (1024*1024):.1f}MB")
        
        # 检查脚本类型
        script_type = self.get_script_type(script_path)
        result['script_type'] = script_type
        
        if script_type:
            result['valid'] = True
            result['info']['interpreter'] = self.interpreter_map.get(script_type, [script_type])[0]
        else:
            result['errors'].append(f"不支持的脚本类型: {script_path}")
        
        # 检查文件头部
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
                
                # 检查shebang
                if first_lines and first_lines[0].startswith('#!'):
                    result['info']['shebang'] = first_lines[0]
                
                # 检查编码声明
                for line in first_lines:
                    if 'coding:' in line.lower() or 'encoding:' in line.lower():
                        result['info']['encoding_declaration'] = line
                        break
                
                # 检查空文件
                if file_size == 0:
                    result['errors'].append("文件为空")
                    result['valid'] = False
                    
        except UnicodeDecodeError:
            result['errors'].append("文件编码无法识别")
            result['valid'] = False
        except Exception as e:
            result['errors'].append(f"读取文件失败: {e}")
            result['valid'] = False
        
        return result
    
    def get_supported_extensions(self) -> list:
        """获取支持的扩展名列表"""
        return list(self.supported_extensions.keys())
    
    def add_supported_extension(self, extension: str, script_type: str):
        """
        添加支持的扩展名
        
        Args:
            extension: 扩展名（以.开头，如 .rs）
            script_type: 脚本类型
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        
        self.supported_extensions[extension.lower()] = script_type
        self.logger.info(f"添加支持的扩展名: {extension} -> {script_type}")


# 单例实例
_global_script_executor: Optional[ScriptExecutor] = None

def get_script_executor() -> ScriptExecutor:
    """获取全局脚本执行器实例"""
    global _global_script_executor
    
    if _global_script_executor is None:
        _global_script_executor = ScriptExecutor()
    
    return _global_script_executor