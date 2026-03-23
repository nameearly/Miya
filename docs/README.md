# MIYA AI Assistant

AI 虚拟助手系统 - Web + Tauri 桌面应用

## 快速启动

### Windows
```bash
.\start.bat
```

### Linux/Mac
```bash
./start.sh
```

## 启动选项

### 1. QQ Client
QQ 机器人客户端

### 2. Web Client
网页界面 - 访问 http://localhost:8000

### 3. Desktop Client (Tauri)
Tauri 桌面应用 - **需要安装 Rust**

**前置要求:**
- 安装 Rust: https://rustup.rs/
- 安装 C++ Build Tools (Windows)

### 4. Terminal Client
命令行终端交互

### 5. All Clients
启动所有客户端 (QQ + Web + Desktop + Terminal)

### 6. Web + Desktop
网页 + 桌面同时启动

### 7. Custom Launch
自定义选择要启动的服务

## 技术栈

### 前端
- **React 18** + TypeScript
- **Vite** 构建工具
- **TailwindCSS** 样式
- **Tauri 2.x** 桌面框架 (比 Electron 小 80%)

### 后端
- **Python** (FastAPI / Uvicorn)
- **Runtime API Server** (端口 8001)
- **WebSocket** 实时通信

### 前端架构
```
共享 React 组件
├── Web 端 (Vite dev server)
└── Desktop 端 (Tauri + WebView)
```

## API 服务

- **Runtime API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs
- **WebSocket**: ws://localhost:8001/ws

## 目录结构

```
Miya/
├── start.bat          # Windows 启动脚本
├── start.sh          # Linux/Mac 启动脚本
├── core/            # 核心逻辑
├── frontend/
│   └── packages/
│       └── web/     # React + Tauri 前端
│           ├── src/      # 源码
│           └── src-tauri/  # Tauri 后端
├── run/             # 运行脚本
├── memory/          # 记忆系统
└── config/          # 配置文件
```

## 开发

### 安装依赖

**Python:**
```bash
pip install -r requirements.txt
```

**Node.js:**
```bash
cd frontend
pnpm install
```

**Rust (桌面开发):**
```bash
# 访问 https://rustup.rs/
```

### 单独启动服务

**API 服务器:**
```bash
python run/runtime_api_start.py
```

**Web 端:**
```bash
cd frontend/packages/web
pnpm run dev
```

**Tauri 桌面:**
```bash
cd frontend/packages/web
pnpm run tauri:dev
```

## 特性

✅ 多终端支持 (QQ, Web, Desktop, Terminal)
✅ 实时 AI 对话
✅ Live2D 虚拟形象
✅ 记忆系统
✅ 插件系统
✅ WebSocket 实时通信

## 体积对比

| 指标 | Electron | Tauri |
|------|----------|--------|
| 运行时 | ~120MB | ~5-10MB |
| 安装包 | ~150MB | ~20-30MB |
| 内存 | ~200MB | ~50-80MB |

## 故障排查

### Desktop 端无法启动?
1. 检查 Rust 安装: `cargo --version`
2. 检查 C++ 工具 (Windows 需 Visual Studio Build Tools)
3. 确保 API 服务器正在运行

### API 连接失败?
1. 检查端口 8001 是否被占用
2. 查看日志: `logs/` 目录
3. 重启服务

## 许可证

MIT License

## 联系方式

- 项目仓库: [待添加]
- 问题反馈: [待添加]
