/**
 * 用户角色
 */
export enum UserRole {
  GUEST = 'guest',
  USER = 'user',
  ADMIN = 'admin',
  DEVELOPER = 'developer'
}

/**
 * 用户状态
 */
export enum UserStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  AWAY = 'away',
  BUSY = 'busy'
}

/**
 * 用户接口
 */
export interface User {
  id: string;
  name: string;
  avatar?: string;
  email?: string;
  role: UserRole;
  status: UserStatus;
  createdAt: number;
  lastActiveAt: number;
}

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: boolean;
  soundEnabled: boolean;
  live2dEnabled: boolean;
  voiceEnabled: boolean;
}
