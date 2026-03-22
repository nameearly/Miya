# P2 阶段快速启动指南

**目标**: 通过4个阶段的灰度发布，验证P1迁移在生产环境的表现  
**时间**: 5-7 天  
**状态**: 准备就绪 ✅

---

## 🚀 快速开始（3个命令）

### 步骤1: 运行性能基准测试（验证性能基线）

```bash
cd d:\AI_MIYA_Facyory\MIYA\Miya

# 快速测试（10秒，5并发）
python performance_baseline_p2.py --duration 10 --concurrency 5

# 完整测试（60秒，10并发）
python performance_baseline_p2.py --duration 60 --concurrency 10
```

**预期输出**:
```
✅ 消息写入性能: 1.4M+ ops/sec
✅ 消息读取性能: 1.8M+ ops/sec
✅ 图片写入性能: 1.0M+ ops/sec
✅ 图片读取性能: 1.9M+ ops/sec
✅ 性能对标: >= 95% of P1 baseline
```

---

### 步骤2: 启动灰度发布管理

```bash
# 启动灰度发布演示（自动推进4个阶段）
python canary_deployment_manager.py

# 手动启动并查看状态
python canary_deployment_manager.py --start
python canary_deployment_manager.py --status
```

**预期流程**:
```
🚀 启动灰度 Stage 1 (1% Canary, 6小时)
  ↓ 6小时后自动推进
▶️ 推进到 Stage 2 (25% Beta, 24小时)
  ↓ 24小时后自动推进
▶️ 推进到 Stage 3 (50% Release, 48小时)
  ↓ 48小时后自动推进
▶️ 推进到 Stage 4 (100% GA)
  ↓
✅ P2 灰度发布完成
```

---

### 步骤3: 启动监控系统

```bash
# 运行单个监控周期（查看当前指标）
python p2_monitor.py

# 连续监控（后台运行，每60秒更新一次）
python p2_monitor.py --watch --interval 60
```

**预期指标**:
```
✅ 缓存指标
   消息缓存              命中率: 75.0%   条数:   123
   图片缓存              命中率: 82.0%   条数:    45
   配置缓存              命中率: 95.0%   条数:    8

✅ 应用指标
   image_handler         响应:  150.0ms  错误率: 0.0000
   message_handler       响应:   75.0ms  错误率: 0.0000
   hybrid_config         响应:   50.0ms  错误率: 0.0000

✅ 系统指标
   内存:    250.0MB    CPU:   5.0%
```

---

## 📋 完整流程清单

### Day 1: 准备与基准测试

```bash
# 1. 准备环境
cd d:\AI_MIYA_Facyory\MIYA\Miya
python -m venv venv  # 如果还没有
source venv/Scripts/Activate  # 或 . venv/Scripts/Activate.ps1

# 2. 运行基准测试
python performance_baseline_p2.py --duration 60

# 3. 保存结果
python performance_baseline_p2.py --duration 60 > p2_baseline.log

# ✅ 检查清单
# [ ] 所有性能指标 >= P1 基线 95%
# [ ] 消息缓存命中率 >= 70%
# [ ] 图片缓存命中率 >= 80%
# [ ] 配置缓存命中率 >= 90%
```

### Day 2: Canary 1% 发布

```bash
# 1. 启动灰度发布管理器
python canary_deployment_manager.py --start-stage canary_1pct

# 2. 启动监控（单独终端）
python p2_monitor.py --watch

# 3. 监控6小时
# - 监控错误率 (目标: < 0.1%)
# - 监控P95延迟 (目标: < 50ms)
# - 检查用户反馈

# ✅ 检查清单
# [ ] 无严重告警（6小时）
# [ ] 错误率 < 0.1%
# [ ] P95延迟 < 50ms
# [ ] 缓存命中率正常
```

### Day 2-3: Beta 25% 发布

```bash
# 1. 推进到下一阶段
python canary_deployment_manager.py --advance-to beta_25pct

# 2. 继续监控（24小时）
python p2_monitor.py --watch

# 3. 性能指标对标
# - 消息缓存命中率应该提升
# - 图片缓存命中率应该提升
# - 整体系统性能稳定

# ✅ 检查清单
# [ ] 性能与Day 1一致
# [ ] 内存增长 < 50%
# [ ] GC暂停 < 100ms
# [ ] 无内存泄漏
```

### Day 3-4: Release 50% 发布

```bash
# 1. 推进到Release阶段
python canary_deployment_manager.py --advance-to release_50pct

# 2. 继续监控（48小时）
# - 每日性能报告
# - 收集用户反馈
# - 性能基准对标

# ✅ 检查清单
# [ ] 性能保持稳定
# [ ] 用户反馈投诉 = 0
# [ ] 系统错误率 < 0.01%
# [ ] 无异常告警
```

### Day 4-5: GA 100% 发布

```bash
# 1. 推进到GA阶段
python canary_deployment_manager.py --advance-to general_availability

# 2. 继续监控（12小时）
# - 全量用户验证
# - 系统稳定性监控
# - 最终性能确认

# ✅ 检查清单
# [ ] 系统正常运行
# [ ] 所有指标达成
# [ ] 无回滚需求
```

### Day 5-6: 总结与报告

```bash
# 1. 生成性能报告
python p2_monitor.py --generate-report

# 2. 性能对标总结
# - 与P1测试数据对标
# - 性能改进数据
# - 缓存效率提升
# - 用户体验改进

# 3. 更新文档
# - P2完成报告
# - 性能指标文档
# - 灰度过程记录

# ✅ 检查清单
# [ ] P2完成报告生成
# [ ] 所有指标对标完成
# [ ] 文档更新
# [ ] Git提交
```

---

## 🔄 回滚命令（如需要）

```bash
# 触发自动回滚（任意时刻）
python canary_deployment_manager.py --rollback --reason "error_rate_exceeded"

# 验证回滚
python canary_deployment_manager.py --status

# 等待一段时间观察
sleep 600  # 10分钟

# 如需重新启动，从Day 1开始
python performance_baseline_p2.py --duration 60
```

---

## 📊 关键指标监控

### 实时监控指标（每分钟收集）

```
缓存层:
  ✅ 消息缓存命中率 (Target: > 75%)
  ✅ 图片缓存命中率 (Target: > 80%)
  ✅ 配置缓存命中率 (Target: > 90%)

应用层:
  ✅ image_handler 响应时间 (Target: < 500ms)
  ✅ message_handler 响应时间 (Target: < 200ms)
  ✅ hybrid_config 响应时间 (Target: < 100ms)

系统层:
  ✅ 内存占用 (Target: < 500MB)
  ✅ CPU占用 (Target: < 15%)
  ✅ 错误率 (Target: < 0.01%)

用户层:
  ✅ P95延迟 (Target: < 100ms)
  ✅ 用户投诉 (Target: 0)
```

---

## 📁 P2相关文件

已创建的P2脚本和文档：

```
d:\AI_MIYA_Facyory\MIYA\Miya\
├── P2_PERFORMANCE_VALIDATION_PLAN.md      # 详细计划
├── P2_QUICK_START.md                      # 本文件
├── performance_baseline_p2.py              # 性能基准测试
├── canary_deployment_manager.py            # 灰度发布管理
├── p2_monitor.py                           # 灰度发布监控
├── p2_metrics.json                         # 监控指标（自动生成）
└── canary_state.json                       # 灰度状态（自动生成）
```

---

## 💡 故障排查

### 问题1: 性能基准测试失败

```bash
# 检查缓存管理器是否正确初始化
python -c "
from webnet.qq.cache_manager import QQCacheManager, CacheConfig
config = CacheConfig()
mgr = QQCacheManager(config)
print('✅ 缓存管理器初始化成功')
"

# 运行最小化测试
python performance_baseline_p2.py --duration 5 --concurrency 1
```

### 问题2: 灰度发布卡住

```bash
# 查看灰度状态
python canary_deployment_manager.py --status --verbose

# 查看灰度状态文件
cat canary_state.json

# 手动重置（如需要）
rm canary_state.json
python canary_deployment_manager.py --start-stage canary_1pct
```

### 问题3: 监控数据异常

```bash
# 检查监控配置
python p2_monitor.py

# 查看最近的指标
tail -100 p2_metrics.json

# 清理历史数据
rm p2_metrics.json
python p2_monitor.py --watch
```

---

## 🎯 P2 成功标准

| 指标 | 要求 | 状态 |
|------|------|------|
| 性能达成 | >= P1 基线 95% | ⏳ |
| 可靠性 | 错误率 < 0.01% | ⏳ |
| 灰度完成 | 4/4 阶段通过 | ⏳ |
| 用户反馈 | 0 重大投诉 | ⏳ |
| 系统稳定 | 100% 运行时间 | ⏳ |

---

## 📞 联系方式

P2阶段问题？

1. 查看 `P2_PERFORMANCE_VALIDATION_PLAN.md` 获取详细背景
2. 运行 `python performance_baseline_p2.py` 进行性能诊断
3. 查看 `canary_state.json` 了解灰度发布状态
4. 查看 `p2_metrics.json` 了解实时监控数据

---

## ✅ P2 → P3 过渡

当P2 完成后（预计Day 6）：

- ✅ 性能验证通过
- ✅ 灰度发布完成
- ✅ 用户反馈收集
- ✅ 生成完成报告

**接下来**：P3 阶段计划
- 扩展缓存到其他子网（TTSNet, VisionNet等）
- 集成分布式缓存系统
- 性能优化与监控完善

---

**🎉 P2阶段准备就绪！**

下一步：运行 `python performance_baseline_p2.py --duration 60` 验证基准性能
