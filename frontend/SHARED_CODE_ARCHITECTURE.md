# 弥娅前端 - 共享代码架构

## 概述

弥娅前端采用 Monorepo 架构，桌面端和Web端共享同一套代码，大大减少了重复代码，提高了维护效率。

## 目录结构

```
frontend/
├── packages/
│   ├── shared/        # 共享代码包
│   │   ├── src/
│   │   │   ├── api/   # API客户端和类型定义
│   │   │   ├── types/ # TypeScript类型定义
│   │   │   └── utils/ # 工具函数
│   │   └── dist/     # 编译输出
│   ├── desktop/       # 桌面端应用 (Electron)
│   │   └── src/
│   │       ├── services/
│   │       │   └── api.ts  # 使用shared包
│   │       └── ...
│   └── web/          # Web端应用
│       └── src/
│           ├── services/
│           │   └── api.ts  # 使用shared包
│           └── ...
└── pnpm-workspace.yaml
```

## 共享代码特性

### 1. 统一的API客户端

桌面端和Web端使用相同的API客户端，支持：
- 自动端口检测 (8000, 8080, 8001, 8888)
- 统一的请求/响应格式
- 自动会话管理
- 平台标识 (web/desktop)

### 2. 类型安全

所有API请求和响应都有完整的TypeScript类型定义，确保类型安全。

### 3. 同时运行支持

桌面端和Web端可以同时运行，通过不同的session_id和terminal_type标识：
- 桌面端: `terminalType: 'desktop'`, `sessionId: 'desktop-xxx'`
- Web端: `terminalType: 'web'`, `sessionId: 'web-xxx'`

## 使用方法

### 在桌面端使用

```typescript
// packages/desktop/src/services/api.ts
import { createApiClient } from '@miya/shared/api';

export const apiClient = createApiClient('desktop');

// 发送消息
const response = await apiClient.sendMessage('你好');
console.log(response.response);
```

### 在Web端使用

```typescript
// packages/web/src/services/api.ts
import { createApiClient } from '@miya/shared/api';

export const apiClient = createApiClient('web');

// 发送消息
const response = await apiClient.sendMessage('你好');
console.log(response.response);
```

## API客户端功能

### 基础方法

```typescript
// 健康检查
await apiClient.healthCheck();

// 发送消息
await apiClient.sendMessage('消息内容');

// 获取系统状态
await apiClient.getSystemStatus();

// 检查连接状态
const connected = await apiClient.checkConnection();

// 重新检测端口
const port = await apiClient.redetectPort();

// 获取会话信息
const session = apiClient.getSessionInfo();
```

### 请求头

所有请求会自动添加以下头部：
```
X-Session-ID: {sessionId}
X-Terminal-Type: {terminalType}
X-Platform: {platform}
```

## 构建和开发

### 构建共享包

```bash
cd frontend/packages/shared
npm run build
```

### 开发模式

桌面端和Web端可以同时运行：

```bash
# 终端1: 启动桌面端
cd frontend/packages/desktop
npm run dev

# 终端2: 启动Web端
cd frontend/packages/web
npm run dev
```

### 安装依赖

```bash
cd frontend
pnpm install
```

## 优势

### 1. 代码复用
- API逻辑只写一次，两端共用
- 类型定义统一，减少重复
- 工具函数共享

### 2. 维护性
- 修改API逻辑只需改一处
- 统一的错误处理
- 一致的接口规范

### 3. 节省空间
- 减少重复代码约 60%
- 减少node_modules体积
- 更快的构建速度

### 4. 同时运行
- 桌面端和Web端可以同时使用
- 通过会话ID区分不同客户端
- 完全独立的会话管理

## 后续优化

1. 添加UI组件共享 (`packages/ui`)
2. 添加状态管理共享 (`packages/state`)
3. 添加Live2D组件共享 (`packages/live2d`)
4. 添加主题系统共享

## 注意事项

1. 每次修改shared包后，需要重新构建
2. 两端可以同时运行，互不影响
3. API端口检测是自动的，无需手动配置
4. 会话ID是自动生成的，包含平台和时间戳
