import React, { useState } from 'react';
import { getMessages, sendMessage } from '@miya/shared/api';
import type { Message } from '@miya/shared/types';
import './Chat.css';

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: '你好！我是弥娅，很高兴见到你！',
      type: 'text' as const,
      direction: 'incoming' as const,
      status: 'sent' as const,
      timestamp: Date.now()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      type: 'text',
      direction: 'outgoing',
      status: 'sending',
      timestamp: Date.now()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendMessage({
        content: input,
        type: 'text',
        direction: 'outgoing',
        status: 'sent',
        timestamp: Date.now()
      });

      setMessages((prev) => [
        ...prev.slice(0, -1),
        { ...userMessage, status: 'sent' },
        response
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { ...userMessage, status: 'failed' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="web-chat-page">
      <div className="web-chat-page__header">
        <h2>聊天</h2>
      </div>

      <div className="web-chat-page__content">
        <div className="web-chat-page__messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`web-chat-page__message web-chat-page__message--${message.direction}`}
            >
              <div className="web-chat-page__message-content">
                {message.content}
              </div>
              <div className="web-chat-page__message-time">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
          {loading && (
            <div className="web-chat-page__message web-chat-page__message--assistant">
              <div className="web-chat-page__message-content web-chat-page__message-content--typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        <div className="web-chat-page__input">
          <input
            type="text"
            placeholder="输入消息..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            className="web-chat-page__input-field"
            disabled={loading}
          />
          <button
            className="web-chat-page__input-button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            {loading ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
};
