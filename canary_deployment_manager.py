#!/usr/bin/env python3
"""
P2 灰度发布管理器
管理灰度发布的各个阶段：1% -> 25% -> 50% -> 100%
"""

import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# FIX: P95 延迟的“推进阈值”和“告警阈值”此前不一致（success 用 50ms，而告警用 100ms），
# 会导致推进被阻止但不触发告警，或监控解释困难。这里统一成可配置常量。
P95_SUCCESS_THRESHOLD_MS = 50
P95_ALERT_THRESHOLD_MS = 50


class CanaryStage(Enum):
    """灰度阶段"""
    CANARY_1PCT = "canary_1pct"
    BETA_25PCT = "beta_25pct"
    RELEASE_50PCT = "release_50pct"
    GA_100PCT = "general_availability"


class CanaryStatus(Enum):
    """灰度状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class P2CanaryManager:
    """P2灰度发布管理器"""
    
    def __init__(self, config_file: str = "canary_config.json"):
        self.config_file = Path(config_file)
        self.state_file = Path("canary_state.json")
        
        self.stages = {
            CanaryStage.CANARY_1PCT: {
                "percentage": 1,
                "duration_hours": 6,
                "auto_advance": True,
            },
            CanaryStage.BETA_25PCT: {
                "percentage": 25,
                "duration_hours": 24,
                "auto_advance": True,
            },
            CanaryStage.RELEASE_50PCT: {
                "percentage": 50,
                "duration_hours": 48,
                "auto_advance": True,
            },
            CanaryStage.GA_100PCT: {
                "percentage": 100,
                "duration_hours": 0,
                "auto_advance": False,
            },
        }
        
        # 从文件加载状态
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载灰度状态"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "current_stage": None,
            "current_percentage": 0,
            "status": CanaryStatus.PENDING.value,
            "start_time": None,
            "stage_start_time": None,
            "metrics": {},
            "alerts": [],
        }
    
    def _save_state(self) -> None:
        """保存灰度状态"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
        logger.info(f"✅ 灰度状态已保存: {self.state_file}")
    
    def start_canary(self, stage: CanaryStage = CanaryStage.CANARY_1PCT) -> bool:
        """启动灰度发布"""
        if self.state["status"] == CanaryStatus.RUNNING.value:
            logger.error("❌ 灰度发布已在运行中")
            return False
        
        logger.info("=" * 60)
        logger.info(f"🚀 启动 P2 灰度发布")
        logger.info("=" * 60)
        
        self.state["current_stage"] = stage.value
        self.state["current_percentage"] = self.stages[stage]["percentage"]
        self.state["status"] = CanaryStatus.RUNNING.value
        self.state["start_time"] = datetime.now().isoformat()
        self.state["stage_start_time"] = datetime.now().isoformat()
        
        logger.info(f"📊 当前阶段: {stage.value}")
        logger.info(f"📈 流量百分比: {self.state['current_percentage']}%")
        logger.info(f"⏱️  预计持续: {self.stages[stage]['duration_hours']} 小时")
        
        self._save_state()
        return True
    
    def advance_stage(self, next_stage: CanaryStage) -> bool:
        """推进到下一个阶段"""
        if self.state["status"] != CanaryStatus.RUNNING.value:
            logger.error("❌ 灰度发布未在运行中")
            return False
        
        current = self.state["current_stage"]
        logger.info("=" * 60)
        logger.info(f"▶️ 推进灰度阶段: {current} -> {next_stage.value}")
        logger.info("=" * 60)
        
        # 检查前置条件
        if not self._check_stage_success():
            logger.error("❌ 前一阶段检查失败，无法推进", )
            return False
        
        self.state["current_stage"] = next_stage.value
        self.state["current_percentage"] = self.stages[next_stage]["percentage"]
        self.state["stage_start_time"] = datetime.now().isoformat()
        
        logger.info(f"✅ 已推进到: {next_stage.value}")
        logger.info(f"📈 流量百分比: {self.state['current_percentage']}%")
        logger.info(f"⏱️  预计持续: {self.stages[next_stage]['duration_hours']} 小时")
        
        self._save_state()
        return True
    
    def check_auto_advance(self) -> bool:
        """检查是否自动推进"""
        if not self.state["current_stage"]:
            return False
        
        current_stage = CanaryStage(self.state["current_stage"])
        
        # GA 不需要自动推进
        if current_stage == CanaryStage.GA_100PCT:
            return False
        
        # 检查是否满足自动推进条件
        if not self._check_stage_success():
            logger.warning("⚠️  阶段检查未通过，不自动推进")
            return False
        
        stage_config = self.stages[current_stage]
        if not stage_config["auto_advance"]:
            logger.info("ℹ️  当前阶段不启用自动推进")
            return False
        
        # 检查时间
        stage_start = datetime.fromisoformat(self.state["stage_start_time"])
        stage_duration = timedelta(hours=stage_config["duration_hours"])
        
        if datetime.now() < stage_start + stage_duration:
            remaining = (stage_start + stage_duration - datetime.now()).total_seconds() / 3600
            logger.info(f"⏳ 还需 {remaining:.1f} 小时才能推进")
            return False
        
        logger.info("✅ 自动推进条件满足，准备推进到下一阶段")
        return True
    
    def _check_stage_success(self) -> bool:
        """检查当前阶段是否成功"""
        metrics = self.state.get("metrics", {})
        
        # 检查关键指标
        checks = {
            "error_rate": (metrics.get("error_rate", 0) < 0.001, "错误率 < 0.1%"),
            "p95_latency": (
                metrics.get("p95_latency", 0) < P95_SUCCESS_THRESHOLD_MS,
                f"P95延迟 < {P95_SUCCESS_THRESHOLD_MS}ms",
            ),
            "memory_growth": (metrics.get("memory_growth_pct", 0) < 50, "内存增长 < 50%"),
        }
        
        success = all(check[0] for check in checks.values())
        
        if success:
            logger.info("✅ 所有检查通过")
        else:
            logger.warning("❌ 部分检查失败:")
            for check_name, (check_result, description) in checks.items():
                status = "✅" if check_result else "❌"
                logger.warning(f"   {status} {description}")
        
        return success
    
    def rollback(self, reason: str) -> bool:
        """回滚灰度发布"""
        if self.state["status"] != CanaryStatus.RUNNING.value:
            logger.error("❌ 灰度发布未在运行中，无需回滚")
            return False
        
        logger.error("=" * 60)
        logger.error(f"🔙 启动回滚: {reason}")
        logger.error("=" * 60)
        
        self.state["status"] = CanaryStatus.ROLLED_BACK.value
        self.state["current_percentage"] = 0  # 回滚到 0%
        self.state["alerts"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "rollback",
            "reason": reason,
        })
        
        logger.error("⚠️  灰度发布已回滚")
        logger.error("📋 回滚步骤:")
        logger.error("   1. 停止向新版本路由流量")
        logger.error("   2. 恢复到上一个稳定版本")
        logger.error("   3. 清理新版本资源")
        logger.error("   4. 进行事后分析")
        
        self._save_state()
        return True
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新性能指标"""
        self.state["metrics"] = metrics
        self.state["metrics"]["last_update"] = datetime.now().isoformat()
        
        # 检查告警条件
        if metrics.get("error_rate", 0) > 0.001:
            self._add_alert("error_rate_exceeded", f"错误率: {metrics['error_rate']:.4f}")
        
        if metrics.get("p95_latency", 0) > P95_ALERT_THRESHOLD_MS:
            self._add_alert(
                "latency_exceeded",
                f"P95延迟: {metrics['p95_latency']:.1f}ms (>{P95_ALERT_THRESHOLD_MS}ms)",
            )
        
        if metrics.get("memory_growth_pct", 0) > 50:
            self._add_alert("memory_exceeded", f"内存增长: {metrics['memory_growth_pct']:.1f}%")
        
        self._save_state()
    
    def _add_alert(self, alert_type: str, message: str) -> None:
        """添加告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
        }
        self.state["alerts"].append(alert)
        logger.warning(f"⚠️  告警: {alert_type} - {message}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取灰度发布状态"""
        return {
            "current_stage": self.state["current_stage"],
            "current_percentage": self.state["current_percentage"],
            "status": self.state["status"],
            "start_time": self.state["start_time"],
            "stage_start_time": self.state["stage_start_time"],
            "metrics": self.state["metrics"],
            "alerts": self.state["alerts"][-5:],  # 最近5个告警
        }
    
    def print_status(self) -> None:
        """打印灰度发布状态"""
        status = self.get_status()
        
        logger.info("=" * 60)
        logger.info("📊 P2 灰度发布状态")
        logger.info("=" * 60)
        logger.info(f"当前阶段: {status['current_stage']}")
        logger.info(f"流量百分比: {status['current_percentage']}%")
        logger.info(f"状态: {status['status']}")
        
        if status['start_time']:
            logger.info(f"启动时间: {status['start_time']}")
        
        if status['metrics']:
            logger.info("\n📈 最新指标:")
            for key, value in status['metrics'].items():
                if key != 'last_update':
                    logger.info(f"   {key}: {value}")
        
        if status['alerts']:
            logger.info("\n⚠️  最近告警:")
            for alert in status['alerts']:
                logger.warning(f"   [{alert['type']}] {alert['message']}")
        
        logger.info("=" * 60)


def demo_canary_flow():
    """演示灰度发布流程"""
    manager = P2CanaryManager()
    
    # 启动 Canary 1%
    print("\n" + "=" * 60)
    print("演示: P2 灰度发布流程")
    print("=" * 60)
    
    manager.start_canary(CanaryStage.CANARY_1PCT)
    manager.print_status()
    
    # 模拟一些指标数据
    time.sleep(1)
    manager.update_metrics({
        "error_rate": 0.0005,
        "p95_latency": 8.5,
        "memory_growth_pct": 15,
    })
    manager.print_status()
    
    # 推进到 Beta 25%
    logger.info("\n⏱️  5秒后推进到 Beta 25%...")
    time.sleep(5)
    
    if manager.advance_stage(CanaryStage.BETA_25PCT):
        manager.print_status()
    
    # 推进到 Release 50%
    logger.info("\n⏱️  5秒后推进到 Release 50%...")
    time.sleep(5)
    
    if manager.advance_stage(CanaryStage.RELEASE_50PCT):
        manager.print_status()
    
    # 推进到 GA 100%
    logger.info("\n⏱️  5秒后推进到 GA 100%...")
    time.sleep(5)
    
    if manager.advance_stage(CanaryStage.GA_100PCT):
        manager.print_status()
    
    logger.info("\n✅ 灰度发布完成！")


if __name__ == "__main__":
    demo_canary_flow()
