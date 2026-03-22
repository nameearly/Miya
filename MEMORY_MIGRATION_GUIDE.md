"""
记忆系统迁移指南

V2.0 重构后的使用说明
"""

# 新旧系统对比

## 旧系统问题

1. **伪向量实现** - 使用MD5哈希代替真实embedding
2. **史官改写空壳** - 只是简单存储，没有调用LLM
3. **短期记忆无持久化** - 服务重启丢失
4. **侧写无限增长** - 从不压缩整理
5. **6套系统各自为政** - 信息孤岛

## 新系统特性

### 1. 真实语义向量检索
```python
from memory.unified_memory_v2 import get_unified_memory

memory = get_unified_memory()
# 支持 OpenAI/智谱AI/本地sentence-transformers
```

### 2. LLM驱动的史官改写
```python
memory.set_llm_func(llm_callable)
# 观察自动转化为绝对化记忆
```

### 3. 记忆持久化
```python
# 短期记忆自动保存到 data/memory/short_term/cache.json
# 服务重启后自动恢复
```

### 4. 侧写自动压缩
```python
# 超过300行自动压缩，保留最近500行
```

### 5. 统一接口
```python
# 一个系统管理所有记忆类型
memory.add_short_term()      # 短期
memory.add_cognitive()        # 认知
memory.add_pinned()           # 置顶
memory.search()               # 语义搜索
memory.get_user_profile()     # 用户侧写
memory.get_group_profile()   # 群组侧写
```

## 迁移步骤

### 1. 导入新系统
```python
from memory.unified_memory_v2 import get_unified_memory
```

### 2. 初始化
```python
memory = get_unified_memory(
    data_dir='data/memory',  # 数据目录
    config={
        'embedding': {
            'provider': 'local',  # openai/zhipu/local
            'local_model': 'paraphrase-multilingual-MiniLM-L12-v2'
        },
        'historian_enabled': True,
        'max_short_term': 50,
        'max_cognitive': 200,
    }
)
await memory.initialize()
```

### 3. 设置LLM函数（可选）
```python
async def llm_call(system, user):
    # 调用你的LLM
    return response

memory.set_llm_func(llm_call)
```

### 4. 使用示例
```python
# 添加短期记忆
await memory.add_short_term(
    content="用户说他喜欢编程",
    user_id="123456",
    priority=0.6
)

# 添加认知记忆（会自动触发史官改写）
await memory.add_cognitive(
    content="用户对编程很感兴趣",
    observations=[
        "用户提到喜欢Python",
        "用户想学机器学习"
    ],
    user_id="123456"
)

# 语义搜索
results = await memory.search("用户喜欢什么", top_k=5)

# 获取置顶备忘
pinned = memory.get_pinned()

# 获取用户侧写
profile = memory.get_user_profile("123456")
```

## 配置选项

### embedding 配置
```python
config = {
    'embedding': {
        'provider': 'local',  # openai | zhipu | local
        
        # OpenAI
        'openai_api_key': 'sk-...',
        
        # 智谱AI
        'zhipu_api_key': '...',
        
        # 本地模型
        'local_model': 'paraphrase-multilingual-MiniLM-L12-v2',
    }
}
```

### historian 配置
```python
config = {
    'historian_enabled': True,  # 启用史官改写
}
```

### 记忆限制
```python
config = {
    'max_short_term': 50,      # 短期记忆上限
    'max_cognitive': 200,       # 认知记忆上限
    'max_long_term': 1000,      # 长期记忆上限
    'profile_max_lines': 500,   # 侧写最大行数
    'profile_compress_threshold': 300,  # 压缩阈值
}
```

## 目录结构

```
data/memory/
├── short_term/
│   └── cache.json          # 短期记忆缓存
├── cognitive/
│   └── cache.json          # 认知记忆缓存
├── long_term/
│   └── cache.json           # 长期记忆缓存
├── profiles/
│   ├── user_123.md         # 用户侧写
│   ├── user_123_summary.md # 用户侧写摘要
│   └── group_456.md       # 群组侧写
├── cache/
│   └── ...                 # 其他缓存
└── pinned_memories.json    # 置顶备忘
```

## 注意事项

1. **首次运行需要下载模型** - 本地embedding需要下载sentence-transformers模型
2. **史官改写需要LLM** - 如果不设置LLM函数，观察会直接存储
3. **数据迁移** - 旧系统的数据需要手动迁移
4. **向量维度** - 不同embedding服务维度不同，新旧数据不兼容
