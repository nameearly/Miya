"""
弥娅记忆系统初始化工具

自动检测并连接 Redis / Milvus / Neo4j 服务

使用方法:
    python -m utils.memory_init
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class MemoryServiceManager:
    """记忆服务管理器"""

    def __init__(self):
        self.redis_client = None
        self.milvus_client = None
        self.neo4j_client = None
        self.config: Dict[str, Any] = {}

    async def initialize(self) -> Dict[str, bool]:
        """初始化所有服务"""
        logger.info("=" * 60)
        logger.info("弥娅记忆系统 - 服务初始化")
        logger.info("=" * 60)

        results = {}

        # 加载配置
        await self._load_config()

        # 连接各服务
        results["redis"] = await self._connect_redis()
        results["milvus"] = await self._connect_milvus()
        results["neo4j"] = await self._connect_neo4j()

        # 汇总
        logger.info("\n" + "=" * 60)
        logger.info("初始化结果:")
        logger.info("=" * 60)
        for service, connected in results.items():
            status = "✅ 已连接" if connected else "❌ 未连接"
            logger.info(f"  {service.upper():10} {status}")

        total = sum(results.values())
        logger.info(f"\n  总计: {total}/3 服务已连接")

        return results

    async def _load_config(self):
        """加载配置"""
        # 尝试加载 .env
        env_file = Path("config/.env")
        if env_file.exists():
            from dotenv import load_dotenv

            load_dotenv(env_file)

        self.config = {
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
                "db": int(os.getenv("REDIS_DB", 0)),
                "password": os.getenv("REDIS_PASSWORD"),
            },
            "milvus": {
                "host": os.getenv("MILVUS_HOST", "localhost"),
                "port": int(os.getenv("MILVUS_PORT", 19530)),
                "collection": os.getenv("MILVUS_COLLECTION", "miya_memory"),
                "dimension": int(os.getenv("MILVUS_DIMENSION", 1536)),
            },
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j"),
            },
        }

        logger.info("\n[配置] 已加载配置:")
        logger.info(
            f"  Redis: {self.config['redis']['host']}:{self.config['redis']['port']}"
        )
        logger.info(
            f"  Milvus: {self.config['milvus']['host']}:{self.config['milvus']['port']}"
        )
        logger.info(f"  Neo4j: {self.config['neo4j']['uri']}")

    async def _connect_redis(self) -> bool:
        """连接 Redis"""
        logger.info("\n[Redis] 正在连接...")

        try:
            import redis

            cfg = self.config["redis"]
            self.redis_client = redis.Redis(
                host=cfg["host"],
                port=cfg["port"],
                db=cfg["db"],
                password=cfg["password"],
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # 测试连接
            self.redis_client.ping()
            logger.info(f"[Redis] ✅ 连接成功")

            # 测试基本操作
            self.redis_client.setex("test_key", 10, "test_value")
            test_val = self.redis_client.get("test_key")
            self.redis_client.delete("test_key")

            logger.info(f"[Redis] ✅ 读写测试通过")
            return True

        except ImportError:
            logger.warning(f"[Redis] ⚠️ redis-py 未安装 (pip install redis)")
            return False
        except Exception as e:
            logger.warning(f"[Redis] ❌ 连接失败: {str(e)[:50]}")
            return False

    async def _connect_milvus(self) -> bool:
        """连接 Milvus"""
        logger.info("\n[Milvus] 正在连接...")

        try:
            from pymilvus import connections, Collection, utility

            cfg = self.config["milvus"]

            # 连接
            alias = "default"
            connections.connect(
                alias=alias,
                host=cfg["host"],
                port=cfg["port"],
                timeout=10,
            )

            # 检查集合
            if utility.has_collection(cfg["collection"]):
                self.milvus_client = Collection(cfg["collection"], using=alias)
                self.milvus_client.load()
                logger.info(f"[Milvus] ✅ 集合 '{cfg['collection']}' 已存在")
            else:
                # 创建集合
                from pymilvus import CollectionSchema, FieldSchema, DataType

                fields = [
                    FieldSchema(
                        name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
                    ),
                    FieldSchema(
                        name="memory_id", dtype=DataType.VARCHAR, max_length=64
                    ),
                    FieldSchema(
                        name="vector", dtype=DataType.FLOAT_VECTOR, dim=cfg["dimension"]
                    ),
                    FieldSchema(
                        name="content", dtype=DataType.VARCHAR, max_length=4096
                    ),
                    FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
                ]

                schema = CollectionSchema(
                    fields=fields, description="Miya Memory Vector Store"
                )
                self.milvus_client = Collection(
                    name=cfg["collection"], schema=schema, using=alias
                )

                # 创建索引
                index_params = {
                    "index_type": "IVF_FLAT",
                    "metric_type": "L2",
                    "params": {"nlist": 128},
                }
                self.milvus_client.create_index(
                    field_name="vector", index_params=index_params
                )
                self.milvus_client.load()

                logger.info(f"[Milvus] ✅ 集合 '{cfg['collection']}' 已创建")

            return True

        except ImportError:
            logger.warning(f"[Milvus] ⚠️ pymilvus 未安装 (pip install pymilvus)")
            return False
        except Exception as e:
            logger.warning(f"[Milvus] ❌ 连接失败: {str(e)[:80]}")
            return False

    async def _connect_neo4j(self) -> bool:
        """连接 Neo4j"""
        logger.info("\n[Neo4j] 正在连接...")

        try:
            from neo4j import GraphDatabase

            cfg = self.config["neo4j"]

            if not cfg["password"]:
                logger.warning(f"[Neo4j] ⚠️ 未配置密码")
                return False

            self.neo4j_client = GraphDatabase.driver(
                cfg["uri"],
                auth=(cfg["user"], cfg["password"]),
                max_connection_lifetime=3600,
            )

            # 测试连接
            with self.neo4j_client.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()

            logger.info(f"[Neo4j] ✅ 连接成功")
            return True

        except ImportError:
            logger.warning(f"[Neo4j] ⚠️ neo4j-driver 未安装 (pip install neo4j)")
            return False
        except Exception as e:
            logger.warning(f"[Neo4j] ❌ 连接失败: {str(e)[:80]}")
            return False

    def get_memory_core_kwargs(self) -> Dict[str, Any]:
        """获取传递给 MiyaMemoryCore 的参数"""
        return {
            "redis_client": self.redis_client,
            "milvus_client": self.milvus_client,
            "neo4j_client": self.neo4j_client,
        }


async def init_memory_system_with_services():
    """初始化记忆系统并连接所有服务"""
    manager = MemoryServiceManager()
    results = await manager.initialize()

    if not any(results.values()):
        logger.warning("\n⚠️ 没有可用的扩展服务，将使用本地JSON存储")
        return None, results

    # 初始化记忆系统
    from memory import get_memory_core

    core = await get_memory_core(
        data_dir="data/memory", **manager.get_memory_core_kwargs()
    )

    logger.info("\n✅ 记忆系统初始化完成!")

    return core, results


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="弥娅记忆系统初始化")
    parser.add_argument("--check", action="store_true", help="仅检查服务状态")
    args = parser.parse_args()

    if args.check:
        manager = MemoryServiceManager()
        await manager._load_config()
        results = {}
        results["redis"] = await manager._connect_redis()
        results["milvus"] = await manager._connect_milvus()
        results["neo4j"] = await manager._connect_neo4j()

        print("\n服务状态:")
        for svc, ok in results.items():
            print(f"  {svc}: [OK]" if ok else f"  {svc}: [FAIL]")
    else:
        await init_memory_system_with_services()


if __name__ == "__main__":
    asyncio.run(main())
