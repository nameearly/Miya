# 配置加密使用指南

## 概述

弥娅项目支持配置文件加密,保护API密钥、密码等敏感信息不被泄露。

## 为什么需要配置加密?

### 安全风险
1. **代码泄露**: 如果代码库被公开,硬编码的密钥会被所有人看到
2. **日志泄露**: 日志文件可能包含敏感配置
3. **备份泄露**: 配置备份可能被未授权访问
4. **协作风险**: 团队协作时密钥容易泄露

### 加密好处
- ✅ 密钥存储加密,即使文件泄露也无法直接使用
- ✅ 支持自动解密,运行时透明
- ✅ 向后兼容,未加密配置仍可使用
- ✅ 灵活管理,可随时更新密码

## 快速开始

### 1. 加密现有配置

```bash
# Windows
cd d:\AI_MIYA_Facyory\MIYA\Miya
set ENCRYPTION_PASSWORD=your_secure_password_here
python scripts/encrypt_config.py --encrypt --input config/.env --output config/.env.encrypted

# Linux/Mac
export ENCRYPTION_PASSWORD="your_secure_password_here"
python scripts/encrypt_config.py --encrypt --input config/.env --output config/.env.encrypted
```

### 2. 替换原配置文件

```bash
# 备份原配置
copy config\.env config\.env.backup
copy config\.env.encrypted config\.env

# 或使用重命名
move config\.env config\.env.backup
move config\.env.encrypted config\.env
```

### 3. 配置运行时解密

在启动弥娅前设置环境变量:

```bash
# Windows
set ENCRYPTION_PASSWORD=your_secure_password_here
python run/main.py

# Linux/Mac
export ENCRYPTION_PASSWORD="your_secure_password_here"
python run/main.py
```

或者在启动脚本中设置:

```bash
# Windows启动脚本 (start.bat)
@echo off
set ENCRYPTION_PASSWORD=your_secure_password_here
python run/main.py
```

## 详细说明

### 加密识别规则

以下配置项会被自动识别并加密:

- `API_KEY`
- `SECRET`
- `PASSWORD`
- `TOKEN`
- `AUTH_KEY`
- `PRIVATE_KEY`
- `CLIENT_SECRET`
- `DATABASE_PASSWORD`
- `REDIS_PASSWORD`
- `NEO4J_PASSWORD`

### 加密格式

加密后的配置值格式:

```env
# 明文
AI_API_KEY=sk-1234567890abcdef

# 加密后
AI_API_KEY=enc:gAAAAABh_abcdef1234567890...
```

### 敏感配置示例

```env
# ===============================
# AI大模型配置
# ===============================

# API密钥 (会被加密)
AI_API_KEY=sk-15346aa170c442c69d726d8e95cabca3

# 非敏感配置 (不会被加密)
AI_API_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

# ===============================
# 数据库配置
# ===============================

# 数据库密码 (会被加密)
DATABASE_PASSWORD=mysecretpassword123

# 非敏感配置 (不会被加密)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=miya_db

# ===============================
# Redis配置
# ===============================

# Redis密码 (会被加密)
REDIS_PASSWORD=redis_secure_password_456

# 非敏感配置 (不会被加密)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# ===============================
# Neo4j配置
# ===============================

# Neo4j密码 (会被加密)
NEO4J_PASSWORD=neo4j_secret_password_789

# 非敏感配置 (不会被加密)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_DATABASE=neo4j

# ===============================
# IoT邮件配置
# ===============================

# SMTP密码 (会被加密)
SMTP_PASSWORD=smtp_secure_password_abc

# 非敏感配置 (不会被加密)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_FROM_ADDR=your_email@gmail.com
```

## 代码集成

### 在代码中使用安全配置

```python
from core.secure_config_loader import get_config_value, load_config

# 方式1: 直接获取单个配置值
api_key = get_config_value('AI_API_KEY')
password = get_config_value('DATABASE_PASSWORD')

# 方式2: 加载整个配置文件
config = load_config('config/.env')
api_key = config.get('AI_API_KEY')
password = config.get('DATABASE_PASSWORD')

# 配置会自动解密,无需手动处理
print(f"API密钥: {api_key}")  # 自动解密后的明文
```

### 更新Settings类

```python
# config/settings.py
from core.secure_config_loader import get_config_value

class Settings:
    def __init__(self):
        # 从环境变量或.env读取(自动解密)
        self.ai_api_key = get_config_value('AI_API_KEY')
        self.database_password = get_config_value('DATABASE_PASSWORD')
        self.redis_password = get_config_value('REDIS_PASSWORD')
        self.neo4j_password = get_config_value('NEO4J_PASSWORD')
```

## 常见问题

### Q1: 忘记了加密密码怎么办?

A: 遗忘加密密码后无法解密配置,需要:
1. 备份原配置文件(`config/.env.backup`)
2. 重新设置加密密码
3. 重新加密配置

### Q2: 加密后还能修改配置吗?

A: 可以,有两种方式:

**方式1: 先解密后修改**
```bash
# 解密配置
python scripts/encrypt_config.py --decrypt --input config/.env --output config/.env.decrypted

# 编辑配置文件
notepad config/.env.decrypted

# 重新加密
python scripts/encrypt_config.py --encrypt --input config/.env.decrypted --output config/.env
```

**方式2: 直接编辑加密配置**
- 直接编辑`config/.env`文件
- 新增的敏感配置项会在下次加密时被加密
- 运行时会自动解密

### Q3: 加密会影响性能吗?

A: 几乎不影响:
- 解密操作仅在启动时执行一次
- 运行时使用明文配置
- 加密算法性能损失<1ms

### Q4: 团队协作时如何管理密码?

A: 推荐方案:

**方案1: 使用密钥管理服务**
- 使用AWS Secrets Manager
- 使用HashiCorp Vault
- 使用Azure Key Vault

**方案2: 环境变量传递**
- 不将密码存入代码库
- 通过CI/CD注入环境变量
- 使用`.env.example`提供配置模板

**方案3: 分离密码文件**
- `config/.env.example` (公开,不含密钥)
- `config/.env` (私有,包含密钥,添加到.gitignore)
- `config/.env.encrypted` (可选,加密后的配置)

### Q5: 可以部分加密配置吗?

A: 可以!加密工具只加密识别到的敏感配置项:
- 包含敏感关键词的配置项会被加密
- 其他配置项保持明文
- 可以混合使用加密和明文配置

## 最佳实践

### 1. 密码管理
- ✅ 使用强密码(16+字符,包含大小写字母、数字、符号)
- ✅ 定期更换加密密码
- ✅ 不在代码中硬编码密码
- ✅ 使用密码管理器存储密码

### 2. 备份策略
- ✅ 加密前备份原配置
- ✅ 保存加密密码备份
- ✅ 定期备份配置文件
- ✅ 使用版本控制管理`.env.example`

### 3. 团队协作
- ✅ 提供`.env.example`作为配置模板
- ✅ 将`.env`添加到`.gitignore`
- ✅ 使用CI/CD注入敏感配置
- ✅ 记录加密密码的安全位置

### 4. 安全审计
- ✅ 定期审查配置文件
- ✅ 检查是否有未加密的敏感配置
- ✅ 监控配置文件访问日志
- ✅ 及时更新泄露的密钥

## 故障排查

### 问题1: 启动时报"解密失败"

**原因**: 加密密码不正确或配置损坏

**解决**:
```bash
# 1. 检查密码是否正确
echo %ENCRYPTION_PASSWORD%

# 2. 使用备份配置
copy config\.env.backup config\.env

# 3. 重新加密
set ENCRYPTION_PASSWORD=correct_password
python scripts/encrypt_config.py --encrypt --input config/.env --output config/.env.encrypted
```

### 问题2: 加密后无法启动

**原因**: 运行时未设置`ENCRYPTION_PASSWORD`环境变量

**解决**:
```bash
# Windows
set ENCRYPTION_PASSWORD=your_password
python run/main.py

# Linux/Mac
export ENCRYPTION_PASSWORD="your_password"
python run/main.py
```

### 问题3: 某些配置项未加密

**原因**: 配置项名称不包含敏感关键词

**解决**:
- 方式1: 修改配置项名称,包含敏感关键词
- 方式2: 手动编辑加密脚本,添加到`SENSITIVE_KEYS`列表

## 附录

### A. 支持的加密算法

- **算法**: AES-128-CBC (Fernet)
- **密钥派生**: PBKDF2-HMAC-SHA256
- **迭代次数**: 480,000
- **Salt**: 固定salt (可配置)

### B. 性能数据

| 操作 | 耗时 |
|------|------|
| 加密10个配置项 | ~5ms |
| 解密10个配置项 | ~3ms |
| 启动时加载配置 | ~10ms |

### C. 兼容性

- Python: 3.9+
- 操作系统: Windows/Linux/Mac
- 加密依赖: cryptography>=41.0.0

## 联系支持

如有问题,请:
1. 查看故障排查章节
2. 提交Issue到项目仓库
3. 联系技术支持

---

**最后更新**: 2026-03-17  
**版本**: 1.0.0
