import { apiClient } from './client';
import type { User, UserPreferences } from '../types';

/**
 * 获取当前用户
 */
export async function getCurrentUser(): Promise<User> {
  return apiClient.get<User>('/api/user/me');
}

/**
 * 获取用户偏好设置
 */
export async function getUserPreferences(): Promise<UserPreferences> {
  return apiClient.get<UserPreferences>('/api/user/preferences');
}

/**
 * 更新用户偏好设置
 */
export async function updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
  return apiClient.put<UserPreferences>('/api/user/preferences', preferences);
}

/**
 * 更新用户状态
 */
export async function updateUserStatus(status: User['status']): Promise<User> {
  return apiClient.put<User>('/api/user/status', { status });
}

/**
 * 上传头像
 */
export async function uploadAvatar(file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append('avatar', file);
  return apiClient.post<{ url: string }>('/api/user/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}
