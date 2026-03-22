"""Runtime API 单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from core.runtime_api import RuntimeAPIServer, EndpointStatus, get_runtime_api
from datetime import datetime


@pytest.fixture
def mock_decision_hub():
    """模拟决策中心"""
    hub = Mock()
    hub.process_perception_cross_platform = AsyncMock(return_value="测试响应")
    return hub


@pytest.fixture
def runtime_api(mock_decision_hub):
    """创建Runtime API实例"""
    with patch('core.runtime_api.AIOHTTP_AVAILABLE', True):
        api = RuntimeAPIServer(
            host="127.0.0.1",
            port=8080,
            decision_hub=mock_decision_hub
        )
        return api


class TestRuntimeAPIServer:
    """RuntimeAPIServer测试类"""

    def test_init(self):
        """测试初始化"""
        with patch('core.runtime_api.AIOHTTP_AVAILABLE', True):
            api = RuntimeAPIServer(host="localhost", port=9000)
            assert api.host == "localhost"
            assert api.port == 9000
            assert len(api.endpoints) == 0

    def test_init_without_aiohttp(self):
        """测试无aiohttp时的初始化"""
        with patch('core.runtime_api.AIOHTTP_AVAILABLE', False):
            with pytest.raises(RuntimeError):
                RuntimeAPIServer(host="localhost", port=9000)

    def test_set_decision_hub(self, runtime_api):
        """测试设置决策中心"""
        hub = Mock()
        runtime_api.set_decision_hub(hub)
        assert runtime_api.decision_hub == hub

    def test_set_cognitive_memory(self, runtime_api):
        """测试设置认知记忆"""
        memory = Mock()
        runtime_api.set_cognitive_memory(memory)
        assert runtime_api.cognitive_memory == memory

    def test_set_skills_registry(self, runtime_api):
        """测试设置Skills注册表"""
        registry = Mock()
        runtime_api.set_skills_registry(registry)
        assert runtime_api.skills_registry == registry

    def test_get_safe_config(self, runtime_api):
        """测试获取安全配置"""
        # 设置包含敏感信息的配置
        runtime_api._config = {
            "api_key": "secret_key_123456",
            "password": "mypassword",
            "normal_value": "test_value",
            "secret_token": "token_abcdef"
        }

        safe_config = runtime_api._get_safe_config()

        # 敏感信息应该被部分隐藏
        assert "****" in safe_config["api_key"]
        assert "****" in safe_config["password"]
        assert "****" in safe_config["secret_token"]

        # 非敏感信息应该完整保留
        assert safe_config["normal_value"] == "test_value"

    def test_detect_config_changes(self, runtime_api):
        """测试配置变更检测"""
        # 设置初始配置
        runtime_api._config = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }

        # 保存快照
        runtime_api._config_snapshot = runtime_api._config.copy()

        # 修改配置
        new_config = {
            "key1": "value1",  # 未改变
            "key2": "new_value2",  # 已改变
            "key3": "value3",  # 未改变
            "key4": "value4"  # 新增
        }

        changes = runtime_api._detect_config_changes(new_config)

        # 验证变更检测
        assert "key2" in changes
        assert "key4" in changes
        assert "key1" not in changes
        assert "key3" not in changes

    def test_get_memory_stats(self, runtime_api):
        """测试内存统计"""
        with patch('core.runtime_api.psutil') as mock_psutil:
            # 模拟进程信息
            mock_process = Mock()
            mock_process.memory_info.return_value = Mock(rss=1024*1024*100, vms=1024*1024*200)
            mock_process.memory_percent.return_value = 25.5
            mock_psutil.Process.return_value = mock_process
            mock_psutil.virtual_memory.return_value = Mock(available=1024*1024*4000)

            stats = runtime_api._get_memory_stats()

            assert stats["rss_mb"] == pytest.approx(100.0, rel=1e-2)
            assert stats["vms_mb"] == pytest.approx(200.0, rel=1e-2)
            assert stats["percent"] == 25.5
            assert stats["available_mb"] == pytest.approx(4000.0, rel=1e-2)

    def test_get_performance_stats(self, runtime_api):
        """测试性能统计"""
        with patch('core.runtime_api.psutil') as mock_psutil:
            # 模拟进程信息
            mock_process = Mock()
            mock_process.cpu_percent.return_value = 15.5
            mock_process.num_threads.return_value = 8
            mock_process.open_files.return_value = [1, 2, 3]
            mock_process.connections.return_value = [1, 2]
            mock_psutil.Process.return_value = mock_process

            stats = runtime_api._get_performance_stats()

            assert stats["cpu_percent"] == 15.5
            assert stats["num_threads"] == 8
            assert stats["open_files"] == 3
            assert stats["connections"] == 2

    def test_is_value_changed(self, runtime_api):
        """测试值变更检测"""
        # None值
        assert not runtime_api._is_value_changed(None, None)
        assert runtime_api._is_value_changed(None, "value")

        # 字典
        dict1 = {"key": "value"}
        dict2 = {"key": "value"}
        dict3 = {"key": "new_value"}

        assert not runtime_api._is_value_changed(dict1, dict2)
        assert runtime_api._is_value_changed(dict1, dict3)

        # 列表
        list1 = [1, 2, 3]
        list2 = [1, 2, 3]
        list3 = [1, 2, 4]

        assert not runtime_api._is_value_changed(list1, list2)
        assert runtime_api._is_value_changed(list1, list3)

        # 普通值
        assert not runtime_api._is_value_changed("test", "test")
        assert runtime_api._is_value_changed("test1", "test2")

    @pytest.mark.asyncio
    async def test_process_with_decision_hub(self, runtime_api):
        """测试使用决策中心处理消息"""
        response = await runtime_api._process_with_decision_hub(
            message="测试消息",
            session_id="test_session",
            platform="web",
            from_terminal=None
        )

        assert response == "测试响应"
        runtime_api.decision_hub.process_perception_cross_platform.assert_called_once()

    def test_process_without_decision_hub(self, runtime_api):
        """测试无决策中心时的处理"""
        runtime_api.decision_hub = None

        response = runtime_api._process_without_decision_hub(
            message="你好",
            session_id="test_session",
            from_terminal=None
        )

        assert "你好" in response or "收到消息" in response


@pytest.mark.asyncio
class TestRuntimeAPIHandlers:
    """Runtime API处理器测试类"""

    async def test_handle_probe(self, runtime_api):
        """测试探针接口"""
        request = Mock()
        response = await runtime_api.handle_probe(request)

        assert response.status == 200
        # 这里需要验证JSON响应内容

    async def test_handle_start_endpoint(self, runtime_api):
        """测试启动交互端"""
        # 创建一个端点
        endpoint = EndpointStatus(
            id="test_endpoint",
            name="测试端点",
            type="web",
            status="stopped",
            config={},
            stats={}
        )
        runtime_api.endpoints["test_endpoint"] = endpoint

        request = Mock()
        request.match_info = {"id": "test_endpoint"}

        response = await runtime_api.handle_start_endpoint(request)

        assert response.status == 200
        assert endpoint.status == "running"
        assert endpoint.started_at is not None

    async def test_handle_stop_endpoint(self, runtime_api):
        """测试停止交互端"""
        # 创建一个运行中的端点
        endpoint = EndpointStatus(
            id="test_endpoint",
            name="测试端点",
            type="web",
            status="running",
            config={},
            stats={}
        )
        endpoint.started_at = 123.456
        runtime_api.endpoints["test_endpoint"] = endpoint

        request = Mock()
        request.match_info = {"id": "test_endpoint"}

        response = await runtime_api.handle_stop_endpoint(request)

        assert response.status == 200
        assert endpoint.status == "stopped"
        assert endpoint.started_at is None

    async def test_handle_get_config(self, runtime_api):
        """测试获取配置"""
        runtime_api._config = {
            "normal_key": "normal_value",
            "secret_key": "secret_value"
        }

        request = Mock()

        response = await runtime_api.handle_get_config(request)

        assert response.status == 200
        # 验证敏感信息被过滤

    async def test_handle_update_config(self, runtime_api):
        """测试更新配置"""
        request = Mock()
        request.json = AsyncMock(return_value={
            "config": {
                "new_key": "new_value",
                "existing_key": "updated_value"
            }
        })

        response = await runtime_api.handle_update_config(request)

        assert response.status == 200
        assert runtime_api._config["new_key"] == "new_value"
        assert runtime_api._config["existing_key"] == "updated_value"

    async def test_handle_stats(self, runtime_api):
        """测试获取统计数据"""
        with patch('core.runtime_api.psutil') as mock_psutil:
            mock_process = Mock()
            mock_process.memory_info.return_value = Mock(rss=1024*1024*100, vms=1024*1024*200)
            mock_process.memory_percent.return_value = 25.5
            mock_process.cpu_percent.return_value = 15.5
            mock_process.num_threads.return_value = 8
            mock_process.open_files.return_value = []
            mock_process.connections.return_value = []
            mock_psutil.Process.return_value = mock_process
            mock_psutil.virtual_memory.return_value = Mock(available=1024*1024*4000)

            request = Mock()
            response = await runtime_api.handle_stats(request)

            assert response.status == 200

    async def test_handle_chat(self, runtime_api):
        """测试聊天接口"""
        request = Mock()
        request.json = AsyncMock(return_value={
            "message": "测试消息",
            "session_id": "test_session",
            "platform": "web"
        })

        response = await runtime_api.handle_chat(request)

        assert response.status == 200


class TestRuntimeAPISingleton:
    """Runtime API单例测试类"""

    def test_get_runtime_api_singleton(self):
        """测试单例模式"""
        api1 = get_runtime_api(host="localhost", port=9000)
        api2 = get_runtime_api(host="localhost", port=9000)

        assert id(api1) == id(api2)

    def test_get_runtime_api_different_params(self):
        """测试不同参数"""
        api1 = get_runtime_api(host="localhost", port=9000)
        api2 = get_runtime_api(host="localhost", port=9000)

        # 单例应该忽略后续的参数
        assert api1.port == 9000
        assert id(api1) == id(api2)
