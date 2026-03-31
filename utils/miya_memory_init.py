"""
弥娅记忆系统初始化工具

提供统一的初始化接口，整合旧系统与新系统
"""

import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


async def init_miya_memory_system(
    data_dir: Union[str, Path] = "data/memory",
    redis_client=None,
    milvus_client=None,
    neo4j_client=None,
    enable_vector: bool = True,
    enable_graph: bool = True,
    short_term_ttl: int = 3600,
):
    """
    初始化弥娅记忆系统

    这是统一的初始化入口，会自动：
    1. 初始化 MiyaMemory 核心
    2. 设置数据库连接
    3. 加载已有数据

    Args:
        data_dir: 数据目录
        redis_client: Redis客户端
        milvus_client: Milvus客户端
        neo4j_client: Neo4j客户端
        enable_vector: 启用向量搜索
        enable_graph: 启用知识图谱
        short_term_ttl: 短期记忆TTL(秒)

    Returns:
        MiyaMemory 实例
    """
    from memory.miya_memory import get_miya_memory

    logger.info("=" * 50)
    logger.info("初始化弥娅统一记忆系统")
    logger.info("=" * 50)

    # 初始化
    memory = await get_miya_memory(
        data_dir=data_dir,
        redis_client=redis_client,
        milvus_client=milvus_client,
        neo4j_client=neo4j_client,
    )

    # 打印统计
    stats = await memory.get_statistics()
    logger.info(f"  对话历史: {stats.get('dialogue_count', 0)} 条")
    logger.info(f"  短期记忆: {stats.get('short_term_count', 0)} 条")
    logger.info(f"  长期记忆: {stats.get('long_term_count', 0)} 条")
    logger.info(f"  标签数量: {stats.get('tag_count', 0)}")
    logger.info(f"  用户数量: {stats.get('user_count', 0)}")

    logger.info("=" * 50)
    logger.info("✅ 记忆系统初始化完成")
    logger.info("=" * 50)

    return memory


async def init_with_auto_clients():
    """
    自动检测并初始化客户端

    自动创建 Redis、Milvus、Neo4j 客户端（如果可用）
    """
    import os
    from dotenv import load_dotenv

    load_dotenv("config/.env")

    redis_client = None
    milvus_client = None
    neo4j_client = None

    # 尝试连接 Redis
    try:
        import redis

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_password = os.getenv("REDIS_PASSWORD")

        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        redis_client.ping()
        logger.info("✅ Redis 连接成功")
    except Exception as e:
        logger.warning(f"⚠️ Redis 连接失败: {e}")

    # 尝试连接 Milvus
    try:
        from storage.milvus_client import MilvusClient

        milvus_host = os.getenv("MILVUS_HOST", "localhost")
        milvus_port = int(os.getenv("MILVUS_PORT", 19530))
        milvus_collection = os.getenv("MILVUS_COLLECTION", "miya_memory")
        milvus_dimension = int(os.getenv("MILVUS_DIMENSION", 1536))

        milvus_client = MilvusClient(
            host=milvus_host,
            port=milvus_port,
            collection_name=milvus_collection,
            dimension=milvus_dimension,
        )
        if milvus_client.connect():
            logger.info("✅ Milvus 连接成功")
        else:
            milvus_client = None
    except Exception as e:
        logger.warning(f"⚠️ Milvus 连接失败: {e}")

    # 尝试连接 Neo4j
    try:
        from storage.neo4j_client import Neo4jClient

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if neo4j_password:
            neo4j_client = Neo4jClient(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password,
            )
            if neo4j_client.connect():
                logger.info("✅ Neo4j 连接成功")
            else:
                neo4j_client = None
    except Exception as e:
        logger.warning(f"⚠️ Neo4j 连接失败: {e}")

    # 初始化记忆系统
    return await init_miya_memory_system(
        redis_client=redis_client,
        milvus_client=milvus_client,
        neo4j_client=neo4j_client,
    )


# ==================== 便捷命令 ====================


async def cmd_store(content: str, tags: list = None, user_id: str = "cli"):
    """命令行存储记忆"""
    from memory.miya_memory import store_important, get_miya_memory

    memory = await get_miya_memory()
    memory_id = await store_important(
        content=content,
        user_id=user_id,
        tags=tags or [],
    )
    print(f"✅ 已存储: {memory_id}")
    return memory_id


async def cmd_search(query: str, user_id: str = None, limit: int = 10):
    """命令行搜索记忆"""
    from memory.miya_memory import search_memory, get_miya_memory

    memory = await get_miya_memory()
    results = await search_memory(query, user_id=user_id, limit=limit)

    print(f"找到 {len(results)} 条记忆:")
    for i, mem in enumerate(results, 1):
        print(f"  {i}. [{mem.level.value}] {mem.content[:60]}...")
        if mem.tags:
            print(f"     标签: {mem.tags}")

    return results


async def cmd_stats():
    """命令行查看统计"""
    from memory.miya_memory import get_miya_memory

    memory = await get_miya_memory()
    stats = await memory.get_statistics()

    print("记忆系统统计:")
    print(f"  对话历史: {stats.get('dialogue_count', 0)} 条")
    print(f"  短期记忆: {stats.get('short_term_count', 0)} 条")
    print(f"  长期记忆: {stats.get('long_term_count', 0)} 条")
    print(f"  标签数量: {stats.get('tag_count', 0)}")
    print(f"  用户数量: {stats.get('user_count', 0)}")

    return stats


async def cmd_profile(user_id: str):
    """命令行查看用户画像"""
    from memory.miya_memory import get_miya_memory

    memory = await get_miya_memory()
    profile = await memory.get_user_profile(user_id)

    print(f"用户 {user_id} 画像:")
    print(f"  记忆总数: {profile['total_memories']}")

    if profile["preferences"]:
        print(f"  偏好 ({len(profile['preferences'])}):")
        for p in profile["preferences"][:5]:
            print(f"    - {p[:50]}")

    if profile["birthdays"]:
        print(f"  生日:")
        for b in profile["birthdays"]:
            print(f"    - {b}")

    if profile["contacts"]:
        print(f"  联系方式:")
        for c in profile["contacts"]:
            print(f"    - {c}")

    if profile["tags"]:
        print(f"  标签分布:")
        for tag, count in sorted(profile["tags"].items(), key=lambda x: -x[1])[:10]:
            print(f"    - {tag}: {count}")

    return profile


async def cmd_cleanup():
    """命令行清理过期记忆"""
    from memory.miya_memory import get_miya_memory

    memory = await get_miya_memory()
    count = await memory.clear_expired()
    print(f"✅ 清理了 {count} 条过期记忆")
    return count


# ==================== 主函数 ====================

if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("用法:")
            print("  python -m utils.miya_memory_init store <内容> [标签]")
            print("  python -m utils.miya_memory_init search <关键词>")
            print("  python -m utils.miya_memory_init stats")
            print("  python -m utils.miya_memory_init profile <用户ID>")
            print("  python -m utils.miya_memory_init cleanup")
            return

        cmd = sys.argv[1]

        if cmd == "store":
            content = sys.argv[2] if len(sys.argv) > 2 else ""
            tags = sys.argv[3].split(",") if len(sys.argv) > 3 else []
            await cmd_store(content, tags)

        elif cmd == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            await cmd_search(query)

        elif cmd == "stats":
            await cmd_stats()

        elif cmd == "profile":
            user_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"
            await cmd_profile(user_id)

        elif cmd == "cleanup":
            await cmd_cleanup()

        else:
            print(f"未知命令: {cmd}")

    asyncio.run(main())
