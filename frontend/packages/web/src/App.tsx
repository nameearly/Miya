import { useState, lazy, Suspense, useEffect } from 'react';
import { Header } from './components/Header';
import { preloadPage, initSmartPreload, preloadApiData } from './utils/preloader';

// 懒加载所有页面组件
const ChatInterface = lazy(() => import('./components/ChatInterface').then(m => ({ default: m.ChatInterface })));
const ManagementDashboard = lazy(() => import('./pages/Management').then(m => ({ default: m.ManagementDashboard })));
const MonitorPage = lazy(() => import('./pages/Monitor').then(m => ({ default: m.MonitorPage })));
const HomePage = lazy(() => import('./pages/Home').then(m => ({ default: m.HomePage })));
const ChatPage = lazy(() => import('./pages/Chat').then(m => ({ default: m.ChatPage })));
const TestPage = lazy(() => import('./pages/Test').then(m => ({ default: m.TestPage })));

type View = 'chat' | 'management' | 'monitor' | 'home' | 'chat-page' | 'test';

function App() {
  const [currentView, setCurrentView] = useState<View>('chat');

  // 预加载策略：鼠标悬停时预加载常用页面
  useEffect(() => {
    const handleMouseEnter = (view: View) => {
      if (view !== currentView) {
        preloadPage(view);
      }
    };

    // 初始化智能预加载
    initSmartPreload();

    // 预加载常用 API 数据
    preloadApiData();

    // 绑定到全局，供导航按钮调用
    window.miyaPreload = handleMouseEnter;
  }, [currentView]);

  const renderView = () => {
    switch (currentView) {
      case 'chat':
        return <ChatInterface />;
      case 'management':
        return <ManagementDashboard />;
      case 'monitor':
        return <MonitorPage />;
      case 'home':
        return <HomePage />;
      case 'chat-page':
        return <ChatPage />;
      case 'test':
        return <TestPage />;
      default:
        return <ChatInterface />;
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <Header currentView={currentView} onViewChange={setCurrentView} />

        <div className="glass-effect rounded-2xl overflow-hidden shadow-2xl animate-fade-in">
          <Suspense fallback={
            <div className="flex items-center justify-center h-96">
              <div className="flex flex-col items-center gap-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                <p className="text-gray-500">加载中...</p>
              </div>
            </div>
          }>
            {renderView()}
          </Suspense>
        </div>

        {/* 底部信息 */}
        <div className="mt-6 text-center text-white/80 text-sm">
          <p>弥娅 V4.0 - 多终端智能管理系统</p>
          <p className="mt-1">按 Ctrl+C 停止服务</p>
        </div>
      </div>
    </div>
  );
}

declare global {
  interface Window {
    miyaPreload?: (view: View) => void;
  }
}

export default App;
