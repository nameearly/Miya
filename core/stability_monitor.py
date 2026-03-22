#!/usr/bin/env python3
"""
系统稳定性监控器
监控API服务器和终端代理的连接稳定性
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetrics:
    """连接指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    server_errors: int = 0
    total_response_time: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        """平均响应时间"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    def record_success(self, response_time: float):
        """记录成功请求"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
    
    def record_error(self, error_type: str, error_message: str = ""):
        """记录错误"""
        self.total_requests += 1
        self.failed_requests += 1
        
        if "timeout" in error_type.lower():
            self.timeout_errors += 1
        elif "connection" in error_type.lower():
            self.connection_errors += 1
        elif "server" in error_type.lower():
            self.server_errors += 1
        
        self.last_error = f"{error_type}: {error_message}"
        self.last_error_time = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "timeout_errors": self.timeout_errors,
            "connection_errors": self.connection_errors,
            "server_errors": self.server_errors,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }

class StabilityMonitor:
    """稳定性监控器"""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.metrics = ConnectionMetrics()
        self._session: Optional[aiohttp.ClientSession] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
        
    async def check_connection(self) -> bool:
        """检查连接状态"""
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            
            start_time = time.time()
            url = f"http://{self.host}:{self.port}/api/status"
            
            async with self._session.get(url, timeout=10) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    self.metrics.record_success(response_time)
                    logger.debug(f"连接检查成功 - 响应时间: {response_time:.3f}s")
                    return True
                else:
                    self.metrics.record_error("ServerError", f"HTTP {response.status}")
                    logger.warning(f"连接检查失败 - 状态码: {response.status}")
                    return False
                    
        except asyncio.TimeoutError:
            self.metrics.record_error("TimeoutError", "连接超时")
            logger.warning("连接检查超时")
            return False
        except aiohttp.ClientError as e:
            self.metrics.record_error("ConnectionError", str(e))
            logger.warning(f"连接检查失败: {e}")
            return False
        except Exception as e:
            self.metrics.record_error("UnknownError", str(e))
            logger.error(f"连接检查异常: {e}")
            return False
    
    async def send_test_message(self, message: str = "稳定性测试") -> Optional[Dict]:
        """发送测试消息"""
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            
            start_time = time.time()
            url = f"http://{self.host}:{self.port}/api/terminal/chat"
            payload = {
                "message": message,
                "session_id": "stability_monitor",
                "from_terminal": "monitor"
            }
            
            async with self._session.post(url, json=payload, timeout=15) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.metrics.record_success(response_time)
                    
                    # 检查API返回的状态
                    if data.get("status") == "error":
                        error_msg = data.get("error", "未知错误")
                        logger.warning(f"测试消息返回错误: {error_msg}")
                        return {"success": False, "error": error_msg, "response_time": response_time}
                    
                    logger.debug(f"测试消息成功 - 响应时间: {response_time:.3f}s")
                    return {"success": True, "data": data, "response_time": response_time}
                else:
                    error_text = await response.text() if response.content else f"状态码: {response.status}"
                    self.metrics.record_error("ServerError", f"HTTP {response.status}: {error_text[:100]}")
                    logger.warning(f"测试消息失败 - 状态码: {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}", "response_time": response_time}
                    
        except asyncio.TimeoutError:
            self.metrics.record_error("TimeoutError", "消息发送超时")
            logger.warning("测试消息超时")
            return {"success": False, "error": "Timeout"}
        except aiohttp.ClientError as e:
            self.metrics.record_error("ConnectionError", str(e))
            logger.warning(f"测试消息连接错误: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            self.metrics.record_error("UnknownError", str(e))
            logger.error(f"测试消息异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def continuous_monitoring(self, interval: int = 30):
        """持续监控"""
        self._is_monitoring = True
        
        logger.info(f"开始持续监控 - 间隔: {interval}秒")
        
        while self._is_monitoring:
            try:
                # 检查连接
                connection_ok = await self.check_connection()
                
                if connection_ok:
                    # 发送测试消息
                    test_result = await self.send_test_message("监控心跳")
                    
                    if test_result and test_result.get("success"):
                        logger.info(f"监控检查通过 - 成功率: {self.metrics.success_rate:.1f}%")
                    else:
                        error_msg = test_result.get("error", "未知错误") if test_result else "无响应"
                        logger.warning(f"监控检查失败: {error_msg}")
                
                # 定期报告指标
                if self.metrics.total_requests % 10 == 0 and self.metrics.total_requests > 0:
                    self.report_metrics()
                
                # 等待下一个检查
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("监控任务被取消")
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(interval)
    
    def report_metrics(self):
        """报告指标"""
        metrics_dict = self.metrics.to_dict()
        
        print("\n" + "=" * 60)
        print("稳定性监控报告")
        print("=" * 60)
        print(f"总请求数: {metrics_dict['total_requests']}")
        print(f"成功请求: {metrics_dict['successful_requests']}")
        print(f"失败请求: {metrics_dict['failed_requests']}")
        print(f"成功率: {metrics_dict['success_rate']:.1f}%")
        print(f"平均响应时间: {metrics_dict['avg_response_time']:.3f}s")
        print(f"超时错误: {metrics_dict['timeout_errors']}")
        print(f"连接错误: {metrics_dict['connection_errors']}")
        print(f"服务器错误: {metrics_dict['server_errors']}")
        
        if metrics_dict['last_error']:
            print(f"最后错误: {metrics_dict['last_error']}")
            print(f"错误时间: {metrics_dict['last_error_time']}")
        
        # 保存到文件
        self.save_metrics()
    
    def save_metrics(self, filename: str = "stability_metrics.json"):
        """保存指标到文件"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self.metrics.to_dict(),
                "system_info": {
                    "host": self.host,
                    "port": self.port,
                    "monitor_running": self._is_monitoring
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"指标已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存指标失败: {e}")
    
    async def start_monitoring(self, interval: int = 30):
        """开始监控"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("监控已经在运行")
            return
        
        self._monitoring_task = asyncio.create_task(self.continuous_monitoring(interval))
        logger.info(f"监控已启动 - 检查间隔: {interval}秒")
    
    async def stop_monitoring(self):
        """停止监控"""
        self._is_monitoring = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._session and not self._session.closed:
            await self._session.close()
        
        logger.info("监控已停止")
    
    def get_diagnosis(self) -> Dict:
        """获取诊断信息"""
        metrics = self.metrics.to_dict()
        
        diagnosis = {
            "overall_health": "good",
            "issues": [],
            "recommendations": [],
            "metrics_summary": metrics
        }
        
        # 分析问题
        if metrics['success_rate'] < 90:
            diagnosis['overall_health'] = "warning"
            diagnosis['issues'].append(f"成功率偏低: {metrics['success_rate']:.1f}%")
            diagnosis['recommendations'].append("检查网络连接或API服务器状态")
        
        if metrics['timeout_errors'] > 5:
            diagnosis['overall_health'] = "warning"
            diagnosis['issues'].append(f"超时错误较多: {metrics['timeout_errors']}")
            diagnosis['recommendations'].append("增加请求超时时间或优化服务器性能")
        
        if metrics['connection_errors'] > 3:
            diagnosis['overall_health'] = "warning"
            diagnosis['issues'].append(f"连接错误较多: {metrics['connection_errors']}")
            diagnosis['recommendations'].append("检查服务器是否稳定运行")
        
        if metrics['avg_response_time'] > 2.0:
            diagnosis['overall_health'] = "warning"
            diagnosis['issues'].append(f"响应时间较慢: {metrics['avg_response_time']:.3f}s")
            diagnosis['recommendations'].append("优化服务器性能或减少并发请求")
        
        # 根据最后错误时间判断
        if metrics['last_error_time']:
            last_error_time = datetime.fromisoformat(metrics['last_error_time'])
            time_since_error = (datetime.now() - last_error_time).total_seconds()
            
            if time_since_error < 300:  # 5分钟内
                diagnosis['overall_health'] = "warning"
                diagnosis['issues'].append(f"最近发生错误: {time_since_error:.0f}秒前")
                diagnosis['recommendations'].append("持续监控系统状态")
        
        return diagnosis

async def run_monitor_cli():
    """运行监控CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="弥娅系统稳定性监控器")
    parser.add_argument("--host", default="localhost", help="API服务器主机")
    parser.add_argument("--port", type=int, default=8001, help="API服务器端口")
    parser.add_argument("--interval", type=int, default=30, help="监控间隔（秒）")
    parser.add_argument("--check", action="store_true", help="只检查一次")
    parser.add_argument("--test", action="store_true", help="发送测试消息")
    parser.add_argument("--diagnose", action="store_true", help="获取诊断信息")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = StabilityMonitor(args.host, args.port)
    
    try:
        if args.check:
            print("检查连接状态...")
            result = await monitor.check_connection()
            print(f"连接状态: {'✅ 成功' if result else '❌ 失败'}")
            monitor.report_metrics()
            
        elif args.test:
            print("发送测试消息...")
            result = await monitor.send_test_message("稳定性测试消息")
            if result and result.get("success"):
                data = result.get("data", {})
                print(f"✅ 测试成功")
                print(f"响应: {data.get('response', '无响应')}")
                print(f"响应时间: {result.get('response_time', 0):.3f}s")
            else:
                error = result.get("error", "未知错误") if result else "无响应"
                print(f"❌ 测试失败: {error}")
            
        elif args.diagnose:
            print("获取诊断信息...")
            await monitor.check_connection()
            diagnosis = monitor.get_diagnosis()
            
            print("\n" + "=" * 60)
            print("系统诊断报告")
            print("=" * 60)
            
            health_emoji = {"good": "✅", "warning": "⚠️", "error": "❌"}
            print(f"整体健康度: {health_emoji.get(diagnosis['overall_health'], '❓')} {diagnosis['overall_health'].upper()}")
            
            if diagnosis['issues']:
                print("\n发现问题:")
                for issue in diagnosis['issues']:
                    print(f"  • {issue}")
            
            if diagnosis['recommendations']:
                print("\n建议:")
                for rec in diagnosis['recommendations']:
                    print(f"  • {rec}")
            
            metrics = diagnosis['metrics_summary']
            print(f"\n指标摘要:")
            print(f"  成功率: {metrics['success_rate']:.1f}%")
            print(f"  平均响应时间: {metrics['avg_response_time']:.3f}s")
            print(f"  总请求数: {metrics['total_requests']}")
            
        else:
            print(f"启动持续监控 - 主机: {args.host}:{args.port}, 间隔: {args.interval}秒")
            print("按 Ctrl+C 停止监控")
            
            await monitor.start_monitoring(args.interval)
            
            # 保持运行
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n收到停止信号...")
                await monitor.stop_monitoring()
                
    finally:
        if monitor._session and not monitor._session.closed:
            await monitor._session.close()

if __name__ == "__main__":
    asyncio.run(run_monitor_cli())