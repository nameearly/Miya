# 弥娅共享包使用指南

## 📦 共享包概览

弥娅前端项目包含以下共享包，可在桌面端和Web端中复用：

| 包名 | 描述 | 作用 |
|------|------|------|
| `@miya/shared` | 核心共享包 | API客户端、类型定义、工具函数 |
| `@miya/ui` | UI组件库 | 通用UI组件 |
| `@miya/state` | 状态管理 | Zustand stores、通知系统 |
| `@miya/live2d` | Live2D组件 | Live2D虚拟角色 |

---

## 1. @miya/shared - 核心共享包

### API 客户端

```typescript
import { createApiClient } from '@miya/shared/api';

// 创建桌面端客户端
const desktopApi = createApiClient('desktop');

// 创建Web端客户端
const webApi = createApiClient('web');

// 发送消息
const response = await desktopApi.sendMessage('你好');
console.log(response.response);

// 健康检查
await desktopApi.healthCheck();

// 获取系统状态
const status = await desktopApi.getSystemStatus();
```

### WebSocket 实时通信

```typescript
import { useWebSocket } from '@miya/shared/api';

function MyComponent() {
  const { client, isConnected, send, on } = useWebSocket();

  useEffect(() => {
    // 监听聊天消息
    const unsubscribe = on('chat', (message) => {
      console.log('收到消息:', message);
    });

    return unsubscribe;
  }, []);

  const handleSend = () => {
    send('chat', { content: 'Hello' });
  };

  return (
    <div>
      <p>连接状态: {isConnected ? '已连接' : '未连接'}</p>
      <button onClick={handleSend}>发送消息</button>
    </div>
  );
}
```

### 类型定义

```typescript
import type {
  Platform,
  TerminalType,
  SessionInfo,
  HealthCheckResponse,
  ChatMessageResponse,
  SystemStatus,
  ApiClientConfig
} from '@miya/shared/api';
```

---

## 2. @miya/ui - UI组件库

### Button 按钮

```typescript
import { Button } from '@miya/ui';

<Button variant="primary" size="md" onClick={handleClick}>
  点击我
</Button>

<Button variant="secondary" icon={<Icon />}>
  带图标
</Button>

<Button variant="danger" loading={isLoading}>
  加载中
</Button>
```

### Card 卡片

```typescript
import { Card, CardHeader, CardBody, CardFooter } from '@miya/ui';

<Card variant="glass" hover>
  <CardHeader>
    <h2>标题</h2>
  </CardHeader>
  <CardBody>
    <p>内容</p>
  </CardBody>
  <CardFooter>
    <Button>确定</Button>
  </CardFooter>
</Card>
```

### Input 输入框

```typescript
import { Input } from '@miya/ui';

<Input
  label="用户名"
  placeholder="请输入用户名"
  error={error}
  icon={<Icon />}
  onChange={(e) => setValue(e.target.value)}
/>
```

### Modal 模态框

```typescript
import { Modal } from '@miya/ui';

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="提示"
  size="lg"
>
  <p>模态框内容</p>
  <div className="flex justify-end gap-2 mt-4">
    <Button variant="secondary" onClick={() => setIsOpen(false)}>
      取消
    </Button>
    <Button onClick={handleConfirm}>确定</Button>
  </div>
</Modal>
```

### Badge 徽章

```typescript
import { Badge } from '@miya/ui';

<Badge variant="success">成功</Badge>
<Badge variant="error" dot>在线</Badge>
<Badge variant="warning" size="sm">警告</Badge>
```

---

## 3. @miya/state - 状态管理

### Chat Store - 聊天状态

```typescript
import { useChatStore } from '@miya/state';

function ChatComponent() {
  const { messages, isLoading, connectionStatus, addMessage } = useChatStore();

  return (
    <div>
      {messages.map((msg) => (
        <div key={msg.id}>
          {msg.role}: {msg.content}
        </div>
      ))}
    </div>
  );
}
```

### Settings Store - 设置状态

```typescript
import { useSettingsStore } from '@miya/state';

function SettingsComponent() {
  const { theme, live2dEnabled, updateSettings } = useSettingsStore();

  const handleThemeChange = (newTheme) => {
    updateSettings({ theme: newTheme });
  };

  return (
    <div>
      <select value={theme} onChange={(e) => handleThemeChange(e.target.value)}>
        <option value="auto">自动</option>
        <option value="light">浅色</option>
        <option value="dark">深色</option>
      </select>
    </div>
  );
}
```

### Notification Store - 通知系统

```typescript
import { notify, useNotificationStore } from '@miya/state';

// 使用便捷方法
notify.success('成功', '操作成功！');
notify.error('错误', '发生错误');
notify.warning('警告', '请注意');
notify.info('信息', '这是一条通知');

// 或使用 store
function NotificationComponent() {
  const { notifications, removeNotification } = useNotificationStore();

  return (
    <div>
      {notifications.map((n) => (
        <div key={n.id}>
          {n.title}: {n.message}
          <button onClick={() => removeNotification(n.id)}>关闭</button>
        </div>
      ))}
    </div>
  );
}
```

### System Store - 系统状态

```typescript
import { useSystemStore } from '@miya/state';

function SystemStatusComponent() {
  const { status, connected } = useSystemStore();

  return (
    <div>
      <p>连接状态: {connected ? '已连接' : '未连接'}</p>
      {status && (
        <div>
          <p>CPU: {status.cpu}%</p>
          <p>内存: {status.memory}%</p>
        </div>
      )}
    </div>
  );
}
```

---

## 4. @miya/live2d - Live2D组件

### Live2DAvatar 组件

```typescript
import { Live2DAvatar, type Live2DMotion } from '@miya/live2d';

function AvatarComponent() {
  const [motion, setMotion] = React.useState<Live2DMotion>('idle');

  return (
    <div>
      <Live2DAvatar
        model="haru"
        width={300}
        height={300}
        interactive
        motion={motion}
        autoMotion
      />
      <div>
        <button onClick={() => setMotion('happy')}>开心</button>
        <button onClick={() => setMotion('sad')}>难过</button>
        <button onClick={() => setMotion('talking')}>说话</button>
      </div>
    </div>
  );
}
```

---

## 完整使用示例

### 桌面端示例

```typescript
// desktop/src/App.tsx
import React from 'react';
import { createApiClient } from '@miya/shared/api';
import { useChatStore, useSettingsStore } from '@miya/state';
import { Button, Card, Modal } from '@miya/ui';
import { Live2DAvatar } from '@miya/live2d';

const api = createApiClient('desktop');

export default function App() {
  const { messages, addMessage } = useChatStore();
  const { theme, updateSettings } = useSettingsStore();

  const handleSend = async () => {
    const response = await api.sendMessage('你好');
    addMessage({
      id: Date.now().toString(),
      role: 'assistant',
      content: response.response,
      timestamp: Date.now(),
    });
  };

  return (
    <div>
      <Card variant="glass">
        <Live2DAvatar model="haru" width={200} height={200} />
        {messages.map((msg) => (
          <p key={msg.id}>{msg.content}</p>
        ))}
        <Button onClick={handleSend}>发送</Button>
      </Card>
    </div>
  );
}
```

### Web端示例

```typescript
// web/src/App.tsx
import React from 'react';
import { createApiClient } from '@miya/shared/api';
import { useWebSocket } from '@miya/shared/api';
import { useChatStore, notify } from '@miya/state';
import { Button, Input, Badge } from '@miya/ui';

const api = createApiClient('web');

export default function App() {
  const { client, isConnected } = useWebSocket();
  const { messages, addMessage } = useChatStore();

  React.useEffect(() => {
    const unsubscribe = client.on('chat', (message) => {
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: message.data.content,
        timestamp: Date.now(),
      });
    });

    return unsubscribe;
  }, [client]);

  const handleSend = async () => {
    try {
      const response = await api.sendMessage('你好');
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: response.response,
        timestamp: Date.now(),
      });
      notify.success('成功', '消息发送成功');
    } catch (error) {
      notify.error('错误', '消息发送失败');
    }
  };

  return (
    <div>
      <Badge variant={isConnected ? 'success' : 'error'}>
        {isConnected ? '已连接' : '未连接'}
      </Badge>
      {messages.map((msg) => (
        <p key={msg.id}>{msg.content}</p>
      ))}
      <Button onClick={handleSend}>发送</Button>
    </div>
  );
}
```

---

## 构建和安装

### 安装所有依赖

```bash
cd frontend
pnpm install
```

### 构建共享包

```bash
# 构建所有共享包
pnpm --filter @miya/shared build
pnpm --filter @miya/ui build
pnpm --filter @miya/state build
pnpm --filter @miya/live2d build
```

### 启动开发服务器

```bash
# 桌面端
cd packages/desktop
pnpm dev

# Web端
cd packages/web
pnpm dev
```

---

## 优势总结

1. **代码复用**: 桌面端和Web端共享代码，减少90%的重复
2. **类型安全**: 统一的TypeScript类型定义
3. **一致性**: 相同的API、UI组件、状态管理逻辑
4. **维护性**: 修改一处，两端同步更新
5. **同时运行**: 桌面端和Web端可以同时使用，互不干扰
6. **实时通信**: WebSocket支持实时双向通信

---

## 注意事项

1. 修改共享包后需要重新构建
2. 桌面端和Web端可以同时运行
3. API客户端会自动检测端口，无需手动配置
4. WebSocket支持自动重连
5. 状态管理数据自动持久化到localStorage
