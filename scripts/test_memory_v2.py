#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弥娅统一记忆系统 v2.0 测试脚本

测试统一记忆系统的所有功能：
1. 短期记忆（持久化）
2. 认知记忆（语义向量）
3. 长期记忆（史官改写）
4. 置顶备忘
5. 用户/群侧写
6. 语义搜索
"""

import asyncio
import os
import sys
import shutil
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def clean_test_data():
    """清理测试数据"""
    test_dir = project_root / "data" / "test_memory"
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("[清理] 测试数据已清理")


def test_memory_system():
    """测试统一记忆系统"""
    from memory.unified_memory import (
        UnifiedMemoryManager,
        MemoryType,
        get_unified_memory,
    )

    print("\n" + "=" * 60)
    print("弥娅统一记忆系统 v2.0 测试")
    print("=" * 60 + "\n")

    async def run_tests():
        memory = get_unified_memory(
            data_dir="data/test_memory",
            config={
                "embedding": {"provider": "local"},
                "historian_enabled": True,
                "max_short_term": 50,
                "max_cognitive": 200,
                "profile_max_lines": 500,
            },
        )

        print("[1/7] 初始化记忆系统...")
        await memory.initialize()
        stats = memory.get_stats()
        print(f"       向量维度: {stats['embedding_dimension']}")
        print(f"       史官启用: {stats['historian_enabled']}")

        print("\n[2/7] 测试短期记忆...")
        st_id1 = await memory.add_short_term(
            content="用户说他喜欢Python编程", user_id="test_user_1", priority=0.6
        )
        st_id2 = await memory.add_short_term(
            content="今天天气很好", user_id="test_user_1", priority=0.4
        )
        st_id3 = await memory.add_short_term(
            content="用户提到想要学习机器学习", user_id="test_user_1", priority=0.7
        )
        print(f"       添加了 3 条短期记忆")
        short_memories = memory.get_short_term()
        print(f"       当前短期记忆: {len(short_memories)} 条")

        print("\n[3/7] 测试认知记忆...")
        cg_id1 = await memory.add_cognitive(
            content="用户对编程有浓厚兴趣，特别是Python和机器学习",
            observations=[
                "用户提到喜欢Python编程",
                "用户说想学机器学习",
                "用户问了一些关于AI的问题",
            ],
            user_id="test_user_1",
            priority=0.8,
        )
        cg_id2 = await memory.add_cognitive(
            content="用户在讨论游戏相关话题",
            observations=["用户问了一些游戏问题", "用户提到喜欢玩RPG游戏"],
            user_id="test_user_2",
            priority=0.5,
        )
        print(f"       添加了 2 条认知记忆")

        print("\n[4/7] 测试置顶备忘...")
        await memory.add_pinned("重要提醒", "记得回复用户关于代码的问题")
        await memory.add_pinned("待办", "优化对话生成逻辑")
        pinned = memory.get_pinned()
        print(f"       置顶备忘: {list(pinned.keys())}")

        print("\n[5/7] 测试语义搜索...")
        queries = [
            "用户喜欢什么编程语言",
            "机器学习相关内容",
            "游戏话题",
        ]
        for query in queries:
            results = await memory.search(query, top_k=3)
            print(f'       查询 "{query}":')
            for r in results[:2]:
                content = r.content[:40] + "..." if len(r.content) > 40 else r.content
                print(f"         - [{r.memory_type.value}] {content}")

        print("\n[6/7] 测试用户侧写...")
        profile = memory.get_user_profile("test_user_1")
        if profile:
            lines = profile.split("\n")
            print(f"       用户侧写: {len(lines)} 行")
        else:
            print("       用户侧写: (等待史官处理)")

        print("\n[7/7] 最终统计...")
        final_stats = memory.get_stats()
        print(f"       短期记忆: {final_stats['short_term_count']}")
        print(f"       认知记忆: {final_stats['cognitive_count']}")
        print(f"       长期记忆: {final_stats['long_term_count']}")
        print(f"       置顶备忘: {final_stats['pinned_count']}")
        print(f"       用户侧写: {final_stats['user_profiles_count']}")
        print(f"       群组侧写: {final_stats['group_profiles_count']}")

        print("\n[清理] 保存并清理...")
        await memory.cleanup()

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

    asyncio.run(run_tests())


def main():
    try:
        clean_test_data()
        test_memory_system()
    except KeyboardInterrupt:
        print("\n测试被中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
