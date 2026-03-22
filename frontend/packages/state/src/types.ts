/**
 * 聊天消息
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

/**
 * 会话信息
 */
export interface SessionInfo {
  id: string;
  terminalType: 'web' | 'desktop' | 'qq' | 'wechat' | 'telegram' | 'discord';
  platform: 'web' | 'desktop' | 'mobile';
  startTime: number;
}

/**
 * 系统状态
 */
export interface SystemStatus {
  status: 'normal' | 'warning' | 'error';
  uptime: number;
  cpu: number;
  memory: number;
  disk: number;
  activeSessions: number;
}

/**
 * 设置
 */
export interface Settings {
  theme: 'auto' | 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
  live2dEnabled: boolean;
  voiceEnabled: boolean;
  soundEnabled: boolean;
  notificationsEnabled: boolean;
  autoReply: boolean;
  typingAnimation: boolean;
  customBackground?: string;
}

/**
 * 连接状态
 */
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

/**
 * 通知类型
 */
export type NotificationType = 'info' | 'success' | 'warning' | 'error';

/**
 * 通知
 */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: number;
  duration?: number;
}
