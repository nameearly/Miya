import React, { useState } from 'react';
import './Test.css';

export default function Test() {
  const [count, setCount] = useState(0);
  const [message, setMessage] = useState('');

  const testAPI = async () => {
    try {
      setMessage('测试中...');
      // 这里可以测试后端 API 连接
      setTimeout(() => {
        setMessage('✓ 前端运行正常！');
      }, 1000);
    } catch (error) {
      setMessage('✗ API 测试失败');
    }
  };

  return (
    <div className="test-page">
      <div className="test-container">
        <h1>弥娅前端测试页面</h1>

        <div className="test-section">
          <h2>React 功能测试</h2>
          <div className="counter">
            <button onClick={() => setCount(c => c - 1)}>-</button>
            <span>{count}</span>
            <button onClick={() => setCount(c => c + 1)}>+</button>
          </div>
        </div>

        <div className="test-section">
          <h2>API 连接测试</h2>
          <button onClick={testAPI}>测试 API</button>
          {message && <p className={message.startsWith('✓') ? 'success' : 'error'}>{message}</p>}
        </div>

        <div className="test-section">
          <h2>系统信息</h2>
          <ul>
            <li>平台: {navigator.platform}</li>
            <li>浏览器: {navigator.userAgent}</li>
            <li>语言: {navigator.language}</li>
          </ul>
        </div>

        <div className="test-section">
          <h2>路由测试</h2>
          <nav>
            <a href="/">首页</a>
            <a href="/chat">聊天</a>
            <a href="/live2d">Live2D</a>
          </nav>
        </div>
      </div>
    </div>
  );
}
