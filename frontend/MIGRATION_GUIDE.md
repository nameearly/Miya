# 前端重构迁移指南

本文档说明如何从旧的前端架构迁移到新的 Monorepo 架构。

## 迁移概览

### 旧架构

```
miya-desktop/  # Vue 3 + Electron
miya-pc-ui/    # React + Electron
```

### 新架构

```
frontend/
├── packages/
│   ├── shared/    # 共享代码
│   ├── live2d/    # Live2D 组件库
│   ├── desktop/   # Electron 桌面应用
│   └── web/       # Web 应用
```

## 统一依赖版本

### PIXI.js

- **旧版本**: 6.5.10 (miya-desktop), 7.3.2 (miya-pc-ui)
- **新版本**: 7.3.2 (统一)
- **影响**: 需要更新 PIXI.js API 调用

### Electron

- **旧版本**: 29.1.4 (miya-desktop), 28.0.0 (miya-pc-ui)
- **新版本**: 29.1.4 (统一)

### React / Vue

- **旧架构**: Vue 3 + React (分离)
- **新架构**: React 18 (统一)

## 迁移步骤

### 1. 安装 pnpm

```bash
npm install -g pnpm
```

### 2. 安装依赖

```bash
cd frontend
pnpm install
```

### 3. 开发模式

#### 启动桌面应用

```bash
pnpm dev:desktop
```

#### 启动 Web 应用

```bash
pnpm dev:web
```

### 4. 构建应用

#### 构建桌面应用

```bash
pnpm build:desktop
```

#### 构建 Web 应用

```bash
pnpm build:web
```

## 代码迁移

### 从 miya-desktop (Vue) 迁移到 desktop (React)

#### 组件迁移

**Vue 组件**:
```vue
<template>
  <div class="chat">
    <div v-for="message in messages" :key="message.id">
      {{ message.content }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const messages = ref([]);
</script>
```

**React 组件**:
```tsx
import React, { useState } from 'react';

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState([]);

  return (
    <div className="chat">
      {messages.map((message) => (
        <div key={message.id}>{message.content}</div>
      ))}
    </div>
  );
};
```

#### 状态管理迁移

**Vue (Pinia)**:
```typescript
import { defineStore } from 'pinia';

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: []
  }),
  actions: {
    addMessage(message) {
      this.messages.push(message);
    }
  }
});
```

**React (Zustand)**:
```typescript
import { create } from 'zustand';

interface ChatState {
  messages: Message[];
  addMessage: (message: Message) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] }))
}));
```

#### API 调用迁移

**旧方式**:
```typescript
import axios from 'axios';

const response = await axios.get('/api/messages');
```

**新方式**:
```typescript
import { getMessages } from '@miya/shared/api';

const messages = await getMessages();
```

### Live2D 组件迁移

**旧方式**:
```vue
<Live2DFull
  model-id="haru"
  :width="500"
  :height="500"
  @load="onLoad"
/>
```

**新方式**:
```tsx
import { Live2DAvatar } from '@miya/live2d';

<Live2DAvatar
  modelId="haru"
  width={500}
  height={500}
  onLoad={onLoad}
/>
```

## 依赖更新

### 更新 PIXI.js API

从 PIXI.js 6.x 迁移到 7.x 的主要变化：

```typescript
// PIXI.js 6.x
const app = new PIXI.Application({
  width: 500,
  height: 500
});
document.body.appendChild(app.view);

// PIXI.js 7.x
const app = new PIXI.Application();
await app.init({
  width: 500,
  height: 500
});
document.body.appendChild(app.canvas);
```

## 常见问题

### 1. 如何解决类型错误？

确保所有包都使用相同的 TypeScript 版本：

```bash
pnpm add -D typescript@~5.4.0 -w
```

### 2. 如何调试共享包？

```bash
# 在 shared 包中启动 watch 模式
pnpm --filter @miya/shared dev

# 在其他包中使用
pnpm --filter @miya/desktop dev
```

### 3. 如何处理 Live2D 资源？

Live2D 模型应放在 `public/live2d/` 目录下，路径为：

```
packages/desktop/public/live2d/haru/model.json
packages/web/public/live2d/haru/model.json
```

## 迁移检查清单

- [ ] 安装 pnpm
- [ ] 安装所有依赖
- [ ] 迁移所有 Vue 组件到 React
- [ ] 更新状态管理（Pinia → Zustand）
- [ ] 更新 API 调用（使用 @miya/shared）
- [ ] 更新 Live2D 组件
- [ ] 测试桌面应用功能
- [ ] 测试 Web 应用功能
- [ ] 构建应用验证

## 获取帮助

如有问题，请查看：
- `/frontend/README.md` - 项目概述
- `/packages/*/README.md` - 各包的详细文档
- 项目的 GitHub Issues
