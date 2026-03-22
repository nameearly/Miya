# 弥娅QQ端功能增强指南

## 概述

弥娅QQ端已经进行了全面的功能增强，增加了图片发送、文件处理、表情包管理、图片识别、主动聊天等多项新功能。本文档提供这些功能的详细使用说明。

## 新功能列表

### 1. 多媒体发送功能
- **图片发送**：支持本地图片、网络图片、Base64图片
- **文件发送**：支持多种格式文件上传和发送
- **表情包发送**：内置表情包和自定义表情包管理

### 2. 智能识别功能
- **图片文字识别**：自动识别图片中的文字
- **图片内容分析**：分析图片内容并进行描述
- **文件内容读取**：读取TXT、PDF、DOCX等格式文件

### 3. 主动交互功能
- **主动聊天**：定时或条件触发主动消息
- **智能提醒**：生日、节日、纪念日提醒
- **用户关怀**：基于用户行为的主动关心

### 4. 任务调度功能
- **增强定时任务**：支持失败重试、优先级管理
- **任务持久化**：重启后自动恢复任务
- **任务监控**：详细的执行日志和统计

## 快速开始

### 1. 配置设置

在 `config/qq_config.yaml` 中配置QQ端：

```yaml
qq:
  onebot:
    ws_url: "ws://localhost:6700"  # OneBot WebSocket地址
    token: ""                      # 访问令牌
    bot_qq: 123456789              # 机器人QQ号
    
  # 启用所需功能
  multimedia:
    image:
      enabled: true
    file:
      enabled: true
      
  image_recognition:
    ocr:
      enabled: true
      
  active_chat:
    enabled: true
```

### 2. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 或安装QQ扩展依赖（如果单独安装）
pip install -r requirements/qq_extras.txt
```

### 3. 启动测试

```bash
# 运行功能测试
python scripts/test_qq_features.py
```

## 功能详细说明

### 图片发送功能

#### 基础使用
```
用户：发一张图片
弥娅：[发送图片]
```

#### 高级选项
- 支持多种图片来源：
  - 本地文件路径
  - 网络图片URL
  - Base64编码图片
- 自动图片压缩
- 支持图片说明文字

#### 工具命令
```bash
# 发送本地图片
工具：qq_image
参数：
  action: send
  target_type: group
  target_id: 123456
  image_source: local
  image_path: /path/to/image.jpg
  caption: "这是一张风景图"
```

### 文件发送功能

#### 支持的文件类型
- **文本文件**：.txt, .log, .md, .json, .xml
- **文档文件**：.pdf, .doc, .docx, .xls, .xlsx
- **图片文件**：.jpg, .png, .gif, .bmp
- **音视频文件**：.mp3, .mp4, .wav
- **压缩文件**：.zip, .rar, .7z
- **代码文件**：.py, .js, .ts, .java

#### 工具命令
```bash
# 发送文件
工具：qq_file
参数：
  action: send
  target_type: private
  target_id: 987654321
  file_path: /path/to/document.pdf
  description: "项目报告PDF文件"
```

### 文件读取功能

#### 自动识别文件内容
当用户发送文件时，弥娅会自动：
1. 检测文件类型
2. 提取文件内容
3. 生成内容摘要
4. 回答相关问题

#### 使用示例
```
用户：[发送 report.pdf]
弥娅：📄 收到PDF文件：report.pdf (1.2MB)
      文档类型：项目进度报告
      页数：15页
      关键词：项目、报告、数据分析
      
      需要我提取具体内容吗？
```

#### 支持的操作
- **read**: 读取文件内容
- **analyze**: 分析文档结构
- **search**: 搜索关键词
- **summary**: 生成内容摘要

### 图片识别功能

#### OCR文字识别
```
用户：[发送包含文字的图片]
弥娅：🔍 识别到图片中的文字：
      "这是一个测试文档"
      "创建时间：2025-03-21"
      
      文字已识别完成！
```

#### 图片内容分析
- **基本分析**：尺寸、格式、文件大小
- **文字识别**：自动OCR识别
- **安全检测**：NSFW内容检测
- **AI描述**：图片内容描述（需要额外配置）

#### 工具命令
```bash
# 分析图片
工具：qq_image_analyzer
参数：
  action: analyze
  image_source: url
  image_url: "https://example.com/image.jpg"
  detail_level: detailed
```

### 主动聊天功能

#### 定时消息
```
用户：每天早上8点给我发早安
弥娅：✅ 已设置定时消息：每天 08:00
      消息模板："早安！今天也是充满希望的一天呢～"
```

#### 触发类型
1. **定时触发**：每天固定时间
2. **事件触发**：生日、节日、纪念日
3. **条件触发**：用户长时间不在线、遇到问题

#### 设置示例
```bash
# 设置早安消息
工具：qq_active_chat
参数：
  action: setup
  trigger_type: time
  schedule: "08:00"
  message_template: "早安！{username}，新的一天开始啦！"
  target_type: private
  target_id: 987654321
```

#### 内置模板
- **早安模板**：多种早安问候语
- **晚安模板**：温馨的晚安消息
- **生日模板**：生日祝福
- **节日模板**：节日问候

### 增强定时任务系统

#### 任务类型
1. **消息发送任务**：定时发送QQ消息
2. **文件发送任务**：定时发送文件
3. **系统操作任务**：执行系统命令
4. **API调用任务**：调用外部API

#### 高级特性
- **失败重试**：指数退避重试策略
- **任务优先级**：优先级管理
- **依赖管理**：任务依赖关系
- **持久化存储**：重启自动恢复
- **详细监控**：执行日志和统计

#### 创建任务示例
```bash
# 创建定时任务
工具：create_schedule_task
参数：
  task_type: qq_message
  task_name: "每日早安"
  cron_expression: "0 8 * * *"
  target_type: group
  target_id: 123456
  message: "大家早上好！新的一天开始啦～"
  enabled: true
```

## 配置详解

### 多媒体配置
```yaml
multimedia:
  image:
    max_size: 10485760           # 10MB限制
    allowed_formats: [".jpg", ".png", ".gif"]
    auto_resize: true
    max_width: 1920
    max_height: 1080
    
  file:
    max_size: 52428800           # 50MB限制
    allowed_formats:
      text: [".txt", ".md", ".json"]
      document: [".pdf", ".docx"]
      code: [".py", ".js"]
```

### 图片识别配置
```yaml
image_recognition:
  ocr:
    enabled: true
    engine: "paddleocr"          # 或 "tesseract"
    languages: ["chi_sim", "eng"]
    confidence_threshold: 0.7
    
  ai_analysis:
    enabled: false               # 需要AI服务
    provider: "openai"           # 或 "baidu", "tencent"
```

### 主动聊天配置
```yaml
active_chat:
  enabled: true
  limits:
    max_daily_messages: 10       # 每天最多消息数
    min_interval: 300            # 消息最小间隔（秒）
    quiet_hours: [23, 0, 1, 2, 3, 4, 5, 6]  # 静默时段
    
  templates:
    morning:
      - "早安！今天也是充满希望的一天呢～ {random_emoji}"
      - "早上好！愿你今天一切顺利！{random_emoji}"
```

### 任务调度配置
```yaml
task_scheduler:
  enabled: true
  execution:
    max_concurrent: 5            # 最大并发任务
    timeout: 300                 # 任务超时（秒）
    max_retries: 3               # 最大重试次数
    
  database:
    path: "./data/tasks.db"      # SQLite数据库
    backup_interval: 86400       # 备份间隔（秒）
```

## 使用场景示例

### 场景1：工作提醒
```
用户：每周一上午10点提醒我开周会
弥娅：✅ 已设置周会提醒：每周一 10:00
      消息："周会时间到啦！记得参加会议哦～"
```

### 场景2：学习助手
```
用户：[发送学习笔记.pdf]
弥娅：📚 识别到学习笔记PDF，共25页
      主要章节：第一章 引言，第二章 理论基础
      关键词：机器学习、深度学习、神经网络
      
      需要我提取具体章节内容吗？
```

### 场景3：社交互动
```
用户：[发送聚会照片.jpg]
弥娅：📸 识别到聚会照片，检测到5个人物
      图片文字："毕业十周年聚会"
      图片描述：一群人在餐厅庆祝
      
      看起来玩得很开心呢！
```

### 场景4：文件管理
```
用户：帮我整理一下这个月的报告
弥娅：📁 收到3个文件：
      1. report1.pdf - 项目进展报告
      2. data.xlsx - 数据统计表
      3. summary.txt - 月度总结
      
      已为您生成综合报告摘要。
```

## 故障排除

### 常见问题

#### 1. 图片发送失败
- **检查**：图片文件是否存在
- **检查**：图片格式是否支持
- **检查**：文件大小是否超限
- **解决**：压缩图片或使用网络链接

#### 2. OCR识别不准确
- **检查**：图片清晰度
- **检查**：语言配置是否正确
- **解决**：调整OCR引擎或参数

#### 3. 主动聊天不工作
- **检查**：配置文件中是否启用
- **检查**：静默时段设置
- **检查**：消息限制配置

#### 4. 文件读取失败
- **检查**：文件编码是否正确
- **检查**：文件是否损坏
- **检查**：依赖包是否安装完整

### 日志查看
日志文件位于：`logs/qq.log`
```bash
# 查看实时日志
tail -f logs/qq.log

# 查看错误日志
grep -i error logs/qq.log
```

## 高级功能

### AI图片描述
需要配置AI服务：
```yaml
image_recognition:
  ai_analysis:
    enabled: true
    provider: "openai"
    api_key: "your-openai-api-key"
```

### 自定义表情包
1. 创建目录：`data/emojis/`
2. 添加表情包图片
3. 配置表情包映射

### 任务依赖链
```bash
# 创建依赖任务
任务1：下载文件
任务2：处理文件（依赖任务1）
任务3：发送结果（依赖任务2）
```

## 性能优化建议

### 图片处理
- 启用图片缓存
- 调整图片压缩质量
- 限制并发处理数量

### 文件读取
- 使用流式读取大文件
- 启用编码检测缓存
- 限制最大预览长度

### 主动聊天
- 调整检查间隔
- 优化用户偏好学习
- 限制每日消息数量

## 更新日志

### v2.0.1 (2025-03-21)
- ✅ 新增图片发送功能
- ✅ 新增文件发送功能
- ✅ 新增表情包发送功能
- ✅ 新增图片识别功能
- ✅ 新增文件读取功能
- ✅ 新增主动聊天功能
- ✅ 新增增强定时任务
- ✅ 完善配置系统和文档

## 技术支持

### 文档资源
- `docs/qq_features_guide.md` - 功能指南
- `config/qq_config.yaml` - 配置示例
- `scripts/test_qq_features.py` - 测试脚本

### 问题反馈
1. 查看日志文件
2. 运行测试脚本
3. 检查依赖包
4. 提交问题报告

---

**注意**：部分高级功能需要额外的AI服务或API密钥，请根据实际需求配置。