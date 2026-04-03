"""
TRPG场景生成流水线
参考 MetaGPT 流水线模式，使用多Agent协作生成场景
"""

from typing import Dict, List
from core.multi_agent_orchestrator import MultiAgentOrchestrator


class TRPGSceneGenerator:
    """TRPG场景生成流水线"""

    def __init__(self, orchestrator: MultiAgentOrchestrator):
        self.orchestrator = orchestrator

        # 定义流水线角色
        self.pipeline = {
            "StoryDirector": {
                "role": "故事总监",
                "capabilities": ["story_outline", "plot_design"],
            },
            "EnvironmentDesigner": {
                "role": "环境设计师",
                "capabilities": ["environment_desc", "atmosphere"],
            },
            "EnemyCreator": {
                "role": "敌人生成器",
                "capabilities": ["enemy_stats", "boss_design"],
            },
            "LootManager": {
                "role": "物品掉落管理器",
                "capabilities": ["item_generation", "treasure"],
            },
            "NarrativeWeaver": {
                "role": "叙事编织者",
                "capabilities": ["narrative", "dialogue"],
            },
        }

    async def register_agents(self):
        """注册流水线Agent"""
        for agent_id, config in self.pipeline.items():
            await self.orchestrator.register_agent(agent_id, config)

    async def generate_scene(self, party_level: int, theme: str) -> Dict:
        """生成TRPG场景"""

        task = {
            "type": "trpg_scene_generation",
            "params": {"party_level": party_level, "theme": theme},
            "description": f"生成{party_level}级{theme}主题的TRPG场景",
            "pipeline": list(self.pipeline.keys()),
        }

        result = await self.orchestrator.execute_task(task)
        return result
