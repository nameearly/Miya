# Miya 新前端

基于React 18 + TypeScript 5.5构建的现代化前端应用,采用淡青色+淡蓝色主题,支持玻璃质感和自定义背景。

## ✨ 特性

- 🎨 **唯美视觉设计**: 淡青色+淡蓝色渐变,玻璃质感UI
- 🎭 **Live2D集成**: 可爱的虚拟形象展示
- 💬 **智能对话**: 支持Markdown渲染,代码高亮
- 📊 **实时监控**: CPU、内存、交互端状态
- 🧠 **记忆查询**: 搜索和管理认知记忆
- 🤖 **技能管理**: 查看和执行AI技能
- 🛠️ **工具调用**: 直接调用系统工具
- 🎯 **交互端管理**: 控制所有交互端
- 🌓 **主题切换**: 支持浅色/深色/自动主题
- 🖼️ **自定义背景**: 支持上传背景图片
- ⚡ **高性能**: 虚拟滚动,懒加载,代码分割

## 🚀 快速开始

### 前置要求

- Node.js 18+
- npm 9+ 或 pnpm 8+

### 安装依赖

```bash
cd frontend
npm install
# 或
pnpm install
```

### 开发模式

```bash
# Web开发
npm run dev

# 桌面应用开发
npm run dev:desktop
```

### 构建生产版本

```bash
# Web构建
npm run build

# 桌面应用构建
npm run build:desktop
```

### 预览生产版本

```bash
npm run preview
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/     # UI组件
│   │   ├── ui/       # 基础组件(Button, Card, Input等)
│   │   ├── layout/    # 布局组件
│   │   ├── chat/      # 聊天组件
│   │   ├── monitor/   # 监控组件
│   │   ├── memory/    # 记忆组件
│   │   └── live2d/   # Live2D组件
│   ├── pages/        # 页面组件
│   ├── stores/       # Zustand状态管理
│   ├── services/     # API服务
│   ├── hooks/        # 自定义Hooks
│   ├── types/        # TypeScript类型
│   ├── utils/        # 工具函数
│   └── styles/       # 全局样式
├── public/          # 静态资源
├── index.html       # Web入口
├── package.json
└── vite.config.ts   # Vite配置
```

## 🎨 设计规范

### 配色方案

#### 主色调
- 淡青色: `#14B8A6` (cyan-500)
- 淡蓝色: `#3B82F6` (blue-500)
- 强调色: `#8B5CF6` (purple-500)

#### 情感色
- 快乐: `#FFB7B2`
- 平静: `#B7E4C7`
- 悲伤: `#B5D8EB`
- 兴奋: `#FFDAC1`
- 中性: `#E0E0E0`

#### 玻璃质感
- 背景透明度: 65%
- 模糊度: 16px
- 边框透明度: 25%
- 阴影: `0 8px 32px rgba(31, 38, 135, 0.12)`

### 组件规范

#### Button组件
```tsx
<Button variant="primary">主要按钮</Button>
<Button variant="secondary">次要按钮</Button>
<Button variant="glass">玻璃按钮</Button>
<Button variant="ghost">幽灵按钮</Button>
```

#### Card组件
```tsx
<Card variant="glass">
  <CardHeader>
    <CardTitle>标题</CardTitle>
  </CardHeader>
  <CardContent>内容</CardContent>
</Card>
```

#### Badge组件
```tsx
<Badge variant="success">运行中</Badge>
<Badge variant="warning">警告</Badge>
<Badge variant="error">错误</Badge>
```

## 🔧 配置

### 主题配置

应用支持三种主题:
- `light`: 浅色主题
- `dark`: 深色主题
- `auto`: 跟随系统

主题设置会持久化到localStorage。

### 自定义背景

1. 进入设置页面
2. 点击"选择背景图片"
3. 上传你的图片
4. 调整磨砂玻璃效果强度

### Live2D配置

- 模型选择: `haru`, `haru_01`, `haru_02`
- 自动动作: 开启/关闭
- 情感联动: 根据对话情感自动调整表情

## 📡 API集成

前端自动检测可用的API端口(8000, 8001, 8080, 8888)。

支持的API端点:
- `POST /api/terminal/chat` - 发送消息
- `GET /api/status` - 获取系统状态
- `GET /api/endpoints` - 获取交互端列表
- `POST /api/endpoints/:id/start` - 启动交互端
- `POST /api/endpoints/:id/stop` - 停止交互端
- `GET /api/skills/list` - 获取技能列表
- `POST /api/skills/execute` - 执行技能
- `GET /api/tools/list` - 获取工具列表
- `POST /api/tools/call` - 调用工具
- `GET /api/mcp/servers` - 获取MCP服务器列表

## 🛠️ 开发指南

### 添加新页面

1. 在`src/pages/`创建页面组件
2. 在`src/App.tsx`添加路由
3. 在侧边栏添加导航项

### 添加新组件

1. 在`src/components/ui/`创建组件
2. 使用`cn`工具函数合并className
3. 遵循设计规范

### 状态管理

使用Zustand管理状态:
```tsx
import { useChatStore } from '@/stores/chatStore';

function MyComponent() {
  const messages = useChatStore((state) => state.messages);
  const sendMessage = useChatStore((state) => state.sendMessage);

  return <div>...</div>;
}
```

### API调用

```tsx
import { api } from '@/services/api';

const result = await api.sendMessage({
  message: '你好',
  session_id: 'session_123',
  platform: 'web',
});

if (result.success) {
  console.log(result.data);
}
```

## 📝 TODO

- [ ] 完善监控页面
- [ ] 完善记忆查询页面
- [ ] 完善技能/工具页面
- [ ] 添加WebSocket实时通信
- [ ] 集成Live2D模型
- [ ] 添加国际化支持
- [ ] 添加单元测试
- [ ] 添加E2E测试
- [ ] 性能优化(虚拟滚动、懒加载)
- [ ] 文档完善

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📄 许可证

MIT License

## 🙏 致谢

- React
- TypeScript
- Tailwind CSS
- Zustand
- TanStack Query
- Recharts
- Lucide Icons
