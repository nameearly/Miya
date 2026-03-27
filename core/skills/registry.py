"""
弥娅技能注册系统 - 统一管理 Agents、Commands、Hooks、MCP Services
为 Terminal Ultra 提供完整的技能生态
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("Miya.SkillsRegistry")


class SkillType(Enum):
    AGENT = "agent"  # Agent
    COMMAND = "command"  # Slash Command
    HOOK = "hook"  # Hook
    MCP = "mcp"  # MCP Service
    TOOL = "tool"  # 工具


@dataclass
class Skill:
    name: str
    type: SkillType
    description: str
    enabled: bool = True
    module: str = ""
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillsRegistry:
    """技能注册中心"""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._initialized = False

    async def initialize(self):
        """初始化所有技能"""
        if self._initialized:
            return

        logger.info("[Skills] 初始化技能注册表...")

        # 加载 Agents
        await self._load_agents()

        # 加载 Commands
        self._load_commands()

        # 加载 Hooks
        self._load_hooks()

        # 加载 MCP Services
        await self._load_mcp_services()

        self._initialized = True
        logger.info(f"[Skills] 已注册 {len(self.skills)} 个技能")

    async def _load_agents(self):
        """加载 Agents"""
        agents_dir = Path("core/skills/agents")
        if not agents_dir.exists():
            return

        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith("_"):
                self.skills[agent_dir.name] = Skill(
                    name=agent_dir.name,
                    type=SkillType.AGENT,
                    description=f"Agent: {agent_dir.name}",
                    module=f"core.skills.agents.{agent_dir.name}.handler",
                )
                logger.info(f"[Skills] 注册 Agent: {agent_dir.name}")

    def _load_commands(self):
        """加载 Slash Commands"""
        from core.skills.slash_commands import _command_manager

        for name, cmd in _command_manager.commands.items():
            self.skills[f"/{name}"] = Skill(
                name=f"/{name}",
                type=SkillType.COMMAND,
                description=cmd.description,
                module="core.skills.slash_commands",
            )
            logger.info(f"[Skills] 注册 Command: /{name}")

    def _load_hooks(self):
        """加载 Hooks"""
        self.skills["hooks"] = Skill(
            name="hooks",
            type=SkillType.HOOK,
            description="安全钩子系统",
            module="core.skills.hooks.hook_manager",
        )
        logger.info("[Skills] 注册 Hooks 系统")

    async def _load_mcp_services(self):
        """加载 MCP Services"""
        mcp_dir = Path("mcpserver")
        if not mcp_dir.exists():
            return

        for service_dir in mcp_dir.iterdir():
            if service_dir.is_dir():
                manifest_file = service_dir / "agent-manifest.json"
                if manifest_file.exists():
                    try:
                        data = json.loads(manifest_file.read_text(encoding="utf-8"))
                        self.skills[data["name"]] = Skill(
                            name=data["name"],
                            type=SkillType.MCP,
                            description=data.get("description", ""),
                            module=data.get("entryPoint", {}).get("module", ""),
                            metadata=data.get("capabilities", {}),
                        )
                        logger.info(f"[Skills] 注册 MCP: {data['name']}")
                    except Exception as e:
                        logger.warning(
                            f"[Skills] 加载 MCP manifest 失败: {service_dir}: {e}"
                        )

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)

    def list_skills(self, skill_type: SkillType = None) -> List[Skill]:
        """列出技能"""
        if skill_type:
            return [s for s in self.skills.values() if s.type == skill_type]
        return list(self.skills.values())

    def list_agents(self) -> List[str]:
        """列出所有 Agent 名称"""
        return [s.name for s in self.skills.values() if s.type == SkillType.AGENT]

    def list_commands(self) -> List[str]:
        """列出所有命令"""
        return [s.name for s in self.skills.values() if s.type == SkillType.COMMAND]

    def list_mcp_services(self) -> List[str]:
        """列出所有 MCP 服务"""
        return [s.name for s in self.skills.values() if s.type == SkillType.MCP]

    def get_help(self) -> str:
        """获取帮助信息"""
        lines = ["## 弥娅技能系统", ""]

        lines.append("### Agents")
        for skill in self.list_skills(SkillType.AGENT):
            lines.append(f"- **{skill.name}**: {skill.description}")

        lines.append("")
        lines.append("### Slash Commands")
        for skill in self.list_skills(SkillType.COMMAND):
            lines.append(f"- **{skill.name}**: {skill.description}")

        lines.append("")
        lines.append("### MCP Services")
        for skill in self.list_skills(SkillType.MCP):
            lines.append(f"- **{skill.name}**: {skill.description}")

        return "\n".join(lines)


_registry = None


async def get_skills_registry() -> SkillsRegistry:
    """获取技能注册表"""
    global _registry
    if _registry is None:
        _registry = SkillsRegistry()
        await _registry.initialize()
    return _registry


def list_all_skills() -> Dict[str, List[str]]:
    """列出所有技能"""

    async def get():
        registry = await get_skills_registry()
        return {
            "agents": registry.list_agents(),
            "commands": registry.list_commands(),
            "mcp_services": registry.list_mcp_services(),
        }

    import asyncio

    return asyncio.run(get())
