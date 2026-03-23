# 弥娅快速入门指南（GLM-4.6V-Flash版）

## ⚡ 5分钟快速部署

### 步骤1：环境准备
```bash
# 1. 确保Python 3.9+
python --version

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 步骤2：配置API密钥
编辑 `config/.env`，确保以下配置正确：

```bash
# 硅基流动（免费额度）
SILICONFLOW_API_KEY=sk-lbybyiqrbaxasvwmspsoxulfkrprzibertsjanyaurcxbird

# DeepSeek（性能优化）
DEEPSEEK_API_KEY=sk-15346aa170c442c69d726d8e95cabca3

# 智谱AI（重点！免费GLM-4.6V-Flash）
ZHIPU_API_KEY=61d87875c2bf4444975409c6df476009.nflDzcqzdHwzTApF
ZHIPU_GLM_46V_FLASH_MODEL=glm-4.6v-flash
```

### 步骤3：配置QQ机器人
编辑 `config/.env` 中的QQ配置：

```bash
# QQ机器人连接
QQ_ONEBOT_WS_URL=ws://localhost:3001
QQ_BOT_QQ=3681817929
QQ_SUPERADMIN_QQ=1234567890
```

### 步骤4：测试配置
```bash
# 测试模型池（重点检查GLM-4.6V-Flash）
python scripts/test_model_pool.py

# 测试QQ功能
python scripts/test_qq_features.py
```

### 步骤5：启动弥娅
```bash
# 启动QQ机器人
python -m webnet.qq.core
```

## 🎯 GLM-4.6V-Flash核心优势

### 💰 完全免费
- **输入成本**: 0元/1000 tokens
- **输出成本**: 0元/1000 tokens
- **无限制使用**: 无需担心预算

### 🚀 高性能
- **支持大图片**: 最大20MB
- **响应快速**: 实时分析
- **多模态能力**: 图片理解、文字识别、文档分析

### 🇨🇳 中文优化
- **中文理解**: 专门优化中文内容
- **本地化**: 完美支持中文场景
- **文化适配**: 理解中文语境

## 🔧 智能路由策略

### 图片分析任务
系统会自动选择最佳模型：

1. **第一选择**: GLM-4.6V-Flash（免费）
2. **第二选择**: GLM-4V（付费，性能更好）
3. **第三选择**: Qwen VL（硅基流动）

### 聊天任务
1. **第一选择**: Qwen 2.5 7B（硅基流动，免费）
2. **第二选择**: DeepSeek V3（性能优秀）
3. **第三选择**: GLM-4（中文优化）

## 📊 监控和管理

### 查看模型使用情况
```python
from core.model_pool import get_model_pool

pool = get_model_pool()
stats = pool.get_usage_stats()

print(f"GLM-4.6V-Flash使用次数: {stats['zhipu_glm_46v_flash']['usage_count']}")
print(f"节省成本: ${stats['zhipu_glm_46v_flash']['cost_saved']}")
```

### 查看成本统计
```bash
# 运行成本监控
python scripts/monitor_costs.py
```

## 🚨 故障排除

### 常见问题1：GLM-4.6V-Flash无法使用
```bash
# 检查API密钥
echo $ZHIPU_API_KEY

# 测试连接
python -c "import requests; r=requests.get('https://open.bigmodel.cn/api/paas/v4'); print(r.status_code)"
```

### 常见问题2：图片分析失败
1. 确认图片大小不超过20MB
2. 检查图片格式（支持jpg, png, gif等）
3. 查看日志文件 `logs/qq_debug.log`

### 常见问题3：模型路由错误
```python
# 检查路由配置
from core.model_pool import select_model_for_task
model = select_model_for_task('image_description', 'qq', 'cost')
print(f"当前路由选择的模型: {model.id}")
```

## 📈 性能调优

### 优化响应速度
```yaml
# 在 config/unified_model_config.yaml 中调整
performance_settings:
  enable_parallel_execution: true
  max_parallel_models: 3
  connection:
    timeout_seconds: 30
    max_retries: 3
```

### 优化图片处理
```yaml
multimedia:
  image:
    compress: true
    compress_quality: 80
    max_size: 10485760  # 10MB
```

## 🎉 开始使用！

### 发送第一张图片给QQ机器人
1. 在QQ群或私聊中发送图片
2. 弥娅会自动使用GLM-4.6V-Flash分析
3. 获取免费的图片描述和分析

### 享受智能聊天
1. 发送任何消息给QQ机器人
2. 系统自动选择最佳模型回复
3. 优先使用免费模型节省成本

## 📞 技术支持

### 文档资源
- **完整文档**: `docs/MIYA_FULL_CONFIG_GUIDE.md`
- **模型配置**: `docs/three_providers_guide.md`
- **QQ配置**: `docs/qq_hybrid_config_guide.md`

### 测试脚本
- `scripts/test_model_pool.py` - 测试模型池
- `scripts/test_qq_features.py` - 测试QQ功能
- `scripts/test_hybrid_config.py` - 测试混合配置

### 日志文件
- `logs/qq_debug.log` - QQ调试日志
- `logs/model_pool.log` - 模型池日志
- `logs/system.log` - 系统日志

---

## 🏁 快速总结

**已配置完成：**
✅ 智谱GLM-4.6V-Flash免费模型  
✅ 硅基流动免费额度模型  
✅ DeepSeek高性能模型  
✅ QQ机器人完美匹配  
✅ 智能模型路由系统  

**立即开始：**
```bash
# 1. 测试
python scripts/test_model_pool.py

# 2. 启动
python -m webnet.qq.core

# 3. 享受免费的图片分析！
```

**你的弥娅现在拥有：**
- 🆓 **免费多模态模型** GLM-4.6V-Flash
- 🧠 **智能模型选择** 自动路由
- 💰 **零成本运行** 优先免费模型
- 📸 **强大图片分析** 支持20MB大图

**开始你的免费AI体验吧！** 🚀