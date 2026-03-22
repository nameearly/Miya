import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import './MainLayout.css';

export const MainLayout: React.FC = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/home', label: '首页', icon: '🏠' },
    { path: '/chat', label: '聊天', icon: '💬' },
    { path: '/monitor', label: '监控', icon: '📊' }
  ];

  return (
    <div className="web-layout">
      <header className="web-layout__header">
        <div className="web-layout__logo">
          <Link to="/home">
            <h1>弥娅</h1>
            <p className="web-layout__logo-subtitle">Miya Web</p>
          </Link>
        </div>

        <nav className="web-layout__nav">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`web-layout__nav-item ${
                location.pathname === item.path ? 'web-layout__nav-item--active' : ''
              }`}
            >
              <span className="web-layout__nav-icon">{item.icon}</span>
              <span className="web-layout__nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>
      </header>

      <main className="web-layout__main">
        <Outlet />
      </main>

      <footer className="web-layout__footer">
        <p>&copy; 2024 弥娅 - Miya</p>
      </footer>
    </div>
  );
};
