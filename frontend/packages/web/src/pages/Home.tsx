import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

export const HomePage: React.FC = () => {
  return (
    <div className="web-home-page">
      <div className="web-home-page__hero">
        <h1>欢迎来到弥娅</h1>
        <p className="web-home-page__subtitle">
          您的智能助手，随时为您服务
        </p>

        <div className="web-home-page__actions">
          <Link to="/chat" className="web-home-page__button web-home-page__button--primary">
            开始聊天
          </Link>
          <Link to="/monitor" className="web-home-page__button web-home-page__button--secondary">
            系统监控
          </Link>
        </div>
      </div>

      <div className="web-home-page__features">
        <div className="web-home-page__feature">
          <div className="web-home-page__feature-icon">💬</div>
          <h3>智能对话</h3>
          <p>自然流畅的对话体验</p>
        </div>
        <div className="web-home-page__feature">
          <div className="web-home-page__feature-icon">🎭</div>
          <h3>虚拟形象</h3>
          <p>生动的 Live2D 形象</p>
        </div>
        <div className="web-home-page__feature">
          <div className="web-home-page__feature-icon">📊</div>
          <h3>实时监控</h3>
          <p>系统状态实时监控</p>
        </div>
      </div>
    </div>
  );
};
