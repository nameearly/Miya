# -*- coding: utf-8 -*-
"""
弥娅 QQ 模式主入口 - 使用新版 ToolNet 架构

启动弥娅 QQ 机器人
"""

import sys
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入配置
from config import Settings
from run.main import Miya
from dotenv import load_dotenv

# 导入QQ相关
from webnet import QQNet


class MiyaQQ:
    """弥娅 QQ 模式主类 - 使用新版 ToolNet 架构"""

    def __init__(self):
        self.logger: logging.Logger = self._setup_logger()
        self.settings: Any = Settings()

        # 初始化核心系统
        self.miya: Any = None
        self.qq_net: Any = None
        self.tts_net: Any = None

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("MiyaQQ")
        logger.setLevel(logging.DEBUG)

        # 控制台处理器 - 使用更详细的格式
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 文件处理器
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "miya_qq.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # 控制台格式化 - 简洁风格
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # 文件格式化 - 完整格式
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def _log_system_info(self):
        """记录系统信息"""
        import platform
        import sys
        from datetime import datetime

        self.logger.info(f"系统信息:")
        self.logger.info(f"  操作系统: {platform.system()} {platform.version()}")
        self.logger.info(f"  Python: {sys.version.split()[0]}")
        self.logger.info(f"  工作目录: {Path(__file__).parent.parent}")
        self.logger.info(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async def initialize(self):
        """初始化系统"""
        self.logger.info("弥娅 QQ 机器人初始化中...")
        self._log_system_info()

        # 加载环境变量
        env_path = Path(__file__).parent.parent / "config" / ".env"
        load_dotenv(env_path)

        # 读取 QQ 配置
        onebot_ws_url = os.getenv("QQ_ONEBOT_WS_URL", "")
        onebot_token = os.getenv("QQ_ONEBOT_TOKEN", "")
        bot_qq = int(os.getenv("QQ_BOT_QQ", "0"))
        superadmin_qq = int(os.getenv("QQ_SUPERADMIN_QQ", "0"))

        if not onebot_ws_url:
            raise RuntimeError("未配置 QQ_ONEBOT_WS_URL，请在 config/.env 中设置")
        if bot_qq == 0:
            raise RuntimeError("未配置 QQ_BOT_QQ，请在 config/.env 中设置")

        self.logger.info(f"QQ 配置加载完成:")
        self.logger.info(f"  OneBot URL: {onebot_ws_url}")
        self.logger.info(f"  Bot QQ: {bot_qq}")
        self.logger.info(f"  Super Admin: {superadmin_qq}")

        # 创建弥娅核心实例（使用新版架构）
        self.miya = Miya()

        # 异步初始化 MemoryNet
        if self.miya.memory_net:
            await self.miya._initialize_memory_net_async()

        self.logger.info("弥娅核心系统初始化完成（新版 ToolNet 架构）")

        # 初始化 TTS 系统
        self._init_tts_system()

        # 初始化 QQNet
        if not self.miya.net_manager:
            raise RuntimeError("NetManager 未初始化")

        # QQNet 的构造函数签名不同，需要调整参数
        self.qq_net = QQNet(
            miya_core=self.miya,
            mlink=self.miya.mlink,
            memory_net=self.miya.memory_net,
            tts_net=self.tts_net,
        )

        # 设置消息处理回调
        self.qq_net.set_message_callback(self._handle_qq_callback)

        # 注册 M-Link 节点
        self._register_mlink_nodes()

        # 注册跨端终端
        self._register_cross_terminal()

        # 配置 QQNet
        self.qq_net.configure(
            onebot_ws_url=onebot_ws_url,
            onebot_token=onebot_token,
            bot_qq=bot_qq,
            superadmin_qq=superadmin_qq,
        )

        self.logger.info("QQNet 配置完成")

    def _init_tts_system(self):
        """初始化 TTS 系统"""
        try:
            from webnet.tts import TTSNet
            import json
            from core.constants import Encoding

            # 初始化 TTSNet
            self.tts_net = TTSNet(self.miya.mlink)

            # 加载TTS配置
            tts_config_path = (
                Path(__file__).parent.parent / "config" / "tts_config.json"
            )
            if tts_config_path.exists():
                with open(tts_config_path, "r", encoding=Encoding.UTF8) as f:
                    tts_config = json.load(f)
                self.tts_net.initialize(tts_config)
                self.logger.info("TTS系统初始化成功")
            else:
                self.logger.warning("TTS配置文件不存在,使用默认配置")
                self.tts_net = None

        except Exception as e:
            self.logger.warning(f"TTS系统初始化失败: {e}")
            self.tts_net = None

    def _register_mlink_nodes(self):
        """注册 M-Link 节点"""
        if not self.miya.mlink:
            return

        try:
            # 注册 QQNet 节点
            self.miya.mlink.register_node(
                "qq_net",
                [
                    "qq_group_chat",
                    "qq_private_chat",
                    "qq_command",
                    "qq_message_history",
                    "qq_poke",
                    "qq_multimedia",
                    "qq_tts",
                ],
            )

            # 注册 TTSNet 节点（如果存在）
            if self.tts_net:
                self.miya.mlink.register_node(
                    "tts_net", ["tts_generation", "voice_synthesis", "audio_output"]
                )

            self.logger.info("M-Link 节点注册完成")
        except Exception as e:
            self.logger.error(f"M-Link 节点注册失败: {e}")

    def _register_cross_terminal(self):
        """注册跨端终端"""
        try:
            from webnet.ToolNet.tools.cross_terminal.cross_terminal import (
                get_cross_terminal_hub,
            )

            hub = get_cross_terminal_hub()
            hub.register_terminal("qq")
            self.logger.info("跨端终端 QQ 已注册")
        except Exception as e:
            self.logger.warning(f"跨端终端注册失败: {e}")

    async def _handle_qq_callback(self, qq_message: Any) -> None:
        """
        处理QQ消息回调

        Args:
            qq_message: QQMessage对象
        """
        try:
            # 记录收到消息
            msg_preview = (
                qq_message.message[:80]
                if len(qq_message.message) > 80
                else qq_message.message
            )
            self.logger.info(
                f"QQ消息 -> {qq_message.message_type} | {qq_message.sender_id}({qq_message.sender_name})"
            )
            if qq_message.group_id:
                self.logger.info(
                    f"    群: {qq_message.group_id}({qq_message.group_name})"
                )
            if qq_message.is_at_bot:
                self.logger.info(f"    @弥娅: 是")
            self.logger.info(f"    内容: {msg_preview}")

            # 构建感知数据（修复：poke等消息也要根据group_id判断群聊/私聊）
            msg_type = qq_message.message_type
            # 如果是poke或其他特殊消息，根据group_id判断
            if msg_type not in ["group", "private"]:
                if qq_message.group_id and qq_message.group_id > 0:
                    msg_type = "group"
                else:
                    msg_type = "private"

            perception = {
                "source": "qq",
                "message_type": msg_type,
                "raw_message_type": qq_message.message_type,
                "user_id": qq_message.sender_id,
                "sender_id": qq_message.sender_id,
                "sender_name": qq_message.sender_name,
                "group_id": qq_message.group_id,
                "group_name": qq_message.group_name,
                "content": qq_message.message,
                "is_at_bot": qq_message.is_at_bot,
                "at_list": qq_message.at_list,
                "bot_qq": self.qq_net.bot_qq if self.qq_net else 0,
                "timestamp": datetime.now().isoformat(),
                "message_id": qq_message.message_id,
                "reply": {
                    "message_id": qq_message.reply.message_id,
                    "sender_name": qq_message.reply.sender_name,
                    "content": qq_message.reply.content,
                }
                if qq_message.reply
                else None,
                "files": [
                    {
                        "file_id": f.file_id,
                        "name": f.name,
                        "size": f.size,
                        "file_type": f.file_type,
                    }
                    for f in qq_message.files
                ]
                if qq_message.files
                else [],
                "has_media": qq_message.has_media,
            }

            # 【修复】检查消息是否已有图片分析回复，如果有则直接发送
            img_keywords_str = ""
            try:
                from core.text_loader import get_text

                img_keywords_str = get_text("image_response.keywords", "")
            except Exception:
                pass

            if hasattr(qq_message, "image_response") and qq_message.image_response:
                self.logger.info("[图片回复] 检测到图片分析回复，直接发送")
                await self._send_qq_response(qq_message, qq_message.image_response)
                return

            if hasattr(qq_message, "message") and qq_message.message:
                msg_content = qq_message.message
                if img_keywords_str:
                    keywords = [
                        k.strip() for k in img_keywords_str.split(",") if k.strip()
                    ]
                    if any(kw in msg_content for kw in keywords):
                        self.logger.info("[图片回复] 检测到图片分析回复内容，直接发送")
                        await self._send_qq_response(qq_message, msg_content)
                        return

            # 检查用户输入是否是TTS切换指令
            content_str = str(perception.get("content", "")).strip().lower()
            direct_response = None

            if content_str in ["/voice", "/语音"]:
                if self.qq_net:
                    _ = self.qq_net.set_tts_mode("voice")
                direct_response = "[OK] 已切换为语音模式"
            elif content_str in ["/text", "/文本"]:
                if self.qq_net:
                    _ = self.qq_net.set_tts_mode("text")
                direct_response = "[OK] 已切换为文本模式"

            # 如果是直接命令，直接发送响应
            if direct_response:
                await self._send_qq_response(qq_message, direct_response)
                return

            # 通过新版 DecisionHub 处理（使用 ToolNet 架构）
            if self.miya.mlink and self.miya.decision_hub:
                from mlink.message import Message, MessageType

                # 创建 M-Link 消息
                message = Message(
                    msg_type=MessageType.DATA.value,
                    content=perception,
                    source="qq_net",
                    destination="decision_hub",
                    priority=1,
                )

                # 通过 M-Link 发送消息
                available_nodes = ["decision_hub"]
                success = await self.miya.mlink.send(message, available_nodes)

                if success:
                    # 决策处理开始
                    self.logger.info("决策处理 -> 开始")

                    # 记录处理开始时间，用于检测延迟
                    import time

                    start_time = time.time()

                    # 收集处理信息
                    tool_info = ""
                    tool_calls = []
                    memory_info = ""

                    # 获取工具调用信息
                    if hasattr(self.miya.decision_hub, "tool_subnet"):
                        tool_info = (
                            self.miya.decision_hub.tool_subnet.get_last_execution_info()
                        )

                    # 获取ToolNet的工具调用记录
                    if hasattr(self.miya.decision_hub, "_last_tool_calls"):
                        tool_calls = self.miya.decision_hub._last_tool_calls or []

                    # 获取记忆操作信息
                    if hasattr(self.miya.decision_hub, "memory_manager"):
                        mm = self.miya.decision_hub.memory_manager
                        if hasattr(mm, "_last_operation"):
                            memory_info = mm._last_operation

                    # 记录工具调用
                    if tool_calls:
                        self.logger.info(f"工具调用 -> {len(tool_calls)} 个工具")
                    if tool_info:
                        self.logger.info(f"工具详情 -> {tool_info}")

                    # 记录记忆操作
                    if memory_info:
                        self.logger.info(f"记忆操作 -> {memory_info}")

                    # 记录消息分析
                    perception = message.content
                    content_preview = perception.get("content", "")[:50]
                    self.logger.info(f"消息分析 -> {content_preview}...")

                    # 处理感知数据
                    response_text = await self.miya.decision_hub.process_perception(
                        message
                    )

                    # 显示模型调用信息
                    last_model = getattr(
                        self.miya.decision_hub, "_last_selected_model", ""
                    )
                    last_task_type = getattr(
                        self.miya.decision_hub, "_last_task_type", ""
                    )
                    if last_model:
                        self.logger.info(
                            f"[模型调用] 使用模型: {last_model} | 任务类型: {last_task_type}"
                        )

                    # 记录处理耗时
                    process_time = time.time() - start_time
                    self.logger.info(f"处理完成 -> 耗时: {process_time:.3f}秒")

                    # 记录并发送响应
                    if response_text:
                        response_preview = response_text[:100]
                        self.logger.info(f"弥娅回复 -> {response_preview}...")

                        # 发送响应
                        await self._send_qq_response(qq_message, response_text)

                        # 处理完成
                        self.logger.info(f"消息处理 -> 完成")
                    else:
                        self.logger.warning("弥娅无回复内容")
                else:
                    self.logger.warning("M-Link 发送消息失败")
            else:
                self.logger.warning("M-Link 或决策层未初始化")

        except Exception as e:
            self.logger.error(f"处理QQ消息失败: {e}", exc_info=True)

    async def _send_qq_response(self, qq_message: Any, response_text: str) -> None:
        """发送QQ响应"""
        if not response_text or not self.qq_net:
            return

        try:
            if qq_message.message_type == "poke":
                if qq_message.group_id and qq_message.group_id > 0:
                    self.logger.info(f"发送群聊拍一拍回复至 {qq_message.group_id}")
                    _ = await self.qq_net.send_group_message(
                        qq_message.group_id, response_text
                    )
                elif qq_message.user_id and qq_message.user_id > 0:
                    self.logger.info(f"发送私聊拍一拍回复至 {qq_message.user_id}")
                    _ = await self.qq_net.send_private_message(
                        qq_message.user_id, response_text
                    )
            elif qq_message.message_type == "group":
                self.logger.info(f"发送群消息至 {qq_message.group_id}")
                _ = await self.qq_net.send_group_message(
                    qq_message.group_id, response_text
                )
            elif qq_message.message_type == "private":
                self.logger.info(f"发送私聊消息至 {qq_message.user_id}")
                _ = await self.qq_net.send_private_message(
                    qq_message.user_id, response_text
                )
        except Exception as e:
            self.logger.error(f"QQ响应发送失败: {e}", exc_info=True)

    async def start(self):
        """启动 QQ 机器人"""
        self.logger.info("弥娅 QQ 机器人启动中...")

        try:
            # 连接到 QQ
            if self.qq_net:
                self.logger.info("连接到 OneBot WebSocket...")
                await self.qq_net.connect()
                self.logger.info("QQ 机器人连接成功！")

                # 设置 onebot_client 到 decision_hub
                if (
                    self.miya.decision_hub
                    and hasattr(self.qq_net, "onebot_client")
                    and self.qq_net.onebot_client
                ):
                    self.miya.decision_hub.onebot_client = self.qq_net.onebot_client
                    self.logger.info("DecisionHub onebot_client 已设置")

                # 设置 qq_net 引用到 decision_hub（用于权限检查）
                if self.miya.decision_hub and self.qq_net:
                    self.miya.decision_hub.qq_net = self.qq_net
                    self.logger.info("DecisionHub qq_net 已设置")

                # 2. 主动聊天系统通过 DecisionHub 管理 (core/proactive_chat)

                # 3. 跨端终端注册
                self.logger.info("注册跨端终端...")
                self._register_cross_terminal()

                # 4. 加载定时任务
                self.logger.info("加载定时任务...")

                # 5. 启动消息接收循环
                self.logger.info("启动消息接收循环...")

                if self.miya.identity:
                    self.logger.info(f"弥娅 QQ 机器人已启动: {self.miya.identity.name}")
                    self.logger.info(f"  UUID: {self.miya.identity.uuid}")
                    self.logger.info(f"  版本: {self.miya.identity.version}")
                self.logger.info(f"  工具: ToolNet (新版架构)")
                self.logger.info(f"  主动聊天: 已启用 (定时+上下文)")
                self.logger.info(f"  跨端联动: 已启用")

                # 启动 QQNet
                await self.qq_net.start()

        except KeyboardInterrupt:
            self.logger.info("\n收到中断信号，正在关闭...")
        except Exception as e:
            self.logger.error(f"启动失败: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理资源...")
        if self.qq_net:
            await self.qq_net.stop()
        self.logger.info("已停止")


async def main():
    """主函数"""
    print("弥娅 QQ 机器人启动中...")

    app = MiyaQQ()

    try:
        await app.initialize()
        await app.start()
    except ConnectionRefusedError as e:
        print()
        print("=" * 60)
        print("[ERROR] 连接失败!")
        print("=" * 60)
        print()
        print(f"错误信息: {e}")
        print()
        print("可能的原因:")
        print("  1. OneBot服务未启动")
        print("  2. WebSocket地址配置错误")
        print("  3. 端口被占用")
        print()
        print("解决方法:")
        print("  1. 启动OneBot服务 (NapCat或go-cqhttp)")
        print("  2. 检查 config/.env 中的 QQ_ONEBOT_WS_URL")
        print("  3. 参考 docs/QQ_BOT_SETUP.md 进行配置")
        print()
        print("=" * 60)
    except Exception as e:
        print(f"启动失败: {e}")
        logging.error(f"运行错误: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
