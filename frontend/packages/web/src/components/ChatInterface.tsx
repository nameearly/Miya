import { useState, useRef, useEffect, useMemo, useCallback, memo } from 'react';
import { Send, Bot, User } from 'lucide-react';
import { apiClient } from '../services/api';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import wsService from '../services/websocket';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface ChatInterfaceProps {
  className?: string;
}

export function ChatInterface({ className }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: '你好！我是弥娅，您的 AI 助手。有什么可以帮助您的吗？',
      timestamp: Date.now(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // WebSocket 连接
  useEffect(() => {
    wsService.connect();

    // 监听系统消息
    const unsubscribe = wsService.on('message', (data) => {
      const systemMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.content || '收到系统消息',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, systemMessage]);
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = useCallback(async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await apiClient.sendMessage(inputText);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.status === 'success' && response.response
          ? response.response
          : '抱歉，连接弥娅核心时出错。请确保 API 服务正在运行。',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，连接弥娅核心时出错。请确保 API 服务正在运行。',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [inputText, isLoading]);

  const quickActions = useMemo(() => [
    { label: '👋 你好', message: '你好' },
    { label: '🤔 你能做什么？', message: '你能做什么？' },
    { label: '📝 打开记事本', message: '打开记事本' },
    { label: '🦊 打开浏览器', message: '打开火狐浏览器' },
    { label: '📊 系统状态', message: '系统状态' },
    { label: '❓ 帮助', message: '帮助' },
  ], []);

  const handleQuickAction = useCallback((message: string) => {
    setInputText(message);
    inputRef.current?.focus();
  }, []);

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* 消息列表 - 使用虚拟滚动优化长对话 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4" style={{ height: '600px' }}>
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-lg">
                <Bot size={20} />
              </div>
              <div className="px-5 py-3 rounded-2xl rounded-bl-sm bg-white border border-gray-200 shadow-lg">
                <div className="flex items-center gap-2 text-gray-600">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 快捷操作按钮 */}
      <div className="px-6 py-4 border-t border-gray-200/50 bg-white/50 backdrop-blur-sm">
        <div className="flex flex-wrap gap-2">
          {quickActions.map((action) => (
            <QuickActionButton
              key={action.label}
              label={action.label}
              message={action.message}
              onClick={handleQuickAction}
            />
          ))}
        </div>
      </div>

      {/* 输入框 */}
      <div className="p-6 bg-white/50 backdrop-blur-sm border-t border-gray-200/50">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="输入消息与弥娅对话..."
            className="flex-1 px-5 py-3 text-base border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:outline-none transition-colors duration-200"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !inputText.trim()}
            className={clsx(
              'px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl active:scale-95',
              (isLoading || !inputText.trim()) && 'opacity-50 cursor-not-allowed'
            )}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}

// 使用 memo 优化消息项组件
const MessageItem = memo(({ message }: { message: ChatMessage }) => {
  return (
    <div
      className={clsx(
        'flex animate-fade-in',
        message.role === 'user' ? 'justify-end' : 'justify-start'
      )}
    >
      <div className="flex items-start gap-3 max-w-[70%]">
        {message.role === 'assistant' && (
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-lg">
            <Bot size={20} />
          </div>
        )}
        <div
          className={clsx(
            'px-5 py-3 rounded-2xl shadow-lg',
            message.role === 'user'
              ? 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white rounded-br-sm'
              : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          <p
            className={clsx(
              'text-xs mt-2 opacity-70',
              message.role === 'user' ? 'text-right' : 'text-left'
            )}
          >
            {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>
        {message.role === 'user' && (
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center text-white shadow-lg">
            <User size={20} />
          </div>
        )}
      </div>
    </div>
  );
});

// 使用 memo 优化快捷操作按钮
const QuickActionButton = memo(({ label, message, onClick }: { label: string; message: string; onClick: (msg: string) => void }) => (
  <button
    onClick={() => onClick(message)}
    className="px-4 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:border-indigo-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all duration-200 shadow-sm"
  >
    {label}
  </button>
));
