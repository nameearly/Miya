# 弥娅 Web 端和桌面端测试指南

## ✅ 构建状态

**Web 前端构建成功！**

```
总大小: 260.7 KB
Gzip 压缩: ~75 KB
```

## 📋 测试检查清单

### Web 端测试

#### 1. 启动开发服务器

```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
pnpm --filter @miya/web dev
```

- [ ] 服务器启动成功（端口 5174）
- [ ] 访问 http://localhost:5174 能看到页面
- [ ] 页面样式正常
- [ ] 控制台无错误

#### 2. 生产环境预览

```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
pnpm --filter @miya/web preview
```

- [ ] 预览服务器启动
- [ ] 访问 http://localhost:4173 能看到页面
- [ ] 所有功能正常

#### 3. PWA 功能测试

- [ ] 浏览器显示"安装弥娅"提示
- [ ] 可以安装为桌面应用
- [ ] 离线时显示离线通知
- [ ] Service Worker 正常注册（F12 → Application → Service Workers）

#### 4. 性能测试

打开浏览器 DevTools（F12）：

**Network 标签：**
- [ ] 首屏加载 < 100 KB
- [ ] 页面切换时懒加载正常
- [ ] 静态资源有缓存标记
- [ ] API 请求正常

**Lighthouse 测试：**
```bash
# 安装 Lighthouse
npm install -g lighthouse

# 运行测试
lighthouse http://localhost:5174 --view
```

关键指标：
- [ ] Performance > 90
- [ ] Best Practices > 90
- [ ] Accessibility > 90
- [ ] PWA > 90

---

### Tauri 桌面端测试

#### 1. 开发模式启动

```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web
pnpm tauri dev
```

**预期结果：**
- [ ] Tauri 窗口打开
- [ ] 应用正常显示
- [ ] 窗口尺寸：1200x800
- [ ] 开发者工具正常（F12）

#### 2. 生产构建

```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web
pnpm tauri build
```

**预期结果：**
- [ ] 构建成功
- [ ] 在 `src-tauri/target/release/` 生成 exe 文件
- [ ] exe 文件可以双击运行
- [ ] 应用体积 < 15 MB

#### 3. 桌面端功能测试

**系统信息 API：**
```javascript
// 在浏览器控制台测试
invoke('get_system_info')
```

- [ ] 能获取 CPU 使用率
- [ ] 能获取内存使用情况
- [ ] 能获取进程数量

**窗口控制：**
```javascript
invoke('minimize_window')  // 最小化
invoke('maximize_window')  // 最大化/还原
invoke('close_window')      // 关闭
```

- [ ] 最小化功能正常
- [ ] 最大化功能正常
- [ ] 关闭功能正常

**文件/URL 操作：**
```javascript
invoke('open_url', { url: 'https://example.com' })
invoke('open_file', { path: 'C:\\path\\to\\file.txt' })
```

- [ ] 打开 URL 功能正常
- [ ] 打开文件功能正常

**系统通知：**
```javascript
invoke('show_notification', {
  title: '测试通知',
  body: '这是一条测试通知'
})
```

- [ ] 通知显示正常
- [ ] 通知点击正常

---

### 功能验证

#### 聊天功能

- [ ] 可以输入消息
- [ ] 可以发送消息
- [ ] AI 回复正常显示
- [ ] 快捷操作按钮工作
- [ ] 消息时间戳正确

#### 管理面板

- [ ] 可以切换到管理页面
- [ ] 概览数据加载正常
- [ ] 工具列表显示正常
- [ ] 日志显示正常
- [ ] 刷新按钮工作

#### 监控页面

- [ ] CPU 使用率显示
- [ ] 内存使用显示
- [ ] 运行时间显示
- [ ] 系统状态显示

#### 路由切换

- [ ] 页面切换流畅
- [ ] 懒加载正常工作
- [ ] URL 更新正确
- [ ] 浏览器前进后退正常

---

### 错误排查

#### 如果 Web 端无法启动

**问题：** 端口被占用
```bash
# 查找占用 5174 端口的进程
netstat -ano | findstr :5174

# 杀死进程
taskkill /PID <进程ID> /F
```

**问题：** 模块依赖错误
```bash
# 重新安装依赖
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
rm -rf node_modules
pnpm install
```

#### 如果 Tauri 无法启动

**问题：** Rust 工具链问题
```bash
# 检查 Rust 版本
rustc --version

# 重新安装 Rust（如需要）
# 下载：https://rustup.rs/
```

**问题：** WebView 缺失
```bash
# Windows: 安装 WebView2
# 下载：https://developer.microsoft.com/en-us/microsoft-edge/webview2
```

**问题：** 图标文件缺失
```bash
# 创建占位图标
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web/src-tauri/icons
# 需要添加 32x32, 128x128, 256x256, 512x512 的 .png 文件
```

---

### 性能基准

| 指标 | 目标值 | Web 端 | 桌面端 |
|------|--------|---------|---------|
| 首屏加载 | < 100 KB | ✅ 75 KB | ✅ 75 KB |
| 首次内容渲染 (FCP) | < 1.8s | ? | ? |
| 最大内容渲染 (LCP) | < 2.5s | ? | ? |
| 首次输入延迟 (FID) | < 100ms | ? | ? |
| 交互时间 (TTI) | < 3.8s | ? | ? |

---

## 🚀 快速启动脚本

### Web 端（开发）
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
pnpm --filter @miya/web dev
```

### Web 端（生产）
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
pnpm --filter @miya/web build && pnpm --filter @miya/web preview
```

### Tauri 桌面端（开发）
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web
pnpm tauri dev
```

### Tauri 桌面端（生产）
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web
pnpm tauri build
```

---

## 📞 问题反馈

如果遇到问题，请记录以下信息：

1. **环境信息**
   - 操作系统：Windows/Linux/macOS
   - Node.js 版本：`node -v`
   - pnpm 版本：`pnpm -v`
   - Rust 版本：`rustc --version`

2. **错误信息**
   - 浏览器控制台错误（F12 → Console）
   - 网络请求错误（F12 → Network）
   - 系统错误信息

3. **复现步骤**
   - 操作步骤
   - 预期结果
   - 实际结果

---

## ✨ 总结

**当前状态：**
- ✅ Web 端构建成功
- ✅ 代码分割完成（13 个 chunk）
- ✅ Service Worker 集成
- ✅ PWA 支持完成
- ⏳ 待测试实际运行

**下一步：**
1. 启动开发服务器测试 Web 端
2. 启动 Tauri 测试桌面端
3. 验证所有功能
4. 性能测试和优化
