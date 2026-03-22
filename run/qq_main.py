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
        logger = logging.getLogger('MiyaQQ')
        logger.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 文件处理器
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / 'miya_qq.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    async def initialize(self):
        """初始化系统"""
        self.logger.info("初始化弥娅 QQ 系统...")

        # 加载环境变量
        env_path = Path(__file__).parent.parent / 'config' / '.env'
        load_dotenv(env_path)

        # 读取 QQ 配置
        onebot_ws_url = os.getenv('QQ_ONEBOT_WS_URL', '')
        onebot_token = os.getenv('QQ_ONEBOT_TOKEN', '')
        bot_qq = int(os.getenv('QQ_BOT_QQ', '0'))
        superadmin_qq = int(os.getenv('QQ_SUPERADMIN_QQ', '0'))

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
            tts_net=self.tts_net
        )

        # 设置消息处理回调
        self.qq_net.set_message_callback(self._handle_qq_callback)

        # 注册 M-Link 节点
        self._register_mlink_nodes()

        # 配置 QQNet
        self.qq_net.configure(
            onebot_ws_url=onebot_ws_url,
            onebot_token=onebot_token,
            bot_qq=bot_qq,
            superadmin_qq=superadmin_qq
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
            tts_config_path = Path(__file__).parent.parent / 'config' / 'tts_config.json'
            if tts_config_path.exists():
                with open(tts_config_path, 'r', encoding=Encoding.UTF8) as f:
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
            self.miya.mlink.register_node('qq_net', [
                'qq_group_chat',
                'qq_private_chat',
                'qq_command',
                'qq_message_history',
                'qq_poke',
                'qq_multimedia',
                'qq_tts'
            ])

            # 注册 TTSNet 节点（如果存在）
            if self.tts_net:
                self.miya.mlink.register_node('tts_net', [
                    'tts_generation',
                    'voice_synthesis',
                    'audio_output'
                ])

            self.logger.info("M-Link 节点注册完成")
        except Exception as e:
            self.logger.error(f"M-Link 节点注册失败: {e}")

    async def _handle_qq_callback(self, qq_message: Any) -> None:
        """
        处理QQ消息回调

        Args:
            qq_message: QQMessage对象
        """
        try:
            self.logger.info(
                f"[QQ消息] type={qq_message.message_type} "
                f"sender={qq_message.sender_id} "
                f"content={qq_message.message[:50]}"
            )

            # 构建感知数据
            perception = {
                'source': 'qq',
                'message_type': qq_message.message_type,
                'user_id': qq_message.sender_id,
                'sender_id': qq_message.sender_id,
                'sender_name': qq_message.sender_name,
                'group_id': qq_message.group_id,
                'group_name': qq_message.group_name,
                'content': qq_message.message,
                'is_at_bot': qq_message.is_at_bot,
                'at_list': qq_message.at_list,
                'bot_qq': self.qq_net.bot_qq if self.qq_net else 0,
                'timestamp': datetime.now().isoformat()
            }

            # 检查用户输入是否是TTS切换指令
            content_str = str(perception.get('content', '')).strip().lower()
            direct_response = None

            if content_str in ['/voice', '/语音']:
                if self.qq_net:
                    _ = self.qq_net.set_tts_mode('voice')
                direct_response = "[OK] 已切换为语音模式"
            elif content_str in ['/text', '/文本']:
                if self.qq_net:
                    _ = self.qq_net.set_tts_mode('text')
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
                    source='qq_net',
                    destination='decision_hub',
                    priority=1
                )

                # 通过 M-Link 发送消息
                available_nodes = ['decision_hub']
                success = await self.miya.mlink.send(message, available_nodes)

                if success:
                    # 决策层处理感知数据并返回响应（使用新版 ToolNet 架构）
                    response_text = await self.miya.decision_hub.process_perception(message)

                    # 发送响应
                    if response_text:
                        await self._send_qq_response(qq_message, response_text)
                else:
                    self.logger.warning("M-Link 发送消息失败")
            else:
                self.logger.warning("M-Link 或决策层未初始化")

        except Exception as e:
            self.logger.error(f"处理QQ消息失败: {e}", exc_info=True)

    async def _send_qq_response(self, qq_message: Any, response_text: str) -> None:
        """
        发送QQ响应

        Args:
            qq_message: QQMessage对象
            response_text: 响应文本
        """
        if not response_text or not self.qq_net:
            return

        try:
            # 拍一拍消息需要在群中发送回复（如果有群ID）
            if qq_message.message_type == "poke":
                if qq_message.group_id and qq_message.group_id > 0:
                    _ = await self.qq_net.send_group_message(
                        qq_message.group_id,
                        response_text
                    )
                elif qq_message.user_id and qq_message.user_id > 0:
                    # 私聊拍一拍
                    _ = await self.qq_net.send_private_message(
                        qq_message.user_id,
                        response_text
                    )
            elif qq_message.message_type == "group":
                self.logger.info(f"[QQBot] 发送群消息: group_id={qq_message.group_id}")
                _ = await self.qq_net.send_group_message(
                    qq_message.group_id,
                    response_text
                )
                self.logger.info(f"[QQBot] 群消息发送完成")
            elif qq_message.message_type == "private":
                self.logger.info(f"[QQBot] 发送私聊消息: user_id={qq_message.user_id}")
                _ = await self.qq_net.send_private_message(
                    qq_message.user_id,
                    response_text
                )
                self.logger.info(f"[QQBot] 私聊消息发送完成")
        except Exception as e:
            self.logger.error(f"发送QQ响应失败: {e}", exc_info=True)

    async def start(self):
        """启动 QQ 机器人"""
        self.logger.info("正在启动弥娅 QQ 机器人...")

        try:
            # 连接到 QQ
            if self.qq_net:
                await self.qq_net.connect()
                self.logger.info("[OK] QQ 机器人连接成功！")

                # 设置 onebot_client 到 decision_hub
                if self.miya.decision_hub and hasattr(self.qq_net, 'onebot_client') and self.qq_net.onebot_client:
                    self.miya.decision_hub.onebot_client = self.qq_net.onebot_client
                    self.logger.info("DecisionHub 已设置 onebot_client")

                # 开始运行
                self.logger.info("弥娅 QQ 机器人已启动，等待消息...")
                self.logger.info("=" * 50)
                if self.miya.identity:
                    self.logger.info(f"        {self.miya.identity.name} QQ机器人")
                    self.logger.info(f"        UUID: {self.miya.identity.uuid}")
                    self.logger.info(f"        版本: {self.miya.identity.version}")
                self.logger.info(f"        工具系统: ToolNet (新版架构)")
                self.logger.info("=" * 50)

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
    print("""
╔══════════════════════════════════════════╗
║                                         ║
║      弥娅 QQ 机器人                     ║
║      Miya QQ Bot                        ║
║                                         ║
║      [ToolNet 新版架构]                  ║
╚══════════════════════════════════════════╝
    """)

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
        print(f"❌ 启动失败: {e}")
        logging.error(f"运行错误: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
