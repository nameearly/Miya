import { apiClient } from './client';
import type { SystemInfo, SystemConfig } from '../types';

/**
 * 获取系统信息
 */
export async function getSystemInfo(): Promise<SystemInfo> {
  return apiClient.get<SystemInfo>('/api/system/info');
}

/**
 * 获取系统配置
 */
export async function getSystemConfig(): Promise<SystemConfig> {
  return apiClient.get<SystemConfig>('/api/system/config');
}

/**
 * 更新系统配置
 */
export async function updateSystemConfig(config: Partial<SystemConfig>): Promise<SystemConfig> {
  return apiClient.put<SystemConfig>('/api/system/config', config);
}

/**
 * 重启系统
 */
export async function restartSystem(): Promise<void> {
  return apiClient.post<void>('/api/system/restart');
}

/**
 * 关闭系统
 */
export async function shutdownSystem(): Promise<void> {
  return apiClient.post<void>('/api/system/shutdown');
}
