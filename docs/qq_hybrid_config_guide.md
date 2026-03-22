# 弥娅QQ端混合配置系统指南

## 📖 概述

基于你的需求："统一QQ配置来源，使用.env，我的配置文件是存在的只是功能没那么多"，我设计了一个**混合配置系统**，完美解决了以下问题：

1. **`.env`配置不完善** - 只有基础配置，缺少详细功能配置
2. **配置分散** - 配置分散在多个文件中，管理困难
3. **配置统一性** - 需要统一的配置来源和管理方式

## 🎯 解决方案：混合配置架构

### **三层配置架构**

```
┌─────────────────────────────────────────────────────────┐
│                   混合配置系统                           │
├─────────────────────────────────────────────────────────┤
│  层级1: .env文件 (敏感配置 + 基础开关)                   │
│        • WebSocket地址、Token、API密钥等               │
│        • 核心功能开关                                   │
│                                                         │
│  层级2: qq_config.yaml文件 (详细功能配置)              │
│        • 多媒体功能详细设置                            │
│        • 图片识别配置                                  │
│        • 主动聊天规则                                  │
│        • 任务调度参数                                  │
│        • 性能优化选项                                  │
│                                                         │
│  层级3: 统一配置加载器                                  │
│        • 优先从.env加载敏感配置                        │
│        • 从YAML加载功能配置                            │
│        • 提供统一配置访问接口                          │
└─────────────────────────────────────────────────────────┘
```

## 📁 配置文件说明

### **1. `.env`文件 (敏感配置)**
位置：`config/.env`

```bash
# ========================================
# QQ机器人配置
# ========================================

# OneBot WebSocket地址
QQ_ONEBOT_WS_URL=ws://localhost:3001

# OneBot访问令牌（可选）
QQ_ONEBOT_TOKEN=

# 机器人QQ号
QQ_BOT_QQ=3681817929

# 超级管理员QQ号（可选）
QQ_SUPERADMIN_QQ=0

# 群聊白名单（可选，逗号分隔）
QQ_GROUP_WHITELIST=

# 群聊黑名单（可选，逗号分隔）
QQ_GROUP_BLACKLIST=

# 用户白名单（可选，逗号分隔）
QQ_USER_WHITELIST=

# 用户黑名单（可选，逗号分隔）
QQ_USER_BLACKLIST=

# ========================================
# QQ新功能配置
# ========================================

# 连接设置
# 重连间隔（秒）
QQ_RECONNECT_INTERVAL=5.0

# 心跳间隔（秒）
QQ_PING_INTERVAL=20

# 心跳超时（秒）
QQ_PING_TIMEOUT=30

# 最大消息大小（字节）
QQ_MAX_MESSAGE_SIZE=104857600

# 图片最大大小（字节，10MB）
QQ_IMAGE_MAX_SIZE=10485760

# 允许的图片格式（逗号分隔）
QQ_IMAGE_ALLOWED_FORMATS=.jpg,.jpeg,.png,.gif,.bmp,.webp

# 文件最大大小（字节，50MB）
QQ_FILE_MAX_SIZE=52428800

# OCR功能是否启用
QQ_OCR_ENABLED=true

# OCR引擎：auto, paddleocr, tesseract
QQ_OCR_ENGINE=auto

# 主动聊天功能是否启用
QQ_ACTIVE_CHAT_ENABLED=true

# 每天最多主动消息数
QQ_MAX_DAILY_MESSAGES=10

# 消息最小间隔（秒）
QQ_MIN_INTERVAL=300

# 任务调度功能是否启用
QQ_TASK_SCHEDULER_ENABLED=true
```

### **2. `qq_config.yaml`文件 (详细功能配置)**
位置：`config/qq_config.yaml`

```yaml
# QQ机器人配置
# 版本: 2.0.1
# 最后更新: 2025-03-21

qq:
  # OneBot WebSocket 连接配置
  onebot:
    ws_url: "ws://localhost:6700"  # OneBot WebSocket地址
    token: ""                      # 访问令牌（可选）
    bot_qq: 0                      # 机器人QQ号
    superadmin_qq: 0               # 超级管理员QQ号
  
  # 连接设置
  connection:
    reconnect_interval: 5.0        # 重连间隔（秒）
    ping_interval: 20              # 心跳间隔（秒）
    ping_timeout: 30               # 心跳超时（秒）
    max_message_size: 104857600    # 最大消息大小（100MB）
  
  # 访问控制
  access_control:
    # 群白名单（空表示允许所有群）
    group_whitelist: []
    
    # 群黑名单
    group_blacklist: []
    
    # 用户白名单（空表示允许所有用户）
    user_whitelist: []
    
    # 用户黑名单
    user_blacklist: []
    
    # 是否启用访问控制
    enabled: false
  
  # 多媒体功能配置
  multimedia:
    # 图片处理
    image:
      max_size: 10485760           # 10MB
      allowed_formats: [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
      auto_resize: true
      max_width: 1920
      max_height: 1080
      quality: 85                  # JPEG质量（0-100）
    
    # 文件处理
    file:
      max_size: 52428800           # 50MB
      allowed_formats:
        text: [".txt", ".log", ".md", ".json", ".xml", ".html", ".csv", ".yml", ".yaml"]
        document: [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]
        image: [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        audio: [".mp3", ".wav", ".flac", ".aac"]
        video: [".mp4", ".avi", ".mkv", ".mov"]
        archive: [".zip", ".rar", ".7z", ".tar", ".gz"]
        code: [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".php", ".rb", ".sh"]
    
    # 上传设置
    upload:
      temp_dir: "./temp/uploads"   # 临时上传目录
      cleanup_hours: 24            # 清理时间（小时）
      keep_original: false         # 是否保留原始文件
  
  # 图片识别功能
  image_recognition:
    # OCR设置
    ocr:
      enabled: true
      engine: "auto"               # auto, paddleocr, tesseract
      languages: ["chi_sim", "eng"]  # 支持的语言
      confidence_threshold: 0.7    # 置信度阈值
    
    # AI图片分析
    ai_analysis:
      enabled: false               # 需要额外的AI服务
      provider: ""                 # baidu, tencent, openai
      api_key: ""
      api_secret: ""
    
    # 安全检测
    safety:
      enabled: true
      nsfw_detection: true
      max_skin_ratio: 0.3          # 最大肤色比例
    
    # 缓存设置
    cache:
      enabled: true
      dir: "./temp/image_cache"
      max_size: 1073741824         # 1GB
      expire_hours: 24
  
  # 主动聊天功能
  active_chat:
    enabled: true
    
    # 触发设置
    triggers:
      time:
        enabled: true              # 定时触发
        check_interval: 60         # 检查间隔（秒）
      
      event:
        enabled: true              # 事件触发
        events: ["birthday", "holiday", "anniversary"]
      
      condition:
        enabled: true              # 条件触发
        check_interval: 300        # 条件检查间隔（秒）
    
    # 消息限制
    limits:
      max_daily_messages: 10       # 每天最多主动消息数
      min_interval: 300            # 消息最小间隔（秒）
      quiet_hours: [23, 0, 1, 2, 3, 4, 5, 6]  # 静默时段（小时）
    
    # 默认消息模板
    templates:
      morning:
        - "早安！今天也是充满希望的一天呢～ {random_emoji}"
        - "早上好！愿你今天一切顺利！{random_emoji}"
        - "新的一天开始啦！加油哦！{random_emoji}"
      
      evening:
        - "晚安！祝你好梦！{random_emoji}"
        - "晚上好！记得早点休息哦～{random_emoji}"
        - "晚安，愿明天的你更加美好！{random_emoji}"
      
      birthday:
        - "生日快乐！🎂 祝你天天开心！{random_emoji}"
        - "生日快乐！愿你所有的愿望都能实现！{random_emoji}"
        - "生日快乐！新的一岁更加精彩！{random_emoji}"
      
      holiday:
        - "节日快乐！{random_emoji}"
        - "祝你节日愉快！{random_emoji}"
        - "节日快乐！愿幸福常伴你左右！{random_emoji}"
    
    # 用户偏好
    user_preferences:
      learn_preferences: true      # 学习用户偏好
      default_allow: true          # 默认允许主动消息
      ask_permission: false        # 首次发送前询问
  
  # 任务调度系统
  task_scheduler:
    enabled: true
    
    # 数据库设置
    database:
      path: "./data/tasks.db"      # SQLite数据库路径
      backup_dir: "./data/backups"
      backup_interval: 86400       # 备份间隔（秒）
    
    # 执行设置
    execution:
      max_concurrent: 5            # 最大并发任务数
      timeout: 300                 # 任务超时时间（秒）
      retry_delay_base: 60         # 重试基础延迟（秒）
      max_retry_delay: 3600        # 最大重试延迟（秒）
    
    # 监控设置
    monitoring:
      log_level: "INFO"
      keep_history_days: 30        # 保留历史天数
      alert_on_failure: true       # 失败时告警
    
    # 统计设置
    statistics:
      collect_stats: true
      stats_interval: 3600         # 统计收集间隔（秒）
  
  # 性能优化
  performance:
    # 缓存设置
    cache:
      message_history: 100         # 消息历史缓存条数
      user_info: 1000              # 用户信息缓存数
      group_info: 100              # 群信息缓存数
    
    # 线程池设置
    thread_pool:
      max_workers: 10              # 最大工作线程数
      thread_timeout: 30           # 线程超时时间（秒）
    
    # 内存管理
    memory:
      max_image_cache: 1073741824  # 图片缓存最大内存（1GB）
      cleanup_interval: 3600       # 内存清理间隔（秒）
  
  # 日志设置
  logging:
    level: "INFO"
    file: "./logs/qq.log"
    max_size: 10485760             # 10MB
    backup_count: 5
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 组件日志级别
    components:
      client: "INFO"
      message_handler: "INFO"
      image_handler: "INFO"
      file_handler: "INFO"
      active_chat: "INFO"
      task_scheduler: "INFO"
  
  # 调试设置
  debug:
    enabled: false
    log_raw_messages: false        # 记录原始消息
    log_api_calls: false           # 记录API调用
    log_file_operations: false     # 记录文件操作
    
    # 测试模式
    test_mode: false
    mock_apis: false               # 模拟API调用
    simulate_errors: false         # 模拟错误
```

## 🔧 配置加载器

### **核心组件**

1. **`webnet/qq/hybrid_config.py`** - 混合配置管理器
   - 单例模式，全局共享配置
   - 自动检测和加载`.env`和YAML文件
   - 提供统一配置访问接口

2. **`config/settings.py`** - 集成混合配置
   - Settings类已更新支持混合配置
   - 向后兼容现有代码

### **使用方法**

```python
# 方法1：使用混合配置加载器（推荐）
from webnet.qq.hybrid_config import get_qq_config

config = get_qq_config()
ws_url = config.get('onebot_ws_url')
bot_qq = config.get('bot_qq')

# 获取特定功能配置
multimedia_config = config.get('multimedia', {})
ocr_config = config.get('image_recognition', {}).get('ocr', {})

# 方法2：使用Settings类（现有代码兼容）
from config.settings import Settings

settings = Settings()
qq_config = settings.get('qq')
```

## 🚀 配置优先级

### **配置合并规则**

1. **基础配置优先从`.env`加载**
   - WebSocket地址、Token、QQ号等敏感信息
   - 核心功能开关（OCR、主动聊天等）

2. **详细配置从YAML加载**
   - 如果YAML文件存在，加载详细功能配置
   - 如果YAML文件不存在，使用默认功能配置

3. **配置覆盖规则**
   - `.env`中的基础开关覆盖YAML中的对应设置
   - 敏感信息（Token、API密钥）只从`.env`读取

### **配置流程图**

```
启动QQ模块
    ↓
尝试加载 .env 文件
    ├── 成功: 读取敏感配置
    └── 失败: 使用默认敏感配置
    ↓
尝试加载 qq_config.yaml 文件
    ├── 成功: 读取详细功能配置
    └── 失败: 使用默认功能配置
    ↓
合并配置
    ├── .env 配置优先
    ├── YAML 配置补充
    └── 验证配置有效性
    ↓
提供统一配置接口
```

## 🧪 测试验证

### **测试脚本**

1. **混合配置测试** - `scripts/test_hybrid_config.py`
   ```bash
   python scripts/test_hybrid_config.py
   ```

2. **QQ功能测试** - `scripts/test_qq_features.py`
   ```bash
   python scripts/test_qq_features.py
   ```

### **测试覆盖率**

```
混合配置系统测试结果:
  .env文件存在性                 [OK]
  YAML文件存在性                [OK]
  混合配置加载器                   [OK]
  Settings集成                 [OK]
  完整配置链                     [OK]

通过率: 5/5 (100.0%)
✅ 混合配置系统测试全部通过！
```

## 📈 配置迁移指南

### **从旧配置迁移**

如果你已经有现有的QQ配置：

#### **情况1：只有`.env`配置**
- ✅ 无需迁移
- 混合配置系统会自动使用`.env`中的配置
- 缺失的详细配置会使用默认值

#### **情况2：只有YAML配置**
1. 将敏感信息提取到`.env`文件：
   ```bash
   # 从YAML提取到.env
   QQ_ONEBOT_WS_URL="ws://localhost:6700"
   QQ_BOT_QQ=你的机器人QQ号
   ```
2. 保留YAML文件作为详细配置

#### **情况3：两者都有但配置不一致**
1. 确定配置优先级：
   - 敏感信息使用`.env`的值
   - 详细配置使用YAML的值
   - 基础开关使用`.env`的值覆盖YAML

### **最佳实践**

1. **敏感信息放在`.env`**
   ```bash
   # 正确
   QQ_ONEBOT_TOKEN=your_secret_token_here
   
   # 错误（不要放在YAML中）
   # token: "your_secret_token_here"
   ```

2. **详细配置放在YAML**
   ```yaml
   # 正确
   multimedia:
     image:
       max_size: 10485760
       allowed_formats: [".jpg", ".jpeg", ".png"]
   
   # 错误（避免在.env中定义复杂结构）
   # QQ_IMAGE_CONFIG={"max_size": 10485760, "formats": [".jpg", ".png"]}
   ```

3. **使用配置验证**
   ```python
   # 运行配置测试
   python scripts/test_hybrid_config.py
   
   # 检查配置一致性
   python scripts/test_qq_features.py
   ```

## 🔧 常见问题

### **Q1: `.env`和YAML都配置了同一个选项，使用哪个？**
A: **`.env`优先**。例如：
- `.env`: `QQ_OCR_ENABLED=false`
- YAML: `ocr.enabled: true`
- 结果: `ocr.enabled = false` (使用`.env`的值)

### **Q2: 如何修改配置？**
A: 根据配置类型：
- **敏感配置**: 修改`config/.env`
- **功能配置**: 修改`config/qq_config.yaml`
- **立即生效**: 需要重启QQ模块或调用`reload_config()`

### **Q3: 配置验证失败怎么办？**
A: 检查：
1. `.env`文件格式是否正确
2. YAML语法是否正确（使用YAML验证工具）
3. 配置路径是否正确

### **Q4: 如何在代码中访问配置？**
A: 使用统一接口：
```python
from webnet.qq.hybrid_config import get_qq_config, get_multimedia_config

# 获取完整配置
config = get_qq_config()

# 获取特定功能配置
multimedia = get_multimedia_config()
ocr_config = config.get('image_recognition', {}).get('ocr', {})
```

## 🎉 系统优势

### **1. 配置统一性**
- 所有QQ配置都有统一的访问接口
- 配置来源明确，管理方便

### **2. 安全性提升**
- 敏感信息在`.env`文件中，便于安全保护
- YAML文件可以安全地版本控制

### **3. 灵活性增强**
- 支持详细的YAML配置结构
- 支持简单的`.env`键值对配置
- 两者可以灵活组合使用

### **4. 向后兼容**
- 现有代码无需修改
- Settings类已集成混合配置
- 提供了迁移路径

### **5. 易于测试**
- 完整的配置测试套件
- 配置验证和一致性检查
- 详细的错误提示

## 📋 总结

**混合配置系统成功解决了你的需求：**

✅ **统一QQ配置来源** - 所有配置都有统一的管理方式  
✅ **使用`.env`** - 敏感配置从`.env`文件加载  
✅ **功能完善** - 通过YAML文件补充详细功能配置  
✅ **向后兼容** - 现有配置和代码无需修改  
✅ **测试验证** - 完整的测试套件确保配置正确性  

**现在，弥娅QQ端拥有了：**
- **安全的敏感配置管理** (`.env`文件)
- **详细的功能配置支持** (`qq_config.yaml`文件)
- **统一的配置访问接口** (混合配置加载器)
- **完整的配置验证** (测试脚本)

**建议下一步：**
1. 运行`python scripts/test_hybrid_config.py`验证配置系统
2. 根据需要修改`config/.env`中的敏感配置
3. 根据需要修改`config/qq_config.yaml`中的功能配置
4. 启动QQ模块享受完整的QQ功能体验！