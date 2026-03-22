/**
 * WebSocket 实时通信服务
 * 用于弥娅前端的实时数据推送和双向通信
 */

type WebSocketEventType = 'message' | 'status' | 'log' | 'error' | 'connection';

interface WebSocketMessage {
  type: WebSocketEventType;
  data: any;
  timestamp: number;
}

type EventHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 3000;
  private eventHandlers: Map<WebSocketEventType, Set<EventHandler>> = new Map();
  private isConnected: boolean = false;

  constructor(url: string = 'ws://localhost:8001/ws') {
    this.url = url;
  }

  /**
   * 连接 WebSocket 服务器
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.emit('connection', { status: 'connected' });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.emit(message.type, message.data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { error: 'Connection error' });
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.emit('connection', { status: 'disconnected' });

        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  /**
   * 发送消息
   */
  send(type: WebSocketEventType, data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: Date.now()
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * 注册事件处理器
   */
  on(event: WebSocketEventType, handler: EventHandler): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);

    // 返回取消订阅函数
    return () => this.off(event, handler);
  }

  /**
   * 移除事件处理器
   */
  off(event: WebSocketEventType, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 触发事件
   */
  private emit(event: WebSocketEventType, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  /**
   * 检查连接状态
   */
  getStatus(): 'connected' | 'disconnected' | 'connecting' {
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) return 'connected';
      if (this.ws.readyState === WebSocket.CONNECTING) return 'connecting';
    }
    return 'disconnected';
  }

  /**
   * 清理所有事件处理器
   */
  cleanup(): void {
    this.eventHandlers.clear();
    this.disconnect();
  }
}

// 创建全局单例
const wsService = new WebSocketService();

// 自动连接
if (typeof window !== 'undefined') {
  // 只在浏览器环境中自动连接
  // 可以根据需要决定是否自动连接
  // wsService.connect();
}

export default wsService;
export type { WebSocketEventType, WebSocketMessage, EventHandler };
