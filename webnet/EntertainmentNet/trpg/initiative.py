"""
先攻轮次管理系统
InitiativeManager - 管理战斗中的先攻顺序
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from core.constants import Encoding


@dataclass
class InitiativeEntry:
    """先攻条目"""
    name: str              # 角色名称
    initiative: int        # 先攻�?
    dex_mod: int = 0       # 敏捷修正
    is_npc: bool = False   # 是否为NPC
    status: str = "active" # 状�? active, hidden, defeated

    def __lt__(self, other):
        """排序：先攻值高的在前，相同则敏捷高的在�?""
        if self.initiative != other.initiative:
            return self.initiative > other.initiative
        return self.dex_mod > other.dex_mod


class InitiativeManager:
    """先攻管理�?""

    def __init__(self, data_path: str = "data/trpg_initiative.json"):
        self.data_path = data_path
        self._initiative_orders: Dict[int, Dict[str, any]] = {}  # group_id -> initiative_order
        self.load()

    def load(self):
        """加载先攻数据"""
        if Path(self.data_path).exists():
            try:
                with open(self.data_path, 'r', encoding=Encoding.UTF8) as f:
                    data = json.load(f)
                    for group_id, order in data.items():
                        self._initiative_orders[int(group_id)] = order
                    print(f"[InitiativeManager] 加载�?{len(self._initiative_orders)} 个战斗轮�?)
            except Exception as e:
                print(f"[InitiativeManager] 加载失败: {e}")

    def save(self):
        """保存先攻数据"""
        try:
            Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
            data = {
                str(gid): order
                for gid, order in self._initiative_orders.items()
            }
            with open(self.data_path, 'w', encoding=Encoding.UTF8) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[InitiativeManager] 保存失败: {e}")

    def start_combat(self, group_id: int):
        """开始新的战�?""
        self._initiative_orders[group_id] = {
            'started_at': datetime.now().isoformat(),
            'round': 1,
            'current_index': 0,
            'entries': []
        }
        self.save()
        return self._initiative_orders[group_id]

    def end_combat(self, group_id: int):
        """结束战斗"""
        if group_id in self._initiative_orders:
            del self._initiative_orders[group_id]
            self.save()
            return True
        return False

    def add_entry(self, group_id: int, name: str, initiative: int,
                  dex_mod: int = 0, is_npc: bool = False):
        """添加先攻条目"""
        if group_id not in self._initiative_orders:
            self.start_combat(group_id)

        entry = InitiativeEntry(
            name=name,
            initiative=initiative,
            dex_mod=dex_mod,
            is_npc=is_npc
        )

        order = self._initiative_orders[group_id]
        order['entries'].append({
            'name': name,
            'initiative': initiative,
            'dex_mod': dex_mod,
            'is_npc': is_npc,
            'status': 'active'
        })

        # 按先攻排�?
        order['entries'].sort(
            key=lambda x: (x['initiative'], x['dex_mod']),
            reverse=True
        )

        self.save()
        return entry

    def remove_entry(self, group_id: int, name: str) -> bool:
        """移除先攻条目"""
        if group_id not in self._initiative_orders:
            return False

        order = self._initiative_orders[group_id]
        order['entries'] = [e for e in order['entries'] if e['name'] != name]

        # 重新调整当前索引
        if order['current_index'] >= len(order['entries']):
            order['current_index'] = 0

        self.save()
        return True

    def set_entry_status(self, group_id: int, name: str, status: str) -> bool:
        """设置条目状�?""
        if group_id not in self._initiative_orders:
            return False

        order = self._initiative_orders[group_id]
        for entry in order['entries']:
            if entry['name'] == name:
                entry['status'] = status
                self.save()
                return True
        return False

    def next_turn(self, group_id: int) -> Optional[Dict]:
        """下一回合"""
        if group_id not in self._initiative_orders:
            return None

        order = self._initiative_orders[group_id]
        entries = order['entries']
        active_entries = [e for e in entries if e['status'] == 'active']

        if not active_entries:
            return None

        # 移动到下一个活跃角�?
        order['current_index'] = (order['current_index'] + 1) % len(entries)

        # 如果当前不是活跃角色，继续查�?
        original_index = order['current_index']
        while entries[order['current_index']]['status'] != 'active':
            order['current_index'] = (order['current_index'] + 1) % len(entries)
            if order['current_index'] == original_index:
                # 所有角色都不活�?
                break

        # 检查是否轮回到第一个角�?
        if order['current_index'] == 0:
            order['round'] += 1

        self.save()
        return self.get_current_turn(group_id)

    def get_current_turn(self, group_id: int) -> Optional[Dict]:
        """获取当前回合"""
        if group_id not in self._initiative_orders:
            return None

        order = self._initiative_orders[group_id]
        if not order['entries']:
            return None

        current_entry = order['entries'][order['current_index']]

        return {
            'round': order['round'],
            'current_index': order['current_index'],
            'current_character': current_entry['name'],
            'initiative': current_entry['initiative'],
            'is_npc': current_entry['is_npc'],
            'status': current_entry['status']
        }

    def get_order(self, group_id: int) -> Optional[Dict]:
        """获取先攻顺序"""
        if group_id not in self._initiative_orders:
            return None
        return self._initiative_orders[group_id]

    def is_combat_active(self, group_id: int) -> bool:
        """检查是否战斗中"""
        if group_id not in self._initiative_orders:
            return False
        return len(self._initiative_orders[group_id]['entries']) > 0


# 单例模式
_initiative_manager = None

def get_initiative_manager() -> InitiativeManager:
    """获取先攻管理器单�?""
    global _initiative_manager
    if _initiative_manager is None:
        _initiative_manager = InitiativeManager()
    return _initiative_manager
