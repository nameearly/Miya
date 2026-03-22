# @miya/live2d

弥娅 Live2D 组件库，提供 React Live2D 组件。

## 安装

```bash
pnpm add @miya/live2d
```

## 使用

```tsx
import { Live2DAvatar } from '@miya/live2d';
import '@miya/live2d/styles.css';

function App() {
  return (
    <Live2DAvatar
      modelId="haru"
      width={500}
      height={500}
      draggable
      scalable
    />
  );
}
```

## 组件

### Live2DAvatar

Live2D 头像组件，支持拖拽和缩放。

#### Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| modelId | `string` | - | Live2D 模型 ID |
| width | `number` | `500` | 容器宽度 |
| height | `number` | `500` | 容器高度 |
| draggable | `boolean` | `false` | 是否可拖拽 |
| scalable | `boolean` | `false` | 是否可缩放 |
| opacity | `number` | `1` | 透明度 (0-1) |
| onLoad | `() => void` | - | 加载完成回调 |
| onError | `(error: Error) => void` | - | 错误回调 |

### Live2DViewer

Live2D 查看器组件，包含更多控制功能。

#### Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| modelId | `string` | - | Live2D 模型 ID |
| width | `number` | `500` | 容器宽度 |
| height | `number` | `500` | 容器高度 |
| showControls | `boolean` | `true` | 是否显示控制面板 |
| autoMotion | `boolean` | `true` | 是否自动播放动作 |
| onMotionChange | `(motion: string) => void` | - | 动作变化回调 |

## 可用模型

- `haru` - 春
- `haru_01` - 春 (制服)
- `haru_02` - 春 (礼服)
- `hijiki` - 羊栖菜
- `haru_greeter` - 春 (迎宾)
- `mark` - 马克
- `rice` - 米饭
- `natori` - 名取
- `tsumiki` - 积木
- `sana` - 小夏
- `izumi` - 泉
- `hiyori` - 日和
- `tororo` - 汤圆
- `wanko` - 小狗
- `miku` - 初音未来

## API

### Live2DManager

Live2D 管理器，用于管理 Live2D 模型和状态。

```typescript
import { Live2DManager } from '@miya/live2d';

const manager = new Live2DManager();
await manager.loadModel('haru');
manager.playMotion('talk');
```

## 示例

详见 `examples/` 目录。
