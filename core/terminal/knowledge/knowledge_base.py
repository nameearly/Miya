#!/usr/bin/env python3
"""
统一的知识库

整合现有的知识查询、搜索和添加功能
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import sqlite3
from datetime import datetime

from ..base.interfaces import IKnowledgeBase
from ..base.types import CommandAnalysis, KnowledgeItem, KnowledgeQuery

logger = logging.getLogger(__name__)


class KnowledgeBase(IKnowledgeBase):
    """统一知识库"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化知识库
        
        Args:
            db_path: SQLite数据库路径，默认为 'data/knowledge.db'
        """
        self.logger = logging.getLogger(__name__)
        
        if db_path:
            self.db_path = db_path
        else:
            # 默认路径
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "knowledge.db")
        
        self._init_database()
        self._load_existing_knowledge()
        
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建知识表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    source TEXT,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items (category)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tags ON knowledge_items (tags)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_priority ON knowledge_items (priority)
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"知识库数据库初始化完成: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
    
    def _load_existing_knowledge(self):
        """加载现有知识"""
        # 这里可以加载现有的知识文件
        self.logger.info("知识库准备就绪")
    
    def query(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """
        查询知识
        
        Args:
            query: 查询条件
            
        Returns:
            匹配的知识项列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建查询
            sql = "SELECT * FROM knowledge_items WHERE "
            params = []
            
            conditions = []
            
            if query.keywords:
                keyword_conditions = []
                for keyword in query.keywords:
                    keyword_conditions.append("(title LIKE ? OR content LIKE ? OR tags LIKE ?)")
                    params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
                
                if keyword_conditions:
                    conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            if query.category:
                conditions.append("category = ?")
                params.append(query.category)
            
            if query.tags:
                tag_conditions = []
                for tag in query.tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                
                if tag_conditions:
                    conditions.append(f"({' OR '.join(tag_conditions)})")
            
            if not conditions:
                # 如果没有条件，返回空
                conn.close()
                return []
            
            sql += " AND ".join(conditions)
            sql += " ORDER BY priority DESC, updated_at DESC"
            
            if query.limit:
                sql += f" LIMIT {query.limit}"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # 转换为KnowledgeItem
            results = []
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    category=row[3],
                    tags=row[4] if row[4] else [],
                    source=row[5],
                    priority=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                    metadata=json.loads(row[9]) if row[9] else {}
                )
                results.append(item)
            
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"查询知识失败: {e}")
            return []
    
    def add(self, item: KnowledgeItem) -> bool:
        """
        添加知识项
        
        Args:
            item: 知识项
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 转换为数据库格式
            tags_str = ",".join(item.tags) if item.tags else ""
            metadata_str = json.dumps(item.metadata) if item.metadata else "{}"
            
            cursor.execute('''
                INSERT INTO knowledge_items 
                (title, content, category, tags, source, priority, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.title,
                item.content,
                item.category,
                tags_str,
                item.source,
                item.priority,
                metadata_str
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加知识项: {item.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加知识项失败: {e}")
            return False
    
    def delete(self, item_id: int) -> bool:
        """
        删除知识项
        
        Args:
            item_id: 知识项ID
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM knowledge_items WHERE id = ?
            ''', (item_id,))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            if deleted:
                self.logger.info(f"删除知识项 ID: {item_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"删除知识项失败: {e}")
            return False
    
    def search(self, keyword: str, category: Optional[str] = None) -> List[KnowledgeItem]:
        """
        搜索知识
        
        Args:
            keyword: 关键词
            category: 可选分类
            
        Returns:
            匹配的知识项列表
        """
        # 使用query方法
        query = KnowledgeQuery(keywords=[keyword])
        if category:
            query.category = category
        
        return self.query(query)
    
    def get_for_command(self, command_analysis: CommandAnalysis) -> List[KnowledgeItem]:
        """
        获取与命令相关的知识
        
        Args:
            command_analysis: 命令分析结果
            
        Returns:
            相关的知识项列表
        """
        # 基于命令意图和分类查找相关知识
        keywords = []
        
        # 添加命令本身
        if command_analysis.command:
            keywords.append(command_analysis.command)
        
        # 添加命令参数
        if command_analysis.parameters:
            for param in command_analysis.parameters:
                if len(param) < 20:  # 避免过长的参数
                    keywords.append(param)
        
        # 添加命令分类
        if command_analysis.category:
            keywords.append(command_analysis.category.value)
        
        # 添加命令意图
        if command_analysis.intent:
            keywords.append(command_analysis.intent.value)
        
        # 执行查询
        return self.query(KnowledgeQuery(keywords=keywords, limit=5))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总知识项数
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            total_count = cursor.fetchone()[0]
            
            # 分类统计
            cursor.execute("SELECT category, COUNT(*) FROM knowledge_items GROUP BY category")
            category_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "total_items": total_count,
                "category_stats": category_stats,
                "database_path": self.db_path
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def backup(self, backup_path: Optional[str] = None) -> bool:
        """
        备份知识库
        
        Args:
            backup_path: 备份路径
            
        Returns:
            是否成功
        """
        try:
            if not backup_path:
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = str(backup_dir / f"knowledge_backup_{timestamp}.db")
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"知识库已备份到: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份知识库失败: {e}")
            return False
    
    # 以下是实现 IKnowledgeBase 接口的抽象方法
    
    def learn_from_execution(self, command: str, analysis: CommandAnalysis, result: CommandResult):
        """从执行中学习"""
        try:
            # 提取命令模式
            command_parts = command.split()
            if len(command_parts) >= 1:
                base_command = command_parts[0]
                
                # 记录命令执行
                self.logger.debug(f"学习命令执行: {command} (成功: {result.success})")
                
                # 这里可以添加更复杂的学习逻辑
                # 例如：记录命令频率、成功率、执行时间等
                
                # 简化实现：只记录日志
                if result.success:
                    self.logger.info(f"成功执行命令已记录: {command}")
                else:
                    self.logger.info(f"失败执行命令已记录: {command} - 错误: {result.error}")
        
        except Exception as e:
            self.logger.error(f"学习执行失败: {e}")
    
    def get_user_patterns(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取用户模式"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT command_pattern, usage_count, success_count, 
                           avg_execution_time, last_used
                    FROM user_patterns 
                    WHERE user_id = ?
                    ORDER BY usage_count DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT command_pattern, usage_count, success_count, 
                           avg_execution_time, last_used
                    FROM user_patterns 
                    ORDER BY usage_count DESC
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            patterns = {}
            for row in rows:
                pattern = {
                    'command_pattern': row[0],
                    'usage_count': row[1],
                    'success_count': row[2],
                    'avg_execution_time': row[3],
                    'last_used': row[4]
                }
                patterns[row[0]] = pattern
            
            return patterns
        
        except sqlite3.OperationalError:
            # 表可能不存在
            return {}
        except Exception as e:
            self.logger.error(f"获取用户模式失败: {e}")
            return {}
    
    def get_suggestions(self, context: str, limit: int = 5) -> List[str]:
        """获取智能建议"""
        try:
            # 简单实现：基于上下文关键词搜索知识库
            from ..base.types import KnowledgeQuery
            
            query = KnowledgeQuery(
                keywords=[context],
                limit=limit
            )
            
            results = self.query(query)
            
            # 提取建议
            suggestions = []
            for item in results:
                if len(item.content) > 100:
                    suggestion = f"{item.title}: {item.content[:100]}..."
                else:
                    suggestion = f"{item.title}: {item.content}"
                
                suggestions.append(suggestion)
            
            return suggestions
        
        except Exception as e:
            self.logger.error(f"获取建议失败: {e}")
            return []
    
    def get_common_commands(self, category: Optional[str] = None) -> List[str]:
        """获取常用命令"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT command, COUNT(*) as count
                    FROM command_history
                    WHERE category = ?
                    GROUP BY command
                    ORDER BY count DESC
                    LIMIT 10
                ''', (category,))
            else:
                cursor.execute('''
                    SELECT command, COUNT(*) as count
                    FROM command_history
                    GROUP BY command
                    ORDER BY count DESC
                    LIMIT 10
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            common_commands = [row[0] for row in rows]
            return common_commands
        
        except sqlite3.OperationalError:
            # 表可能不存在
            return []
        except Exception as e:
            self.logger.error(f"获取常用命令失败: {e}")
            return []
    
    def save_knowledge(self, filepath: str):
        """保存知识库到文件"""
        try:
            # 导出所有知识项到JSON文件
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM knowledge_items')
            rows = cursor.fetchall()
            
            # 转换为字典列表
            knowledge_data = []
            for row in rows:
                item = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'category': row[3],
                    'tags': row[4].split(',') if row[4] else [],
                    'source': row[5],
                    'priority': row[6],
                    'created_at': row[7],
                    'updated_at': row[8],
                    'metadata': json.loads(row[9]) if row[9] else {}
                }
                knowledge_data.append(item)
            
            conn.close()
            
            # 保存到JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"知识库已保存到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存知识库失败: {e}")
            raise
    
    def load_knowledge(self, filepath: str):
        """从文件加载知识库"""
        try:
            # 从JSON文件加载
            with open(filepath, 'r', encoding='utf-8') as f:
                knowledge_data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 清空现有数据
            cursor.execute('DELETE FROM knowledge_items')
            
            # 插入新数据
            for item in knowledge_data:
                tags_str = ','.join(item.get('tags', []))
                metadata_str = json.dumps(item.get('metadata', {}))
                
                cursor.execute('''
                    INSERT INTO knowledge_items 
                    (title, content, category, tags, source, priority, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['title'],
                    item['content'],
                    item.get('category'),
                    tags_str,
                    item.get('source', 'import'),
                    item.get('priority', 1),
                    metadata_str
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"知识库已从文件加载: {filepath}")
            
        except Exception as e:
            self.logger.error(f"加载知识库失败: {e}")
            raise


# 单例实例
_global_knowledge_base: Optional[KnowledgeBase] = None

def get_knowledge_base() -> KnowledgeBase:
    """获取全局知识库实例"""
    global _global_knowledge_base
    
    if _global_knowledge_base is None:
        _global_knowledge_base = KnowledgeBase()
    
    return _global_knowledge_base