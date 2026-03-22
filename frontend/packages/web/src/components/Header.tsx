import { Activity, Cpu, HardDrive, Zap, MessageSquare, Settings } from 'lucide-react';
import { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

type View = 'chat' | 'management';

interface HeaderProps {
  currentView: View;
  onViewChange: (view: View) => void;
}

function clsx(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

export function Header({ currentView, onViewChange }: HeaderProps) {
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [apiPort, setApiPort] = useState<number>(8001);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      await apiClient.healthCheck();
      setApiStatus('connected');
      try {
        const port = await apiClient.redetectPort();
        setApiPort(port);
      } catch {
        setApiPort(8001);
      }
    } catch {
      setApiStatus('disconnected');
    }
  };

  return (
    <div className="glass-effect rounded-2xl p-6 mb-6 animate-slide-up">
      <div className="flex items-center justify-between">
        {/* 左侧：标题和状态 */}
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              🎭 弥娅 AI
            </h1>
            <p className="text-gray-600 text-sm mt-1">Miya Virtual Avatar System</p>
          </div>

          <div className="h-12 w-px bg-gray-300/50" />

          <div className="flex items-center gap-3">
            <div
              className={`${clsx(
                'w-3 h-3 rounded-full animate-pulse',
                apiStatus === 'connected' ? 'bg-green-500' : apiStatus === 'disconnected' ? 'bg-red-500' : 'bg-yellow-500'
              )}`}
            />
            <span className="text-sm text-gray-700 font-medium">
              {apiStatus === 'connected' ? '已连接' : apiStatus === 'disconnected' ? '未连接' : '检测中'}
            </span>
          </div>
        </div>

        {/* 中间：视图切换 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onViewChange('chat')}
            className={`${clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-all',
              currentView === 'chat'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}`}
          >
            <MessageSquare size={18} />
            <span className="font-medium">对话</span>
          </button>
          <button
            onClick={() => onViewChange('management')}
            className={`${clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-all',
              currentView === 'management'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}`}
          >
            <Settings size={18} />
            <span className="font-medium">管理</span>
          </button>
        </div>

        {/* 右侧：API 信息 */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-xs text-gray-500">API 服务</p>
            <p className="text-sm font-semibold text-gray-800">
              http://localhost:{apiPort}
            </p>
          </div>

          <div className="flex items-center gap-2 text-gray-600">
            <Activity size={20} />
            <Cpu size={20} />
            <HardDrive size={20} />
          </div>
        </div>
      </div>
    </div>
  );
}
