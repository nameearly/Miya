#!/usr/bin/env python3
"""
意图分析器

分析命令的意图和分类
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..base.types import (
    CommandIntent, CommandCategory, CommandComplexity,
    RiskLevel, CommandAnalysis
)

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """意图分析器"""
    
    def __init__(self):
        # 命令模式到意图的映射
        self.intent_patterns = {
            CommandIntent.EXECUTE: [
                r'^ls\b', r'^cd\b', r'^cat\b', r'^grep\b', r'^find\b',
                r'^cp\b', r'^mv\b', r'^rm\b', r'^mkdir\b', r'^touch\b',
                r'^python\b', r'^node\b', r'^npm\b', r'^pip\b',
                r'^git\b', r'^docker\b', r'^kubectl\b'
            ],
            CommandIntent.QUERY: [
                r'^pwd\b', r'^whoami\b', r'^uname\b', r'^df\b', r'^du\b',
                r'^ps\b', r'^top\b', r'^htop\b', r'^free\b',
                r'^ifconfig\b', r'^ip\b', r'^netstat\b', r'^ss\b',
                r'^date\b', r'^cal\b', r'^uptime\b'
            ],
            CommandIntent.CONFIGURE: [
                r'^export\b', r'^alias\b', r'^source\b',
                r'^vim\b', r'^nano\b', r'^edit\b',
                r'^chmod\b', r'^chown\b', r'^ln\b'
            ],
            CommandIntent.AUTOMATE: [
                r'^cron\b', r'^at\b', r'^batch\b',
                r'^screen\b', r'^tmux\b', r'^nohup\b'
            ],
            CommandIntent.DEBUG: [
                r'^debug\b', r'^strace\b', r'^ltrace\b',
                r'^gdb\b', r'^valgrind\b', r'^perf\b'
            ],
            CommandIntent.INSTALL: [
                r'^apt-get\b', r'^apt\b', r'^yum\b', r'^dnf\b',
                r'^pacman\b', r'^brew\b', r'^snap\b',
                r'^install\b', r'^update\b', r'^upgrade\b'
            ],
            CommandIntent.MANAGE: [
                r'^service\b', r'^systemctl\b',
                r'^journalctl\b', r'^log\b',
                r'^useradd\b', r'^usermod\b', r'^groupadd\b'
            ],
            CommandIntent.HELP: [
                r'^help\b', r'^\?$', r'^man\b', r'^info\b',
                r'^--help\b', r'^-h\b', r'^whatis\b'
            ]
        }
        
        # 命令到分类的映射
        self.category_patterns = {
            CommandCategory.FILE_SYSTEM: [
                r'^ls\b', r'^cd\b', r'^pwd\b', r'^cat\b', r'^more\b',
                r'^less\b', r'^head\b', r'^tail\b', r'^cp\b', r'^mv\b',
                r'^rm\b', r'^mkdir\b', r'^rmdir\b', r'^touch\b',
                r'^ln\b', r'^find\b', r'^locate\b', r'^whereis\b',
                r'^chmod\b', r'^chown\b', r'^stat\b', r'^file\b'
            ],
            CommandCategory.PROCESS_MANAGEMENT: [
                r'^ps\b', r'^top\b', r'^htop\b', r'^kill\b', r'^pkill\b',
                r'^killall\b', r'^nice\b', r'^renice\b', r'^bg\b', r'^fg\b',
                r'^jobs\b', r'^nohup\b', r'^timeout\b', r'^watch\b'
            ],
            CommandCategory.NETWORK: [
                r'^ping\b', r'^traceroute\b', r'^tracepath\b',
                r'^ifconfig\b', r'^ip\b', r'^netstat\b', r'^ss\b',
                r'^dig\b', r'^nslookup\b', r'^host\b', r'^whois\b',
                r'^curl\b', r'^wget\b', r'^scp\b', r'^rsync\b',
                r'^ssh\b', r'^telnet\b', r'^nc\b', r'^netcat\b'
            ],
            CommandCategory.SYSTEM_INFO: [
                r'^uname\b', r'^hostname\b', r'^domainname\b',
                r'^dmesg\b', r'^uptime\b', r'^who\b', r'^w\b',
                r'^last\b', r'^date\b', r'^cal\b', r'^free\b',
                r'^df\b', r'^du\b', r'^vmstat\b', r'^iostat\b'
            ],
            CommandCategory.DEVELOPMENT: [
                r'^git\b', r'^svn\b', r'^hg\b',
                r'^make\b', r'^cmake\b', r'^gcc\b', r'^g\+\+\b',
                r'^clang\b', r'^javac\b', r'^python\b', r'^node\b',
                r'^npm\b', r'^yarn\b', r'^pip\b', r'^conda\b'
            ],
            CommandCategory.SECURITY: [
                r'^passwd\b', r'^su\b', r'^sudo\b',
                r'^visudo\b', r'^adduser\b', r'^deluser\b',
                r'^addgroup\b', r'^delgroup\b', r'^chage\b',
                r'^openssl\b', r'^gpg\b'
            ]
        }
        
        # 危险命令模式
        self.dangerous_patterns = [
            (r'rm\s+-rf\s+/', CommandComplexity.DANGEROUS, RiskLevel.CRITICAL),
            (r'dd\s+if=/dev/', CommandComplexity.DANGEROUS, RiskLevel.CRITICAL),
            (r':\(\)\{.*:;\s*\}&', CommandComplexity.DANGEROUS, RiskLevel.CRITICAL),
            (r'chmod\s+[0-7]{3,4}\s+/', CommandComplexity.COMPLEX, RiskLevel.HIGH),
            (r'chown\s+-R\s+root:root\s+/', CommandComplexity.COMPLEX, RiskLevel.HIGH),
            (r'mv\s+/\s+', CommandComplexity.DANGEROUS, RiskLevel.HIGH),
        ]
        
        # 复杂度评估规则
        self.complexity_rules = [
            (r'\|\s*', 1),  # 管道增加复杂度
            (r'&\s*$', 2),  # 后台执行增加复杂度
            (r'>\s*\w+', 1),  # 输出重定向增加复杂度
            (r'\$\w+', 1),  # 变量使用增加复杂度
            (r'`.*`', 2),  # 命令替换增加复杂度
            (r'\$\(.*\)', 2),  # 命令替换增加复杂度
        ]
        
        logger.info("意图分析器初始化完成")
    
    def analyze_intent(self, command: str) -> CommandIntent:
        """
        分析命令意图
        
        Args:
            command: 命令字符串
            
        Returns:
            命令意图
        """
        # 清理命令
        clean_command = command.strip()
        
        # 检查每个意图的模式
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.match(pattern, clean_command, re.IGNORECASE):
                    logger.debug(f"命令 '{command}' 匹配意图: {intent}")
                    return intent
        
        # 默认返回执行意图
        return CommandIntent.EXECUTE
    
    def analyze_category(self, command: str) -> CommandCategory:
        """
        分析命令分类
        
        Args:
            command: 命令字符串
            
        Returns:
            命令分类
        """
        clean_command = command.strip().split()[0] if command.strip() else ""
        
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.match(pattern, clean_command, re.IGNORECASE):
                    logger.debug(f"命令 '{command}' 匹配分类: {category}")
                    return category
        
        # 默认返回工具分类
        return CommandCategory.UTILITY
    
    def analyze_complexity(self, command: str) -> CommandComplexity:
        """
        分析命令复杂度
        
        Args:
            command: 命令字符串
            
        Returns:
            命令复杂度
        """
        # 检查危险命令
        for pattern, complexity, _ in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                logger.debug(f"命令 '{command}' 识别为危险命令: {complexity}")
                return complexity
        
        # 计算复杂度分数
        complexity_score = 0
        
        for pattern, score in self.complexity_rules:
            matches = re.findall(pattern, command)
            complexity_score += len(matches) * score
        
        # 基于分数确定复杂度
        if complexity_score >= 5:
            return CommandComplexity.COMPLEX
        elif complexity_score >= 2:
            return CommandComplexity.COMPLEX
        else:
            return CommandComplexity.SIMPLE
    
    def analyze_risk(self, command: str) -> RiskLevel:
        """
        分析命令风险
        
        Args:
            command: 命令字符串
            
        Returns:
            风险等级
        """
        # 检查危险模式
        for pattern, _, risk_level in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                logger.debug(f"命令 '{command}' 识别为高风险: {risk_level}")
                return risk_level
        
        # 检查系统级命令
        system_commands = [
            r'^shutdown\b', r'^reboot\b', r'^halt\b', r'^poweroff\b',
            r'^init\b', r'^telinit\b', r'^systemctl\s+(stop|restart|reload)'
        ]
        
        for pattern in system_commands:
            if re.search(pattern, command, re.IGNORECASE):
                logger.debug(f"命令 '{command}' 识别为系统命令: {RiskLevel.HIGH}")
                return RiskLevel.HIGH
        
        # 检查权限修改命令
        privilege_commands = [
            r'^sudo\b', r'^su\b', r'^chmod\s+[0-7]{3,4}', r'^chown\s+',
            r'^visudo\b', r'^adduser\b', r'^deluser\b'
        ]
        
        for pattern in privilege_commands:
            if re.search(pattern, command, re.IGNORECASE):
                logger.debug(f"命令 '{command}' 识别为权限命令: {RiskLevel.MEDIUM}")
                return RiskLevel.MEDIUM
        
        # 默认低风险
        return RiskLevel.LOW
    
    def extract_parameters(self, command: str) -> Dict[str, Any]:
        """
        提取命令参数
        
        Args:
            command: 命令字符串
            
        Returns:
            参数字典
        """
        params = {
            'raw_command': command,
            'command_parts': [],
            'flags': [],
            'arguments': [],
            'options': {}
        }
        
        try:
            # 使用shlex解析命令
            import shlex
            parts = shlex.split(command)
            
            if parts:
                params['command_parts'] = parts
                
                # 提取命令名
                params['command_name'] = parts[0]
                
                # 分析参数
                for i, part in enumerate(parts[1:], 1):
                    if part.startswith('-'):
                        # 可能是标志或选项
                        if '=' in part:
                            # 选项键值对
                            key, value = part.split('=', 1)
                            params['options'][key] = value
                        elif len(part) > 1 and part[1] != '-':
                            # 短标志
                            for flag in part[1:]:
                                params['flags'].append(f'-{flag}')
                        else:
                            # 长标志
                            params['flags'].append(part)
                    else:
                        # 普通参数
                        params['arguments'].append(part)
        
        except Exception as e:
            logger.warning(f"解析命令参数失败: {e}")
        
        return params
    
    def analyze(self, command: str) -> Dict[str, Any]:
        """
        完整分析命令
        
        Args:
            command: 命令字符串
            
        Returns:
            分析结果字典
        """
        if not command or not command.strip():
            return {
                'intent': CommandIntent.UNKNOWN,
                'category': CommandCategory.UTILITY,
                'complexity': CommandComplexity.SIMPLE,
                'risk_level': RiskLevel.LOW,
                'parameters': {},
                'safe_to_execute': True,
                'confirmation_needed': False
            }
        
        intent = self.analyze_intent(command)
        category = self.analyze_category(command)
        complexity = self.analyze_complexity(command)
        risk_level = self.analyze_risk(command)
        parameters = self.extract_parameters(command)
        
        # 确定是否需要确认
        confirmation_needed = (
            risk_level.value >= RiskLevel.HIGH.value or
            complexity == CommandComplexity.DANGEROUS
        )
        
        # 确定是否安全可执行
        safe_to_execute = not (
            risk_level.value >= RiskLevel.CRITICAL.value or
            complexity == CommandComplexity.DANGEROUS
        )
        
        # 生成建议命令（如果有）
        suggested_commands = []
        if not safe_to_execute:
            # 为危险命令生成安全建议
            if 'rm -rf' in command:
                suggested_commands.append(command.replace('rm -rf', 'rm -r'))
                suggested_commands.append(f'echo "危险命令: {command}"')
        
        return {
            'raw_command': command,
            'normalized_command': command.strip(),
            'intent': intent,
            'category': category,
            'complexity': complexity,
            'risk_level': risk_level,
            'parameters': parameters,
            'safe_to_execute': safe_to_execute,
            'confirmation_needed': confirmation_needed,
            'suggested_commands': suggested_commands
        }
    
    def create_analysis_from_dict(self, data: Dict[str, Any]) -> CommandAnalysis:
        """
        从字典创建CommandAnalysis对象
        
        Args:
            data: 分析数据字典
            
        Returns:
            CommandAnalysis对象
        """
        return CommandAnalysis(
            raw_command=data.get('raw_command', ''),
            normalized_command=data.get('normalized_command', ''),
            intent=data.get('intent', CommandIntent.UNKNOWN),
            category=data.get('category', CommandCategory.UTILITY),
            complexity=data.get('complexity', CommandComplexity.SIMPLE),
            parameters=data.get('parameters', {}),
            safe_to_execute=data.get('safe_to_execute', True),
            confirmation_needed=data.get('confirmation_needed', False),
            suggested_commands=data.get('suggested_commands', []),
            risk_level=data.get('risk_level', RiskLevel.LOW)
        )


# 单例实例
_global_intent_analyzer: Optional[IntentAnalyzer] = None

def get_intent_analyzer() -> IntentAnalyzer:
    """获取全局意图分析器实例"""
    global _global_intent_analyzer
    
    if _global_intent_analyzer is None:
        _global_intent_analyzer = IntentAnalyzer()
    
    return _global_intent_analyzer