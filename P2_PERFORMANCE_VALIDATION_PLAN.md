# P2 阶段计划 - 性能验证与灰度发布

**目标**: 验证P1迁移在生产环境中的性能表现，通过灰度发布策略安全地将更新推送到全量用户

**时间估计**: 5-7 天  
**风险等级**: 低（P1已通过所有测试，此阶段是验证性不是功能性）  
**回滚时间**: < 5 分钟（通过配置文件切换）

---

## 📋 P2 阶段分解

### 阶段1: 性能基准测试 (Day 1)

**目标**: 建立性能基线，与P1测试数据对标

#### 1.1 准备生产级测试数据
```
- 获取实际QQ数据样本（>1000用户）
- 生成典型的消息历史（>10000条消息）
- 准备图片分析任务（>1000张图片）
- 准备配置变更序列（>500条变更）
```

#### 1.2 运行基准测试
```bash
# 在测试环境运行
python performance_baseline_p2.py --data-source production-sample --duration 3600 --concurrency 50

# 预期结果
- 消息缓存: 1M+ ops/sec（与P1对标✓）
- 图片缓存: 1M+ ops/sec（与P1对标✓）
- 内存占用: < 500MB（6种缓存类型）
- CPU占用: < 10%（单线程测试）
```

#### 1.3 建立性能指标基线
| 指标 | P1测试 | P2生产基线 | 阈值 |
|------|-------|----------|------|
| 消息写入 | 1.4M ops/sec | ? | > 1.0M |
| 消息读取 | 1.8M ops/sec | ? | > 1.0M |
| 图片写入 | 1.0M ops/sec | ? | > 0.8M |
| 图片读取 | 1.9M ops/sec | ? | > 1.0M |
| 配置写入 | 1.0M ops/sec | ? | > 0.8M |
| 命中率 | N/A | ? | > 70% |
| P95延迟 | N/A | ? | < 10ms |

---

### 阶段2: 灰度发布策略 (Day 2-5)

#### 2.1 灰度阶段定义

**Stage 1: 1% Canary (6小时)**
- 覆盖: 1% 活跃用户（内测组）
- 监控指标: 错误率, 响应时间, 缓存命中率
- 黄线: 错误率 > 0.1%, P95 > 50ms
- 回滚条件: 任意黄线触发
- 成功标准: 6小时无严重告警

**Stage 2: 25% Beta (24小时)**
- 覆盖: 25% 活跃用户（分区A+B）
- 监控指标: 缓存命中率, 内存占用, GC暂停
- 黄线: 内存增长 > 50%, GC > 100ms
- 回滚条件: 任意黄线触发
- 成功标准: 24小时无错误升级

**Stage 3: 50% Release (48小时)**
- 覆盖: 50% 活跃用户（分区A+B+C）
- 监控指标: 用户反馈, 性能趋势分析
- 黄线: 用户反馈投诉 > 1%, 性能下降 > 20%
- 回滚条件: 收到平台反馈
- 成功标准: 48小时保持稳定

**Stage 4: 100% GA (12小时)**
- 覆盖: 100% 活跃用户
- 监控指标: 整体系统健康度
- 黄线: 系统故障指标
- 回滚条件: 严重问题（用户无法使用）
- 成功标准: P2 GA完成

#### 2.2 灰度发布配置

创建 `webnet/qq/config/canary_config.yaml`:
```yaml
canary:
  enabled: true
  stages:
    - name: "canary_1pct"
      percentage: 1
      duration_hours: 6
      auto_advance: true
      
    - name: "beta_25pct"
      percentage: 25
      duration_hours: 24
      auto_advance: true
      
    - name: "release_50pct"
      percentage: 50
      duration_hours: 48
      auto_advance: true
      
    - name: "general_availability"
      percentage: 100
      duration_hours: 0
      auto_advance: false

rollback:
  enabled: true
  auto_rollback: true
  conditions:
    - error_rate_threshold: 0.001  # 0.1%
    - p95_latency_threshold: 50  # ms
    - memory_increase_threshold: 50  # %
```

#### 2.3 灰度发布执行

```bash
# 启动灰度发布管理器
python canary_deployment_manager.py --config canary_config.yaml --start-stage canary_1pct

# 监控灰度过程
python canary_monitor.py --watch --alert-on "error_rate,latency,memory"

# 查询灰度状态
python canary_status.py --verbose
```

---

### 阶段3: 监控和指标收集 (Continuous)

#### 3.1 建立监控仪表板

**实时监控指标**:
```
✅ 缓存层
  - 消息缓存命中率 (Target: > 75%)
  - 图片缓存命中率 (Target: > 80%)
  - 配置缓存命中率 (Target: > 90%)
  - 平均命中延迟 (Target: < 5ms)

✅ 应用层
  - image_handler 响应时间 (Target: < 500ms)
  - message_handler 响应时间 (Target: < 200ms)
  - hybrid_config 加载时间 (Target: < 100ms)

✅ 系统层
  - 内存占用 (Target: < 500MB)
  - CPU占用 (Target: < 15%)
  - GC暂停时间 (Target: < 50ms)

✅ 用户层
  - 错误率 (Target: < 0.01%)
  - P95延迟 (Target: < 100ms)
  - 用户投诉数 (Target: 0)
```

#### 3.2 监控数据收集脚本

创建 `monitor_p2_deployment.py`:
```python
#!/usr/bin/env python3
"""P2 灰度发布监控脚本"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class P2Monitor:
    def __init__(self):
        self.metrics_file = Path("p2_metrics.json")
        self.alerts_file = Path("p2_alerts.json")
        
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cache_metrics": await self._collect_cache_metrics(),
            "app_metrics": await self._collect_app_metrics(),
            "system_metrics": await self._collect_system_metrics(),
        }
        return metrics
    
    async def _collect_cache_metrics(self) -> Dict[str, Any]:
        """收集缓存指标"""
        # TODO: 从QQCacheManager获取统计信息
        pass
    
    async def _collect_app_metrics(self) -> Dict[str, Any]:
        """收集应用层指标"""
        # TODO: 从各处理器收集响应时间统计
        pass
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        # TODO: 从psutil收集系统资源占用
        pass
    
    async def run_continuous_monitoring(self, interval: int = 60):
        """连续监控"""
        while True:
            metrics = await self.collect_metrics()
            self._save_metrics(metrics)
            self._check_alerts(metrics)
            await asyncio.sleep(interval)
    
    def _save_metrics(self, metrics: Dict[str, Any]):
        """保存指标"""
        # TODO: 保存到本地JSON或发送到监控系统
        pass
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """检查告警条件"""
        # TODO: 检查性能指标是否超过阈值
        pass

if __name__ == "__main__":
    monitor = P2Monitor()
    asyncio.run(monitor.run_continuous_monitoring())
```

---

### 阶段4: 验证和总结 (Day 5-6)

#### 4.1 P2 验收标准

```
✅ 性能指标
  - 所有缓存操作性能 >= P1 基线 95%
  - 缓存命中率 >= 70%
  - P95 延迟 < 100ms

✅ 可靠性
  - 错误率 < 0.01%
  - 无内存泄漏
  - GC暂停 < 50ms

✅ 用户体验
  - 用户反馈投诉 = 0
  - 系统稳定性 = 100%
  - 性能无明显下降

✅ 灰度过程
  - 所有4个灰度阶段顺利完成
  - 无自动回滚触发
  - 无手动干预需求
```

#### 4.2 成功条件检查清单

- [ ] P1 代码在生产环境通过验收
- [ ] 消息缓存命中率 >= 70%
- [ ] 图片缓存命中率 >= 80%
- [ ] 配置缓存命中率 >= 90%
- [ ] 灰度 1% 完成无告警
- [ ] 灰度 25% 完成无告警
- [ ] 灰度 50% 完成无告警
- [ ] 灰度 100% 完成
- [ ] 性能指标对标 P1 测试结果
- [ ] 生成 P2 完成报告

#### 4.3 生成 P2 完成报告

```python
# 报告内容
P2 COMPLETION REPORT
====================
Date: YYYY-MM-DD
Duration: X days

1. 性能验证结果
   - 基准测试: PASS/FAIL
   - 性能对标: X% of P1 baseline
   
2. 灰度发布结果
   - Stage 1 (1%): PASS
   - Stage 2 (25%): PASS
   - Stage 3 (50%): PASS
   - Stage 4 (100%): PASS
   
3. 指标收集
   - 消息缓存命中率: X%
   - 图片缓存命中率: X%
   - 配置缓存命中率: X%
   - 平均响应时间: Xms
   
4. 问题和改进
   - Issue 1: ...
   - Issue 2: ...
   - Improvement: ...
   
5. 下阶段建议
   - P3: 扩展缓存到其他子网
   - P4: 集成分布式缓存系统
```

---

## 🔄 灰度发布回滚策略

### 回滚触发条件

```yaml
回滚条件:
  - 错误率 > 0.1%
  - P95延迟 > 50ms (Canary) / 100ms (Beta/Release)
  - 内存增长 > 50%
  - GC暂停 > 100ms
  - 用户投诉 > 5例
  - 严重服务故障
```

### 回滚执行步骤

```bash
# 1. 触发自动回滚
python canary_rollback.py --stage current --reason "error_rate_exceeded"

# 2. 验证回滚
python canary_status.py --verify-rollback

# 3. 等待一段时间观察
sleep 600  # 10 分钟

# 4. 分析失败原因
python analyze_failure.py --stage <failed_stage>

# 5. 修复问题后重试
git log --oneline -5  # 查看最近提交
# 修复 bug...
# git push...
# 重新启动灰度
```

---

## 📊 P2 检查清单

### Pre-Launch (Day 1)
- [ ] 准备生产级测试数据
- [ ] 验证 P1 代码在测试环境稳定运行
- [ ] 建立监控仪表板
- [ ] 配置灰度发布策略
- [ ] 通知相关团队
- [ ] 准备回滚脚本

### During Canary (Day 2, 6小时)
- [ ] 监控错误率（目标: < 0.1%）
- [ ] 监控响应时间（目标: < 50ms P95）
- [ ] 收集缓存命中率数据
- [ ] 查看用户反馈
- [ ] 每小时检查一次状态

### During Beta (Day 2-3, 24小时)
- [ ] 监控内存占用（目标: < 500MB）
- [ ] 监控 GC 暂停（目标: < 100ms）
- [ ] 分析缓存效率
- [ ] 检查性能趋势
- [ ] 每4小时汇总一次状态

### During Release (Day 3-4, 48小时)
- [ ] 每日性能报告
- [ ] 用户反馈收集
- [ ] 性能基准对标
- [ ] 系统稳定性验证

### Post-Launch (Day 5-6)
- [ ] 最终性能确认
- [ ] 生成 P2 完成报告
- [ ] 文档更新
- [ ] 下阶段规划

---

## 💡 关键指标说明

### 缓存命中率
- **定义**: 从缓存成功获取的请求 / 总请求数
- **目标**: 消息 > 75%, 图片 > 80%, 配置 > 90%
- **影响**: 直接影响响应时间和系统性能

### P95 延迟
- **定义**: 95% 的请求在该时间内完成
- **目标**: 缓存命中 < 5ms, 应用层 < 100ms
- **影响**: 用户体验的关键指标

### 内存占用
- **定义**: QQCacheManager 占用的堆内存
- **目标**: < 500MB（6种缓存类型）
- **影响**: 系统整体内存压力

---

## 🎯 P2 成功指标

| 指标 | 阈值 | 状态 |
|------|------|------|
| ✅ 功能完整性 | 100% | |
| ✅ 性能达成 | >= P1 基线 95% | |
| ✅ 可靠性 | 错误率 < 0.01% | |
| ✅ 灰度完成 | 4/4 阶段通过 | |
| ✅ 用户反馈 | 0 重大投诉 | |

---

## 📅 时间表

| 日期 | 活动 | 所有者 |
|------|------|-------|
| Day 1 | 准备工作 + 基准测试 | 性能团队 |
| Day 2 | Canary (1%) + Beta 启动 | 发布团队 |
| Day 2-3 | Beta (25%) 进行中 | 监控团队 |
| Day 3-4 | Release (50%) 进行中 | 产品团队 |
| Day 4-5 | GA (100%) 进行中 | QA团队 |
| Day 5-6 | 总结报告 | 所有人 |

---

## 🚀 P2 → P3 过渡

P2 完成后的下一步（P3 阶段）:

1. **扩展到其他子网**
   - TTSNet (文本转语音缓存)
   - VisionNet (视觉模型缓存)
   - WebSearchNet (搜索结果缓存)

2. **集成分布式缓存**
   - Redis 后端支持
   - 多进程缓存同步
   - 故障转移机制

3. **性能优化**
   - 自适应 TTL 调整
   - 缓存预热策略
   - 智能驱逐算法

---

**下一步**: 确认是否开始 P2 阶段？
