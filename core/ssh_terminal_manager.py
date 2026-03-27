"""SSH终端管理器 - 支持远程SSH连接和命令执行"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import asyncssh
    ASYNCSSH_AVAILABLE = True
except ImportError:
    ASYNCSSH_AVAILABLE = False
    logger.warning("[SSH Terminal] asyncssh未安装，SSH终端功能将不可用")


@dataclass
class SSHConfig:
    """SSH连接配置"""
    host: str
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    private_key: Optional[str] = None
    private_key_password: Optional[str] = None
    timeout: int = 10


class SSHTerminalManager:
    """SSH终端管理器"""

    def __init__(self):
        """初始化SSH终端管理器"""
        if not ASYNCSSH_AVAILABLE:
            # 不抛出异常，只是标记为不可用
            self.available = False
            return

        self.available = True
        # SSH连接池
        self.connections: Dict[str, asyncssh.SSHClientConnection] = {}
        self.sessions: Dict[str, asyncssh.SSHClientProcess] = {}

    async def create_terminal(
        self,
        config: SSHConfig,
        name: str = "ssh-terminal"
    ) -> str:
        """创建SSH终端

        Args:
            config: SSH配置
            name: 终端名称

        Returns:
            会话ID
        """
        try:
            # 创建SSH连接
            conn = await asyncssh.connect(
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                client_keys=[config.private_key] if config.private_key else None,
                passphrase=config.private_key_password,
                known_hosts=None,  # 跳过主机密钥验证（仅用于测试）
                connect_timeout=config.timeout
            )

            # 创建SSH会话
            # FIX: asyncssh 的 create_process 返回 awaitable；不 await 会保存协程/awaitable 而非会话对象。
            session = await conn.create_process(
                terminal_type='xterm-256color',
                term_size=(80, 24)
            )

            session_id = f"ssh-{name}-{id(conn)}"

            # 保存连接和会话
            self.connections[session_id] = conn
            self.sessions[session_id] = session

            logger.info(f"[SSH Terminal] 创建SSH终端成功: {name} @ {config.host}:{config.port}")

            return session_id

        except Exception as e:
            logger.error(f"[SSH Terminal] 创建SSH终端失败: {e}", exc_info=True)
            raise

    async def execute_command(
        self,
        session_id: str,
        command: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """在SSH终端执行命令

        Args:
            session_id: 会话ID
            command: 要执行的命令
            timeout: 超时时间（秒）

        Returns:
            执行结果
        """
        try:
            # 获取SSH会话
            conn = self.connections.get(session_id)
            if not conn:
                return {
                    "success": False,
                    "error": "SSH会话不存在"
                }

            # 执行命令
            result = await asyncio.wait_for(
                conn.run(command),
                timeout=timeout
            )

            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "exit_status": result.exit_status,
                "command": command
            }

        except asyncio.TimeoutError:
            logger.error(f"[SSH Terminal] 命令执行超时: {command}")
            return {
                "success": False,
                "error": "命令执行超时",
                "command": command
            }
        except Exception as e:
            logger.error(f"[SSH Terminal] 命令执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def close_terminal(self, session_id: str) -> bool:
        """关闭SSH终端

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        try:
            # 关闭会话
            session = self.sessions.pop(session_id, None)
            if session:
                session.close()

            # 关闭连接
            conn = self.connections.pop(session_id, None)
            if conn:
                conn.close()
                await conn.wait_closed()

            logger.info(f"[SSH Terminal] 关闭SSH终端: {session_id}")
            return True

        except Exception as e:
            logger.error(f"[SSH Terminal] 关闭SSH终端失败: {e}", exc_info=True)
            return False

    async def close_all(self) -> None:
        """关闭所有SSH连接"""
        for session_id in list(self.sessions.keys()):
            await self.close_terminal(session_id)

        logger.info("[SSH Terminal] 所有SSH连接已关闭")

    def get_terminal_list(self) -> list:
        """获取SSH终端列表"""
        return list(self.sessions.keys())


# 全局单例
_ssh_manager: Optional[SSHTerminalManager] = None


def get_ssh_manager() -> Optional[SSHTerminalManager]:
    """获取SSH终端管理器单例

    Returns:
        SSHTerminalManager实例，如果asyncssh未安装则返回None
    """
    global _ssh_manager

    if not ASYNCSSH_AVAILABLE:
        return None

    if _ssh_manager is None:
        _ssh_manager = SSHTerminalManager()

    return _ssh_manager
