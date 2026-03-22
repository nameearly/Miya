/**
 * Live2D 模型接口
 */
export interface Live2DModel {
  id: string;
  name: string;
  path: string;
  thumbnail?: string;
  version: string;
  author?: string;
}

/**
 * Live2D 动作类型
 */
export enum Live2DMotionType {
  IDLE = 'idle',
  TALK = 'talk',
  HAPPY = 'happy',
  SAD = 'sad',
  SURPRISED = 'surprised',
  ANGRY = 'angry'
}

/**
 * Live2D 配置接口
 */
export interface Live2DConfig {
  modelId: string;
  position: {
    x: number;
    y: number;
  };
  scale: number;
  rotation: number;
  opacity: number;
  draggingEnabled: boolean;
  scalingEnabled: boolean;
}

/**
 * Live2D 状态接口
 */
export interface Live2DState {
  isLoaded: boolean;
  isPlaying: boolean;
  currentMotion: Live2DMotionType;
  currentExpression?: string;
}
