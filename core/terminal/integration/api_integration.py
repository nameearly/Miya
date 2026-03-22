#!/usr/bin/env python3
"""
终端API集成

统一整合弥娅的API功能
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

from ..base.types import CommandResult, CommandAnalysis
from ..parser import get_command_parser
from ..executor import get_intelligent_executor
from ..safety import get_safety_checker
from ..knowledge import get_knowledge_base

logger = logging.getLogger(__name__)


@dataclass
class APIRequest:
    """API请求"""
    method: str
    endpoint: str
    data: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class APIResponse:
    """API响应"""
    status: int
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    headers: Dict[str, str] = field(default_factory=dict)


class APIIntegration:
    """API集成"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.command_parser = get_command_parser()
        self.executor = get_intelligent_executor()
        self.safety_checker = get_safety_checker()
        self.knowledge_base = get_knowledge_base()
        
        # API处理器映射
        self.api_handlers: Dict[str, Callable] = {
            "/terminal/execute": self.handle_terminal_execute,
            "/terminal/analyze": self.handle_terminal_analyze,
            "/terminal/status": self.handle_terminal_status,
            "/knowledge/query": self.handle_knowledge_query,
            "/knowledge/add": self.handle_knowledge_add,
            "/safety/check": self.handle_safety_check,
            "/system/stats": self.handle_system_stats,
        }
        
        # API统计
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "endpoint_stats": {}
        }
        
        self.logger.info("API集成初始化完成")
    
    async def handle_request(self, request: APIRequest) -> APIResponse:
        """
        处理API请求
        
        Args:
            request: API请求
            
        Returns:
            API响应
        """
        self.api_stats["total_requests"] += 1
        
        try:
            # 查找处理器
            handler = self.api_handlers.get(request.endpoint)
            
            if not handler:
                self.api_stats["failed_requests"] += 1
                return APIResponse(
                    status=404,
                    message=f"未知的API端点: {request.endpoint}",
                    data={"available_endpoints": list(self.api_handlers.keys())}
                )
            
            # 更新端点统计
            if request.endpoint not in self.api_stats["endpoint_stats"]:
                self.api_stats["endpoint_stats"][request.endpoint] = {
                    "count": 0,
                    "success": 0,
                    "fail": 0
                }
            
            self.api_stats["endpoint_stats"][request.endpoint]["count"] += 1
            
            # 执行处理器
            response = await handler(request)
            
            # 更新统计
            if 200 <= response.status < 300:
                self.api_stats["successful_requests"] += 1
                self.api_stats["endpoint_stats"][request.endpoint]["success"] += 1
            else:
                self.api_stats["failed_requests"] += 1
                self.api_stats["endpoint_stats"][request.endpoint]["fail"] += 1
            
            return response
            
        except Exception as e:
            self.logger.error(f"处理API请求失败: {e}", exc_info=True)
            self.api_stats["failed_requests"] += 1
            
            return APIResponse(
                status=500,
                message=f"内部服务器错误: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_terminal_execute(self, request: APIRequest) -> APIResponse:
        """处理终端执行请求"""
        try:
            # 获取参数
            command = request.data.get("command", "")
            working_directory = request.data.get("working_directory", "")
            timeout = request.data.get("timeout", 60)
            async_execution = request.data.get("async", False)
            
            if not command:
                return APIResponse(
                    status=400,
                    message="缺少命令参数",
                    data={"error": "command参数不能为空"}
                )
            
            # 分析命令
            analysis = self.command_parser.parse(command)
            
            # 安全检查
            safety_report = self.safety_checker.check(command, analysis)
            
            # 准备执行上下文
            from ..executor.intelligent_executor import ExecutionContext
            
            context = ExecutionContext(
                working_directory=working_directory or None,
                timeout=timeout,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            # 执行命令
            if async_execution:
                # 异步执行
                pid = self.executor.execute_async(command, context, analysis)
                
                return APIResponse(
                    status=202,  # Accepted
                    message="命令已开始异步执行",
                    data={
                        "process_id": pid,
                        "command": command,
                        "analysis": analysis.to_dict() if hasattr(analysis, "to_dict") else str(analysis),
                        "safety_report": safety_report.to_dict() if hasattr(safety_report, "to_dict") else str(safety_report)
                    }
                )
            else:
                # 同步执行
                result = self.executor.execute(command, context, analysis)
                
                return APIResponse(
                    status=200,
                    message="命令执行完成",
                    data={
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                        "error_code": result.error_code,
                        "process_id": result.process_id,
                        "execution_time": result.execution_time,
                        "analysis": analysis.to_dict() if hasattr(analysis, "to_dict") else str(analysis),
                        "safety_report": result.safety_report.to_dict() if hasattr(result.safety_report, "to_dict") else str(result.safety_report)
                    }
                )
                
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return APIResponse(
                status=500,
                message=f"执行命令失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_terminal_analyze(self, request: APIRequest) -> APIResponse:
        """处理命令分析请求"""
        try:
            command = request.data.get("command", "")
            
            if not command:
                return APIResponse(
                    status=400,
                    message="缺少命令参数",
                    data={"error": "command参数不能为空"}
                )
            
            # 分析命令
            analysis = self.command_parser.parse(command)
            
            # 安全检查
            safety_report = self.safety_checker.check(command, analysis)
            
            # 查询相关知识
            knowledge_items = self.knowledge_base.get_for_command(analysis)
            
            return APIResponse(
                status=200,
                message="命令分析完成",
                data={
                    "command": command,
                    "analysis": analysis.to_dict() if hasattr(analysis, "to_dict") else str(analysis),
                    "safety_report": safety_report.to_dict() if hasattr(safety_report, "to_dict") else str(safety_report),
                    "related_knowledge": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                            "category": item.category,
                            "tags": item.tags
                        }
                        for item in knowledge_items[:5]  # 最多5条
                    ]
                }
            )
            
        except Exception as e:
            self.logger.error(f"分析命令失败: {e}")
            return APIResponse(
                status=500,
                message=f"分析命令失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_terminal_status(self, request: APIRequest) -> APIResponse:
        """处理终端状态请求"""
        try:
            # 获取运行中的进程
            running_processes = self.executor.get_running_processes()
            
            # 获取执行统计
            execution_stats = self.executor.get_execution_stats()
            
            # 获取安全检查器状态
            safety_stats = self.safety_checker.get_stats() if hasattr(self.safety_checker, "get_stats") else {}
            
            # 获取知识库状态
            knowledge_stats = self.knowledge_base.get_stats()
            
            return APIResponse(
                status=200,
                message="系统状态获取成功",
                data={
                    "running_processes": [
                        {
                            "pid": process.pid,
                            "command": process.command,
                            "status": process.status,
                            "return_code": process.return_code
                        }
                        for process in running_processes
                    ],
                    "execution_stats": execution_stats,
                    "safety_stats": safety_stats,
                    "knowledge_stats": knowledge_stats,
                    "api_stats": self.api_stats
                }
            )
            
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return APIResponse(
                status=500,
                message=f"获取系统状态失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_knowledge_query(self, request: APIRequest) -> APIResponse:
        """处理知识查询请求"""
        try:
            from ..base.types import KnowledgeQuery
            
            # 构建查询
            query_data = request.data.get("query", {})
            
            query = KnowledgeQuery(
                keywords=query_data.get("keywords", []),
                category=query_data.get("category"),
                tags=query_data.get("tags", []),
                limit=query_data.get("limit", 10)
            )
            
            # 执行查询
            results = self.knowledge_base.query(query)
            
            return APIResponse(
                status=200,
                message=f"找到 {len(results)} 条相关记录",
                data={
                    "count": len(results),
                    "results": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "content": item.content,
                            "category": item.category,
                            "tags": item.tags,
                            "source": item.source,
                            "priority": item.priority,
                            "created_at": item.created_at,
                            "updated_at": item.updated_at
                        }
                        for item in results
                    ]
                }
            )
            
        except Exception as e:
            self.logger.error(f"查询知识失败: {e}")
            return APIResponse(
                status=500,
                message=f"查询知识失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_knowledge_add(self, request: APIRequest) -> APIResponse:
        """处理知识添加请求"""
        try:
            from ..base.types import KnowledgeItem
            
            # 验证必要字段
            title = request.data.get("title")
            content = request.data.get("content")
            
            if not title or not content:
                return APIResponse(
                    status=400,
                    message="缺少必要字段",
                    data={"required_fields": ["title", "content"]}
                )
            
            # 创建知识项
            item = KnowledgeItem(
                title=title,
                content=content,
                category=request.data.get("category"),
                tags=request.data.get("tags", []),
                source=request.data.get("source", "api"),
                priority=request.data.get("priority", 1),
                metadata=request.data.get("metadata", {})
            )
            
            # 添加到知识库
            success = self.knowledge_base.add(item)
            
            if success:
                return APIResponse(
                    status=201,
                    message="知识添加成功",
                    data={"item_id": item.id if hasattr(item, "id") else "unknown"}
                )
            else:
                return APIResponse(
                    status=500,
                    message="知识添加失败",
                    data={"error": "知识库操作失败"}
                )
            
        except Exception as e:
            self.logger.error(f"添加知识失败: {e}")
            return APIResponse(
                status=500,
                message=f"添加知识失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_safety_check(self, request: APIRequest) -> APIResponse:
        """处理安全检查请求"""
        try:
            command = request.data.get("command", "")
            analysis_data = request.data.get("analysis", {})
            
            if not command:
                return APIResponse(
                    status=400,
                    message="缺少命令参数",
                    data={"error": "command参数不能为空"}
                )
            
            # 如果有分析数据，转换为CommandAnalysis对象
            analysis = None
            if analysis_data and hasattr(self.command_parser, "create_analysis_from_dict"):
                try:
                    analysis = self.command_parser.create_analysis_from_dict(analysis_data)
                except:
                    pass
            
            # 如果没有分析数据，进行解析
            if not analysis:
                analysis = self.command_parser.parse(command)
            
            # 执行安全检查
            safety_report = self.safety_checker.check(command, analysis)
            
            return APIResponse(
                status=200,
                message="安全检查完成",
                data={
                    "command": command,
                    "safety_report": safety_report.to_dict() if hasattr(safety_report, "to_dict") else str(safety_report),
                    "risk_level": safety_report.risk_level.value if hasattr(safety_report.risk_level, "value") else str(safety_report.risk_level),
                    "is_safe": safety_report.risk_level.value <= 1 if hasattr(safety_report.risk_level, "value") else True
                }
            )
            
        except Exception as e:
            self.logger.error(f"安全检查失败: {e}")
            return APIResponse(
                status=500,
                message=f"安全检查失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def handle_system_stats(self, request: APIRequest) -> APIResponse:
        """处理系统统计请求"""
        try:
            # 获取所有组件的统计信息
            stats = {
                "api_integration": {
                    "total_requests": self.api_stats["total_requests"],
                    "successful_requests": self.api_stats["successful_requests"],
                    "failed_requests": self.api_stats["failed_requests"],
                    "endpoint_stats": self.api_stats["endpoint_stats"]
                },
                "executor": self.executor.get_execution_stats(),
                "knowledge_base": self.knowledge_base.get_stats(),
                "safety_checker": self.safety_checker.get_stats() if hasattr(self.safety_checker, "get_stats") else {},
                "command_parser": {
                    "type": type(self.command_parser).__name__,
                    "status": "active"
                }
            }
            
            return APIResponse(
                status=200,
                message="系统统计获取成功",
                data=stats
            )
            
        except Exception as e:
            self.logger.error(f"获取系统统计失败: {e}")
            return APIResponse(
                status=500,
                message=f"获取系统统计失败: {str(e)}",
                data={"error": str(e)}
            )
    
    def register_handler(self, endpoint: str, handler: Callable):
        """
        注册API处理器
        
        Args:
            endpoint: API端点
            handler: 处理器函数
        """
        self.api_handlers[endpoint] = handler
        self.logger.info(f"注册API处理器: {endpoint}")
    
    def get_available_endpoints(self) -> List[str]:
        """获取可用的API端点列表"""
        return list(self.api_handlers.keys())
    
    def get_api_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        return self.api_stats.copy()
    
    def reset_api_stats(self):
        """重置API统计"""
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "endpoint_stats": {}
        }
        self.logger.info("API统计已重置")


# 单例实例
_global_api_integration: Optional[APIIntegration] = None

def get_api_integration() -> APIIntegration:
    """获取全局API集成实例"""
    global _global_api_integration
    
    if _global_api_integration is None:
        _global_api_integration = APIIntegration()
    
    return _global_api_integration