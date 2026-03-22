# 前端开发常见问题

## 1. 依赖冲突

### 问题描述
```
WARN Issues with peer dependencies found
packages/desktop
└─┬ pixi.js 7.3.2
  └─┬ @pixi/assets 7.3.2
    └── ✕ unmet peer @pixi/utils@7.3.2: found 6.5.10
```

### 解决方案
已在 `frontend/package.json` 中添加 `pnpm.overrides` 配置，统一所有 PIXI.js 子包版本为 7.3.2。

如果问题仍然存在，执行：
```bash
cd frontend
rm pnpm-lock.yaml  # 删除 lockfile
pnpm install       # 重新安装依赖
```

## 2. Electron 应用启动失败

### 问题描述
```
TypeError: options.start is not a function
```

### 原因
`vite-plugin-electron` 插件 API 变化，旧版配置不再兼容。

### 解决方案
已更新 `packages/desktop/vite.config.ts`，移除不兼容的 `onstart` 回调。

### 测试步骤
1. **先测试 Web 应用**（推荐）
   ```bash
   cd frontend
   pnpm dev:web
   ```

2. **再测试桌面应用**
   ```bash
   cd frontend
   pnpm dev:desktop
   ```

## 3. 批处理文件乱码

### 问题描述
Windows 控制台显示乱码，如：
```
寮ュ鍓嶇鍚姩
```

### 解决方案
已在批处理文件开头添加 `chcp 65001` 设置 UTF-8 编码。

如果仍有乱码，请：
1. 右键点击批处理文件
2. 选择"编辑"
3. 另存为时选择编码为"UTF-8 with BOM"

## 4. 依赖安装失败

### 问题描述
```
ERR_PNPM_NO_IMPORTER_MANIFEST_FOUND
```

### 解决方案
确保在正确的目录执行命令：
```bash
# 错误
cd miya
pnpm install

# 正确
cd miya/frontend
pnpm install
```

## 5. 构建失败

### 问题描述
```
Type error: Cannot find module
```

### 解决方案
```bash
cd frontend
pnpm clean          # 清理构建文件
pnpm install        # 重新安装依赖
pnpm build          # 重新构建
```

## 6. 端口被占用

### 问题描述
```
Error: Port 5173 is already in use
```

### 解决方案
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -ti:5173 | xargs kill -9
```

或修改 `packages/desktop/vite.config.ts` 中的端口配置：
```typescript
server: {
  port: 5174,  // 改为其他端口
  strictPort: false
}
```

## 快速开始

### 安装依赖
```bash
cd frontend
pnpm install
```

### 启动开发服务器

**Web 应用（推荐先测试）**
```bash
pnpm dev:web
```
访问: http://localhost:5174

**桌面应用**
```bash
pnpm dev:desktop
```

### 构建生产版本

**Web 应用**
```bash
pnpm build:web
```

**桌面应用**
```bash
pnpm build:desktop
```

## 开发环境要求

- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Python 3.8+ (用于某些原生模块编译)
- Visual Studio Build Tools (Windows)

## 常用命令

```bash
# 安装所有依赖
pnpm install

# 启动 Web 应用
pnpm dev:web

# 启动桌面应用
pnpm dev:desktop

# 构建所有包
pnpm build

# 清理构建文件
pnpm clean

# 类型检查
pnpm typecheck

# 代码检查
pnpm lint
```

## 获取帮助

如果遇到其他问题，请查看：
- [README.md](./README.md) - 项目概述
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - 迁移指南
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - 开发指南
