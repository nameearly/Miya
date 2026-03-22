import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { ChatMessage } from '../types';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';

  // Actions
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  deleteMessage: (id: string) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setConnectionStatus: (status: 'connected' | 'connecting' | 'disconnected' | 'error') => void;
}

export const useChatStore = create<ChatState>()(
  immer((set) => ({
    messages: [
      {
        id: 'welcome',
        role: 'assistant',
        content: '你好！我是弥娅，很高兴见到你！',
        timestamp: Date.now(),
      },
    ],
    isLoading: false,
    connectionStatus: 'disconnected',

    addMessage: (message) =>
      set((state) => {
        state.messages.push(message);
      }),

    updateMessage: (id, updates) =>
      set((state) => {
        const message = state.messages.find((m) => m.id === id);
        if (message) {
          Object.assign(message, updates);
        }
      }),

    deleteMessage: (id) =>
      set((state) => {
        state.messages = state.messages.filter((m) => m.id !== id);
      }),

    clearMessages: () =>
      set((state) => {
        state.messages = [];
      }),

    setLoading: (loading) =>
      set((state) => {
        state.isLoading = loading;
      }),

    setConnectionStatus: (status) =>
      set((state) => {
        state.connectionStatus = status;
      }),
  }))
);
