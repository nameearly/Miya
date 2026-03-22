import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Settings } from '../types';

const DEFAULT_SETTINGS: Settings = {
  theme: 'auto',
  language: 'zh-CN',
  live2dEnabled: true,
  voiceEnabled: true,
  soundEnabled: true,
  notificationsEnabled: true,
  autoReply: true,
  typingAnimation: true,
  customBackground: undefined,
};

interface SettingsState extends Settings {
  updateSettings: (updates: Partial<Settings>) => void;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULT_SETTINGS,

      updateSettings: (updates) =>
        set((state) => ({
          ...state,
          ...updates,
        })),

      resetSettings: () => set(DEFAULT_SETTINGS),
    }),
    {
      name: 'miya-settings',
      version: 1,
    }
  )
);
