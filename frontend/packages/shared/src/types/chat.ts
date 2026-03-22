/**
 * 消息类型
 */
export enum MessageType {
  TEXT = 'text',
  IMAGE = 'image',
  AUDIO = 'audio',
  VIDEO = 'video',
  FILE = 'file',
  SYSTEM = 'system'
}

/**
 * 消息方向
 */
export enum MessageDirection {
  INCOMING = 'incoming',
  OUTGOING = 'outgoing'
}

/**
 * 消息状态
 */
export enum MessageStatus {
  SENDING = 'sending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  READ = 'read',
  FAILED = 'failed'
}

/**
 * 消息接口
 */
export interface Message {
  id: string;
  content: string;
  type: MessageType;
  direction: MessageDirection;
  status: MessageStatus;
  timestamp: number;
  emotion?: string;
  metadata?: Record<string, unknown>;
}

/**
 * 聊天配置
 */
export interface ChatConfig {
  autoReply: boolean;
  emotionEnabled: boolean;
  voiceEnabled: boolean;
  typingAnimation: boolean;
}
