"""
场景管理系统
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from core.constants import Encoding


@dataclass
class NPC:
    """NPC 数据"""
    name: str
    description: str
    personality: str = ""        # 性格特点
    attitude: str = "neutral"    # 态度：friendly, neutral, hostile
    notes: str = ""              # 备注
    is_kp: bool = False          # 是否�?KP 角色


@dataclass
class Clue:
    """线索数据"""
    content: str                 # 线索内容
    found_by: List[int] = field(default_factory=list)  # 发现者列�?
    hidden: bool = True          # 是否隐藏


@dataclass
class TRPGScene:
    """TRPG 场景"""
    scene_id: str
    group_id: int
    name: str
    description: str

    # NPC 列表
    npcs: List[NPC] = field(default_factory=list)

    # 线索列表
    clues: List[Clue] = field(default_factory=list)

    # 当前状�?
    phase: str = "exploration"  # exploration, combat, interaction, rest

    # 环境描述
    environment: str = ""       # 环境描述
    atmosphere: str = ""        # 氛围描述

    # 元数�?
    created_by: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_npc(self, name: str, description: str, **kwargs) -> NPC:
        """添加 NPC"""
        npc = NPC(name=name, description=description, **kwargs)
        self.npcs.append(npc)
        self.updated_at = datetime.now()
        return npc

    def remove_npc(self, name: str) -> bool:
        """移除 NPC"""
        for i, npc in enumerate(self.npcs):
            if npc.name == name:
                self.npcs.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def add_clue(self, content: str, hidden: bool = True) -> Clue:
        """添加线索"""
        clue = Clue(content=content, hidden=hidden)
        self.clues.append(clue)
        self.updated_at = datetime.now()
        return clue

    def find_clue(self, user_id: int) -> Optional[Clue]:
        """发现线索"""
        for clue in self.clues:
            if clue.hidden and user_id not in clue.found_by:
                clue.found_by.append(user_id)
                clue.hidden = False
                self.updated_at = datetime.now()
                return clue
        return None

    def to_dict(self) -> dict:
        """转换为字�?""
        return {
            'scene_id': self.scene_id,
            'group_id': self.group_id,
            'name': self.name,
            'description': self.description,
            'npcs': [
                {
                    'name': npc.name,
                    'description': npc.description,
                    'personality': npc.personality,
                    'attitude': npc.attitude,
                    'notes': npc.notes,
                    'is_kp': npc.is_kp
                }
                for npc in self.npcs
            ],
            'clues': [
                {
                    'content': clue.content,
                    'found_by': clue.found_by,
                    'hidden': clue.hidden
                }
                for clue in self.clues
            ],
            'phase': self.phase,
            'environment': self.environment,
            'atmosphere': self.atmosphere,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class SceneManager:
    """场景管理�?""

    def __init__(self, data_path: str = "data/trpg_scenes.json"):
        self.data_path = Path(data_path)
        self.scenes: Dict[int, TRPGScene] = {}  # group_id -> TRPGScene
        self.load()

    def load(self):
        """加载场景数据"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding=Encoding.UTF8) as f:
                    data = json.load(f)
                    for scene_data in data:
                        # 恢复 NPC
                        npcs = [
                            NPC(
                                name=npc['name'],
                                description=npc['description'],
                                personality=npc.get('personality', ''),
                                attitude=npc.get('attitude', 'neutral'),
                                notes=npc.get('notes', ''),
                                is_kp=npc.get('is_kp', False)
                            )
                            for npc in scene_data.get('npcs', [])
                        ]

                        # 恢复线索
                        clues = [
                            Clue(
                                content=clue['content'],
                                found_by=clue.get('found_by', []),
                                hidden=clue.get('hidden', True)
                            )
                            for clue in scene_data.get('clues', [])
                        ]

                        scene = TRPGScene(
                            scene_id=scene_data['scene_id'],
                            group_id=scene_data['group_id'],
                            name=scene_data['name'],
                            description=scene_data['description'],
                            npcs=npcs,
                            clues=clues,
                            phase=scene_data.get('phase', 'exploration'),
                            environment=scene_data.get('environment', ''),
                            atmosphere=scene_data.get('atmosphere', ''),
                            created_by=scene_data.get('created_by', 0)
                        )
                        self.scenes[scene.group_id] = scene
                    print(f"[SceneManager] 加载�?{len(self.scenes)} 个场�?)
            except Exception as e:
                print(f"[SceneManager] 加载失败: {e}")

    def save(self):
        """保存场景数据"""
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            data = [scene.to_dict() for scene in self.scenes.values()]
            with open(self.data_path, 'w', encoding=Encoding.UTF8) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SceneManager] 保存失败: {e}")

    def get_or_create(self, group_id: int, user_id: int) -> TRPGScene:
        """获取或创建场�?""
        if group_id not in self.scenes:
            scene = TRPGScene(
                scene_id=f"scene_{group_id}",
                group_id=group_id,
                name="新场�?,
                description="等待 KP 设置...",
                created_by=user_id
            )
            self.scenes[group_id] = scene
            self.save()
        return self.scenes[group_id]

    def get(self, group_id: int) -> Optional[TRPGScene]:
        """获取场景"""
        return self.scenes.get(group_id)

    def delete(self, group_id: int):
        """删除场景"""
        if group_id in self.scenes:
            del self.scenes[group_id]
            self.save()

    def set_scene(self, group_id: int, name: str, description: str,
                 environment: str = "", atmosphere: str = "") -> TRPGScene:
        """设置场景"""
        scene = self.get_or_create(group_id, 0)
        scene.name = name
        scene.description = description
        scene.environment = environment
        scene.atmosphere = atmosphere
        self.save()
        return scene

    def add_npc(self, group_id: int, name: str, description: str, **kwargs) -> Optional[NPC]:
        """添加 NPC"""
        scene = self.get(group_id)
        if scene:
            npc = scene.add_npc(name, description, **kwargs)
            self.save()
            return npc
        return None

    def list_npcs(self, group_id: int) -> List[NPC]:
        """列出 NPC"""
        scene = self.get(group_id)
        return scene.npcs if scene else []

    def add_clue(self, group_id: int, content: str, hidden: bool = True) -> Optional[Clue]:
        """添加线索"""
        scene = self.get(group_id)
        if scene:
            clue = scene.add_clue(content, hidden)
            self.save()
            return clue
        return None

    def list_clues(self, group_id: int, user_id: int = None) -> List[Clue]:
        """列出线索"""
        scene = self.get(group_id)
        if not scene:
            return []

        if user_id is None:
            return scene.clues

        # 返回已发现的线索
        return [clue for clue in scene.clues if not clue.hidden or user_id in clue.found_by]


# 全局单例
_scene_manager = None


def get_scene_manager() -> SceneManager:
    """获取场景管理器单�?""
    global _scene_manager
    if _scene_manager is None:
        _scene_manager = SceneManager()
    return _scene_manager
