# Tauri 图标说明

## 当前状态
图标目录 `icons/` 不存在，需要添加图标文件。

## 需要的图标尺寸

```
icons/
├── 32x32.png      (32x32 像素)
├── 128x128.png    (128x128 像素)
├── 128x128@2x.png (256x256 像素，高 DPI）
├── icon.png        (任意尺寸，推荐 512x512）
└── icon.icns       (macOS 专用）
```

## 快速创建占位图标

如果你没有设计图标，可以临时创建纯色图标：

### Windows
- 32x32.png → 纯蓝/紫渐变
- 128x128.png → 纯蓝/紫渐变

### macOS
- icon.icns → 使用 `iconutil` 或在线工具生成

### 临时解决方案

**选项 1：禁用图标验证**
编辑 `tauri.conf.json`，添加：
```json
{
  "bundle": {
    "icon": []
  }
}
```

**选项 2：使用 Tauri 默认图标**
不指定图标路径，Tauri 会使用默认图标。

**选项 3：下载免费图标**
- https://www.flaticon.com/
- https://icon-icons.com/
- 搜索 "AI", "robot", "assistant" 关键词

## 验证图标

创建图标后，运行：
```bash
pnpm tauri build
```

如果成功，图标会出现在：
- Windows: `src-tauri/target/release/bundle/nsis/MIYA AI Assistant-setup.exe`
- macOS: `src-tauri/target/release/bundle/dmg/`
- Linux: `src-tauri/target/release/bundle/appimage/`
