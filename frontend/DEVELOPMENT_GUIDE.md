# 弥娅前端开发指南

## 技术栈

### 核心框架
- **React 18.2.0** - UI 框架
- **TypeScript 5.4.0** - 类型系统
- **Vite 5.1.6** - 构建工具
- **pnpm 8.x** - 包管理器

### 桌面应用
- **Electron 29.1.4** - 桌面应用框架
- **@miya/desktop** - 桌面应用包

### Web 应用
- **@miya/web** - Web 应用包

### 共享包
- **@miya/shared** - 共享代码
- **@miya/live2d** - Live2D 组件库

## 项目结构

```
frontend/
├── packages/
│   ├── shared/           # 共享代码
│   │   ├── src/
│   │   │   ├── types/    # 类型定义
│   │   │   ├── api/      # API 客户端
│   │   │   └── utils/    # 工具函数
│   │   └── package.json
│   ├── live2d/           # Live2D 组件库
│   │   ├── src/
│   │   │   ├── components/  # React 组件
│   │   │   ├── hooks/       # React Hooks
│   │   │   └── core/        # 核心逻辑
│   │   └── package.json
│   ├── desktop/          # Electron 桌面应用
│   │   ├── src/
│   │   │   ├── components/  # UI 组件
│   │   │   ├── pages/       # 页面组件
│   │   │   └── App.tsx
│   │   ├── electron/
│   │   │   ├── main.ts      # 主进程
│   │   │   └── preload.ts   # 预加载脚本
│   │   └── package.json
│   └── web/              # Web 应用
│       ├── src/
│       │   ├── components/  # UI 组件
│       │   └── pages/       # 页面组件
│       └── package.json
├── package.json
└── pnpm-workspace.yaml
```

## 快速开始

### 环境准备

```bash
# 安装 pnpm
npm install -g pnpm

# 安装依赖
cd frontend
pnpm install
```

### 开发模式

```bash
# 启动桌面应用
pnpm dev:desktop

# 启动 Web 应用
pnpm dev:web
```

### 构建

```bash
# 构建桌面应用
pnpm build:desktop

# 构建 Web 应用
pnpm build:web

# 构建所有包
pnpm build
```

## 开发规范

### 代码风格

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 样式使用 Tailwind CSS
- 遵循 ESLint + Prettier 规则

### 命名规范

#### 文件命名

- 组件文件：`PascalCase.tsx` (如 `ChatPage.tsx`)
- 工具文件：`camelCase.ts` (如 `formatDate.ts`)
- 类型文件：`PascalCase.ts` (如 `Message.ts`)
- 样式文件：`PascalCase.css` (如 `ChatPage.css`)

#### 变量命名

- 组件：`PascalCase`
- 函数：`camelCase`
- 常量：`UPPER_SNAKE_CASE`
- 类型：`PascalCase`

### 组件规范

#### 组件结构

```tsx
import React, { useState, useEffect } from 'react';
import type { ComponentProps } from './types';
import './Component.css';

/**
 * 组件描述
 */
export const Component: React.FC<ComponentProps> = ({
  prop1,
  prop2,
  onEvent
}) => {
  // Hooks
  const [state, setState] = useState(initialState);

  // Effects
  useEffect(() => {
    // 副作用
  }, [dependencies]);

  // 事件处理
  const handleClick = () => {
    onEvent?.(data);
  };

  // 渲染
  return (
    <div className="component">
      {/* JSX */}
    </div>
  );
};
```

#### Props 类型定义

```typescript
export interface ComponentProps {
  /** 属性描述 */
  prop1: string;
  /** 可选属性 */
  prop2?: number;
  /** 事件回调 */
  onEvent?: (data: unknown) => void;
  /** 子元素 */
  children?: React.ReactNode;
}
```

## 使用共享包

### 使用类型定义

```typescript
import type { Message, EmotionType } from '@miya/shared/types';

const message: Message = {
  id: '1',
  content: 'Hello',
  type: MessageType.TEXT,
  direction: MessageDirection.INCOMING,
  status: MessageStatus.SENT,
  timestamp: Date.now()
};
```

### 使用 API 客户端

```typescript
import { getMessages, sendMessage } from '@miya/shared/api';

// 获取消息
const messages = await getMessages();

// 发送消息
await sendMessage({
  content: 'Hello',
  type: MessageType.TEXT,
  direction: MessageDirection.OUTGOING,
  status: MessageStatus.SENDING,
  timestamp: Date.now()
});
```

### 使用工具函数

```typescript
import { formatDate, debounce, throttle } from '@miya/shared/utils';

// 格式化日期
const formatted = formatDate(new Date(), 'short');

// 防抖函数
const debouncedFn = debounce(myFunction, 300);

// 节流函数
const throttledFn = throttle(myFunction, 200);
```

## 使用 Live2D 组件

### Live2DAvatar

```tsx
import { Live2DAvatar } from '@miya/live2d';

<Live2DAvatar
  modelId="haru"
  width={500}
  height={500}
  draggable
  scalable
  opacity={1}
  onLoad={() => console.log('Loaded')}
  onError={(error) => console.error(error)}
/>
```

### Live2DViewer

```tsx
import { Live2DViewer } from '@miya/live2d';

<Live2DViewer
  modelId="haru"
  width={500}
  height={500}
  showControls
  autoMotion
  onMotionChange={(motion) => console.log(motion)}
/>
```

## 状态管理

### Zustand Store

```typescript
import { create } from 'zustand';

interface AppState {
  // 状态
  user: User | null;
  isLoading: boolean;

  // 操作
  setUser: (user: User) => void;
  setLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  isLoading: false,

  setUser: (user) => set({ user }),
  setLoading: (isLoading) => set({ isLoading })
}));
```

### 使用 Store

```tsx
import { useAppStore } from './store';

export const MyComponent: React.FC = () => {
  const { user, isLoading, setUser } = useAppStore();

  return <div>{isLoading ? 'Loading...' : user?.name}</div>;
};
```

## 路由管理

### 定义路由

```tsx
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/live2d" element={<Live2DPage />} />
    </Routes>
  );
}
```

### 路由跳转

```tsx
import { useNavigate } from 'react-router-dom';

export const MyComponent: React.FC = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/chat');
  };

  return <button onClick={handleClick}>Go to Chat</button>;
};
```

## 测试

### 单元测试

```bash
# 运行所有测试
pnpm test

# 运行特定包的测试
pnpm --filter @miya/desktop test
```

### E2E 测试

```bash
# 运行 E2E 测试
pnpm test:e2e
```

## 调试

### 开发工具

- **React DevTools** - React 组件调试
- **Redux DevTools** - Zustand 状态调试
- **Electron DevTools** - Electron 主进程调试

### 日志

```typescript
import { logger } from '@miya/shared/utils';

logger.info('Info message');
logger.warn('Warning message');
logger.error('Error message');
```

## 部署

### 构建

```bash
# 构建桌面应用
pnpm build:desktop

# 构建 Web 应用
pnpm build:web
```

### 发布

#### 桌面应用

```bash
# 构建 Electron 应用
pnpm --filter @miya/desktop build

# 输出位置
packages/desktop/release/
```

#### Web 应用

```bash
# 构建 Web 应用
pnpm --filter @miya/web build

# 输出位置
packages/web/dist/
```

## 常见问题

### 如何调试 Electron 主进程？

```bash
# 在 VS Code 中配置 launch.json
{
  "type": "node",
  "request": "launch",
  "name": "Electron Main",
  "runtimeExecutable": "${workspaceFolder}/node_modules/.bin/electron",
  "program": "${workspaceFolder}/packages/desktop/dist-electron/main.js"
}
```

### 如何解决依赖问题？

```bash
# 清理并重新安装依赖
pnpm clean
pnpm install

# 检查依赖冲突
pnpm why <package-name>
```

### 如何更新共享包？

```bash
# 更新 shared 包
pnpm --filter @miya/shared build

# 重新使用该包的应用会自动获取更新
```

## 贡献指南

### 提交代码

1. 创建功能分支
2. 编写代码和测试
3. 确保通过所有检查
4. 提交 Pull Request

### 代码审查

- 遵循项目规范
- 添加必要的注释
- 更新相关文档
- 确保测试通过

## 资源链接

- [React 文档](https://react.dev/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [Vite 文档](https://vitejs.dev/)
- [Electron 文档](https://www.electronjs.org/)
- [pnpm 文档](https://pnpm.io/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
