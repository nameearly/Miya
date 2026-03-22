"""
错误处理模块测试
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.error_handler import (
    ErrorCode,
    AppError,
    AIError,
    TerminalError,
    ConfigError,
    error_handler,
    retry_with_backoff,
    validate_input,
    ValidationError,
    PerformanceMonitor
)


class TestErrorClasses:
    """测试错误类"""
    
    def test_app_error_initialization(self):
        """测试AppError初始化"""
        error = AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI服务不可用",
            details={"reason": "timeout"},
            original_error=Exception("连接超时")
        )
        
        assert error.code == ErrorCode.AI_SERVICE_UNAVAILABLE
        assert error.message == "AI服务不可用"
        assert error.details == {"reason": "timeout"}
        assert str(error.original_error) == "连接超时"
        assert str(error) == "[AI_001] AI服务不可用"
    
    def test_app_error_to_dict(self):
        """测试AppError转换为字典"""
        error = AppError(
            code=ErrorCode.AI_INVALID_RESPONSE,
            message="无效的AI响应",
            details={"response": "empty"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error"] == "AI_003"
        assert error_dict["message"] == "无效的AI响应"
        assert error_dict["details"] == {"response": "empty"}
        assert error_dict["type"] == "AppError"
    
    def test_ai_error(self):
        """测试AIError"""
        error = AIError(
            code=ErrorCode.AI_RATE_LIMIT,
            message="API调用频率限制",
            details={"limit": 100, "reset_in": 60}
        )
        
        assert isinstance(error, AppError)
        assert error.code == ErrorCode.AI_RATE_LIMIT
        assert error.message == "API调用频率限制"
    
    def test_terminal_error(self):
        """测试TerminalError"""
        error = TerminalError(
            code=ErrorCode.TERMINAL_NOT_FOUND,
            message="终端不存在"
        )
        
        assert isinstance(error, AppError)
        assert error.code == ErrorCode.TERMINAL_NOT_FOUND
        assert error.message == "终端不存在"


class TestErrorHandlerDecorator:
    """测试错误处理装饰器"""
    
    @pytest.mark.asyncio
    async def test_error_handler_success_async(self):
        """测试异步函数成功情况"""
        @error_handler
        async def async_func():
            return "success"
        
        result = await async_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_error_handler_app_error_async(self):
        """测试异步函数抛出AppError"""
        @error_handler
        async def async_func():
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="测试错误"
            )
        
        with pytest.raises(AppError) as exc_info:
            await async_func()
        
        assert exc_info.value.code == ErrorCode.AI_SERVICE_UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_error_handler_unexpected_error_async(self):
        """测试异步函数抛出未预期错误"""
        @error_handler
        async def async_func():
            raise ValueError("意外的错误")
        
        with pytest.raises(AppError) as exc_info:
            await async_func()
        
        assert exc_info.value.code == ErrorCode.AI_INVALID_RESPONSE
        assert "内部服务器错误" in exc_info.value.message
    
    def test_error_handler_success_sync(self):
        """测试同步函数成功情况"""
        @error_handler
        def sync_func():
            return "success"
        
        result = sync_func()
        assert result == "success"
    
    def test_error_handler_app_error_sync(self):
        """测试同步函数抛出AppError"""
        @error_handler
        def sync_func():
            raise AppError(
                code=ErrorCode.TERMINAL_NOT_FOUND,
                message="终端不存在"
            )
        
        with pytest.raises(AppError) as exc_info:
            sync_func()
        
        assert exc_info.value.code == ErrorCode.TERMINAL_NOT_FOUND


class TestRetryDecorator:
    """测试重试装饰器"""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_try(self):
        """测试第一次就成功"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        async def async_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await async_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failure(self):
        """测试失败后重试成功"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("连接失败")
            return "success"
        
        result = await async_func()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0
        
        @retry_with_backoff(max_retries=2)
        async def async_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("连接失败")
        
        with pytest.raises(ConnectionError):
            await async_func()
        
        assert call_count == 3  # 初始调用 + 2次重试
    
    @pytest.mark.asyncio
    async def test_retry_with_app_error(self):
        """测试AppError不重试"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        async def async_func():
            nonlocal call_count
            call_count += 1
            raise AppError(
                code=ErrorCode.AI_INVALID_RESPONSE,
                message="不重试的错误"
            )
        
        with pytest.raises(AppError):
            await async_func()
        
        assert call_count == 1  # AppError不重试


class TestValidationDecorator:
    """测试验证装饰器"""
    
    def test_validation_success(self):
        """测试验证成功"""
        @validate_input
        def func(value: int):
            if not isinstance(value, int):
                raise ValidationError("必须是整数")
            return value * 2
        
        result = func(5)
        assert result == 10
    
    def test_validation_failure(self):
        """测试验证失败"""
        @validate_input
        def func(value: int):
            if not isinstance(value, int):
                raise ValidationError("必须是整数")
            return value * 2
        
        with pytest.raises(ValidationError) as exc_info:
            func("not a number")
        
        assert "必须是整数" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validation_async_success(self):
        """测试异步函数验证成功"""
        @validate_input
        async def async_func(value: str):
            if not isinstance(value, str):
                raise ValidationError("必须是字符串")
            return value.upper()
        
        result = await async_func("test")
        assert result == "TEST"
    
    def test_validation_error_details(self):
        """测试验证错误详情"""
        @validate_input
        def func(data: dict):
            if "name" not in data:
                raise ValidationError(
                    "缺少必要字段",
                    details={"required_fields": ["name"]}
                )
            return data["name"]
        
        with pytest.raises(ValidationError) as exc_info:
            func({})
        
        assert exc_info.value.details == {"required_fields": ["name"]}


class TestPerformanceMonitor:
    """测试性能监控器"""
    
    def setup_method(self):
        """测试设置"""
        self.monitor = PerformanceMonitor(window_size=10)
    
    def test_record_success(self):
        """测试记录成功"""
        self.monitor.record("test_func", 0.1, success=True)
        
        assert "test_func" in self.monitor.metrics
        metric = self.monitor.metrics["test_func"]
        assert metric.call_count == 1
        assert metric.success_count == 1
        assert metric.error_count == 0
        assert len(metric.durations) == 1
        assert metric.durations[0] == 0.1
    
    def test_record_error(self):
        """测试记录错误"""
        self.monitor.record("error_func", 0.2, success=False)
        
        metric = self.monitor.metrics["error_func"]
        assert metric.call_count == 1
        assert metric.success_count == 0
        assert metric.error_count == 1
    
    def test_get_stats(self):
        """测试获取统计信息"""
        # 记录多次调用
        self.monitor.record("test_func", 0.1, True)
        self.monitor.record("test_func", 0.2, True)
        self.monitor.record("test_func", 0.3, False)
        
        stats = self.monitor.get_stats("test_func")
        
        assert stats is not None
        assert stats["function"] == "test_func"
        assert stats["calls"] == 3
        assert stats["success_rate"] == 2/3
        assert 0.1 <= stats["average_time"] <= 0.3
        assert stats["error_count"] == 1
    
    def test_get_stats_nonexistent(self):
        """测试获取不存在的函数统计"""
        stats = self.monitor.get_stats("nonexistent")
        assert stats is None
    
    def test_get_slow_functions(self):
        """测试获取慢函数"""
        self.monitor.record("fast_func", 0.1, True)
        self.monitor.record("slow_func", 0.6, True)  # 超过0.5阈值
        
        slow_funcs = self.monitor.get_slow_functions(threshold=0.5)
        
        assert len(slow_funcs) == 1
        assert slow_funcs[0]["function"] == "slow_func"
        assert slow_funcs[0]["average_time"] == 0.6
    
    def test_reset(self):
        """测试重置"""
        self.monitor.record("test_func", 0.1, True)
        assert len(self.monitor.metrics) == 1
        
        self.monitor.reset()
        assert len(self.monitor.metrics) == 0


class TestLogExecutionTimeDecorator:
    """测试执行时间日志装饰器"""
    
    @pytest.mark.asyncio
    async def test_log_execution_time_success_async(self, caplog):
        """测试异步函数执行时间记录"""
        caplog.set_level(logging.INFO)
        
        from core.error_handler import log_execution_time
        
        @log_execution_time
        async def async_func():
            await asyncio.sleep(0.01)
            return "done"
        
        result = await async_func()
        
        assert result == "done"
        # 检查日志记录
        assert any("async_func" in record.message for record in caplog.records)
    
    def test_log_execution_time_success_sync(self, caplog):
        """测试同步函数执行时间记录"""
        caplog.set_level(logging.INFO)
        
        from core.error_handler import log_execution_time
        
        @log_execution_time
        def sync_func():
            return "done"
        
        result = sync_func()
        
        assert result == "done"
        assert any("sync_func" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_log_execution_time_warning(self, caplog):
        """测试执行时间过长警告"""
        caplog.set_level(logging.WARNING)
        
        from core.error_handler import log_execution_time
        
        @log_execution_time
        async def slow_func():
            await asyncio.sleep(0.1)  # 这个应该不会触发警告（默认5秒阈值）
            return "done"
        
        result = await slow_func()
        
        assert result == "done"
        # 0.1秒不应该触发警告
        assert not any("执行时间过长" in record.message for record in caplog.records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])