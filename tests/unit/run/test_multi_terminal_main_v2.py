"""
multi_terminal_main_v2.py 单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from run.multi_terminal_main_v2 import (
    MiyaTerminalAI,
    MiyaMultiTerminalShell,
    AIProcessingResult,
    AICommandInfo,
)
from core.ai_client import AIMessage


class TestAIProcessingResult:
    """测试AI处理结果数据类"""

    def test_initialization(self):
        """测试初始化"""
        result = AIProcessingResult(
            success=True, type="conversation", message="测试消息", needs_command=False
        )

        assert result.success == True
        assert result.type == "conversation"
        assert result.message == "测试消息"
        assert result.needs_command == False
        assert result.commands == []

    def test_with_commands(self):
        """测试带命令的结果"""
        commands = [
            AICommandInfo(session_id="test-1", command="ls"),
            AICommandInfo(session_id="test-2", command="pwd"),
        ]

        result = AIProcessingResult(
            success=True,
            type="command_execution",
            message="执行命令",
            needs_command=True,
            commands=commands,
        )

        assert len(result.commands) == 2
        assert result.commands[0].command == "ls"
        assert result.commands[1].session_id == "test-2"


class TestMiyaTerminalAI:
    """测试MiyaTerminalAI类"""

    @pytest.fixture
    def ai_instance(self):
        """创建测试实例"""
        instance = MiyaTerminalAI()
        instance.ai_enabled = False  # 禁用AI用于测试
        return instance

    def test_initialization(self, ai_instance):
        """测试初始化"""
        assert ai_instance.prompt_manager is not None
        assert ai_instance.conversation_history == []
        assert ai_instance.terminal_context == {}
        assert ai_instance.ai_client is None
        assert ai_instance.ai_enabled == False

    def test_is_greeting(self, ai_instance):
        """测试问候语检测"""
        # 中文问候语
        assert ai_instance.is_greeting("你好") == True
        assert ai_instance.is_greeting("在吗") == True
        assert ai_instance.is_greeting("嗨") == True
        assert ai_instance.is_greeting("早上好") == True

        # 英文问候语
        assert ai_instance.is_greeting("hello") == True
        assert ai_instance.is_greeting("hi") == True
        assert ai_instance.is_greeting("good morning") == True

        # 非问候语
        assert ai_instance.is_greeting("") == False
        assert ai_instance.is_greeting("test") == False
        assert ai_instance.is_greeting("执行命令") == False
        assert ai_instance.is_greeting("123") == False

    def test_get_greeting(self, ai_instance):
        """测试获取问候语"""
        greeting = ai_instance.get_greeting()

        assert isinstance(greeting, str)
        assert len(greeting) > 0
        # 确保问候语包含中文（因为是中文项目）
        assert any("\u4e00" <= char <= "\u9fff" for char in greeting)

    def test_get_help_response(self, ai_instance):
        """测试帮助响应"""
        help_text = ai_instance.get_help_response()

        assert isinstance(help_text, str)
        assert len(help_text) > 100  # 帮助文本应该比较长
        # 确保包含关键信息
        assert "弥娅多终端管理系统" in help_text
        assert "核心功能" in help_text
        assert "常用命令" in help_text

    def test_get_system_prompt(self, ai_instance):
        """测试获取系统提示词"""
        prompt = ai_instance.get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_prompt_info(self, ai_instance):
        """测试获取提示词信息"""
        info = ai_instance.get_prompt_info()

        assert isinstance(info, dict)
        assert "system_prompt" in info
        assert "user_template" in info
        assert "memory_enabled" in info
        assert "memory_max_count" in info

        # 检查数据类型
        assert isinstance(info["system_prompt"], str)
        assert isinstance(info["user_template"], str)
        assert isinstance(info["memory_enabled"], bool)
        assert isinstance(info["memory_max_count"], int)

    @pytest.mark.asyncio
    async def test_process_with_ai_disabled(self, ai_instance):
        """测试AI禁用时的处理"""
        result = await ai_instance.process_with_ai("测试输入")

        assert isinstance(result, AIProcessingResult)
        assert result.success == False
        assert result.type == "conversation"
        assert "AI未配置" in result.message
        assert result.needs_command == False
        assert result.commands == []

    @pytest.mark.asyncio
    async def test_process_with_ai_enabled_success(self, ai_instance):
        """测试AI启用时的成功处理"""
        ai_instance.ai_enabled = True
        ai_instance.ai_client = MagicMock()
        ai_instance.ai_client.chat = AsyncMock(return_value="这是一个测试AI响应")

        # 模拟_analyze_ai_response方法
        expected_result = AIProcessingResult(
            success=True,
            type="conversation",
            message="分析后的响应",
            needs_command=False,
            commands=[],
        )

        with patch.object(
            ai_instance, "_analyze_ai_response", return_value=expected_result
        ) as mock_analyze:
            result = await ai_instance.process_with_ai("测试输入")

            # 验证结果
            assert result == expected_result
            # 验证方法调用
            assert ai_instance.ai_client.chat.called
            assert mock_analyze.called

    @pytest.mark.asyncio
    async def test_process_with_ai_enabled_error(self, ai_instance):
        """测试AI启用时的错误处理"""
        ai_instance.ai_enabled = True
        ai_instance.ai_client = MagicMock()
        ai_instance.ai_client.chat = AsyncMock(side_effect=Exception("AI服务错误"))

        result = await ai_instance.process_with_ai("测试输入")

        assert isinstance(result, AIProcessingResult)
        assert result.success == False
        assert result.type == "error"
        assert "AI处理失败" in result.message
        assert result.needs_command == False
        assert result.commands == []

    def test_analyze_ai_response_conversation(self, ai_instance):
        """测试AI响应分析 - 对话类型"""
        response = "你好，我是弥娅，很高兴为你服务。"
        result = ai_instance._analyze_ai_response(response, None)

        assert isinstance(result, AIProcessingResult)
        assert result.success == True
        assert result.type == "conversation"
        assert result.message == response
        assert result.needs_command == False
        assert result.commands == []

    def test_analyze_ai_response_command_execution(self, ai_instance):
        """测试AI响应分析 - 命令执行类型"""
        test_cases = [
            "请执行 ls 命令查看目录内容",
            "运行 pwd 查看当前路径",
            "执行命令: git status",
            "帮我运行一下 npm install",
            "RUN: python script.py",
        ]

        for response in test_cases:
            result = ai_instance._analyze_ai_response(response, None)

            assert isinstance(result, AIProcessingResult)
            assert result.success == True
            assert result.type == "command_execution"
            assert result.needs_command == True
            # 确保响应包含命令信息
            assert len(result.commands) > 0

    def test_extract_commands_from_response(self, ai_instance):
        """测试从响应中提取命令"""
        test_responses = [
            # 工具调用格式应该被转换
            ('create_file "test.txt" "hello"', ['echo hello > "test.txt"']),
            ("python_interpreter 'script.py'", ['python "script.py"']),
            # 代码块命令
            ("```\npython script.py\n```", ["python script.py"]),
            # Linux命令应该被转换
            ("touch file.txt", ["type nul > file.txt"]),
            ("ls", ["dir"]),
            # 明确的命令
            ("执行: notepad", ["notepad"]),
            ("命令: python test.py", ["python test.py"]),
        ]

        for response, expected_commands in test_responses:
            commands = ai_instance._extract_commands_from_response(response)

            assert isinstance(commands, list), f"Expected list, got {type(commands)}"
            # 检查是否提取到了命令
            found = any(
                any(exp in cmd for exp in expected_commands) for cmd in commands
            )
            assert found, f"未找到命令: {expected_commands}, 实际: {commands}"

    def test_convert_linux_to_windows(self, ai_instance):
        """测试Linux到Windows命令转换"""
        test_cases = [
            ("touch file.txt", "type nul > file.txt"),
            ("rm file.txt", "del file.txt"),
            ("ls", "dir"),
            ("ls -la", "dir -la"),
            ("cat file.txt", "type file.txt"),
            ("mkdir test", "mkdir test"),
            ("python script.py", "python script.py"),  # 不变
            ("notepad", "notepad"),  # 不变
        ]

        for linux_cmd, expected_windows in test_cases:
            result = ai_instance._convert_linux_to_windows(linux_cmd)
            assert result == expected_windows, (
                f"Expected {expected_windows}, got {result}"
            )

    def test_build_ai_messages(self, ai_instance):
        """测试构建AI消息"""
        user_input = "帮我查看当前目录"
        terminal_context = {
            "terminals": [{"id": "test", "name": "test"}],
            "system": "Linux",
            "current_dir": "/home/test",
        }

        messages = ai_instance._build_ai_messages(user_input, terminal_context)

        assert isinstance(messages, list)
        assert len(messages) >= 2  # 至少包含系统消息和用户消息

        # 检查消息结构
        for msg in messages:
            assert hasattr(msg, "role")
            assert hasattr(msg, "content")
            assert msg.role in ["system", "user", "assistant"]


class TestMiyaMultiTerminalShell:
    """测试MiyaMultiTerminalShell类"""

    @pytest.fixture
    def shell_instance(self):
        """创建测试实例"""
        # 模拟orchestrator和terminal_manager
        mock_terminal_manager = MagicMock()
        mock_terminal_manager.active_session_id = None
        mock_terminal_manager.get_all_status = MagicMock(return_value=[])

        mock_orchestrator = MagicMock()
        mock_orchestrator.terminal_manager = mock_terminal_manager

        # 模拟AI实例
        mock_ai = MagicMock()
        mock_ai.ai_enabled = True
        mock_ai.get_prompt_info = MagicMock(
            return_value={"memory_enabled": True, "memory_max_count": 10}
        )

        # 创建Shell实例并注入模拟对象
        shell = MiyaMultiTerminalShell()
        shell.orchestrator = mock_orchestrator
        shell.ai = mock_ai

        return shell

    def test_initialization(self):
        """测试初始化"""
        shell = MiyaMultiTerminalShell()

        assert hasattr(shell, "orchestrator")
        assert hasattr(shell, "ai")
        assert shell.running == True

    @pytest.mark.asyncio
    async def test_get_prompt_input_no_active_terminal(self, shell_instance):
        """测试获取提示输入 - 无活动终端"""
        shell_instance.orchestrator.terminal_manager.active_session_id = None

        # 模拟输入
        test_input = "测试输入"
        with patch("run.multi_terminal_main_v2.chinese_input", return_value=test_input):
            result = await shell_instance._get_prompt_input()

            assert result == test_input

    @pytest.mark.asyncio
    async def test_get_prompt_input_with_active_terminal(self, shell_instance):
        """测试获取提示输入 - 有活动终端"""
        shell_instance.orchestrator.terminal_manager.active_session_id = "test-session"
        shell_instance.orchestrator.terminal_manager.get_session_status = MagicMock(
            return_value={"name": "测试终端", "is_active": True}
        )

        test_input = "测试命令"
        with patch("run.multi_terminal_main_v2.chinese_input", return_value=test_input):
            result = await shell_instance._get_prompt_input()

            assert result == test_input

    @pytest.mark.asyncio
    async def test_execute_direct_command(self, shell_instance):
        """测试直接执行命令"""
        shell_instance.orchestrator.terminal_manager.active_session_id = "test-session"

        # 模拟命令执行结果
        mock_result = MagicMock()
        mock_result.output = "命令输出"
        mock_result.error = ""
        mock_result.exit_code = 0

        shell_instance.orchestrator.terminal_manager.execute_command = AsyncMock(
            return_value=mock_result
        )

        command = "ls -la"
        await shell_instance._execute_direct_command(command)

        # 验证命令被正确执行
        shell_instance.orchestrator.terminal_manager.execute_command.assert_called_once_with(
            "test-session", command
        )

    @pytest.mark.asyncio
    async def test_execute_ai_commands(self, shell_instance):
        """测试执行AI命令"""
        commands = [
            AICommandInfo(session_id="session-1", command="ls"),
            AICommandInfo(session_id="session-2", command="pwd"),
        ]

        # 模拟命令执行
        mock_result = MagicMock()
        mock_result.output = "命令输出"

        shell_instance.orchestrator.terminal_manager.execute_command = AsyncMock(
            return_value=mock_result
        )

        await shell_instance._execute_ai_commands(commands)

        # 验证每个命令都被执行
        assert (
            shell_instance.orchestrator.terminal_manager.execute_command.call_count == 2
        )

    @pytest.mark.asyncio
    async def test_handle_system_command_exit(self, shell_instance):
        """测试处理系统命令 - 退出"""
        # 模拟输入返回 "exit"
        with patch("run.multi_terminal_main_v2.chinese_input", return_value="exit"):
            shell_instance.running = True
            await shell_instance._handle_system_command("exit")

            assert shell_instance.running == False

    @pytest.mark.asyncio
    async def test_handle_system_command_help(self, shell_instance):
        """测试处理系统命令 - 帮助"""
        result = await shell_instance._handle_system_command("help")

        # 帮助命令应该返回True表示已处理
        assert result == True

    @pytest.mark.asyncio
    async def test_run_shell_exit(self, shell_instance):
        """测试运行Shell - 退出"""
        # 模拟用户输入"exit"
        with patch.object(
            shell_instance, "_get_prompt_input", AsyncMock(side_effect=["exit"])
        ):
            with patch.object(shell_instance, "_process_input", AsyncMock()):
                shell_instance.running = True
                await shell_instance.run()

                assert shell_instance.running == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
