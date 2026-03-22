"""IoT管理器 - 弥娅统一物联网控制系统

整合webnet/iot.py并扩展能力：
- 设备注册和发现
- 设备状态监控
- 远程控制
- 自动化规则引擎
- 协议扩展（MQTT/CoAP）
- 事件驱动的自动化
"""

import asyncio
import json
import logging
import platform
import time
from datetime import datetime, timedelta, time as dt_time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """设备状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


class DeviceType(Enum):
    """设备类型枚举"""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"
    GATEWAY = "gateway"
    HUB = "hub"


@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str
    device_type: str
    name: str = ""
    description: str = ""
    manufacturer: str = ""
    model: str = ""
    firmware_version: str = ""
    capabilities: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)


@dataclass
class DeviceState:
    """设备状态"""
    device_id: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_seen: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    max_history: int = 100

    def update(self, attributes: Dict[str, Any]):
        """更新属性"""
        timestamp = time.time()

        # 记录历史
        if len(self.history) >= self.max_history:
            self.history.pop(0)

        self.history.append({
            "timestamp": timestamp,
            "changes": attributes.copy(),
            "previous_status": self.status.value
        })

        # 更新当前状态
        self.attributes.update(attributes)
        self.last_seen = timestamp


@dataclass
class AutomationRule:
    """自动化规则"""
    rule_id: str
    name: str
    description: str = ""
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    trigger_count: int = 0
    last_triggered: Optional[float] = None


@dataclass
class AutomationEvent:
    """自动化事件"""
    event_id: str
    event_type: str
    device_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class IoTManager:
    """IoT管理器 - 统一物联网控制"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # 设备管理
        self.devices: Dict[str, DeviceInfo] = {}  # device_id -> DeviceInfo
        self.device_states: Dict[str, DeviceState] = {}  # device_id -> DeviceState
        self.device_groups: Dict[str, Set[str]] = {}  # group_name -> set of device_ids

        # 自动化规则
        self.automation_rules: Dict[str, AutomationRule] = {}  # rule_id -> AutomationRule
        self.event_handlers: Dict[str, List[Callable]] = {}  # event_type -> handlers

        # 协议适配器（未来扩展）
        self.protocol_adapters: Dict[str, Any] = {}

        # 心跳检测
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30)
        self.device_timeout = self.config.get("device_timeout", 120)
        self._heartbeat_task: Optional[asyncio.Task] = None

        # 锁
        self._lock = asyncio.Lock()

    # ==================== 设备管理 ====================

    async def register_device(
        self,
        device_id: str,
        device_type: str,
        name: str = "",
        **kwargs
    ) -> bool:
        """注册设备"""
        async with self._lock:
            if device_id in self.devices:
                logger.warning(f"[IoT] 设备已存在: {device_id}")
                return False

            # 创建设备信息
            info = DeviceInfo(
                device_id=device_id,
                device_type=device_type,
                name=name,
                **kwargs
            )

            # 创建设备状态
            state = DeviceState(device_id=device_id, status=DeviceStatus.ONLINE)

            self.devices[device_id] = info
            self.device_states[device_id] = state

            logger.info(f"[IoT] 设备注册成功: {device_id} ({device_type})")
            return True

    async def unregister_device(self, device_id: str) -> bool:
        """注销设备"""
        async with self._lock:
            if device_id not in self.devices:
                return False

            del self.devices[device_id]
            del self.device_states[device_id]

            # 从组中移除
            for group_name in list(self.device_groups.keys()):
                if device_id in self.device_groups[group_name]:
                    self.device_groups[group_name].remove(device_id)

            logger.info(f"[IoT] 设备注销成功: {device_id}")
            return True

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """获取设备信息"""
        info = self.devices.get(device_id)
        state = self.device_states.get(device_id)

        if not info or not state:
            return None

        return {
            "device_id": info.device_id,
            "device_type": info.device_type,
            "name": info.name,
            "description": info.description,
            "manufacturer": info.manufacturer,
            "model": info.model,
            "firmware_version": info.firmware_version,
            "capabilities": info.capabilities,
            "status": state.status.value,
            "last_seen": state.last_seen,
            "attributes": state.attributes,
            "registered_at": info.registered_at
        }

    def get_all_devices(self, device_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有设备"""
        devices = []

        for device_id, info in self.devices.items():
            if device_type is None or info.device_type == device_type:
                devices.append(self.get_device(device_id))

        return devices

    async def update_device_status(
        self,
        device_id: str,
        status: DeviceStatus,
        attributes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新设备状态"""
        state = self.device_states.get(device_id)
        if not state:
            return False

        state.status = status

        if attributes:
            state.update(attributes)

        logger.debug(f"[IoT] 设备状态更新: {device_id} -> {status.value}")
        return True

    async def control_device(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """控制设备"""
        state = self.device_states.get(device_id)
        if not state:
            logger.warning(f"[IoT] 设备不存在: {device_id}")
            return False

        # 更新设备状态
        state.status = DeviceStatus.BUSY
        if parameters:
            state.update(parameters)

        logger.info(f"[IoT] 控制设备: {device_id} -> {command}")

        # 通过协议适配器发送控制命令
        success = await self._send_command_to_device(device_id, command, parameters)

        # 恢复设备状态
        state.status = DeviceStatus.IDLE if success else DeviceStatus.ERROR

        return success

    # ==================== 设备分组 ====================

    async def create_group(self, group_name: str, device_ids: List[str]) -> bool:
        """创建设备分组"""
        async with self._lock:
            # 验证设备存在
            for device_id in device_ids:
                if device_id not in self.devices:
                    logger.warning(f"[IoT] 设备不存在，无法添加到组: {device_id}")
                    return False

            self.device_groups[group_name] = set(device_ids)
            logger.info(f"[IoT] 创建设备组: {group_name} ({len(device_ids)} 设备)")
            return True

    def get_group_devices(self, group_name: str) -> List[str]:
        """获取组内设备列表"""
        return list(self.device_groups.get(group_name, set()))

    async def control_group(
        self,
        group_name: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """控制组内所有设备"""
        device_ids = self.get_group_devices(group_name)

        results = {}
        tasks = [
            self.control_device(device_id, command, parameters)
            for device_id in device_ids
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for device_id, result in zip(device_ids, results_list):
            results[device_id] = isinstance(result, bool) and result

        logger.info(f"[IoT] 组控制完成: {group_name} -> {command}")
        return results

    # ==================== 自动化规则 ====================

    async def add_automation_rule(
        self,
        rule_id: str,
        name: str,
        triggers: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        **kwargs
    ) -> bool:
        """添加自动化规则"""
        async with self._lock:
            if rule_id in self.automation_rules:
                logger.warning(f"[IoT] 自动化规则已存在: {rule_id}")
                return False

            rule = AutomationRule(
                rule_id=rule_id,
                name=name,
                triggers=triggers,
                actions=actions,
                **kwargs
            )

            self.automation_rules[rule_id] = rule
            logger.info(f"[IoT] 添加自动化规则: {rule_id}")
            return True

    async def trigger_automation(
        self,
        event: AutomationEvent
    ) -> List[Dict[str, Any]]:
        """触发自动化规则"""
        triggered_actions = []

        for rule in self.automation_rules.values():
            if not rule.enabled:
                continue

            # 检查触发条件
            if await self._match_triggers(rule.triggers, event):
                # 检查前置条件
                if await self._check_conditions(rule.conditions, event):
                    # 执行动作
                    for action in rule.actions:
                        result = await self._execute_action(action)
                        triggered_actions.append({
                            "rule_id": rule.rule_id,
                            "action": action,
                            "result": result
                        })

                    # 更新统计
                    rule.trigger_count += 1
                    rule.last_triggered = time.time()

                    logger.info(f"[IoT] 自动化规则触发: {rule.rule_id}")

        return triggered_actions

    async def _match_triggers(
        self,
        triggers: List[Dict[str, Any]],
        event: AutomationEvent
    ) -> bool:
        """匹配触发条件"""
        for trigger in triggers:
            # 简化实现：类型匹配
            if trigger.get("event_type") == event.event_type:
                # 检查设备ID
                if "device_id" in trigger:
                    if trigger["device_id"] != event.device_id:
                        continue

                # 检查数据匹配
                if "data" in trigger:
                    for key, value in trigger["data"].items():
                        if event.data.get(key) != value:
                            continue

                return True

        return False

    async def _check_conditions(
        self,
        conditions: List[Dict[str, Any]],
        event: AutomationEvent
    ) -> bool:
        """检查前置条件"""
        # 简化实现：所有条件必须满足
        for condition in conditions:
            # 设备状态条件
            if condition.get("type") == "device_status":
                device_id = condition["device_id"]
                expected_status = condition["status"]
                state = self.device_states.get(device_id)

                if not state or state.status.value != expected_status:
                    return False

            # 时间条件
            elif condition.get("type") == "time":
                # 检查时间条件
                if not self._check_time_condition(condition):
                    return False

        return True

    async def _execute_action(self, action: Dict[str, Any]) -> bool:
        """执行动作"""
        action_type = action.get("type")

        if action_type == "control_device":
            return await self.control_device(
                action["device_id"],
                action["command"],
                action.get("parameters")
            )

        elif action_type == "control_group":
            return await self.control_group(
                action["group_name"],
                action["command"],
                action.get("parameters")
            )

        elif action_type == "notify":
            # 实现通知功能
            return await self._send_notification(action.get('message'), action)

        else:
            logger.warning(f"[IoT] 未知动作类型: {action_type}")
            return False

    # ==================== 事件处理 ====================

    async def emit_event(self, event: AutomationEvent):
        """发送事件"""
        # 触发自动化规则
        await self.trigger_automation(event)

        # 调用事件处理器
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"[IoT] 事件处理器执行失败: {e}")

    def on_event(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.debug(f"[IoT] 注册事件处理器: {event_type}")

    # ==================== 心跳检测 ====================

    async def start_heartbeat_monitor(self):
        """启动心跳检测"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("[IoT] 心跳检测已启动")

    async def stop_heartbeat_monitor(self):
        """停止心跳检测"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

            self._heartbeat_task = None
            logger.info("[IoT] 心跳检测已停止")

    async def _heartbeat_loop(self):
        """心跳检测循环"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._check_devices_timeout()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[IoT] 心跳检测错误: {e}")

    async def _check_devices_timeout(self):
        """检查设备超时"""
        current_time = time.time()

        for device_id, state in self.device_states.items():
            if state.status == DeviceStatus.OFFLINE:
                continue

            time_since_last_seen = current_time - state.last_seen

            if time_since_last_seen > self.device_timeout:
                logger.warning(f"[IoT] 设备超时: {device_id} (离线 {time_since_last_seen:.1f}秒)")
                await self.update_device_status(device_id, DeviceStatus.OFFLINE)

    # ==================== 统计信息 ====================

    async def _send_command_to_device(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """通过协议适配器发送控制命令到设备"""
        device = self.devices.get(device_id)
        if not device:
            logger.error(f"[IoT] 设备不存在: {device_id}")
            return False

        protocol = device.protocol
        protocol_config = device.config

        try:
            # 根据协议类型发送命令
            if protocol == "mqtt":
                success = await self._send_mqtt_command(
                    device_id, command, parameters, protocol_config
                )
            elif protocol == "http":
                success = await self._send_http_command(
                    device_id, command, parameters, protocol_config
                )
            elif protocol == "websocket":
                success = await self._send_websocket_command(
                    device_id, command, parameters, protocol_config
                )
            elif protocol == "serial":
                success = await self._send_serial_command(
                    device_id, command, parameters, protocol_config
                )
            else:
                logger.warning(f"[IoT] 不支持的协议: {protocol}")
                # 使用通用模拟模式
                await asyncio.sleep(0.2)
                success = True

            if success:
                logger.info(f"[IoT] 命令发送成功: {device_id} -> {command}")
            else:
                logger.error(f"[IoT] 命令发送失败: {device_id} -> {command}")

            return success

        except Exception as e:
            logger.error(f"[IoT] 发送命令异常: {e}", exc_info=True)
            return False

    async def _send_mqtt_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> bool:
        """发送MQTT命令"""
        try:
            # 尝试导入 aiomqtt
            try:
                from aiomqtt import Client as MqttClient
            except ImportError:
                # 回退到模拟模式
                logger.warning("[IoT] aiomqtt未安装，MQTT使用模拟模式")
                await asyncio.sleep(0.1)
                return True

            # 获取MQTT配置
            broker = config.get("broker", "localhost")
            port = config.get("port", 1883)
            topic = config.get("topic", f"miya/devices/{device_id}/command")
            qos = config.get("qos", 1)
            retain = config.get("retain", False)
            username = config.get("username")
            password = config.get("password")

            # 构建命令payload
            payload = {
                "device_id": device_id,
                "command": command,
                "parameters": parameters or {},
                "timestamp": datetime.now().isoformat()
            }

            # 连接并发布消息
            async with MqttClient(
                hostname=broker,
                port=port,
                username=username,
                password=password
            ) as client:
                await client.publish(
                    topic,
                    payload=json.dumps(payload),
                    qos=qos,
                    retain=retain
                )
                logger.info(f"[IoT] MQTT命令已发送: {device_id} <- {command} (topic: {topic})")
                return True

        except Exception as e:
            logger.error(f"[IoT] MQTT命令发送失败: {e}", exc_info=True)
            return False

    async def _send_http_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> bool:
        """发送HTTP命令"""
        try:
            import aiohttp

            url = config.get("url")
            if not url:
                logger.warning(f"[IoT] 设备{device_id}缺少HTTP URL配置")
                return False

            # 构建请求
            endpoint = f"{url}/command"
            payload = {
                "device_id": device_id,
                "command": command,
                "parameters": parameters or {}
            }

            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"[IoT] HTTP请求失败: {response.status}")
                        return False

        except ImportError:
            logger.warning("[IoT] aiohttp未安装，使用模拟模式")
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"[IoT] HTTP命令发送失败: {e}", exc_info=True)
            return False

    async def _send_websocket_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> bool:
        """发送WebSocket命令"""
        try:
            import aiohttp

            # 获取WebSocket配置
            url = config.get("url")
            if not url:
                logger.warning(f"[IoT] 设备{device_id}缺少WebSocket URL配置")
                return False

            # 构建命令payload
            payload = {
                "device_id": device_id,
                "command": command,
                "parameters": parameters or {},
                "timestamp": datetime.now().isoformat()
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(url) as ws:
                    # 发送命令
                    await ws.send_json(payload)

                    # 等待响应
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            response = msg.json()
                            if response.get("status") == "success":
                                logger.info(f"[IoT] WebSocket命令成功: {device_id} <- {command}")
                                return True
                            else:
                                logger.error(f"[IoT] WebSocket命令失败: {response.get('error')}")
                                return False
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.warning("[IoT] WebSocket连接已关闭")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"[IoT] WebSocket错误: {ws.exception()}")
                            break

            return False

        except ImportError:
            logger.warning("[IoT] aiohttp未安装，WebSocket使用模拟模式")
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"[IoT] WebSocket命令发送失败: {e}", exc_info=True)
            return False

    async def _send_serial_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> bool:
        """发送串口命令"""
        try:
            import serial
            import serial.tools.list_ports
            from serial.serialutil import SerialException

            # 获取串口配置
            port = config.get("port", "/dev/ttyUSB0")
            baudrate = config.get("baudrate", 9600)
            bytesize = config.get("bytesize", serial.EIGHTBITS)
            parity = config.get("parity", serial.PARITY_NONE)
            stopbits = config.get("stopbits", serial.STOPBITS_ONE)
            timeout = config.get("timeout", 1.0)

            # 转换参数类型
            if isinstance(baudrate, str):
                baudrate = int(baudrate)

            # 构建命令数据
            command_data = command
            if parameters:
                # 如果命令包含占位符，进行替换
                for key, value in parameters.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in command:
                        command_data = command_data.replace(placeholder, str(value))

            # 转换为字节
            if isinstance(command_data, str):
                encoding = config.get("encoding", "utf-8")
                command_bytes = command_data.encode(encoding)
            elif isinstance(command_data, (list, tuple)):
                command_bytes = bytes(command_data)
            elif isinstance(command_data, bytes):
                command_bytes = command_data
            else:
                logger.error(f"[IoT] 不支持的命令格式: {type(command_data)}")
                return False

            # 打开串口连接
            logger.debug(f"[IoT] 打开串口: {port}, 波特率: {baudrate}")
            serial_conn = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=timeout
            )

            # 发送命令
            bytes_written = serial_conn.write(command_bytes)
            serial_conn.flush()

            # 等待响应（可选）
            wait_for_response = config.get("wait_for_response", False)
            response = None
            if wait_for_response:
                read_timeout = config.get("read_timeout", 2.0)
                serial_conn.timeout = read_timeout

                # 读取响应
                response_bytes = serial_conn.read(serial_conn.in_waiting or 1024)
                if response_bytes:
                    response_encoding = config.get("response_encoding", "utf-8")
                    response = response_bytes.decode(response_encoding)
                    logger.debug(f"[IoT] 串口响应: {response}")

            # 关闭串口连接
            serial_conn.close()

            logger.info(f"[IoT] 串口命令已发送: {device_id} <- {command} ({bytes_written}字节)")
            if response:
                logger.debug(f"[IoT] 串口响应: {response}")

            return True

        except ImportError:
            logger.error("[IoT] pyserial未安装，请运行: pip install pyserial")
            return False
        except SerialException as e:
            logger.error(f"[IoT] 串口操作失败: {e}")
            return False
        except Exception as e:
            logger.error(f"[IoT] 发送串口命令失败: {e}", exc_info=True)
            return False

    def _check_time_condition(self, condition: Dict[str, Any]) -> bool:
        """检查时间条件"""
        from datetime import datetime, time as dt_time

        current_time = datetime.now()
        current_time_obj = current_time.time()

        time_value = condition.get("time")
        time_type = condition.get("time_type", "at")  # at, before, after, between

        if time_type == "at":
            # 检查是否在指定时间
            if isinstance(time_value, str):
                target_time = dt_time.fromisoformat(time_value)
                return current_time_obj.hour == target_time.hour and \
                       current_time_obj.minute == target_time.minute

        elif time_type == "before":
            # 检查是否在指定时间之前
            if isinstance(time_value, str):
                target_time = dt_time.fromisoformat(time_value)
                return current_time_obj < target_time

        elif time_type == "after":
            # 检查是否在指定时间之后
            if isinstance(time_value, str):
                target_time = dt_time.fromisoformat(time_value)
                return current_time_obj > target_time

        elif time_type == "between":
            # 检查是否在时间范围内
            if isinstance(time_value, list) and len(time_value) == 2:
                start_time = dt_time.fromisoformat(time_value[0])
                end_time = dt_time.fromisoformat(time_value[1])
                return start_time <= current_time_obj <= end_time

        # 默认返回False
        return False

    async def _send_notification(
        self,
        message: str,
        action: Dict[str, Any]
    ) -> bool:
        """发送通知"""
        if not message:
            return False

        try:
            # 获取通知配置
            notify_type = action.get("notify_type", "log")  # log, email, webhook, desktop
            notify_config = action.get("config", {})

            if notify_type == "log":
                logger.info(f"[IoT通知] {message}")
                return True

            elif notify_type == "email":
                # 实现邮件通知
                return await self._send_email_notification(message, notify_config)

            elif notify_type == "webhook":
                return await self._send_webhook_notification(message, notify_config)

            elif notify_type == "desktop":
                return await self._send_desktop_notification(message, notify_config)

            else:
                logger.warning(f"[IoT] 未知通知类型: {notify_type}")
                return False

        except Exception as e:
            logger.error(f"[IoT] 发送通知失败: {e}", exc_info=True)
            return False

    async def _send_webhook_notification(
        self,
        message: str,
        config: Dict[str, Any]
    ) -> bool:
        """发送Webhook通知"""
        try:
            import aiohttp

            url = config.get("url")
            if not url:
                logger.warning("[IoT] Webhook缺少URL配置")
                return False

            payload = {
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "source": "miya_iot"
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    return response.status == 200

        except ImportError:
            logger.warning("[IoT] aiohttp未安装，跳过Webhook通知")
            return False
        except Exception as e:
            logger.error(f"[IoT] Webhook通知失败: {e}", exc_info=True)
            return False

    async def _send_email_notification(
        self,
        message: str,
        config: Dict[str, Any]
    ) -> bool:
        """发送邮件通知"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.utils import formataddr
            import ssl

            # 获取邮件配置
            smtp_server = config.get("smtp_server", "smtp.gmail.com")
            smtp_port = config.get("smtp_port", 587)
            smtp_username = config.get("username")
            smtp_password = config.get("password")
            from_addr = config.get("from_addr", smtp_username)
            to_addrs = config.get("to_addrs", [])
            subject = config.get("subject", "Miya IoT通知")
            use_tls = config.get("use_tls", True)

            # 验证必要配置
            if not smtp_username or not smtp_password:
                logger.warning("[IoT] 邮件配置缺失: username或password")
                return False

            if not to_addrs:
                logger.warning("[IoT] 邮件配置缺失: to_addrs")
                return False

            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = formataddr(('Miya IoT', from_addr))
            msg['To'] = ', '.join(to_addrs) if isinstance(to_addrs, list) else to_addrs
            msg['Subject'] = subject

            # 添加邮件正文
            body = f"""
Miya IoT系统通知

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

消息内容:
{message}

---
此邮件由Miya IoT系统自动发送，请勿回复。
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 发送邮件
            if use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)

            # 登录
            server.login(smtp_username, smtp_password)

            # 发送
            recipients = to_addrs if isinstance(to_addrs, list) else [to_addrs]
            server.send_message(msg, from_addr=from_addr, to_addrs=recipients)

            # 退出
            server.quit()

            logger.info(f"[IoT] 邮件通知已发送: {len(recipients)}个收件人")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[IoT] 邮件认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"[IoT] SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"[IoT] 发送邮件失败: {e}", exc_info=True)
            return False

    async def _send_desktop_notification(
        self,
        message: str,
        config: Dict[str, Any]
    ) -> bool:
        """发送桌面通知"""
        try:
            # 尝试使用系统通知
            if platform.system() == "Windows":
                import subprocess
                subprocess.run([
                    "powershell",
                    "-Command",
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"[System.Windows.Forms.MessageBox]::Show('{message}')"
                ], shell=True)
                return True
            elif platform.system() == "Darwin":  # macOS
                import subprocess
                subprocess.run([
                    "osascript",
                    "-e",
                    f'display notification "{message}" with title "Miya IoT"'
                ])
                return True
            elif platform.system() == "Linux":
                try:
                    import subprocess
                    subprocess.run([
                        "notify-send",
                        "Miya IoT",
                        message
                    ])
                    return True
                except FileNotFoundError:
                    logger.warning("[IoT] notify-send未安装")
                    return False
            else:
                logger.warning(f"[IoT] 不支持的系统: {platform.system()}")
                return False

        except Exception as e:
            logger.error(f"[IoT] 桌面通知失败: {e}", exc_info=True)
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        status_counts = {}
        for state in self.device_states.values():
            status = state.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_devices": len(self.devices),
            "status_counts": status_counts,
            "total_groups": len(self.device_groups),
            "total_rules": len(self.automation_rules),
            "enabled_rules": sum(1 for r in self.automation_rules.values() if r.enabled),
            "total_events": sum(r.trigger_count for r in self.automation_rules.values()),
            "heartbeat_running": self._heartbeat_task is not None
        }


# 全局单例
_IOT_MANAGER: Optional[IoTManager] = None


def get_iot_manager(config: Optional[Dict[str, Any]] = None) -> IoTManager:
    """获取IoT管理器单例"""
    global _IOT_MANAGER

    if _IOT_MANAGER is None:
        _IOT_MANAGER = IoTManager(config=config)

    return _IOT_MANAGER


def reset_iot_manager():
    """重置IoT管理器（主要用于测试）"""
    global _IOT_MANAGER
    _IOT_MANAGER = None
