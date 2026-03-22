# 弥娅前端 Monorepo

这是弥娅项目的统一前端代码仓库，使用 pnpm workspace 管理。

## 项目结构

```
frontend/
├── packages/
│   ├── shared/          # 共享代码（类型定义、API、工具函数）
│   ├── live2d/          # Live2D 组件库
│   ├── desktop/         # Electron 桌面应用
│   └── web/             # Web 应用
└── package.json
```

## 快速开始

### 安装依赖

```bash
pnpm install
```

### 开发

```bash
# 启动桌面应用
pnpm dev:desktop

# 启动 Web 应用
pnpm dev:web

# 启动所有应用
pnpm dev
```

### 构建

```bash
# 构建所有包
pnpm build

# 构建桌面应用
pnpm build:desktop

# 构建 Web 应用
pnpm build:web
```

## 技术栈

- **框架**: React 18 + TypeScript
- **桌面端**: Electron 29.x
- **状态管理**: Zustand 4.x
- **路由**: React Router DOM 6.x
- **构建工具**: Vite 5.x
- **包管理**: pnpm workspace

## 统一依赖版本

- PIXI.js: 7.3.2
- Electron: 29.x
- React: 18.2.0
- TypeScript: 5.4.x

## 开发规范

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 样式使用 Tailwind CSS
- 代码风格遵循 ESLint + Prettier

## 迁移说明

详见 `MIGRATION_GUIDE.md`
