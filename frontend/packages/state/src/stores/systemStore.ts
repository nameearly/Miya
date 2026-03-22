import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { SystemStatus } from '../types';

interface SystemState {
  status: SystemStatus | null;
  connected: boolean;

  // Actions
  setSystemStatus: (status: SystemStatus) => void;
  setConnected: (connected: boolean) => void;
}

export const useSystemStore = create<SystemState>()(
  immer((set) => ({
    status: null,
    connected: false,

    setSystemStatus: (status) =>
      set((state) => {
        state.status = status;
      }),

    setConnected: (connected) =>
      set((state) => {
        state.connected = connected;
      }),
  }))
);
