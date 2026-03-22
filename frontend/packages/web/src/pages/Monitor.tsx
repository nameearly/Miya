import React, { useEffect, useState } from 'react';
import { getSystemInfo } from '@miya/shared/api';
import type { SystemInfo } from '@miya/shared/types';
import './Monitor.css';

export const MonitorPage: React.FC = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);

  useEffect(() => {
    loadSystemInfo();
    const interval = setInterval(loadSystemInfo, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemInfo = async () => {
    try {
      const info = await getSystemInfo();
      setSystemInfo(info);
    } catch (error) {
      console.error('Failed to load system info:', error);
    }
  };

  return (
    <div className="web-monitor-page">
      <div className="web-monitor-page__header">
        <h2>系统监控</h2>
      </div>

      <div className="web-monitor-page__content">
        {systemInfo ? (
          <div className="web-monitor-page__cards">
            <div className="web-monitor-page__card">
              <h3>CPU 使用率</h3>
              <div className="web-monitor-page__card-value">
                {systemInfo.cpuUsage.toFixed(1)}%
              </div>
              <div className="web-monitor-page__card-bar">
                <div
                  className="web-monitor-page__card-bar-fill"
                  style={{ width: `${systemInfo.cpuUsage}%` }}
                />
              </div>
            </div>

            <div className="web-monitor-page__card">
              <h3>内存使用</h3>
              <div className="web-monitor-page__card-value">
                {(systemInfo.memoryUsage / 1024 / 1024 / 1024).toFixed(2)} GB
              </div>
              <div className="web-monitor-page__card-bar">
                <div
                  className="web-monitor-page__card-bar-fill"
                  style={{ width: `${(systemInfo.memoryUsage / (16 * 1024 * 1024 * 1024)) * 100}%` }}
                />
              </div>
            </div>

            <div className="web-monitor-page__card">
              <h3>运行时间</h3>
              <div className="web-monitor-page__card-value">
                {Math.floor(systemInfo.uptime / 3600)}h {Math.floor((systemInfo.uptime % 3600) / 60)}m
              </div>
            </div>

            <div className="web-monitor-page__card">
              <h3>系统状态</h3>
              <div
                className={`web-monitor-page__card-value web-monitor-page__card-value--${systemInfo.status}`}
              >
                {systemInfo.status === 'ready' && '正常'}
                {systemInfo.status === 'busy' && '忙碌'}
                {systemInfo.status === 'error' && '错误'}
                {systemInfo.status === 'offline' && '离线'}
              </div>
            </div>

            <div className="web-monitor-page__card web-monitor-page__card--full">
              <h3>系统信息</h3>
              <div className="web-monitor-page__info">
                <div className="web-monitor-page__info-item">
                  <span className="web-monitor-page__info-label">版本</span>
                  <span className="web-monitor-page__info-value">{systemInfo.version}</span>
                </div>
                <div className="web-monitor-page__info-item">
                  <span className="web-monitor-page__info-label">最后更新</span>
                  <span className="web-monitor-page__info-value">
                    {new Date(systemInfo.lastUpdated).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="web-monitor-page__loading">
            <div className="web-monitor-page__spinner"></div>
            <p>加载中...</p>
          </div>
        )}
      </div>
    </div>
  );
};
