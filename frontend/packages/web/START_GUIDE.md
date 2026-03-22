# 弥娅 Web 和桌面端启动指南

## 🚀 快速启动

### Web 端（推荐用于开发）

#### 开发模式
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
pnpm --filter @miya/web dev
```
访问：http://localhost:5174

#### 生产预览
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend
pnpm --filter @miya/web build
pnpm --filter @miya/web preview
```
访问：http://localhost:4173

---

### Tauri 桌面端（推荐用于生产）

#### 开发模式
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web
pnpm tauri dev
```

#### 生产构建
```bash
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web
pnpm tauri build
```

生成的安装包位置：
- Windows: `src-tauri/target/release/bundle/nsis/MIYA AI Assistant-setup.exe`
- macOS: `src-tauri/target/release/bundle/dmg/`
- Linux: `src-tauri/target/release/bundle/appimage/`

---

## ✅ 验证清单

### Web 端
- [ ] 页面正常加载
- [ ] 样式显示正确
- [ ] 控制台无错误（F12）
- [ ] Service Worker 已注册（F12 → Application）
- [ ] PWA 可安装

### Tauri 桌面端
- [ ] 应用窗口正常打开
- [ ] 窗口尺寸为 1200x800
- [ ] 可以调整窗口大小
- [ ] 开发者工具可用（F12）
- [ ] 系统信息 API 工作
- [ ] 窗口控制 API 工作
- [ ] 文件/URL 打开工作

---

## 🔧 常见问题

### Web 端

**Q: 端口被占用？**
```bash
# 查找占用 5174 端口的进程
netstat -ano | findstr :5174

# 杀死进程
taskkill /PID <进程ID> /F
```

**Q: 样式不正常？**
- 清除浏览器缓存
- 检查 `index.css` 是否正确加载

**Q: API 请求失败？**
- 确保后端服务运行在 http://localhost:8001
- 检查浏览器控制台网络错误

### Tauri 桌面端

**Q: 构建失败？**
```bash
# 检查 Rust 版本
rustc --version

# 检查 WebView2（Windows）
# 下载：https://developer.microsoft.com/en-us/microsoft-edge/webview2
```

**Q: 图标缺失？**
参考：`src-tauri/README_ICONS.md`

**Q: Rust 依赖错误？**
```bash
# 重新构建 Tauri
cd d:/AI_MIYA_Facyory/MIYA/Miya/frontend/packages/web/src-tauri
cargo clean
cargo build
```

---

## 📊 性能测试

### Web 端 Lighthouse 评分
```bash
npm install -g lighthouse
lighthouse http://localhost:5174 --view
```

目标分数：
- Performance: > 90
- Best Practices: > 90
- Accessibility: > 90
- PWA: > 90

---

## 🎯 浏览器测试

### 推荐测试浏览器
- ✅ Chrome/Edge（主要测试）
- ✅ Firefox（兼容性测试）
- ✅ Safari（macOS 测试）

### 关键测试点
1. 页面加载速度
2. 聊天消息发送和接收
3. 页面切换流畅度
4. 窗口调整大小
5. 离线功能（PWA）

---

## 📝 测试反馈

请记录以下信息：

**环境：**
- 操作系统：Windows 11 / macOS / Linux
- 浏览器版本：
- Node.js 版本：`node -v`
- Rust 版本：`rustc --version`

**测试结果：**
- Web 端：通过 / 失败
- Tauri 端：通过 / 失败
- 功能测试结果：
- 遇到的问题：

---

## 🎉 成功标准

### Web 端
- [x] 构建成功（260.7 KB）
- [x] 代码分割完成（13 个 chunk）
- [x] Service Worker 集成
- [x] PWA 支持
- [x] 懒加载
- [x] 虚拟滚动
- [x] React.memo 优化

### Tauri 桌面端
- [x] Tauri 配置完成
- [x] 系统信息 API（8 个命令）
- [x] Rust 后端
- [ ] 图标文件（待添加）
- [ ] 实际运行测试

---

## 🚀 下一步

1. ✅ 运行 Web 端开发服务器
2. ⏳ 测试所有功能
3. ⏳ 运行 Tauri 开发模式
4. ⏳ 添加自定义图标
5. ⏳ 构建生产版本
6. ⏳ 性能测试和优化
