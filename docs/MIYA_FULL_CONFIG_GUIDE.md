# 弥娅（MIYA）完整配置教学文档

## 📖 文档概述

本文档是弥娅系统的**完整配置指南**，涵盖了QQ机器人匹配、模型配置、环境设置等所有必要的配置步骤。特别针对**智谱GLM-4.6V-Flash免费多模态模型**进行了详细配置。

## 🎯 配置目标

1. **QQ机器人完美匹配** - 配置QQ机器人连接和功能
2. **模型池优化配置** - 智能路由三家厂商模型
3. **GLM-4.6V-Flash免费模型** - 配置智谱最新免费多模态模型
4. **系统环境完整设置** - 从零开始部署弥娅

## 📁 文件结构

```
MIYA/
├── config/                    # 配置文件目录
│   ├── .env                  # 环境变量（敏感配置）
│   ├── .env.example          # 环境变量示例
│   ├── settings.py           # 主配置文件
│   ├── qq_config.yaml        # QQ详细配置
│   ├── unified_model_config.yaml  # 统一模型配置
│   └── multi_model_config.json    # 多模型配置
├── webnet/qq/                # QQ核心模块
│   ├── core.py              # QQ主程序
│   ├── hybrid_config.py     # 混合配置加载器
│   └── handlers/            # 消息处理器
├── core/                     # 核心模块
│   └── model_pool.py        # 模型池管理器
├── scripts/                  # 脚本目录
│   ├── test_hybrid_config.py # 混合配置测试
│   ├── test_qq_features.py   # QQ功能测试
│   └── test_model_pool.py    # 模型池测试
└── docs/                     # 文档目录
```

## 🔧 第一部分：环境配置

### 1.1 安装Python环境

```bash
# 1. 确保Python 3.9+已安装
python --version

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

### 1.2 配置环境变量

复制环境变量模板并编辑：

```bash
# 复制示例文件
cp config/.env.example config/.env

# 编辑配置文件
vim config/.env
```

### 1.3 关键环境变量配置

#### **API密钥配置**
```bash
# ========================================
# 硅基流动配置（优先使用）
# ========================================
SILICONFLOW_API_KEY=sk-lbybyiqrbaxasvwmspsoxulfkrprzibertsjanyaurcxbird
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# ========================================
# DeepSeek 官方配置（备选）
# ========================================
DEEPSEEK_API_KEY=sk-15346aa170c442c69d726d8e95cabca3
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# ========================================
# 智谱AI配置（重点！）
# ========================================
ZHIPU_API_KEY=61d87875c2bf4444975409c6df476009.nflDzcqzdHwzTApF
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_GLM_46V_FLASH_MODEL=glm-4.6v-flash  # 免费多模态模型
ZHIPU_GLM_4V_MODEL=glm-4v                 # 付费多模态模型
ZHIPU_GLM_4_MODEL=glm-4                   # 文本模型
ZHIPU_GLM_4_PLUS_MODEL=glm-4-plus         # 增强模型
```

#### **QQ机器人配置**
```bash
# ========================================
# QQ机器人连接配置
# ========================================
# OneBot WebSocket地址（根据你的QQ机器人设置）
QQ_ONEBOT_WS_URL=ws://localhost:3001
QQ_ONEBOT_TOKEN=your_token_here          # 如果需要Token验证

# 机器人QQ号
QQ_BOT_QQ=3681817929

# 超级管理员QQ号
QQ_SUPERADMIN_QQ=1234567890

# 白名单和黑名单
QQ_GROUP_WHITELIST=123456789,987654321    # 允许的群聊
QQ_GROUP_BLACKLIST=                        # 禁止的群聊
QQ_USER_WHITELIST=1234567890,9876543210   # 允许的用户
QQ_USER_BLACKLIST=                        # 禁止的用户

# 连接设置
QQ_RECONNECT_INTERVAL=5.0                 # 重连间隔（秒）
QQ_PING_INTERVAL=20                       # 心跳间隔（秒）
QQ_PING_TIMEOUT=30                        # 心跳超时（秒）
QQ_MAX_MESSAGE_SIZE=104857600             # 最大消息大小（100MB）
```

## 🤖 第二部分：QQ机器人配置

### 2.1 QQ机器人设置（以NoneBot为例）

#### **安装NoneBot**
```bash
pip install nonebot2 nonebot-adapter-onebot
```

#### **配置OneBot连接**
```yaml
# config/qq_config.yaml 中的OneBot配置
onebot:
  # WebSocket连接配置
  ws:
    host: "127.0.0.1"
    port: 3001
    access_token: "your_token_here"
  
  # HTTP连接配置（可选）
  http:
    host: "127.0.0.1"
    port: 5700
    access_token: "your_token_here"
  
  # 反向WebSocket配置
  reverse_ws:
    - host: "127.0.0.1"
      port: 3002
      access_token: "your_token_here"
```

### 2.2 QQ功能配置详解

#### **多媒体功能配置**
```yaml
# config/qq_config.yaml
multimedia:
  image:
    max_size: 10485760                     # 图片最大大小：10MB
    allowed_formats:                        # 允许的格式
      - ".jpg"
      - ".jpeg"
      - ".png"
      - ".gif"
      - ".webp"
    compress: true                         # 是否压缩图片
    compress_quality: 80                   # 压缩质量（百分比）
  
  file:
    max_size: 52428800                     # 文件最大大小：50MB
    allowed_extensions:                    # 允许的扩展名
      - ".txt"
      - ".pdf"
      - ".doc"
      - ".docx"
      - ".zip"
```

#### **图片识别配置**
```yaml
image_recognition:
  ocr:
    enabled: true                          # 启用OCR功能
    engine: "paddleocr"                    # OCR引擎
    languages: ["ch", "en"]                # 支持语言
    confidence_threshold: 0.7              # 置信度阈值
  
  ai_analysis:
    enabled: true                          # 启用AI图片分析
    model: "zhipu_glm_46v_flash"           # 使用GLM-4.6V-Flash
    max_analysis_time: 30                  # 最大分析时间（秒）
    
  safety:
    enabled: true                          # 启用安全检测
    nsfw_detection: true                   # NSFW内容检测
    content_safety: true                   # 内容安全分析
```

#### **主动聊天配置**
```yaml
active_chat:
  enabled: true                            # 启用主动聊天
  triggers:                                # 触发条件
    inactivity_threshold: 3600             # 无活动阈值（秒）
    time_based: true                       # 基于时间触发
    
  limits:                                  # 限制条件
    max_daily_messages: 10                 # 每日最大消息数
    min_interval: 300                      # 最小间隔（5分钟）
    per_user_daily_limit: 3                # 每用户每日限制
    
  templates:                               # 消息模板
    - "今天过得怎么样？"
    - "有什么需要帮助的吗？"
    - "最近发现了什么有趣的事情？"
```

## 🧠 第三部分：模型池配置

### 3.1 统一模型配置系统

#### **配置结构**
```yaml
# config/unified_model_config.yaml
models:
  # 文本模型
  siliconflow_qwen_7b:
    name: "Qwen/Qwen2.5-7B-Instruct"
    type: "text"
    provider: "siliconflow"
    description: "Qwen 2.5 7B - 快速通用模型（免费）"
    cost_per_1k_tokens:
      input: 0.0001
      output: 0.0002
  
  # 重点：GLM-4.6V-Flash免费模型
  zhipu_glm_46v_flash:
    name: "glm-4.6v-flash"
    type: "vision"
    provider: "zhipu"
    description: "GLM-4.6V-Flash - 智谱最新免费多模态模型"
    cost_per_1k_tokens:
      input: 0.0    # 完全免费！
      output: 0.0   # 完全免费！
    max_image_size: "20MB"
    priority: 1.0   # 最高优先级
```

### 3.2 智能路由策略

#### **路由配置**
```yaml
model_routing:
  tasks:
    # 简单聊天 - 优先免费模型
    simple_chat:
      primary: "siliconflow_qwen_7b"      # 硅基流动免费
      secondary: "deepseek_v3_official"    # DeepSeek性能
      fallback: "zhipu_glm_4"              # 智谱中文优化
    
    # 图片描述 - 优先免费视觉模型
    image_description:
      primary: "zhipu_glm_46v_flash"       # GLM-4.6V-Flash（免费）
      secondary: "zhipu_glm_4v"            # GLM-4V（付费）
      fallback: "siliconflow_qwen_vl"      # Qwen视觉模型
      cost_priority: 1.0                   # 成本优先级最高
    
    # 代码生成
    code_generation:
      primary: "siliconflow_glm_4"         # GLM-4代码能力强
      secondary: "deepseek_v3_official"    # DeepSeek通用
      fallback: "siliconflow_qwen_7b"      # Qwen基础
```

### 3.3 端特定配置

#### **QQ端模型配置**
```yaml
endpoints:
  qq:
    # QQ端启用的模型
    enabled_models:
      - "siliconflow_qwen_7b"      # 基础聊天
      - "siliconflow_glm_4"        # 代码分析
      - "deepseek_v3_official"     # 高性能聊天
      - "zhipu_glm_4"              # 中文聊天
      - "paddleocr"                # 文字识别
      - "zhipu_glm_46v_flash"      # 免费多模态（重点！）
      - "zhipu_glm_4v"             # 付费多模态
      - "nsfw_detector"            # 安全检测
    
    # 默认模型选择
    defaults:
      chat: "siliconflow_qwen_7b"          # 日常聊天
      code_analysis: "siliconflow_glm_4"   # 代码相关
      ocr: "paddleocr"                     # 文字识别
      image_analysis: "zhipu_glm_46v_flash" # 图片分析（免费！）
      safety_check: "nsfw_detector"        # 安全检测
```

## 🔍 第四部分：GLM-4.6V-Flash详细配置

### 4.1 模型特点

**GLM-4.6V-Flash优势：**
- ✅ **完全免费** - 无需付费，无限使用
- ✅ **高性能** - 支持20MB大图片
- ✅ **多模态** - 图片理解、文字识别、文档分析
- ✅ **实时分析** - 响应速度快
- ✅ **中文优化** - 专门优化中文内容理解

### 4.2 配置步骤

#### **步骤1：添加环境变量**
```bash
# 在config/.env中添加
ZHIPU_GLM_46V_FLASH_MODEL=glm-4.6v-flash
```

#### **步骤2：配置模型定义**
```yaml
# 在config/unified_model_config.yaml中添加
zhipu_glm_46v_flash:
  name: "${ZHIPU_GLM_46V_FLASH_MODEL:-glm-4.6v-flash}"
  type: "vision"
  provider: "zhipu"
  base_url: "${ZHIPU_API_BASE:-https://open.bigmodel.cn/api/paas/v4}"
  api_key: "${ZHIPU_API_KEY}"
  description: "GLM-4.6V-Flash - 智谱最新免费多模态模型"
  capabilities:
    - "image_description"
    - "visual_qa"
    - "document_understanding"
    - "image_analysis"
    - "real_time_analysis"
  cost_per_1k_tokens:
    input: 0.0    # 免费
    output: 0.0   # 免费
  max_image_size: "20MB"
  priority: 1.0   # 最高优先级
```

#### **步骤3：配置路由**
```yaml
# 更新路由配置，将GLM-4.6V-Flash设为默认
image_description:
  primary: "zhipu_glm_46v_flash"       # 优先使用免费模型
  secondary: "zhipu_glm_4v"            # 备选付费模型
  fallback: "siliconflow_qwen_vl"      # 备选其他模型
  cost_priority: 1.0                   # 成本优先级最高
```

#### **步骤4：配置QQ端**
```yaml
# 在QQ端配置中启用
qq:
  enabled_models:
    - "zhipu_glm_46v_flash"            # 添加免费模型
  
  defaults:
    image_analysis: "zhipu_glm_46v_flash"  # 设为默认图片分析模型
```

## 🧪 第五部分：测试和验证

### 5.1 运行配置测试

#### **测试模型池**
```bash
python scripts/test_model_pool.py
```

**预期输出：**
```
✅ 模型池加载成功，共 16 个模型
✅ GLM-4.6V-Flash模型已配置
✅ 免费模型成本为0
✅ QQ端默认使用GLM-4.6V-Flash
```

#### **测试QQ功能**
```bash
python scripts/test_qq_features.py
```

**预期输出：**
```
✅ QQ连接配置正常
✅ 图片识别功能就绪
✅ GLM-4.6V-Flash模型可用
✅ 所有功能测试通过
```

#### **测试混合配置**
```bash
python scripts/test_hybrid_config.py
```

### 5.2 验证模型路由

```python
# 手动验证模型选择
from core.model_pool import get_model_pool

pool = get_model_pool()

# 测试图片分析任务
model = pool.select_model_for_task('image_description', 'qq', 'cost')
print(f"成本优先选择的模型: {model.id}")  # 应该是zhipu_glm_46v_flash

# 测试质量优先
model = pool.select_model_for_task('image_description', 'qq', 'quality')
print(f"质量优先选择的模型: {model.id}")  # 应该是zhipu_glm_46v_flash
```

## 🚀 第六部分：启动和使用

### 6.1 启动QQ机器人

#### **方法1：使用启动脚本**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

#### **方法2：手动启动**
```bash
# 激活虚拟环境
venv\Scripts\activate

# 启动弥娅
python -m webnet.qq.core
```

### 6.2 使用模型池

#### **在代码中调用**
```python
# 获取模型配置
from webnet.qq.hybrid_config import get_qq_model

# 获取QQ端图片分析模型
vision_config = get_qq_model('vision')
print(f"QQ图片分析模型: {vision_config.get('name')}")
print(f"模型提供商: {vision_config.get('provider')}")
print(f"模型成本: {vision_config.get('cost_per_1k_tokens')}")

# 输出结果：
# QQ图片分析模型: glm-4.6v-flash
# 模型提供商: zhipu
# 模型成本: {'input': 0.0, 'output': 0.0}
```

#### **使用智能路由**
```python
from core.model_pool import select_model_for_task

# 自动选择最佳模型
task_type = "image_description"  # 图片描述任务
endpoint = "qq"                  # QQ端
priority = "balanced"            # 平衡模式

model = select_model_for_task(task_type, endpoint, priority)
print(f"选择的模型: {model.id}")
print(f"模型描述: {model.description}")
print(f"是否免费: {model.cost_per_1k_tokens.input == 0}")
```

## 🔧 第七部分：故障排除

### 7.1 常见问题

#### **问题1：QQ连接失败**
**症状：** 无法连接到QQ机器人
**解决方案：**
1. 检查 `QQ_ONEBOT_WS_URL` 是否正确
2. 确认QQ机器人服务已启动
3. 检查防火墙设置

#### **问题2：GLM-4.6V-Flash无法使用**
**症状：** 图片分析功能报错
**解决方案：**
1. 确认 `ZHIPU_API_KEY` 有效
2. 检查网络连接
3. 验证模型名称是否正确

#### **问题3：模型路由错误**
**症状：** 选择了错误的模型
**解决方案：**
1. 检查 `unified_model_config.yaml` 配置
2. 验证路由优先级设置
3. 运行测试脚本检查配置

### 7.2 调试方法

#### **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### **检查模型池状态**
```bash
python scripts/test_model_pool.py --debug
```

#### **查看配置加载过程**
```bash
python scripts/test_hybrid_config.py --verbose
```

## 📊 第八部分：性能优化

### 8.1 成本优化建议

1. **优先使用免费模型**
   - 日常聊天：硅基流动 Qwen 2.5 7B
   - 图片分析：智谱 GLM-4.6V-Flash

2. **智能预算控制**
   ```yaml
   budget_control:
     daily_budget_usd: 10.0
     monthly_budget_usd: 300.0
     alert_threshold: 0.8
   ```

3. **缓存策略**
   ```yaml
   performance_settings:
     enable_caching: true
     cache_ttl_seconds: 3600
   ```

### 8.2 响应速度优化

1. **并行执行**
   ```yaml
   enable_parallel_execution: true
   max_parallel_models: 3
   ```

2. **连接优化**
   ```yaml
   connection:
     timeout_seconds: 30
     max_retries: 3
     retry_delay_base: 1.0
   ```

## 📈 第九部分：监控和维护

### 9.1 监控配置

#### **启用监控**
```yaml
monitoring:
  enabled: true
  metrics:
    - "model_usage"
    - "response_time"
    - "error_rate"
    - "cost_tracking"
  
  alerts:
    cost_exceeded: true
    error_rate_high: true
    response_time_slow: true
```

#### **查看监控数据**
```bash
# 查看模型使用统计
python scripts/monitor_model_usage.py

# 查看成本统计
python scripts/monitor_costs.py
```

### 9.2 定期维护

1. **每周检查**
   - 更新API密钥有效期
   - 清理缓存文件
   - 检查日志文件大小

2. **每月维护**
   - 更新模型列表
   - 优化配置参数
   - 备份配置文件

## 🎯 第十部分：高级配置

### 10.1 自定义模型路由

#### **基于内容的路由**
```yaml
custom_routing:
  rules:
    - condition: "message.contains('代码')"
      task_type: "code_generation"
      priority: "quality"
    
    - condition: "message.contains('图片') or has_image"
      task_type: "image_description"
      priority: "cost"
    
    - condition: "message.length > 100"
      task_type: "summarization"
      priority: "balanced"
```

#### **基于时间的路由**
```yaml
time_based_routing:
  daytime:
    start: "08:00"
    end: "18:00"
    priority: "speed"
  
  nighttime:
    start: "18:00"
    end: "08:00"
    priority: "cost"
```

### 10.2 多模型融合

#### **启用融合策略**
```yaml
model_fusion:
  enabled: true
  strategy: "consensus"
  min_confidence: 0.7
  
  fusion_rules:
    - task_type: "image_description"
      models:
        - "zhipu_glm_46v_flash"
        - "zhipu_glm_4v"
      weight: [0.6, 0.4]
```

## 🏁 总结

### 已完成的配置

✅ **环境变量配置** - 三家厂商API密钥  
✅ **QQ机器人匹配** - OneBot连接配置  
✅ **模型池系统** - 16个模型智能路由  
✅ **GLM-4.6V-Flash** - 免费多模态模型集成  
✅ **成本优化** - 免费模型优先策略  
✅ **测试验证** - 完整测试套件  

### 立即开始使用

```bash
# 1. 激活环境
venv\Scripts\activate

# 2. 测试配置
python scripts/test_model_pool.py

# 3. 启动弥娅
python -m webnet.qq.core

# 4. 享受智能QQ机器人
#    - 免费图片分析
#    - 智能模型选择
#    - 低成本运行
```

### 技术支持

- **文档目录**: `docs/`
- **配置示例**: `config/.env.example`
- **测试脚本**: `scripts/`
- **问题反馈**: 检查日志文件 `logs/`

**你的弥娅现在已配置完成，可以享受免费的GLM-4.6V-Flash多模态模型和智能的模型路由系统！** 🚀

---
*最后更新: 2024年*
*文档版本: v2.0*
*配置状态: ✅ 完成*