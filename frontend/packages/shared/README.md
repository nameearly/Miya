# @miya/shared

弥娅前端共享代码包，包含类型定义、API 客户端和工具函数。

## 安装

```bash
pnpm add @miya/shared
```

## 使用

### 类型定义

```typescript
import type { Message, EmotionState, User } from '@miya/shared/types';
```

### API 客户端

```typescript
import { apiClient } from '@miya/shared/api';

// 获取消息
const messages = await apiClient.getMessages();

// 发送消息
await apiClient.sendMessage({
  content: '你好',
  emotion: 'happy'
});
```

### 工具函数

```typescript
import { formatDate, debounce, throttle } from '@miya/shared/utils';

const formatted = formatDate(new Date());
const debouncedFn = debounce(myFunction, 300);
```

## 包结构

```
src/
├── index.ts           # 主入口
├── types/             # 类型定义
│   ├── index.ts       # 导出所有类型
│   ├── chat.ts        # 聊天相关类型
│   ├── emotion.ts     # 情感相关类型
│   └── user.ts        # 用户相关类型
├── api/               # API 客户端
│   ├── index.ts       # 导出 API 客户端
│   ├── client.ts      # Axios 客户端配置
│   ├── chat.ts        # 聊天 API
│   └── system.ts      # 系统 API
└── utils/             # 工具函数
    ├── index.ts       # 导出所有工具函数
    ├── date.ts        # 日期处理
    ├── format.ts      # 格式化
    └── throttle.ts    # 防抖节流
```
