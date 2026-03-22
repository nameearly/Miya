/**
 * Web端 API 服务
 * 使用共享的 @miya/shared 包
 */

import { createApiClient, type Platform } from '@miya/shared/api';

// 创建Web端专用API客户端
export const apiClient = createApiClient('web');

// 导出类型供组件使用
export type {
  Platform,
  TerminalType,
  SessionInfo,
  HealthCheckResponse,
  ChatMessageResponse,
  SystemStatus,
  ApiClientConfig
} from '@miya/shared/api';

// 导出客户端实例
export default apiClient;

// 便捷方法导出
export const {
  healthCheck,
  sendMessage,
  getSystemStatus,
  checkConnection,
  redetectPort,
  getSessionInfo
} = apiClient;

// ========== 弥娅核心管理 API ==========

/**
 * 获取弥娅核心状态
 */
export const getMiyaStatus = async () => {
  const response = await fetch('http://localhost:8001/api/miya/status');
  if (!response.ok) throw new Error('Failed to get Miya status');
  return response.json();
};

/**
 * 获取记忆系统统计
 */
export const getMiyaMemory = async () => {
  const response = await fetch('http://localhost:8001/api/miya/memory');
  if (!response.ok) throw new Error('Failed to get Miya memory');
  return response.json();
};

/**
 * 获取工具列表
 */
export const getMiyaTools = async () => {
  const response = await fetch('http://localhost:8001/api/miya/tools');
  if (!response.ok) throw new Error('Failed to get Miya tools');
  return response.json();
};

/**
 * 获取人设和人格配置
 */
export const getMiyaPersonality = async () => {
  const response = await fetch('http://localhost:8001/api/miya/personality');
  if (!response.ok) throw new Error('Failed to get Miya personality');
  return response.json();
};

/**
 * 获取AI模型信息
 */
export const getMiyaModels = async () => {
  const response = await fetch('http://localhost:8001/api/miya/models');
  if (!response.ok) throw new Error('Failed to get Miya models');
  return response.json();
};

/**
 * 获取系统日志
 */
export const getMiyaLogs = async (limit: number = 100) => {
  const response = await fetch(`http://localhost:8001/api/miya/logs?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to get Miya logs');
  return response.json();
};
