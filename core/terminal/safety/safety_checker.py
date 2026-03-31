"""
统一的安全检查器

整合intelligent_executor.py中的SafetyChecker和
ai_terminal_system.py中的安全检查逻辑
"""

import re
import os
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..base.types import SafetyReport, RiskLevel, CommandAnalysis
from ..base.interfaces import ISafetyChecker

logger = logging.getLogger(__name__)

# 定义一个简单的执行上下文类
@dataclass
class SafetyContext:
    """安全检查上下文"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    working_directory: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)

class SafetyChecker(ISafetyChecker):
    """统一的安全检查器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # 危险命令模式 (从intelligent_executor.py整合)
        self.dangerous_patterns = [
            # 高危险模式
            (r"rm\s+-rf\s+/", RiskLevel.CATASTROPHIC, "危险: 强制删除根目录"),
            (r"dd\s+if=/dev/", RiskLevel.EXTREME, "危险: 磁盘操作"),
            (r">\s+/dev/sda", RiskLevel.EXTREME, "危险: 磁盘写入"),
            (r":\(\)\{:\|:\&\};\:", RiskLevel.CATASTROPHIC, "危险: fork炸弹"),
            
            # 中等危险模式
            (r"chmod\s+777\s+/", RiskLevel.VERY_DANGEROUS, "危险: 全局权限设置"),
            (r"mv\s+/\s+", RiskLevel.DANGEROUS, "危险: 移动根目录"),
            (r"sudo\s+.*\s+&&\s+.*", RiskLevel.HIGH, "警告: 链式sudo命令"),
            
            # 从ai_terminal_system.py整合的危险命令
            (r"format\s+", RiskLevel.EXTREME, "危险: 格式化操作"),
            (r"shutdown\s+", RiskLevel.HIGH, "危险: 关机命令"),
            (r"reboot\s+", RiskLevel.HIGH, "危险: 重启命令"),
            (r"mkfs\s+", RiskLevel.EXTREME, "危险: 创建文件系统")
        ]
        
        # 警告模式
        self.warning_patterns = [
            (r"rm\s+.*\.(py|js|java|cpp|ts|go|rs)$", RiskLevel.MEDIUM, "警告: 删除源代码文件"),
            (r"kill\s+-9\s+\d+", RiskLevel.HIGH, "警告: 强制终止进程"),
            (r"chmod\s+.*\s+\.ssh/", RiskLevel.VERY_HIGH, "警告: 修改SSH目录权限"),
            (r"del\s+/f\s+.*\.(exe|dll|sys)$", RiskLevel.MEDIUM, "警告: 删除系统文件"),
            (r"chmod\s+000\s+", RiskLevel.HIGH, "警告: 设置文件不可访问")
        ]
        
        # 自定义规则
        self.custom_rules = []
        
        logger.info("安全检查器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "enable_dangerous_check": True,
            "enable_warning_check": True,
            "check_working_directory": True,
            "require_confrimination_for_high_risk": True,
            "high_risk_threshold": RiskLevel.HIGH.value,
            "block_extreme_risk": True,
            "log_all_checks": False
        }
    
    def check(self, command: str, analysis: Optional[CommandAnalysis] = None, context: Optional[dict] = None) -> SafetyReport:
        """
        同步检查命令安全性（便捷方法）
        
        Args:
            command: 命令字符串
            analysis: 可选的命令分析结果
            context: 可选的上下文信息
            
        Returns:
            安全检查报告
        """
        import asyncio
        
        # 创建安全上下文
        safety_context = None
        if context:
            safety_context = SafetyContext(**context)
        
        # 运行异步检查
        return asyncio.run(self.check_command(command, safety_context))
    
    async def check_command(self, command: str, context: Optional[SafetyContext] = None) -> SafetyReport:
        """检查命令安全性"""
        logger.debug(f"安全检查: {command}")
        
        # 收集所有警告和风险评估
        warnings = []
        max_risk_level = RiskLevel.VERY_LOW
        requires_confirmation = False
        blocked = False
        rationale = []
        
        # 1. 检查危险模式
        if self.config["enable_dangerous_check"]:
            for pattern, risk_level, message in self.dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    warnings.append(message)
                    if risk_level.value > max_risk_level.value:
                        max_risk_level = risk_level
                    
                    rationale.append(f"匹配危险模式: {pattern}")
                    
                    # 极高风险命令被阻止
                    if self.config["block_extreme_risk"] and risk_level.value >= RiskLevel.EXTREME.value:
                        blocked = True
                        rationale.append(f"极高风险命令被阻止 (等级: {risk_level.name})")
        
        # 2. 检查警告模式
        if self.config["enable_warning_check"]:
            for pattern, risk_level, message in self.warning_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    warnings.append(message)
                    if risk_level.value > max_risk_level.value:
                        max_risk_level = risk_level
                    
                    rationale.append(f"匹配警告模式: {pattern}")
        
        # 3. 检查工作目录 (从intelligent_executor.py整合)
        if self.config["check_working_directory"]:
            cwd = context.working_directory
            
            # 在根目录执行删除操作
            if cwd == "/" and any(cmd in command.lower() for cmd in ["rm ", "del ", "删除"]):
                warning_msg = "警告: 当前在根目录执行删除操作"
                warnings.append(warning_msg)
                max_risk_level = max(max_risk_level, RiskLevel.HIGH)
                rationale.append("在根目录执行删除操作风险较高")
            
            # 检查目录权限
            if not context.writable and ">" in command:
                warning_msg = "警告: 当前目录不可写，但命令包含输出重定向"
                warnings.append(warning_msg)
                max_risk_level = max(max_risk_level, RiskLevel.MEDIUM)
                rationale.append("不可写目录中的输出重定向可能失败")
        
        # 4. 检查自定义规则
        for rule_func in self.custom_rules:
            try:
                rule_result = rule_func(command, context)
                if rule_result:
                    warnings.extend(rule_result.get("warnings", []))
                    risk = rule_result.get("risk_level", RiskLevel.VERY_LOW)
                    if risk.value > max_risk_level.value:
                        max_risk_level = risk
                    
                    if rule_result.get("requires_confirmation", False):
                        requires_confirmation = True
                    
                    if rule_result.get("blocked", False):
                        blocked = True
            except Exception as e:
                logger.error(f"自定义规则检查失败: {e}")
        
        # 5. 确定是否需要确认
        if self.config["require_confirmation_for_high_risk"]:
            if max_risk_level.value >= self.config["high_risk_threshold"]:
                requires_confirmation = True
                rationale.append(f"高风险命令需要确认 (风险等级: {max_risk_level.name})")
        
        # 6. 生成建议的替代命令
        suggested_alternative = None
        if blocked or requires_confirmation:
            suggested_alternative = self._suggest_alternative(command, max_risk_level)
            if suggested_alternative:
                rationale.append(f"建议替代命令: {suggested_alternative}")
        
        # 7. 记录检查结果
        if self.config["log_all_checks"] or max_risk_level.value >= RiskLevel.MEDIUM.value:
            log_msg = f"安全检查结果: {command} -> 风险: {max_risk_level.name}"
            if warnings:
                log_msg += f", 警告: {len(warnings)}个"
            logger.info(log_msg)
        
        return SafetyReport(
            safe=max_risk_level.value < RiskLevel.HIGH.value and not blocked,
            risk_level=max_risk_level,
            requires_confirmation=requires_confirmation,
            warnings=warnings,
            blocked=blocked,
            rationale="; ".join(rationale) if rationale else None,
            suggested_alternative=suggested_alternative
        )
    
    def _suggest_alternative(self, command: str, risk_level: RiskLevel) -> Optional[str]:
        """建议替代命令"""
        command_lower = command.lower()
        
        # rm -rf 替代建议
        if "rm -rf" in command_lower and risk_level.value >= RiskLevel.DANGEROUS.value:
            # 建议使用交互式删除
            parts = command.split()
            if len(parts) > 2:
                target = " ".join(parts[2:])
                return f"rm -ri {target}  # 交互式删除，需要确认每个文件"
        
        # chmod 777 替代建议
        if "chmod 777" in command_lower:
            # 建议更严格的权限
            parts = command.split()
            if len(parts) > 2:
                target = parts[2]
                return f"chmod 755 {target}  # 更安全的权限设置"
        
        # 删除源代码文件警告
        if any(ext in command_lower for ext in [".py", ".js", ".java"]) and "rm " in command_lower:
            return f"# 考虑使用git rm或移动到回收站而不是直接删除"
        
        return None
    
    def add_dangerous_pattern(self, pattern: str, risk_level: RiskLevel, description: str):
        """添加危险模式"""
        self.dangerous_patterns.append((pattern, risk_level, description))
        logger.info(f"添加危险模式: {pattern} (风险: {risk_level.name})")
    
    def get_dangerous_patterns(self) -> List[Dict[str, Any]]:
        """获取所有危险模式"""
        return [
            {
                "pattern": pattern,
                "risk_level": risk_level.name,
                "description": description,
                "value": risk_level.value
            }
            for pattern, risk_level, description in self.dangerous_patterns
        ]
    
    def should_confirm(self, report: SafetyReport) -> bool:
        """判断是否需要用户确认"""
        if report.blocked:
            return False  # 被阻止的命令不需要确认
        
        if report.requires_confirmation:
            return True
        
        # 额外的确认逻辑
        if report.risk_level.value >= RiskLevel.HIGH.value:
            return True
        
        # 如果有多个警告，也建议确认
        if len(report.warnings) >= 3:
            return True
        
        return False
    
    def add_custom_rule(self, rule_func):
        """添加自定义规则函数"""
        self.custom_rules.append(rule_func)
        logger.info(f"添加自定义规则: {rule_func.__name__}")
    
    def enable_feature(self, feature: str, enabled: bool = True):
        """启用或禁用特定功能"""
        if feature in self.config:
            old_value = self.config[feature]
            self.config[feature] = enabled
            logger.info(f"{feature}: {old_value} -> {enabled}")
        else:
            logger.warning(f"未知配置项: {feature}")
    
    def get_configuration(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()


# 使用示例
async def example_usage():
    """使用示例"""
    checker = SafetyChecker()
    
    # 创建测试上下文
    context = ExecutionContext(
        working_directory="/home/user",
        user="user",
        home_directory="/home/user",
        system_platform="linux",
        python_version="3.9.0",
        environment_vars={},
        sudo_required=False,
        writable=True,
        terminal_type="local"
    )
    
    # 测试命令
    test_commands = [
        "rm -rf /tmp/test",      # 危险命令
        "ls -la",                # 安全命令
        "chmod 777 /etc/passwd", # 危险命令
        "echo hello",            # 安全命令
    ]
    
    for cmd in test_commands:
        print(f"\n检查命令: {cmd}")
        report = await checker.check_command(cmd, context)
        
        print(f"  安全: {report.safe}")
        print(f"  风险等级: {report.risk_level.name}")
        print(f"  需要确认: {report.requires_confirmation}")
        print(f"  被阻止: {report.blocked}")
        
        if report.warnings:
            print(f"  警告:")
            for warning in report.warnings:
                print(f"    • {warning}")
        
        if report.suggested_alternative:
            print(f"  建议替代: {report.suggested_alternative}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())