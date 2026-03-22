#!/usr/bin/env python3
"""
清理旧的缓存模块并更新导入

这个脚本将：
1. 删除旧的缓存模块文件
2. 检查项目中是否有导入旧缓存模块的代码
3. 提供迁移建议
"""

import os
import re
from pathlib import Path

# 要删除的旧缓存模块
OLD_CACHE_FILES = [
    "core/cache_manager.py",
    "core/prompt_cache.py",
]

# 要检查的目录
CHECK_DIRS = [
    "core",
    "tests",
    "scripts",
]

# 旧导入模式
OLD_IMPORT_PATTERNS = [
    r"from\s+core\.cache_manager\b",
    r"from\s+core\.prompt_cache\b",
    r"import\s+core\.cache_manager\b",
    r"import\s+core\.prompt_cache\b",
]


def delete_old_cache_files() -> None:
    """删除旧的缓存模块文件"""
    print("\n=== 删除旧的缓存模块文件 ===")
    
    deleted = 0
    for file_path in OLD_CACHE_FILES:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[DELETED] {file_path}")
                deleted += 1
            except Exception as e:
                print(f"[ERROR] 删除 {file_path} 失败: {e}")
        else:
            print(f"[INFO] 文件不存在: {file_path}")
    
    print(f"\n总计删除了 {deleted} 个旧缓存文件。")


def find_old_imports() -> None:
    """查找项目中导入旧缓存模块的代码"""
    print("\n=== 查找导入旧缓存模块的代码 ===")
    
    found_files = []
    
    for check_dir in CHECK_DIRS:
        if not os.path.exists(check_dir):
            continue
            
        for root, dirs, files in os.walk(check_dir):
            # 跳过 __pycache__ 目录
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        for pattern in OLD_IMPORT_PATTERNS:
                            if re.search(pattern, content):
                                found_files.append(file_path)
                                print(f"[FOUND] {file_path} 包含旧缓存导入")
                                break
                                
                    except Exception as e:
                        print(f"[ERROR] 读取 {file_path} 失败: {e}")
    
    if found_files:
        print(f"\n总计找到 {len(found_files)} 个文件包含旧缓存导入:")
        for file in found_files:
            print(f"  - {file}")
    else:
        print("\n[INFO] 未找到导入旧缓存模块的代码。")


def show_migration_guide() -> None:
    """显示迁移指南"""
    print("\n=== 迁移指南 ===")
    print("""
如果您在项目中使用了旧的缓存模块，请按照以下步骤迁移到新的统一缓存系统：

1. 更新导入语句：
   旧代码：
       from core.cache_manager import CacheManager
       from core.prompt_cache import PromptCache
   
   新代码：
       # 使用统一缓存系统
       from core.cache import get_cache
       cache = get_cache("my_cache")
       
       # 或者使用适配器（保持兼容性）
       from core.cache import get_cache_manager, get_global_prompt_cache
       cache_manager = get_cache_manager()
       prompt_cache = get_global_prompt_cache()

2. 更新缓存使用方式：
   旧代码：
       cache_manager = CacheManager()
       cache_manager.set("key", "value")
       value = cache_manager.get("key")
   
   新代码：
       cache = get_cache("my_cache")
       await cache.set("key", "value", ttl=3600)
       value = await cache.get("key")

3. 更新装饰器：
   旧代码：
       from core.cache_manager import cached_decorator
       @cached_decorator(ttl=300)
       def my_function():
           return result
   
   新代码：
       from core.cache import cached
       @cached(cache_type="memory", ttl=300)
       async def my_function():
           return result

详细迁移指南请参考 CACHE_MIGRATION_GUIDE.md 文件。
""")


def main() -> None:
    """主函数"""
    print("弥娅缓存系统清理工具")
    print("=" * 50)
    
    # 删除旧文件
    delete_old_cache_files()
    
    # 查找旧导入
    find_old_imports()
    
    # 显示迁移指南
    show_migration_guide()
    
    print("\n=== 清理完成 ===")
    print("旧的缓存模块已清理。请参考迁移指南更新您的代码。")


if __name__ == "__main__":
    main()
