/**
 * WebSocket 客户端
 * 支持实时双向通信
 */

import React from 'react';

export interface WebSocketConfig {
  url?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface WebSocketMessage {
  type: 'chat' | 'system' | 'event' | 'error';
  data: unknown;
  timestamp: number;
  sessionId?: string;
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private config: Required<WebSocketConfig>;
  private handlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isManualClose = false;

  constructor(config: WebSocketConfig = {}) {
    this.config = {
      url: config.url || this.getDefaultUrl(),
      autoReconnect: config.autoReconnect ?? true,
      reconnectInterval: config.reconnectInterval ?? 3000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
    };
    this.url = this.config.url;
  }

  /**
   * 获取默认WebSocket URL
   */
  private getDefaultUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
    return `${protocol}//${host}:${port}/ws`;
  }

  /**
   * 连接WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.isManualClose = false;

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.handleConnectionError(error);
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] Disconnected:', event.code, event.reason);
          this.handleDisconnect(event);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 发送消息
   */
  send(type: string, data: unknown): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Not connected, cannot send message');
      return;
    }

    const message: WebSocketMessage = {
      type: type as WebSocketMessage['type'],
      data,
      timestamp: Date.now(),
    };

    this.ws.send(JSON.stringify(message));
  }

  /**
   * 注册事件处理器
   */
  on(type: string, handler: WebSocketEventHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // 返回取消订阅函数
    return () => {
      this.off(type, handler);
    };
  }

  /**
   * 取消事件处理器
   */
  off(type: string, handler: WebSocketEventHandler): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 处理收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.handlers.get(message.type) || this.handlers.get('*');
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }

    // 通用消息处理器
    const allHandlers = this.handlers.get('*');
    if (allHandlers) {
      allHandlers.forEach((handler) => handler(message));
    }
  }

  /**
   * 处理连接错误
   */
  private handleConnectionError(error: Event): void {
    this.emit({
      type: 'error',
      data: { error: 'WebSocket connection error' },
      timestamp: Date.now(),
    });
  }

  /**
   * 处理断开连接
   */
  private handleDisconnect(event: CloseEvent): void {
    if (this.isManualClose) {
      return;
    }

    if (this.config.autoReconnect && this.reconnectAttempts < this.config.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`[WebSocket] Reconnecting... Attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts}`);

      this.reconnectTimer = setTimeout(() => {
        this.connect().catch((error) => {
          console.error('[WebSocket] Reconnect failed:', error);
        });
      }, this.config.reconnectInterval);
    }
  }

  /**
   * 发送消息给所有处理器
   */
  private emit(message: WebSocketMessage): void {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }
  }

  /**
   * 获取连接状态
   */
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

/**
 * 创建WebSocket客户端实例
 */
export function createWebSocketClient(config?: WebSocketConfig): WebSocketClient {
  return new WebSocketClient(config);
}

/**
 * WebSocket Hook
 */
export function useWebSocket(config?: WebSocketConfig) {
  const [client] = React.useState(() => new WebSocketClient(config));
  const [isConnected, setIsConnected] = React.useState(false);

  React.useEffect(() => {
    const unsubscribe = client.on('system', (message) => {
      if (message.data === 'connected') {
        setIsConnected(true);
      } else if (message.data === 'disconnected') {
        setIsConnected(false);
      }
    });

    client.connect();

    return () => {
      unsubscribe();
      client.disconnect();
    };
  }, [client]);

  return {
    client,
    isConnected,
    send: client.send.bind(client),
    on: client.on.bind(client),
    off: client.off.bind(client),
  };
}

