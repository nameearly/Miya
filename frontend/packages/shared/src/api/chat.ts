import { apiClient } from './client';
import type { Message, ChatConfig } from '../types';

/**
 * 获取消息列表
 */
export async function getMessages(): Promise<Message[]> {
  return apiClient.get<Message[]>('/api/messages');
}

/**
 * 发送消息
 */
export async function sendMessage(
  message: Omit<Message, 'id' | 'timestamp' | 'status'>
): Promise<Message> {
  return apiClient.post<Message>('/api/messages', message);
}

/**
 * 获取聊天配置
 */
export async function getChatConfig(): Promise<ChatConfig> {
  return apiClient.get<ChatConfig>('/api/chat/config');
}

/**
 * 更新聊天配置
 */
export async function updateChatConfig(config: Partial<ChatConfig>): Promise<ChatConfig> {
  return apiClient.put<ChatConfig>('/api/chat/config', config);
}

/**
 * 删除消息
 */
export async function deleteMessage(messageId: string): Promise<void> {
  return apiClient.delete<void>(`/api/messages/${messageId}`);
}

/**
 * 清空消息历史
 */
export async function clearMessages(): Promise<void> {
  return apiClient.delete<void>('/api/messages');
}
