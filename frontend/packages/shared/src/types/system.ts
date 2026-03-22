/**
 * 系统状态
 */
export enum SystemStatus {
  INITIALIZING = 'initializing',
  READY = 'ready',
  BUSY = 'busy',
  ERROR = 'error',
  OFFLINE = 'offline'
}

/**
 * 系统信息接口
 */
export interface SystemInfo {
  status: SystemStatus;
  version: string;
  uptime: number;
  memoryUsage: number;
  cpuUsage: number;
  lastUpdated: number;
}

/**
 * 系统配置接口
 */
export interface SystemConfig {
  apiUrl: string;
  websocketUrl: string;
  debugMode: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

/**
 * 系统错误接口
 */
export interface SystemError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: number;
}
