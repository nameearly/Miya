import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import type { SystemError } from '../types';

// ImportMeta 类型定义
declare global {
  interface ImportMeta {
    env?: {
      VITE_API_PORTS?: string;
      [key: string]: any;
    };
  }
}

/**
 * 平台类型
 */
export type Platform = 'web' | 'desktop' | 'mobile';

/**
 * 终端类型标识
 */
export type TerminalType = 'web' | 'desktop' | 'qq' | 'wechat' | 'telegram' | 'discord';

/**
 * 会话信息
 */
export interface SessionInfo {
  sessionId: string;
  terminalType: TerminalType;
  platform: Platform;
  startTime: number;
}

/**
 * API 客户端配置
 */
export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
  platform?: Platform;
  terminalType?: TerminalType;
  sessionId?: string;
  onError?: (error: SystemError) => void;
}

/**
 * 健康检查响应
 */
export interface HealthCheckResponse {
  status: 'ok' | 'error';
  version?: string;
  uptime?: number;
  services?: Record<string, boolean>;
}

/**
 * 聊天消息响应
 */
export interface ChatMessageResponse {
  status: 'success' | 'error';
  response?: string;
  error?: string;
  timestamp: string;
  stream_id?: string;
}

/**
 * 系统状态
 */
export interface SystemStatus {
  status: 'normal' | 'warning' | 'error';
  uptime: number;
  cpu: number;
  memory: number;
  disk: number;
  active_sessions: number;
}

/**
 * 自动检测可用的API端口
 */
async function detectApiPort(): Promise<number> {
  // 从环境变量获取端口列表，或使用默认值
  const envPorts = import.meta.env?.VITE_API_PORTS
    ? import.meta.env.VITE_API_PORTS.split(',').map(Number)
    : [];

  const ports = envPorts.length > 0 ? envPorts : [8002, 8001, 8000, 8080, 8888, 8003];
  const endpoints = ['/api/health', '/health', '/api/status', '/api/probe'];

  for (const port of ports) {
    for (const endpoint of endpoints) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1000);

        const response = await fetch(`http://localhost:${port}${endpoint}`, {
          method: 'GET',
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          console.log(`[ApiClient] 检测到API服务运行在端口 ${port}`);
          return port;
        }
      } catch {
        // 端口不可用，继续尝试下一个
      }
    }
  }

  console.warn('[ApiClient] 未检测到可用的API服务，使用默认端口 8001');
  return 8001;
}

/**
 * 创建 API 客户端
 */
export class ApiClient {
  private instance: AxiosInstance;
  private config: ApiClientConfig;
  private baseUrlPromise: Promise<string>;

  constructor(config: ApiClientConfig = {}) {
    this.config = {
      platform: 'web',
      terminalType: config.platform === 'desktop' ? 'desktop' : 'web',
      sessionId: this.generateSessionId(),
      ...config
    };

    this.baseUrlPromise = this.initializeBaseUrl();

    this.instance = axios.create({
      timeout: this.config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...this.config.headers
      },
      withCredentials: false // 允许跨域请求
    });

    this.setupInterceptors();
  }

  /**
   * 生成会话ID
   */
  private generateSessionId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 9);
    return `${this.config?.platform || 'web'}-${this.config?.terminalType || 'web'}-${timestamp}-${random}`;
  }

  /**
   * 初始化基础URL
   */
  private async initializeBaseUrl(): Promise<string> {
    if (this.config.baseURL) {
      return this.config.baseURL;
    }

    const port = await detectApiPort();
    return `http://localhost:${port}`;
  }

  /**
   * 获取基础URL
   */
  private async getBaseUrl(): Promise<string> {
    return this.baseUrlPromise;
  }

  /**
   * 重新检测端口
   */
  async redetectPort(): Promise<number> {
    this.baseUrlPromise = this.initializeBaseUrl();
    const baseUrl = await this.getBaseUrl();
    const match = baseUrl.match(/:(\d+)$/);
    return match ? parseInt(match[1], 10) : 8001;
  }

  /**
   * 获取当前会话信息
   */
  getSessionInfo(): SessionInfo {
    return {
      sessionId: this.config.sessionId || 'unknown',
      terminalType: this.config.terminalType || 'web',
      platform: this.config.platform || 'web',
      startTime: Date.now()
    };
  }

  /**
   * 设置拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器 - 自动添加会话信息
    this.instance.interceptors.request.use(
      async (request) => {
        const baseUrl = await this.getBaseUrl();
        request.baseURL = baseUrl;

        // 添加会话标识到请求头
        request.headers['X-Session-ID'] = this.config.sessionId;
        request.headers['X-Terminal-Type'] = this.config.terminalType;
        request.headers['X-Platform'] = this.config.platform;

        return request;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        const systemError: SystemError = {
          code: error.code || 'API_ERROR',
          message: error.message || '请求失败',
          details: error.response?.data,
          timestamp: Date.now()
        };

        if (this.config.onError) {
          this.config.onError(systemError);
        }

        return Promise.reject(systemError);
      }
    );
  }

  /**
   * GET 请求
   */
  async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  /**
   * POST 请求
   */
  async post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  /**
   * PUT 请求
   */
  async put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  /**
   * DELETE 请求
   */
  async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  /**
   * 获取 Axios 实例
   */
  getInstance(): AxiosInstance {
    return this.instance;
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.get<HealthCheckResponse>('/api/health');
  }

  /**
   * 发送聊天消息
   */
  async sendMessage(message: string): Promise<ChatMessageResponse> {
    return this.post<ChatMessageResponse>('/api/terminal/chat', {
      message,
      session_id: this.config.sessionId,
      from_terminal: this.config.terminalType
    });
  }

  /**
   * 获取系统状态
   */
  async getSystemStatus(): Promise<SystemStatus> {
    return this.get<SystemStatus>('/api/status');
  }

  /**
   * 检查连接状态
   */
  async checkConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * 根据平台创建API客户端
 */
export function createApiClient(platform: Platform, additionalConfig?: Partial<ApiClientConfig>): ApiClient {
  const terminalType: TerminalType = platform === 'desktop' ? 'desktop' : 'web';

  return new ApiClient({
    platform,
    terminalType,
    ...additionalConfig
  });
}

/**
 * 默认 API 客户端实例（向后兼容）
 */
export const apiClient = new ApiClient({
  baseURL: undefined, // 让客户端自动检测
  platform: 'web'
});
