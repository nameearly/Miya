"""
弥娅记忆可视化工具

生成记忆系统的可视化报告

使用方式:
    python -m utils.memory_visualize              # 查看概览
    python -m utils.memory_visualize --user 123   # 查看用户记忆
    python -m utils.memory_visualize --html      # 生成HTML报告
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


async def get_memory_data():
    """获取记忆数据"""
    from memory import get_memory_core, reset_memory_core

    reset_memory_core()
    core = await get_memory_core("data/memory")

    stats = await core.get_statistics()

    # 获取所有记忆
    all_memories = await core.retrieve(query="", limit=10000)

    return core, stats, all_memories


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_stats(stats: Dict):
    """打印统计信息"""
    print_header("Memory System Overview")

    print(f"\n[TOTAL] Memories: {stats.get('total_cached', 0)}")
    print(f"[INDEX] Indexed: {stats.get('total_indexed', 0)}")
    print(f"[USERS] Users: {stats.get('by_user', 0)}")
    print(f"[TAGS] Tags: {stats.get('by_tag', 0)}")

    print("\n[LEVEL] Distribution:")
    by_level = stats.get("by_level", {})
    total = sum(by_level.values())

    bar_width = 30
    for level, count in sorted(by_level.items(), key=lambda x: -x[1]):
        pct = (count / total * 100) if total > 0 else 0
        filled = int(bar_width * count / max(total, 1))
        bar = "#" * filled + "-" * (bar_width - filled)
        print(f"  {level:12} [{bar}] {count:4} ({pct:5.1f}%)")


def print_user_summary(memories: List):
    """打印用户摘要"""
    print_header("User Memory Summary")

    # 按用户分组
    by_user = defaultdict(list)
    for mem in memories:
        by_user[mem.user_id].append(mem)

    # 排序
    users = sorted(by_user.items(), key=lambda x: -len(x[1]))

    for user_id, mems in users[:10]:
        level_counts = defaultdict(int)
        for m in mems:
            level_counts[m.level.value] += 1

        levels = " | ".join(f"{k}:{v}" for k, v in level_counts.items())
        print(f"\n[USER] {user_id}")
        print(f"   Count: {len(mems)} | {levels}")


def print_tag_cloud(memories: List):
    """打印标签云"""
    print_header("Tag Cloud")

    # 统计标签
    tag_counts = defaultdict(int)
    for mem in memories:
        for tag in mem.tags:
            tag_counts[tag] += 1

    # 排序
    tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:30]

    if not tags:
        print("\n[No tags found]")
        return

    for i in range(0, len(tags), 3):
        row = []
        for j in range(3):
            if i + j < len(tags):
                tag, count = tags[i + j]
                row.append(f"{tag}({count})")
            else:
                row.append(" " * 20)
        print("  " + " | ".join(f"{s:20}" for s in row))


def print_recent_memories(memories: List, limit: int = 20):
    """打印最近记忆"""
    print_header(f"Recent {limit} Memories")

    # 按时间排序
    sorted_memories = sorted(memories, key=lambda x: x.created_at, reverse=True)[:limit]

    for i, mem in enumerate(sorted_memories, 1):
        # 截断内容
        content = mem.content[:50] + "..." if len(mem.content) > 50 else mem.content
        tags_str = " ".join(f"[{t}]" for t in mem.tags[:3])

        print(f"\n{i:2}. [{mem.level.value}] {content}")
        print(f"    [USER]{mem.user_id} | {tags_str}")


def print_user_detail(memories: List, user_id: str):
    """打印用户详情"""
    print_header(f"User '{user_id}' Memory")

    user_mems = [m for m in memories if m.user_id == user_id]

    if not user_mems:
        print(f"\n[Not found] User '{user_id}'")
        return

    print(f"\n[Total] {len(user_mems)} memories\n")

    # 按层级分组
    by_level = defaultdict(list)
    for mem in user_mems:
        by_level[mem.level.value].append(mem)

    for level, mems in sorted(by_level.items()):
        print(f"\n[LEVEL] {level} ({len(mems)} items):")

        # 显示前5条
        for mem in mems[:5]:
            content = mem.content[:60] + "..." if len(mem.content) > 60 else mem.content
            print(f"   - {content}")

        if len(mems) > 5:
            print(f"   ... and {len(mems) - 5} more")


async def generate_html_report(memories: List, stats: Dict):
    """生成HTML报告"""
    print("\n正在生成HTML报告...")

    # 准备数据
    by_user = defaultdict(list)
    by_tag = defaultdict(int)
    by_level = defaultdict(int)

    for mem in memories:
        by_user[mem.user_id].append(mem)
        for tag in mem.tags:
            by_tag[tag] += 1
        by_level[mem.level.value] += 1

    # 按时间排序
    sorted_memories = sorted(memories, key=lambda x: x.created_at, reverse=True)

    html = (
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>弥娅记忆系统可视化</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        
        h1 { 
            text-align: center; 
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #00d9ff;
        }
        
        .stat-card .label { color: #888; margin-top: 5px; }
        
        .section {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .section h2 { 
            color: #00ff88; 
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .level-bar {
            display: flex;
            align-items: center;
            margin: 15px 0;
        }
        
        .level-bar .name {
            width: 120px;
            color: #888;
        }
        
        .level-bar .bar-container {
            flex: 1;
            height: 24px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            overflow: hidden;
            margin: 0 15px;
        }
        
        .level-bar .bar {
            height: 100%;
            border-radius: 12px;
            transition: width 0.5s ease;
        }
        
        .level-bar .count {
            width: 60px;
            text-align: right;
            color: #00d9ff;
        }
        
        .memory-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .memory-item {
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            border-left: 3px solid #00d9ff;
        }
        
        .memory-item .meta {
            display: flex;
            gap: 15px;
            margin-top: 8px;
            font-size: 0.85em;
            color: #888;
        }
        
        .memory-item .level-dialogue { border-color: #00d9ff; }
        .memory-item .level-short_term { border-color: #ff9500; }
        .memory-item .level-long_term { border-color: #00ff88; }
        .memory-item .level-semantic { border-color: #af52de; }
        .memory-item .level-knowledge { border-color: #ff2d55; }
        
        .tag {
            display: inline-block;
            padding: 3px 10px;
            background: rgba(0,217,255,0.2);
            border-radius: 15px;
            font-size: 0.8em;
            margin: 2px;
        }
        
        .user-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .user-card {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
        }
        
        .user-card .name { color: #00d9ff; font-weight: bold; }
        .user-card .count { color: #888; font-size: 0.9em; }
        
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 弥娅记忆系统可视化</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">"""
        + str(stats.get("total_cached", 0))
        + """</div>
                <div class="label">总记忆数</div>
            </div>
            <div class="stat-card">
                <div class="number">"""
        + str(stats.get("by_user", 0))
        + """</div>
                <div class="label">用户数</div>
            </div>
            <div class="stat-card">
                <div class="number">"""
        + str(stats.get("by_tag", 0))
        + """</div>
                <div class="label">标签数</div>
            </div>
            <div class="stat-card">
                <div class="number">"""
        + str(sum(by_level.values()))
        + """</div>
                <div class="label">层级总数</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 记忆层级分布</h2>
"""
    )

    # 层级分布
    colors = {
        "dialogue": "#00d9ff",
        "short_term": "#ff9500",
        "long_term": "#00ff88",
        "semantic": "#af52de",
        "knowledge": "#ff2d55",
    }

    total = sum(by_level.values())
    for level, count in sorted(by_level.items(), key=lambda x: -x[1]):
        pct = (count / total * 100) if total > 0 else 0
        color = colors.get(level, "#00d9ff")
        html += f"""
            <div class="level-bar">
                <div class="name">{level}</div>
                <div class="bar-container">
                    <div class="bar" style="width: {pct}%; background: {color};"></div>
                </div>
                <div class="count">{count} ({pct:.1f}%)</div>
            </div>
"""

    # 最近记忆
    html += """
        </div>
        
        <div class="section">
            <h2>📝 最近记忆</h2>
            <div class="memory-list">
"""

    for mem in sorted_memories[:50]:
        content = (
            mem.content.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
        )
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in mem.tags[:5])

        html += f"""
                <div class="memory-item level-{mem.level.value}">
                    <div>{content[:200]}</div>
                    <div class="meta">
                        <span>👤 {mem.user_id}</span>
                        <span>📁 {mem.level.value}</span>
                        <span>⏰ {mem.created_at[:19]}</span>
                    </div>
                    <div style="margin-top: 8px;">{tags_html}</div>
                </div>
"""

    # 用户分布
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>👥 用户分布</h2>
            <div class="user-grid">
"""

    for user_id, mems in sorted(by_user.items(), key=lambda x: -len(x[1]))[:20]:
        level_counts = defaultdict(int)
        for m in mems:
            level_counts[m.level.value] += 1
        level_str = ", ".join(f"{k}:{v}" for k, v in level_counts.items())
        html += f"""
                <div class="user-card">
                    <div class="name">{user_id}</div>
                    <div class="count">{len(mems)} 条记忆 ({level_str})</div>
                </div>
"""

    html += (
        """
            </div>
        </div>
        
        <div class="footer">
            生成时间: """
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        + """
        </div>
    </div>
</body>
</html>
"""
    )

    # 保存文件
    output_path = Path("data/memory/visualization.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[OK] HTML report generated: {output_path.absolute()}")
    print(f"   Please open in browser")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="弥娅记忆可视化")
    parser.add_argument("--user", type=str, help="查看指定用户的记忆")
    parser.add_argument("--html", action="store_true", help="生成HTML报告")
    parser.add_argument("--recent", type=int, default=20, help="显示最近N条")
    args = parser.parse_args()

    print("正在加载记忆数据...")
    core, stats, memories = await get_memory_data()

    if args.html:
        await generate_html_report(memories, stats)
        return

    if args.user:
        print_user_detail(memories, args.user)
        return

    # 默认显示概览
    print_stats(stats)
    print_user_summary(memories)
    print_tag_cloud(memories)
    print_recent_memories(memories, args.recent)

    print("\n" + "=" * 60)
    print("提示: 使用 --html 生成可视化网页")
    print("      使用 --user <用户ID> 查看特定用户")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
