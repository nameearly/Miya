# 主动聊天动态生成系统

## 概述

主动聊天动态生成系统是弥娅主动聊天功能的核心组件，实现了完全动态化的话题生成，移除了所有硬编码的预设模板。

## 主要特性

### 1. 插件式架构
- **时间感知插件**：根据时间段生成合适的问候和话题
- **情绪感知插件**：分析用户情绪，生成关怀话题
- **兴趣学习插件**：学习用户兴趣，生成相关话题
- **上下文感知插件**：跟进用户提到的活动、计划等
- **生成策略插件**：智能选择最佳生成策略

### 2. 配置驱动
所有配置集中在 `config/personalities/_base.yaml` 的 `proactive_chat` 部分：

```yaml
proactive_chat:
  enabled: true
  check_interval: 60
  max_daily_messages: 10
  quiet_hours: [23, 0, 1, 2, 3, 4, 5, 6]
  
  # 时间感知配置
  time_awareness:
    enabled: true
    time_slots:
      morning:
        start: 6
        end: 9
        topics:
          - category: "health"
            weight: 0.3
```

### 3. 热重载机制
- **文件监控**：监控配置文件变化
- **定时检查**：可配置间隔（默认300秒）
- **手动触发**：支持API接口、命令行、配置文件标记三种方式

### 4. 失败处理
- 动态生成失败时记录日志并跳过
- 连续失败次数过多时自动暂停
- 提供详细的错误信息

## 目录结构

```
config/proactive_chat/
├── __init__.py
├── dynamic_message_generator.py  # 主生成器类
├── plugins/
│   ├── __init__.py
│   ├── base_plugin.py            # 插件基类
│   ├── time_awareness/
│   │   ├── config.yaml
│   │   └── plugin.py
│   ├── emotion_perception/
│   │   ├── config.yaml
│   │   └── plugin.py
│   ├── interest_learning/
│   │   ├── config.yaml
│   │   └── plugin.py
│   ├── context_awareness/
│   │   ├── config.yaml
│   │   └── plugin.py
│   └── generation_strategy/
│       ├── config.yaml
│       └── plugin.py
├── config/
│   ├── __init__.py
│   ├── loader.py                 # 配置加载器
│   └── reloader.py               # 配置热重载器
└── utils/
    ├── __init__.py
    ├── validators.py             # 消息验证器
    └── helpers.py                # 辅助函数
```

## 使用方法

### 1. 初始化

```python
from config.proactive_chat import DynamicMessageGenerator

generator = DynamicMessageGenerator()
await generator.initialize()
```

### 2. 生成消息

```python
message = await generator.generate_message(user_id=12345, context={"message": "早上好"})
if message:
    print(f"生成的消息: {message}")
else:
    print("动态生成失败，跳过发送")
```

### 3. 重载配置

```python
await generator.reload_config()
```

## 配置说明

### 基本配置
- `enabled`: 是否启用主动聊天
- `check_interval`: 检查间隔（秒）
- `max_daily_messages`: 每日最大消息数
- `quiet_hours`: 静默时段（小时）

### 时间感知配置
- `time_slots`: 时间段配置
- 每个时间段可以配置不同的话题和权重

### 情绪感知配置
- `emotion_keywords`: 情绪关键词
- `response_strategies`: 情绪响应策略

### 兴趣学习配置
- `categories`: 兴趣分类
- `learning_params`: 学习参数

### 上下文感知配置
- `context_types`: 上下文类型
- `follow_up_params`: 跟进参数

### 生成策略配置
- `strategies`: 生成策略
- `selection_params`: 选择参数

## 测试

### 单元测试
```bash
python -m pytest tests/proactive_chat/
```

### 集成测试
```bash
python tests/proactive_chat/integration_test.py
```

### 手动测试
```bash
python tests/proactive_chat/manual_test.py
```

## 注意事项

1. **性能考虑**：动态生成可能比模板生成稍慢，但提供了更好的个性化体验
2. **失败处理**：动态生成失败时会跳过发送，不会影响系统稳定性
3. **配置热重载**：配置修改后会自动重载，无需重启系统
4. **向后兼容**：保留了传统生成方法作为备用

## 更新日志

### v1.0.0
- 实现插件式动态生成架构
- 移除所有硬编码模板
- 添加热重载机制
- 支持时间、情绪、兴趣、上下文感知