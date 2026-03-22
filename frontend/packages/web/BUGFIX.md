# Web端错误修复说明

## 修复的问题

### 1. React.memo 导入错误 ✅
**问题**: `ChatInterface.tsx` 中使用了 `memo` 但未导入
**修复**: 在 `ChatInterface.tsx` 添加了 `memo` 和 `wsService` 的导入
```typescript
import { useState, useRef, useEffect, useMemo, useCallback, memo } from 'react';
import wsService from '../services/websocket';
```

### 2. PWA 图标资源缺失 ✅
**问题**: manifest.json 引用了不存在的 PNG 图标文件
**修复**:
- 创建了 SVG 格式的图标文件 (`icon-192.svg`, `icon-512.svg`)
- 更新 manifest.json 使用 SVG 图标
- 在 index.html 添加了正确的 favicon 和图标链接

### 3. API 端口配置优化 ✅
**问题**: 前端尝试连接错误的 API 端口
**修复**:
- 更新 `.env.development` 指向正确的端口 8002
- 更新 shared 包的端口检测逻辑，优先使用环境变量配置的端口
- 在 `web_main.py` 添加了缺失的 `/api/system/info` 端点

### 4. CORS 配置 ✅
**问题**: 前端跨域请求被阻止
**确认**: 后端已正确配置 CORS，支持所有来源
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. 构建问题 ✅
**问题**: Vite 8 无法找到入口文件
**修复**:
- 降级到 Vite 5.4.21
- 在 vite.config.ts 中明确配置 `root` 和 `publicDir`
- 安装缺失的依赖 (lucide-react, clsx, tailwind-merge)
- 成功构建前端到 `dist` 目录

## 服务架构

### 端口分配
- **8001**: Runtime API Server (核心API)
- **8002**: Web Server (前端静态服务 + API代理)
- **5174**: Vite Dev Server (开发环境)

### 数据流向
```
浏览器 → Web Server (8002) → Runtime API (8001) → 弥娅核心
```

## 测试步骤

### 1. 启动服务
```bash
# 方式1: 使用启动脚本
start.bat
# 选择 [2] Web Client

# 方式2: 手动启动
# 终端1: 启动 Runtime API
python run/runtime_api_start.py

# 终端2: 启动 Web 服务
python webnet/web_main.py
```

### 2. 访问应用
打开浏览器访问: http://localhost:8002

### 3. 验证功能
- [ ] 页面正常加载，无控制台错误
- [ ] 可以发送消息并获得响应
- [ ] WebSocket 连接正常（查看控制台日志）
- [ ] PWA 可以安装（检查浏览器地址栏图标）
- [ ] Service Worker 正常注册（开发者工具 > Application > Service Workers）
- [ ] 图标和 favicon 正常显示

### 4. 检查控制台
打开浏览器开发者工具 (F12)，检查：
- Console 标签：不应有错误
- Network 标签：API 请求返回 200 状态码
- Application 标签：Service Worker 已激活

## 构建命令

### 开发模式
```bash
cd frontend/packages/web
npm run dev
# 访问: http://localhost:5174
```

### 生产构建
```bash
cd frontend/packages/web
node node_modules/vite/bin/vite.js build
# 输出到: frontend/packages/web/dist
```

## 注意事项

1. **端口冲突**: 如果默认端口被占用，服务会自动切换到下一个可用端口
2. **API 代理**: Web Server 会自动代理 API 请求到 Runtime API
3. **CORS**: 已配置为允许所有来源，生产环境应该限制为特定域名
4. **Service Worker**: 需要在 HTTPS 或 localhost 环境下才能正常工作
5. **WebSocket**: 需要确保 Runtime API 的 WebSocket 端点可用

## 错误排查

### 如果看到 CORS 错误
检查 Runtime API 服务是否正在运行在端口 8001

### 如果 API 请求失败
检查浏览器 Network 标签，查看具体是哪个请求失败
- `/api/health` - Runtime API 健康检查
- `/api/terminal/chat` - 聊天接口
- `/api/system/info` - 系统信息

### 如果页面空白
检查控制台是否有 JavaScript 错误，通常是：
- memo 未定义（已修复）
- 模块加载失败
- React 渲染错误

## 已知限制

1. WebSocket 服务当前默认连接 `ws://localhost:8001/ws`，如果端口改变需要修改
2. 部分 API 端点返回模拟数据，需要连接真实的弥娅核心
3. PWA 离线功能依赖 Service Worker 缓存策略
