"""
统一的命令解析器

整合ai_terminal_system.py的CommandAnalyzer和
intelligent_executor.py的CommandParser功能
"""

import re
import shlex
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import os

from ..base.types import (
    CommandAnalysis, CommandIntent, CommandCategory,
    CommandComplexity, RiskLevel
)
from ..base.interfaces import ICommandParser
from .intent_analyzer import IntentAnalyzer
from .command_normalizer import CommandNormalizer

logger = logging.getLogger(__name__)

class CommandParser(ICommandParser):
    """统一的命令解析器"""
    
    def __init__(self, use_learning: bool = True):
        self.intent_analyzer = IntentAnalyzer()
        self.normalizer = CommandNormalizer()
        self.use_learning = use_learning
        
        # 缓存解析结果
        self._cache = {}
        self._cache_size = 100
        
        # 命令复杂度评估规则
        self.complexity_rules = [
            # 管道和重定向
            (r'[|><&]', 3, "包含管道或重定向"),
            
            # 脚本执行
            (r'\b(bash|sh|python|perl|ruby|node)\b', 2, "脚本执行"),
            
            # 危险命令
            (r'\b(rm\s+-rf|chmod\s+777|dd\s+if=)\b', 5, "危险命令"),
            
            # 系统命令
            (r'\b(sudo|chmod|chown|systemctl|service)\b', 2, "系统级命令"),
            
            # 网络命令
            (r'\b(curl|wget|ssh|scp)\b', 2, "网络操作"),
            
            # 复杂参数
            (r'--\w+', 1, "复杂参数"),
            (r'-\w{2,}', 1, "多字母标志")
        ]
        
        logger.info("命令解析器初始化完成")
    
    async def parse(self, user_input: str) -> CommandAnalysis:
        """解析用户输入为命令分析结果"""
        # 检查缓存
        cache_key = user_input.strip().lower()
        if cache_key in self._cache:
            logger.debug(f"使用缓存解析结果: {cache_key}")
            return self._cache[cache_key]
        
        # 规范化命令
        normalized = self.normalizer.normalize(user_input)
        
        # 分析意图
        intent = await self.intent_analyzer.detect_intent(user_input, normalized)
        
        # 分类命令
        category = self.categorize(normalized)
        
        # 评估复杂度
        complexity = self._assess_complexity(normalized)
        
        # 提取参数
        parameters = self.extract_parameters(normalized)
        
        # 评估风险（初始评估，详细检查在安全模块）
        risk_level = self._initial_risk_assessment(normalized, intent, complexity)
        
        # 检查安全性（基础检查）
        safe_to_execute, confirmation_needed = self._basic_safety_check(normalized, risk_level)
        
        # 生成建议命令
        suggested_commands = self._generate_suggestions(normalized, intent, category)
        
        # 创建分析结果
        analysis = CommandAnalysis(
            raw_command=user_input,
            normalized_command=normalized,
            intent=intent,
            category=category,
            complexity=complexity,
            parameters=parameters,
            safe_to_execute=safe_to_execute,
            confirmation_needed=confirmation_needed,
            suggested_commands=suggested_commands,
            risk_level=risk_level
        )
        
        # 缓存结果
        self._cache[cache_key] = analysis
        if len(self._cache) > self._cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        logger.debug(f"命令解析完成: {normalized} -> {intent.value}")
        return analysis
    
    def categorize(self, command: str) -> CommandCategory:
        """分类命令"""
        command_lower = command.lower()
        
        # 文件系统操作
        file_patterns = [
            r'^\s*(ls|cd|cp|mv|rm|mkdir|touch|cat|head|tail|find|grep)\b',
            r'文件|目录|文件夹|复制|移动|删除|创建|查看'
        ]
        
        # 进程管理
        process_patterns = [
            r'^\s*(ps|kill|top|htop|pkill|pgrep)\b',
            r'进程|程序|运行|停止|终止|监控'
        ]
        
        # 网络操作
        network_patterns = [
            r'^\s*(ping|curl|wget|ssh|scp|netstat|ifconfig|ipconfig)\b',
            r'网络|连接|下载|上传|访问|测试'
        ]
        
        # 系统信息
        system_patterns = [
            r'^\s*(uname|df|free|whoami|pwd|hostname|uptime)\b',
            r'系统|信息|状态|磁盘|内存|CPU|用户'
        ]
        
        # 开发工具
        dev_patterns = [
            r'^\s*(git|python|pip|npm|node|docker|kubectl)\b',
            r'代码|版本|提交|安装|包|容器'
        ]
        
        # 自动化任务
        automation_patterns = [
            r'任务|计划|自动化|备份|部署|清理|监控|定时'
        ]
        
        # 安全检查
        if any(re.search(pattern, command_lower) for pattern in file_patterns):
            return CommandCategory.FILE_SYSTEM
        
        if any(re.search(pattern, command_lower) for pattern in process_patterns):
            return CommandCategory.PROCESS_MANAGEMENT
        
        if any(re.search(pattern, command_lower) for pattern in network_patterns):
            return CommandCategory.NETWORK
        
        if any(re.search(pattern, command_lower) for pattern in system_patterns):
            return CommandCategory.SYSTEM_INFO
        
        if any(re.search(pattern, command_lower) for pattern in dev_patterns):
            return CommandCategory.DEVELOPMENT
        
        if any(re.search(pattern, command_lower) for pattern in automation_patterns):
            return CommandCategory.AUTOMATION
        
        # 安全检查特定命令
        security_cmds = ['chmod', 'chown', 'passwd', 'su', 'sudo']
        if any(cmd in command_lower for cmd in security_cmds):
            return CommandCategory.SECURITY
        
        return CommandCategory.CUSTOM
    
    def extract_parameters(self, command: str) -> Dict[str, Any]:
        """提取命令参数"""
        params = {
            "raw": command,
            "command": "",
            "args": [],
            "flags": [],
            "arguments": [],
            "has_redirection": False,
            "has_pipe": False
        }
        
        try:
            # 尝试使用shlex进行正确的分词（处理引号等）
            parts = shlex.split(command)
        except:
            # 如果shlex失败，使用简单空格分割
            parts = command.split()
        
        if parts:
            params["command"] = parts[0]
            
            if len(parts) > 1:
                args = parts[1:]
                params["args"] = args
                
                # 分离标志和参数
                flags = []
                arguments = []
                
                for arg in args:
                    if arg.startswith('-'):
                        flags.append(arg)
                    else:
                        arguments.append(arg)
                
                params["flags"] = flags
                params["arguments"] = arguments
            
            # 检查重定向和管道
            if any(char in command for char in ['>', '<', '>>']):
                params["has_redirection"] = True
            
            if '|' in command:
                params["has_pipe"] = True
        
        return params
    
    def normalize_command(self, command: str) -> str:
        """规范化命令"""
        return self.normalizer.normalize(command)
    
    def _assess_complexity(self, command: str) -> CommandComplexity:
        """评估复杂度"""
        score = 0
        
        for pattern, weight, _ in self.complexity_rules:
            if re.search(pattern, command, re.IGNORECASE):
                score += weight
        
        # 根据分数确定复杂度
        if score >= 5:
            return CommandComplexity.DANGEROUS
        elif score >= 3:
            return CommandComplexity.COMPLEX
        elif score >= 2:
            return CommandComplexity.SYSTEM
        else:
            return CommandComplexity.SIMPLE
    
    def _initial_risk_assessment(self, command: str, intent: CommandIntent, 
                                complexity: CommandComplexity) -> RiskLevel:
        """初始风险评估"""
        risk_score = 1  # 初始分数
        
        # 根据意图调整风险
        if intent in [CommandIntent.INSTALL, CommandIntent.MANAGE]:
            risk_score += 1
        
        # 根据复杂度调整风险
        if complexity == CommandComplexity.DANGEROUS:
            risk_score += 3
        elif complexity == CommandComplexity.COMPLEX:
            risk_score += 1
        
        # 危险命令模式
        dangerous_patterns = [
            (r'rm\s+-rf\s+/', 5),
            (r'dd\s+if=/dev/', 4),
            (r'chmod\s+777\s+/', 4),
            (r':\(\)\{:\|:\&\};', 5),  # fork炸弹
            (r'mv\s+/\s+', 3),
            (r'>\s+/dev/sda', 4)
        ]
        
        for pattern, weight in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                risk_score += weight
        
        # 转换为RiskLevel枚举
        if risk_score >= 9:
            return RiskLevel.CATASTROPHIC
        elif risk_score >= 8:
            return RiskLevel.EXTREME
        elif risk_score >= 7:
            return RiskLevel.VERY_DANGEROUS
        elif risk_score >= 6:
            return RiskLevel.DANGEROUS
        elif risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.VERY_LOW
    
    def _basic_safety_check(self, command: str, risk_level: RiskLevel) -> Tuple[bool, bool]:
        """基础安全检查"""
        # 高风险命令需要确认
        if risk_level.value >= RiskLevel.CRITICAL.value:
            return False, True
        
        # 中等风险命令可能需要确认
        if risk_level.value >= RiskLevel.HIGH.value:
            return True, True
        
        return True, False
    
    def _generate_suggestions(self, command: str, intent: CommandIntent, 
                             category: CommandCategory) -> List[str]:
        """生成建议命令"""
        suggestions = []
        
        # 根据意图和类别提供建议
        if intent == CommandIntent.QUERY:
            if category == CommandCategory.FILE_SYSTEM:
                suggestions = ["ls -la", "find . -type f", "du -sh *"]
            elif category == CommandCategory.SYSTEM_INFO:
                suggestions = ["uname -a", "df -h", "free -h", "top"]
            elif category == CommandCategory.NETWORK:
                suggestions = ["ifconfig", "netstat -tulpn", "ping localhost"]
        
        elif intent == CommandIntent.FILE_OPS:
            suggestions = ["cp -r", "mv -i", "rm -i", "mkdir -p"]
        
        elif intent == CommandIntent.AUTOMATE:
            suggestions = [
                "创建一个备份任务",
                "自动化清理临时文件",
                "计划定时任务"
            ]
        
        # 添加通用建议
        generic_suggestions = [
            "使用 --help 查看命令帮助",
            "使用 man <命令> 查看手册页",
            "使用 apropos <关键词> 搜索相关命令"
        ]
        
        # 合并并限制数量
        all_suggestions = suggestions + generic_suggestions
        return all_suggestions[:5]
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("命令解析缓存已清空")