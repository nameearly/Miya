# Miya 新前端设计方案

## 视觉设计理念

### 核心关键词
- **淡青色 + 淡蓝色**: 主色调
- **柔和 + 唯美**: 整体风格
- **简约 + 二次元**: 设计语言
- **技术 + 自然**: 平衡感
- **自定义背景**: 个性化
- **磨砂 + 玻璃质感**: 现代感

### 配色方案

#### 主色调
```css
/* 淡青色系 */
--color-cyan-50: #F0FDFA;
--color-cyan-100: #CCFBF1;
--color-cyan-200: #99F6E4;
--color-cyan-300: #5EEAD4;
--color-cyan-400: #2DD4BF;
--color-cyan-500: #14B8A6;

/* 淡蓝色系 */
--color-blue-50: #EFF6FF;
--color-blue-100: #DBEAFE;
--color-blue-200: #BFDBFE;
--color-blue-300: #93C5FD;
--color-blue-400: #60A5FA;
--color-blue-500: #3B82F6;

/* Miya 品牌色 */
--color-primary: #14B8A6;       /* 主色 - 青色 */
--color-secondary: #3B82F6;     /* 次色 - 蓝色 */
--color-accent: #8B5CF6;        /* 强调色 - 紫色 */
```

#### 情感色
```css
--emotion-happy: #FFB7B2;      /* 快乐 - 淡粉色 */
--emotion-calm: #B7E4C7;       /* 平静 - 淡绿色 */
--emotion-sad: #B5D8EB;        /* 悲伤 - 淡蓝色 */
--emotion-excited: #FFDAC1;    /* 兴奋 - 淡橙色 */
--emotion-neutral: #E0E0E0;    /* 中性 - 灰色 */
```

#### 玻璃质感
```css
--glass-bg: rgba(255, 255, 255, 0.65);
--glass-bg-hover: rgba(255, 255, 255, 0.8);
--glass-border: rgba(255, 255, 255, 0.25);
--glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.12);
--glass-blur: blur(16px);
```

## 技术架构

### 项目结构 (单代码库复用)

```
frontend/
├── src/                      # 源代码 (Web和Desktop共享)
│   ├── components/            # UI组件库
│   │   ├── ui/              # 基础UI组件
│   │   ├── layout/          # 布局组件
│   │   ├── chat/            # 聊天相关组件
│   │   ├── monitor/         # 监控相关组件
│   │   ├── memory/          # 记忆相关组件
│   │   └── live2d/         # Live2D组件
│   │
│   ├── pages/               # 页面组件
│   │   ├── ChatPage.tsx
│   │   ├── MonitorPage.tsx
│   │   ├── MemoryPage.tsx
│   │   ├── EndpointsPage.tsx
│   │   ├── SkillsPage.tsx
│   │   ├── ToolsPage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── stores/              # Zustand状态管理
│   │   ├── chatStore.ts
│   │   ├── monitorStore.ts
│   │   ├── systemStore.ts
│   │   └── settingsStore.ts
│   │
│   ├── services/            # API服务
│   │   ├── api.ts          # 统一API客户端
│   │   ├── chat.ts         # 聊天API
│   │   ├── monitor.ts      # 监控API
│   │   └── websocket.ts   # WebSocket客户端
│   │
│   ├── hooks/              # 自定义Hooks
│   │   ├── useChat.ts
│   │   ├── useMonitor.ts
│   │   ├── useWebSocket.ts
│   │   └── useTheme.ts
│   │
│   ├── types/              # TypeScript类型
│   │   ├── chat.ts
│   │   ├── system.ts
│   │   └── api.ts
│   │
│   ├── utils/              # 工具函数
│   │   ├── cn.ts          # className合并
│   │   ├── format.ts      # 格式化函数
│   │   └── validation.ts  # 验证函数
│   │
│   ├── styles/             # 全局样式
│   │   ├── globals.css     # 全局CSS
│   │   └── themes/        # 主题样式
│   │       ├── light.css
│   │       └── dark.css
│   │
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件 (Web)
│   └── router.tsx         # 路由配置
│
├── electron/              # Electron特定代码
│   ├── main.ts            # Electron主进程
│   ├── preload.ts         # 预加载脚本
│   └── build.ts          # 构建配置
│
├── public/               # 静态资源
│   ├── images/           # 背景图片
│   ├── icons/           # 图标
│   └── live2d/         # Live2D资源
│
├── index.html           # Web入口
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vite.config.ts       # Web配置
└── electron.vite.config.ts  # Electron配置
```

## 核心页面设计

### 1. 聊天页面 (ChatPage)

#### 布局
```
┌─────────────────────────────────────────────────────┐
│  Header: 弥娅 | 情感状态 | 设置 | Live2D开关       │
├─────────────────────────────────────────────────────┤
│  │                                                 │
│  │        消息列表区 (可滚动)                       │
│  │                                                 │
│  │  ┌──────────────────────────────────┐           │
│  │  │ 用户: 你好                      │           │
│  │  │ 时间: 10:30                    │           │
│  │  └──────────────────────────────────┘           │
│  │                                                 │
│  │  ┌──────────────────────────────────┐           │
│  │  │ 弥娅: 在呢~                     │           │
│  │  │ 😊 情感: 快乐                  │           │
│  │  └──────────────────────────────────┘           │
│  │                                                 │
├─────────────────────────────────────────────────────┤
│  输入框 + 工具栏 (表情、文件、语音)                │
└─────────────────────────────────────────────────────┘
```

#### 特性
- 消息气泡(用户右侧,助手左侧)
- Live2D展示(可折叠到右侧或独立窗口)
- 实时情感状态显示
- Markdown渲染(代码高亮)
- 支持多行输入

### 2. 监控页面 (MonitorPage)

#### 布局
```
┌─────────────────────────────────────────────────────┐
│  Header: 系统监控 | 自动刷新: ON                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐               │
│  │  CPU 使用率   │  │  内存使用     │               │
│  │   45%        │  │   2.4 GB     │               │
│  └──────────────┘  └──────────────┘               │
│                                                     │
│  ┌──────────────────────────────────────┐           │
│  │        CPU/内存 实时图表              │           │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━       │           │
│  └──────────────────────────────────────┘           │
│                                                     │
│  ┌──────────────────────────────────────┐           │
│  │        交互端状态列表               │           │
│  │  ┌────────────────────────────┐    │           │
│  │  │ Web终端      ● 运行中      │    │           │
│  │  │ 桌面终端      ● 运行中      │    │           │
│  │  │ QQ机器人     ● 运行中      │    │           │
│  │  └────────────────────────────┘    │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

#### 特性
- 实时CPU/内存/网络图表
- 交互端状态列表(带启动/停止按钮)
- 服务健康状态
- 日志查看器
- 性能指标卡片

### 3. 记忆页面 (MemoryPage)

#### 布局
```
┌─────────────────────────────────────────────────────┐
│  Header: 记忆查询 | 搜索                         │
├─────────────────────────────────────────────────────┤
│  搜索框: [在此搜索记忆...]                       │
│  标签: [全部] [系统] [修复] [最佳实践] [用户偏好] │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐         │
│  │ 📌 最佳实践: API调用优化          │         │
│  │ 时间: 2026-03-20 | 置信度: 95%  │         │
│  │ 内容: 使用缓存减少API调用...       │         │
│  └──────────────────────────────────────┘         │
│                                                     │
│  ┌──────────────────────────────────────┐         │
│  │ 🔧 修复历史: 终端I/O错误         │         │
│  │ 时间: 2026-03-19 | 置信度: 90%  │         │
│  │ 内容: 修改multi_terminal_main...   │         │
│  └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

#### 特性
- 智能搜索(支持关键词、时间范围)
- 记忆分类标签
- 记忆卡片(展示关键信息)
- 详情弹窗
- 记忆编辑/删除

### 4. 交互端管理页面 (EndpointsPage)

#### 布局
```
┌─────────────────────────────────────────────────────┐
│  Header: 交互端管理 | 添加交互端                  │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐         │
│  │  Web终端                          │         │
│  │  状态: ● 运行中                   │         │
│  │  类型: HTTP API                    │         │
│  │  会话数: 3                        │         │
│  │  [查看详情] [停止] [重启]         │         │
│  └──────────────────────────────────────┘         │
│                                                     │
│  ┌──────────────────────────────────────┐         │
│  │  桌面终端                          │         │
│  │  状态: ● 运行中                   │         │
│  │  类型: Electron App                │         │
│  │  会话数: 1                        │         │
│  │  [查看详情] [停止] [重启]         │         │
│  └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

#### 特性
- 所有交互端状态列表
- 启动/停止/重启控制
- 实时状态更新(WebSocket)
- 交互端详情(会话、日志、统计)
- 批量操作

### 5. 技能/工具页面

#### 布局
```
┌─────────────────────────────────────────────────────┐
│  Header: 技能 & 工具 | 执行历史                  │
├─────────────────────────────────────────────────────┤
│  Tabs: [技能] [工具] [执行历史]                 │
│                                                     │
│  ┌──────────────────────────────────────┐         │
│  │ 🤖 程序启动器                     │         │
│  │ 启动本地应用程序                    │         │
│  │ [执行]                              │         │
│  └──────────────────────────────────────┘         │
│                                                     │
│  ┌──────────────────────────────────────┐         │
│  │ 🔍 记忆搜索                       │         │
│  │ 搜索认知记忆                        │         │
│  │ [执行]                              │         │
│  └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

#### 特性
- 可用技能/工具列表
- 参数输入表单
- 执行历史记录
- 执行状态追踪
- 权限管理

### 6. 设置页面 (SettingsPage)

#### 布局
```
┌─────────────────────────────────────────────────────┐
│  Header: 设置                                      │
├─────────────────────────────────────────────────────┤
│  Tabs: [外观] [Live2D] [语音] [API] [高级]       │
│                                                     │
│  ┌──────────────────────────────────────┐         │
│  │ 外观设置                           │         │
│  │                                    │         │
│  │ 主题: ○ 浅色 ● 深色 ○ 自动       │         │
│  │                                    │         │
│  │ 背景图片:                         │         │
│  │ [选择图片...]                      │         │
│  │ [恢复默认]                         │         │
│  │                                    │         │
│  │ 磨砂玻璃效果: ● 启用              │         │
│  │ 透明度: [━━━━━○━━━] 50%         │         │
│  └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

#### 特性
- 主题切换(浅色/深色/自动)
- 自定义背景图片
- 磨砂玻璃效果强度调节
- Live2D设置(模型、动作、位置)
- 语音设置(TTS/STT)
- API配置(端口、认证)

## UI组件系统

### 基础组件 (components/ui/)

```typescript
// Button - 按钮
<Button variant="primary">发送</Button>
<Button variant="ghost">取消</Button>

// Card - 卡片(玻璃质感)
<Card variant="glass">
  <CardHeader>标题</CardHeader>
  <CardContent>内容</CardContent>
</Card>

// Input - 输入框
<Input placeholder="请输入..." />

// Badge - 标签
<Badge variant="success">运行中</Badge>
<Badge variant="warning">警告</Badge>

// Progress - 进度条
<Progress value={75} />

// StatCard - 统计卡片
<StatCard
  title="CPU使用率"
  value="45%"
  icon={<CpuIcon />}
  trend="+2%"
/>

// EndpointCard - 交互端卡片
<EndpointCard
  name="Web终端"
  status="running"
  onAction={handleAction}
/>

// MessageBubble - 消息气泡
<MessageBubble
  role="assistant"
  content="在呢~"
  emotion="happy"
/>

// Live2DViewer - Live2D展示器
<Live2DViewer
  model="haru"
  emotion={emotion}
  size="medium"
  collapsible
/>
```

### 布局组件 (components/layout/)

```typescript
// MainLayout - 主布局
<MainLayout>
  <Sidebar />
  <MainContent />
  <Live2DPanel />
</MainLayout>

// Sidebar - 侧边栏
<Sidebar>
  <NavItem icon={<ChatIcon />} to="/chat">聊天</NavItem>
  <NavItem icon={<MonitorIcon />} to="/monitor">监控</NavItem>
  <NavItem icon={<MemoryIcon />} to="/memory">记忆</NavItem>
  <NavItem icon={<EndpointIcon />} to="/endpoints">交互端</NavItem>
</Sidebar>

// Header - 头部
<Header>
  <Logo />
  <SystemStatus />
  <UserMenu />
</Header>
```

## 状态管理 (Zustand)

```typescript
// stores/chatStore.ts
interface ChatStore {
  messages: Message[];
  isSending: boolean;
  sessionId: string;
  emotion: EmotionState;

  sendMessage: (content: string) => Promise<void>;
  clearHistory: () => void;
  setEmotion: (emotion: EmotionState) => void;
}

// stores/monitorStore.ts
interface MonitorStore {
  endpoints: Endpoint[];
  systemStatus: SystemStatus;
  isAutoRefresh: boolean;

  refreshEndpoints: () => Promise<void>;
  startAutoRefresh: () => void;
  stopAutoRefresh: () => void;
  toggleEndpoint: (id: string) => Promise<void>;
}

// stores/settingsStore.ts
interface SettingsStore {
  theme: 'light' | 'dark' | 'auto';
  backgroundImage: string;
  glassEffect: boolean;
  glassOpacity: number;
  live2dEnabled: boolean;

  updateSettings: (settings: Partial<Settings>) => void;
  resetSettings: () => void;
}
```

## API服务层

```typescript
// services/api.ts
class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = await this.detectApiPort();
  }

  async detectApiPort(): Promise<string> {
    // 自动检测可用API端口
  }

  // 聊天API
  async sendMessage(data: ChatRequest): Promise<ChatResponse>
  async getHistory(sessionId: string): Promise<Message[]>

  // 系统API
  async getStatus(): Promise<SystemStatus>
  async getEndpoints(): Promise<Endpoint[]>
  async toggleEndpoint(id: string, action: 'start' | 'stop'): Promise<void>

  // 记忆API
  async searchMemories(query: string, filters: MemoryFilters): Promise<Memory[]>
  async getMemoryTypes(): Promise<MemoryType[]>

  // 技能/工具API
  async getSkills(): Promise<Skill[]>
  async executeSkill(name: string, params: any): Promise<ExecutionResult>
  async getTools(): Promise<Tool[]>
  async callTool(name: string, params: any): Promise<ExecutionResult>
}

// services/websocket.ts
class WebSocketService {
  private ws: WebSocket;
  private subscriptions: Map<string, Set<Callback>>;

  connect(): void
  subscribe(event: string, callback: Callback): Unsubscribe
  emit(event: string, data: any): void
  disconnect(): void
}
```

## 样式系统

### 全局样式 (styles/globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  /* 基础颜色 */
  --color-primary: #14B8A6;
  --color-secondary: #3B82F6;
  --color-accent: #8B5CF6;

  /* 背景色 */
  --color-bg-primary: #F0FDFA;
  --color-bg-secondary: #EFF6FF;

  /* 文本色 */
  --color-text-primary: #1E293B;
  --color-text-secondary: #64748B;

  /* 玻璃质感 */
  --glass-bg: rgba(255, 255, 255, 0.65);
  --glass-border: rgba(255, 255, 255, 0.25);
  --glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.12);
  --glass-blur: blur(16px);

  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
}

.dark {
  /* 深色主题 */
  --color-bg-primary: #0F172A;
  --color-bg-secondary: #1E293B;
  --color-text-primary: #F1F5F9;
  --color-text-secondary: #94A3B8;

  --glass-bg: rgba(30, 41, 59, 0.65);
  --glass-border: rgba(255, 255, 255, 0.1);
}

body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  transition: background-color 0.3s ease;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(20, 184, 166, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(20, 184, 166, 0.5);
}

/* 玻璃质感类 */
.glass {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
```

## 开发步骤

### Phase 1: 基础设施 (1-2周)
1. ✅ 创建项目结构
2. 配置Tailwind CSS + 主题系统
3. 创建基础UI组件(Button, Card, Input等)
4. 配置Zustand状态管理
5. 创建API服务层
6. 配置路由

### Phase 2: 核心功能 (2-3周)
1. 聊天页面
2. 监控页面
3. 交互端管理页面
4. WebSocket实时通信

### Phase 3: 高级功能 (2-3周)
1. 记忆查询页面
2. 技能/工具页面
3. 设置页面
4. Live2D集成优化

### Phase 4: 优化完善 (1-2周)
1. 性能优化(虚拟滚动、懒加载)
2. 主题系统完善
3. 自定义背景功能
4. 文档和测试

## Web和Desktop复用方案

### 共享代码
```
src/
├── components/    # Web和Desktop共享
├── pages/         # Web和Desktop共享
├── stores/        # Web和Desktop共享
├── services/      # Web和Desktop共享
├── hooks/         # Web和Desktop共享
├── types/         # Web和Desktop共享
└── styles/        # Web和Desktop共享
```

### 平台特定代码
```
src/
├── web/          # Web特定
│   └── main.tsx
│
└── electron/     # Electron特定
    ├── main.ts   # 主进程
    └── preload.ts # 预加载脚本
```

### 构建配置
```typescript
// vite.config.ts - Web构建
export default defineConfig({
  root: 'src/web',
  build: {
    outDir: '../../dist/web',
  },
})

// electron.vite.config.ts - Electron构建
export default defineConfig({
  root: 'src/electron',
  build: {
    outDir: '../../dist/electron',
  },
})
```

## 设计亮点

### 1. 视觉效果
- 淡青色+淡蓝色渐变背景
- 玻璃质感卡片和面板
- 柔和的阴影和模糊效果
- 流畅的动画过渡

### 2. 交互体验
- 响应式设计(适配桌面和移动)
- 实时状态更新
- 直观的操作反馈
- 快捷键支持

### 3. 功能完整性
- 覆盖所有Miya核心功能
- 完整的交互端管理
- 详细的监控和日志
- 丰富的自定义选项

### 4. 技术先进性
- 现代React特性(Concurrent Mode)
- TypeScript类型安全
- WebSocket实时通信
- 高性能渲染

## 总结

这个设计方案实现了:
✅ 淡青色+淡蓝色主题
✅ 柔和唯美的玻璃质感
✅ 简约二次元风格
✅ 自定义背景支持
✅ 磨砂玻璃效果
✅ 完整的交互端管理和监控
✅ Web和Desktop代码复用
✅ 现代化技术栈

下一步可以开始创建具体的组件和页面实现!
