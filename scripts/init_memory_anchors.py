#!/usr/bin/env python3
"""
弥娅记忆锚点初始化脚本
用于将关于"佳"的重要信息预先存入记忆系统

运行方式: python scripts/init_memory_anchors.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def init_memory_anchors():
    """初始化记忆锚点"""
    print("=" * 60)
    print("弥娅记忆锚点初始化")
    print("=" * 60)
    print("\n正在初始化关于'佳'的记忆锚点...\n")

    # 记忆锚点数据 - 来自十四神格人设提示词
    memory_anchors = [
        # ========== 健康记忆 ==========
        {
            "fact": "佳有先天性心脏病，经历过心脏手术和射频消融手术",
            "tags": ["健康", "疾病", "重要"],
            "importance": 0.95,
            "category": "important",
        },
        {
            "fact": "佳先天体弱，手时常冰凉，体力较差",
            "tags": ["健康", "体质"],
            "importance": 0.85,
            "category": "important",
        },
        # ========== 生活记忆 - 饮食 ==========
        {
            "fact": "佳爱吃的菜：酸汤鱼、凉拌折耳根、牛干巴、炒螺蛳、爆炒小龙虾",
            "tags": ["喜好", "饮食", "美食"],
            "importance": 0.8,
            "category": "emotion",
        },
        {
            "fact": "佳爱喝的：椰奶、茉莉蜜茶、草莓味香飘飘",
            "tags": ["喜好", "饮品"],
            "importance": 0.75,
            "category": "emotion",
        },
        # ========== 生活记忆 - 个人偏好 ==========
        {
            "fact": "佳喜欢的颜色：青色、淡蓝色、黑色、白色",
            "tags": ["喜好", "颜色"],
            "importance": 0.75,
            "category": "emotion",
        },
        {
            "fact": "佳穿衣偏好：冲锋衣、工装等硬朗版型，配色单调",
            "tags": ["喜好", "穿着"],
            "importance": 0.7,
            "category": "emotion",
        },
        {
            "fact": "佳的睡眠习惯：侧躺，腿上夹着枕头或被子",
            "tags": ["习惯", "睡眠"],
            "importance": 0.7,
            "category": "daily",
        },
        {
            "fact": "佳的洗漱偏好：薄荷牙膏、柠檬肥皂、海盐沐浴露",
            "tags": ["喜好", "洗漱"],
            "importance": 0.65,
            "category": "daily",
        },
        {
            "fact": "佳喜欢的味道：桂花香",
            "tags": ["喜好", "香味"],
            "importance": 0.7,
            "category": "emotion",
        },
        {
            "fact": "佳喜欢泡热水澡和泡脚",
            "tags": ["习惯", "放松"],
            "importance": 0.7,
            "category": "daily",
        },
        # ========== 精神世界记忆 ==========
        {
            "fact": "佳有虚无主义倾向，会'开摆'，但对想做的事执行力极强",
            "tags": ["性格", "精神", "重要"],
            "importance": 0.9,
            "category": "important",
        },
        {
            "fact": "佳喜欢玩二游：鸣潮、战双帕弥什、原神、崩坏星穹铁道",
            "tags": ["喜好", "游戏"],
            "importance": 0.85,
            "category": "emotion",
        },
        {
            "fact": "佳喜欢写小说、cosplay、下厨",
            "tags": ["爱好", "创作"],
            "importance": 0.8,
            "category": "emotion",
        },
        {
            "fact": "佳喜欢的游戏角色：丹恒、魈、钟离、万叶、镜流、阮梅、黄泉、流萤、飞霄、卡芙卡、遐蝶、雷电将军、八重神子、宵宫、坎特雷拉、爱弥斯、守岸人、阿尔法",
            "tags": ["喜好", "角色", "游戏"],
            "importance": 0.9,
            "category": "emotion",
        },
        {
            "fact": "佳分享欲强，喜欢分享小说手稿",
            "tags": ["性格", "习惯"],
            "importance": 0.8,
            "category": "emotion",
        },
        {
            "fact": "佳喜欢优美浪漫的古诗词",
            "tags": ["喜好", "文学"],
            "importance": 0.75,
            "category": "emotion",
        },
        {
            "fact": "佳会在睡前冥想",
            "tags": ["习惯", "睡前"],
            "importance": 0.7,
            "category": "daily",
        },
        # ========== 个人信息记忆 ==========
        {
            "fact": "佳是计算机专业大学生，学习网络信息安全、人工智能、编程等",
            "tags": ["信息", "学业", "重要"],
            "importance": 0.85,
            "category": "important",
        },
        {
            "fact": "佳的生日：2005年3月20日",
            "tags": ["信息", "生日", "重要"],
            "importance": 0.95,
            "category": "important",
        },
        {
            "fact": "佳身高175cm，皮肤白，O型血",
            "tags": ["信息", "外貌"],
            "importance": 0.8,
            "category": "important",
        },
        {
            "fact": "佳的声音是标准男低音，很有磁性",
            "tags": ["信息", "声音"],
            "importance": 0.75,
            "category": "emotion",
        },
        {
            "fact": "佳的手时常冰凉",
            "tags": ["健康", "体质"],
            "importance": 0.8,
            "category": "important",
        },
    ]

    # 尝试初始化统一记忆系统
    try:
        from memory.unified_memory import get_unified_memory

        memory = get_unified_memory()

        print(f"共 {len(memory_anchors)} 条记忆锚点需要添加\n")

        success_count = 0
        for i, anchor in enumerate(memory_anchors, 1):
            try:
                # 添加记忆
                result = await memory.add(
                    content=anchor["fact"],
                    tags=anchor["tags"],
                    importance=anchor["importance"],
                    category=anchor.get("category", "important"),
                    source="system_init",
                )

                if result:
                    print(
                        f"✓ [{i}/{len(memory_anchors)}] 添加成功: {anchor['fact'][:30]}..."
                    )
                    success_count += 1
                else:
                    print(
                        f"✗ [{i}/{len(memory_anchors)}] 添加失败: {anchor['fact'][:30]}..."
                    )

            except Exception as e:
                print(
                    f"✗ [{i}/{len(memory_anchors)}] 错误: {anchor['fact'][:30]}... - {e}"
                )

        print("\n" + "=" * 60)
        print(f"记忆锚点初始化完成: {success_count}/{len(memory_anchors)} 条成功")
        print("=" * 60)

    except ImportError as e:
        print(f"\n⚠ 无法导入统一记忆系统: {e}")
        print("请确保已正确配置数据库连接\n")

        # 打印记忆锚点供手动添加
        print("\n以下是待添加的记忆锚点（可手动添加到数据库）：")
        print("-" * 60)
        for anchor in memory_anchors:
            print(f"事实: {anchor['fact']}")
            print(f"标签: {anchor['tags']}")
            print(f"重要性: {anchor['importance']}")
            print("-" * 60)

    except Exception as e:
        print(f"\n⚠ 初始化过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(init_memory_anchors())
