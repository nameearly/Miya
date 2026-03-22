import { create } from 'zustand';
import type { Notification } from '../types';

interface NotificationState {
  notifications: Notification[];

  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],

  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: Date.now(),
    };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // 自动移除通知
    const duration = notification.duration !== undefined && notification.duration !== 0
      ? notification.duration
      : 3000;

    if (duration !== 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, duration);
    }
  },

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clearNotifications: () =>
    set(() => ({
      notifications: [],
    })),
}));

// 便捷方法
export const notify = {
  info: (title: string, message: string, duration?: number) =>
    useNotificationStore.getState().addNotification({
      type: 'info',
      title,
      message,
      duration,
    }),

  success: (title: string, message: string, duration?: number) =>
    useNotificationStore.getState().addNotification({
      type: 'success',
      title,
      message,
      duration,
    }),

  warning: (title: string, message: string, duration?: number) =>
    useNotificationStore.getState().addNotification({
      type: 'warning',
      title,
      message,
      duration,
    }),

  error: (title: string, message: string, _duration?: number) =>
    useNotificationStore.getState().addNotification({
      type: 'error',
      title,
      message,
      duration: _duration || 5000,
    }),
};
