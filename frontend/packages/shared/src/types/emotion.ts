/**
 * 情感类型
 */
export enum EmotionType {
  HAPPY = 'happy',
  SAD = 'sad',
  ANGRY = 'angry',
  SURPRISED = 'surprised',
  NEUTRAL = 'neutral',
  LOVE = 'love',
  EXCITED = 'excited',
  CALM = 'calm'
}

/**
 * 情感强度
 */
export enum EmotionIntensity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

/**
 * 情感状态接口
 */
export interface EmotionState {
  type: EmotionType;
  intensity: EmotionIntensity;
  confidence: number; // 0-1
  timestamp: number;
}

/**
 * 情感变化事件
 */
export interface EmotionEvent {
  previous: EmotionState;
  current: EmotionState;
  reason?: string;
}
