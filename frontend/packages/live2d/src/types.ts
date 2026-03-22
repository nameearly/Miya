/**
 * Live2D 模型类型
 */
export type Live2DModelType = 'haru' | 'hiyori' | 'mark' | 'natori' | 'rice';

/**
 * Live2D 表情类型
 */
export type Live2DMotion =
  | 'idle'
  | 'greeting'
  | 'talking'
  | 'thinking'
  | 'happy'
  | 'sad'
  | 'angry'
  | 'surprised';

/**
 * Live2D 组件配置
 */
export interface Live2DConfig {
  model: Live2DModelType;
  width?: number;
  height?: number;
  interactive?: boolean;
  motion?: Live2DMotion;
  scale?: number;
  position?: { x: number; y: number };
  autoMotion?: boolean;
}

/**
 * Live2D 事件
 */
export interface Live2DEvents {
  onModelLoaded?: () => void;
  onMotionStart?: (motion: Live2DMotion) => void;
  onMotionEnd?: (motion: Live2DMotion) => void;
  onTap?: () => void;
  onDrag?: (x: number, y: number) => void;
}
