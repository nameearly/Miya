#!/usr/bin/env python3
"""
命令规范化器

规范化命令格式，处理别名、缩写和环境变量
"""

import re
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CommandNormalizer:
    """命令规范化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 命令别名映射
        self.command_aliases: Dict[str, str] = {
            # Linux/Unix 别名
            'll': 'ls -la',
            'la': 'ls -a',
            'l': 'ls -CF',
            '..': 'cd ..',
            '...': 'cd ../..',
            '....': 'cd ../../..',
            '.....': 'cd ../../../..',
            
            # Git 别名
            'g': 'git',
            'ga': 'git add',
            'gc': 'git commit',
            'gcm': 'git commit -m',
            'gp': 'git push',
            'gpl': 'git pull',
            'gst': 'git status',
            'gco': 'git checkout',
            'gb': 'git branch',
            'glog': 'git log --oneline --graph',
            
            # Docker 别名
            'd': 'docker',
            'dc': 'docker-compose',
            'di': 'docker images',
            'dps': 'docker ps',
            'dpsa': 'docker ps -a',
            
            # Python 别名
            'py': 'python',
            'py3': 'python3',
            'pip3': 'pip',
            'venv': 'python -m venv',
            
            # 系统管理别名
            'cls': 'clear',
            'md': 'mkdir',
            'rd': 'rmdir',
            'del': 'rm',
            'copy': 'cp',
            'move': 'mv',
            'type': 'cat',
            'dir': 'ls',
        }
        
        # 常用命令的默认参数
        self.default_arguments: Dict[str, List[str]] = {
            'ls': ['-la', '--color=auto'],
            'grep': ['--color=auto'],
            'll': ['-la'],
            'find': ['.', '-type', 'f'],
            'ps': ['aux'],
            'top': ['-b', '-n', '1'],
            'df': ['-h'],
            'du': ['-h'],
            'free': ['-h'],
            'docker': ['--help'],
            'kubectl': ['--help'],
        }
        
        # 路径缩写
        self.path_abbreviations: Dict[str, str] = {
            '~': os.path.expanduser('~'),
            '.': os.getcwd(),
            '..': str(Path(os.getcwd()).parent),
        }
        
        # 环境变量模式
        self.env_var_pattern = re.compile(r'\$(\w+|\{[^}]+\})')
        
        # 规范化统计
        self.stats = {
            "total_normalizations": 0,
            "alias_expansions": 0,
            "path_expansions": 0,
            "env_var_expansions": 0,
            "argument_additions": 0
        }
        
        self.logger.info("命令规范化器初始化完成")
    
    def normalize(self, command: str) -> str:
        """
        规范化命令
        
        Args:
            command: 原始命令字符串
            
        Returns:
            规范化后的命令字符串
        """
        self.stats["total_normalizations"] += 1
        
        if not command or not command.strip():
            return command
        
        # 步骤1: 去除多余空格
        normalized = ' '.join(command.strip().split())
        
        # 步骤2: 扩展别名
        normalized = self._expand_aliases(normalized)
        
        # 步骤3: 扩展环境变量
        normalized = self._expand_env_vars(normalized)
        
        # 步骤4: 扩展路径缩写
        normalized = self._expand_path_abbreviations(normalized)
        
        # 步骤5: 添加默认参数
        normalized = self._add_default_arguments(normalized)
        
        # 步骤6: 规范化路径分隔符（Windows到Unix）
        normalized = self._normalize_path_separators(normalized)
        
        # 步骤7: 处理引号和转义
        normalized = self._normalize_quotes(normalized)
        
        return normalized
    
    def _expand_aliases(self, command: str) -> str:
        """扩展命令别名"""
        parts = command.split()
        if not parts:
            return command
        
        # 检查第一个单词是否为别名
        first_word = parts[0]
        if first_word in self.command_aliases:
            self.stats["alias_expansions"] += 1
            alias_expansion = self.command_aliases[first_word]
            
            # 如果别名扩展包含多个单词
            alias_parts = alias_expansion.split()
            if len(alias_parts) > 1:
                # 替换第一个单词，保留其他部分
                return ' '.join(alias_parts + parts[1:])
            else:
                # 只替换第一个单词
                return ' '.join([alias_expansion] + parts[1:])
        
        return command
    
    def _expand_env_vars(self, command: str) -> str:
        """扩展环境变量"""
        def replace_env_var(match):
            var_name = match.group(1)
            # 处理 ${VAR} 格式
            if var_name.startswith('{') and var_name.endswith('}'):
                var_name = var_name[1:-1]
            
            # 获取环境变量值
            env_value = os.environ.get(var_name, '')
            
            if env_value:
                self.stats["env_var_expansions"] += 1
                return env_value
            else:
                # 如果环境变量不存在，保留原样
                return match.group(0)
        
        # 使用正则表达式替换环境变量
        result = self.env_var_pattern.sub(replace_env_var, command)
        return result
    
    def _expand_path_abbreviations(self, command: str) -> str:
        """扩展路径缩写"""
        parts = command.split()
        expanded_parts = []
        
        for part in parts:
            expanded_part = part
            
            # 检查是否为路径缩写
            for abbr, full_path in self.path_abbreviations.items():
                if part.startswith(abbr):
                    # 替换缩写
                    expanded_part = part.replace(abbr, full_path, 1)
                    self.stats["path_expansions"] += 1
                    break
            
            expanded_parts.append(expanded_part)
        
        return ' '.join(expanded_parts)
    
    def _add_default_arguments(self, command: str) -> str:
        """添加默认参数"""
        parts = command.split()
        if not parts:
            return command
        
        command_name = parts[0]
        
        # 检查是否有默认参数
        if command_name in self.default_arguments:
            default_args = self.default_arguments[command_name]
            
            # 检查是否已经包含任何默认参数
            has_default_arg = False
            for arg in default_args:
                if arg in parts:
                    has_default_arg = True
                    break
            
            # 如果没有包含默认参数，添加它们
            if not has_default_arg:
                self.stats["argument_additions"] += 1
                return ' '.join([command] + default_args)
        
        return command
    
    def _normalize_path_separators(self, command: str) -> str:
        """规范化路径分隔符"""
        # 将Windows路径分隔符转换为Unix风格
        normalized = command.replace('\\', '/')
        
        # 处理Windows盘符
        if ':/' in normalized and not normalized.startswith('http://') and not normalized.startswith('https://'):
            # 可能是Windows路径，不进行转换
            return command
        
        return normalized
    
    def _normalize_quotes(self, command: str) -> str:
        """规范化引号"""
        # 确保引号配对
        single_quotes = command.count("'")
        double_quotes = command.count('"')
        
        # 如果引号不成对，添加缺失的引号
        if single_quotes % 2 == 1:
            command += "'"
        
        if double_quotes % 2 == 1:
            command += '"'
        
        return command
    
    def add_alias(self, alias: str, expansion: str):
        """
        添加命令别名
        
        Args:
            alias: 别名
            expansion: 扩展内容
        """
        self.command_aliases[alias] = expansion
        self.logger.info(f"添加别名: {alias} -> {expansion}")
    
    def remove_alias(self, alias: str) -> bool:
        """
        移除命令别名
        
        Args:
            alias: 要移除的别名
            
        Returns:
            是否成功移除
        """
        if alias in self.command_aliases:
            del self.command_aliases[alias]
            self.logger.info(f"移除别名: {alias}")
            return True
        return False
    
    def add_default_arguments(self, command: str, arguments: List[str]):
        """
        添加默认参数
        
        Args:
            command: 命令名
            arguments: 默认参数列表
        """
        self.default_arguments[command] = arguments
        self.logger.info(f"为命令 {command} 添加默认参数: {arguments}")
    
    def add_path_abbreviation(self, abbreviation: str, full_path: str):
        """
        添加路径缩写
        
        Args:
            abbreviation: 缩写
            full_path: 完整路径
        """
        self.path_abbreviations[abbreviation] = full_path
        self.logger.info(f"添加路径缩写: {abbreviation} -> {full_path}")
    
    def learn_from_history(self, command_history: List[str]):
        """
        从命令历史中学习
        
        Args:
            command_history: 命令历史列表
        """
        # 分析常用命令模式
        command_patterns: Dict[str, Dict[str, int]] = {}
        
        for cmd in command_history:
            parts = cmd.split()
            if len(parts) < 1:
                continue
            
            command_name = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            if command_name not in command_patterns:
                command_patterns[command_name] = {}
            
            # 统计参数使用频率
            for arg in args:
                command_patterns[command_name][arg] = command_patterns[command_name].get(arg, 0) + 1
        
        # 更新默认参数
        for cmd, arg_counts in command_patterns.items():
            if arg_counts:
                # 获取最常用的参数
                common_args = sorted(arg_counts.items(), key=lambda x: x[1], reverse=True)
                top_args = [arg for arg, count in common_args[:3] if count > 1]  # 至少出现2次
                
                if top_args:
                    self.add_default_arguments(cmd, top_args)
    
    def get_normalization_stats(self) -> Dict[str, int]:
        """获取规范化统计"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "total_normalizations": 0,
            "alias_expansions": 0,
            "path_expansions": 0,
            "env_var_expansions": 0,
            "argument_additions": 0
        }
        self.logger.info("规范化统计已重置")
    
    def get_aliases(self) -> Dict[str, str]:
        """获取所有别名"""
        return self.command_aliases.copy()
    
    def get_default_arguments(self) -> Dict[str, List[str]]:
        """获取所有默认参数"""
        return self.default_arguments.copy()


# 单例实例
_global_command_normalizer: Optional[CommandNormalizer] = None

def get_command_normalizer() -> CommandNormalizer:
    """获取全局命令规范化器实例"""
    global _global_command_normalizer
    
    if _global_command_normalizer is None:
        _global_command_normalizer = CommandNormalizer()
    
    return _global_command_normalizer