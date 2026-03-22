# 弥娅 Web 前端

现代化的 React Web 界面，用于与弥娅 AI 系统交互。

## 功能特点

- 🎨 现代化 UI 设计，使用 Tailwind CSS
- 💬 实时聊天界面，支持快捷操作
- 🔄 自动检测 API 服务端口
- 📱 响应式设计，支持移动端
- ✨ 流畅的动画效果
- 🌐 支持跨域 API 调用

## 开发

### 安装依赖

```bash
cd frontend/packages/web
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5174

### 构建生产版本

```bash
npm run build
```

构建输出到 `dist/` 目录。

## 技术栈

- React 18 + TypeScript
- Vite 5
- Tailwind CSS 3
- Axios
- Lucide React (图标)

## API 配置

开发模式下，Vite 会自动代理 `/api` 请求到 `http://localhost:8001`。

生产模式下，需要配置后端 CORS 允许跨域请求。
