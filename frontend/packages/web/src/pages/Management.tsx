import { useState, useEffect, useMemo, useCallback, memo } from 'react';
import {
  getMiyaStatus,
  getMiyaMemory,
  getMiyaTools,
  getMiyaPersonality,
  getMiyaModels,
  getMiyaLogs
} from '../services/api';
import {
  Activity,
  Cpu,
  HardDrive,
  Zap,
  Settings,
  FileText,
  Wrench,
  User,
  Database,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import './Management.css';

interface MiyaStatus {
  status: string;
  memory: any;
  tools: { count: number; status: string };
  personality: { prompt_length: number; status: string };
}

export const ManagementDashboard: React.FC = () => {
  const [status, setStatus] = useState<MiyaStatus | null>(null);
  const [memory, setMemory] = useState<any>(null);
  const [tools, setTools] = useState<any>(null);
  const [personality, setPersonality] = useState<any>(null);
  const [models, setModels] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'memory' | 'tools' | 'personality' | 'models' | 'logs'>('overview');

  const loadAllData = useCallback(async () => {
    try {
      const [statusData, memoryData, toolsData, personalityData, modelsData, logsData] = await Promise.all([
        getMiyaStatus(),
        getMiyaMemory(),
        getMiyaTools(),
        getMiyaPersonality(),
        getMiyaModels(),
        getMiyaLogs(50)
      ]);
      setStatus(statusData);
      setMemory(memoryData);
      setTools(toolsData);
      setPersonality(personalityData);
      setModels(modelsData);
      setLogs(logsData.logs || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  }, []);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 10000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  const renderOverview = () => (
    <div className="management-overview">
      <h3 className="management-overview__title">🎯 系统概览</h3>
      
      {status && (
        <div className="management-overview__cards">
          <div className="management-overview__card">
            <div className="management-overview__card-icon">
              <Zap size={24} />
            </div>
            <div className="management-overview__card-content">
              <h4>核心状态</h4>
              <p className="management-overview__card-value">
                {status.status === 'running' ? '✅ 运行中' : '❌ 离线'}
              </p>
            </div>
          </div>

          <div className="management-overview__card">
            <div className="management-overview__card-icon">
              <Database size={24} />
            </div>
            <div className="management-overview__card-content">
              <h4>工具系统</h4>
              <p className="management-overview__card-value">
                {status.tools.count} 个工具
              </p>
            </div>
          </div>

          <div className="management-overview__card">
            <div className="management-overview__card-icon">
              <User size={24} />
            </div>
            <div className="management-overview__card-content">
              <h4>人设系统</h4>
              <p className="management-overview__card-value">
                {status.personality.prompt_length} 字符
              </p>
            </div>
          </div>

          <div className="management-overview__card">
            <div className="management-overview__card-icon">
              <HardDrive size={24} />
            </div>
            <div className="management-overview__card-content">
              <h4>对话历史</h4>
              <p className="management-overview__card-value">
                {memory?.data?.conversation_history?.total_messages || 0} 条
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderMemory = () => (
    <div className="management-section">
      <h3 className="management-section__title">🧠 记忆系统管理</h3>
      
      {memory?.data && (
        <div className="management-section__content">
          <div className="management-section__grid">
            <div className="management-section__item">
              <h4>对话历史</h4>
              <div className="management-section__stats">
                <div className="management-section__stat">
                  <span className="management-section__stat-label">总会话数</span>
                  <span className="management-section__stat-value">
                    {memory.data.conversation_history.total_sessions}
                  </span>
                </div>
                <div className="management-section__stat">
                  <span className="management-section__stat-label">总消息数</span>
                  <span className="management-section__stat-value">
                    {memory.data.conversation_history.total_messages}
                  </span>
                </div>
              </div>
            </div>

            <div className="management-section__item">
              <h4>Undefined 记忆</h4>
              <div className="management-section__stats">
                <div className="management-section__stat">
                  <span className="management-section__stat-label">记忆数量</span>
                  <span className="management-section__stat-value">
                    {memory.data.undefined_memory.count}
                  </span>
                </div>
                <div className="management-section__stat">
                  <span className="management-section__stat-label">存储文件</span>
                  <span className="management-section__stat-value">
                    {memory.data.undefined_memory.file}
                  </span>
                </div>
              </div>
            </div>

            <div className="management-section__item">
              <h4>潮汐记忆</h4>
              <div className="management-section__stats">
                <div className="management-section__stat">
                  <span className="management-section__stat-label">记忆数量</span>
                  <span className="management-section__stat-value">
                    {memory.data.tide_memory.count}
                  </span>
                </div>
                <div className="management-section__stat">
                  <span className="management-section__stat-label">Redis状态</span>
                  <span className="management-section__stat-value">
                    {memory.data.tide_memory.redis_available ? '✅ 已连接' : '⚠️ 模拟模式'}
                  </span>
                </div>
              </div>
            </div>

            <div className="management-section__item">
              <h4>梦境压缩</h4>
              <div className="management-section__stats">
                <div className="management-section__stat">
                  <span className="management-section__stat-label">记忆数量</span>
                  <span className="management-section__stat-value">
                    {memory.data.dream_memory.count}
                  </span>
                </div>
                <div className="management-section__stat">
                  <span className="management-section__stat-label">Milvus状态</span>
                  <span className="management-section__stat-value">
                    {memory.data.dream_memory.milvus_available ? '✅ 已连接' : '⚠️ 模拟模式'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTools = () => (
    <div className="management-section">
      <h3 className="management-section__title">🔧 工具管理</h3>
      
      {tools && (
        <div className="management-section__content">
          <div className="management-section__header">
            <span>共 {tools.count} 个工具</span>
            <button className="management-section__refresh" onClick={loadAllData}>
              🔄 刷新
            </button>
          </div>
          
          <div className="management-section__tools-list">
            {tools.tools.map((tool: any, index: number) => (
              <div key={index} className="management-section__tool-item">
                <div className="management-section__tool-header">
                  <span className="management-section__tool-name">{tool.name}</span>
                  <span className="management-section__tool-type">{tool.type}</span>
                </div>
                <p className="management-section__tool-desc">{tool.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderPersonality = () => (
    <div className="management-section">
      <h3 className="management-section__title">🎭 人设管理</h3>
      
      {personality?.personality && (
        <div className="management-section__content">
          <div className="management-section__personality-info">
            <div className="management-section__personality-stats">
              <div className="management-section__stat">
                <span className="management-section__stat-label">提示词长度</span>
                <span className="management-section__stat-value">
                  {personality.personality.length} 字符
                </span>
              </div>
              <div className="management-section__stat">
                <span className="management-section__stat-label">加载状态</span>
                <span className="management-section__stat-value">
                  {personality.personality.loaded ? '✅ 已加载' : '❌ 未加载'}
                </span>
              </div>
            </div>
            
            <div className="management-section__personality-prompt">
              <h4>系统提示词</h4>
              <div className="management-section__personality-prompt-content">
                <pre>{personality.personality.system_prompt}</pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderModels = () => (
    <div className="management-section">
      <h3 className="management-section__title">🤖 AI模型管理</h3>
      
      {models && (
        <div className="management-section__content">
          <div className="management-section__header">
            <span>共 {models.count} 个模型</span>
            <button className="management-section__refresh" onClick={loadAllData}>
              🔄 刷新
            </button>
          </div>
          
          <div className="management-section__models-list">
            {models.models.map((model: any, index: number) => (
              <div key={index} className="management-section__model-item">
                <div className="management-section__model-header">
                  <span className="management-section__model-name">{model.name}</span>
                  <span className="management-section__model-provider">{model.provider}</span>
                </div>
                <div className="management-section__model-info">
                  <span>ID: {model.id}</span>
                  <span>类型: {model.type}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderLogs = () => (
    <div className="management-section">
      <h3 className="management-section__title">📋 系统日志</h3>

      <div className="management-section__content">
        <div className="management-section__header">
          <span>最近 {logs.length} 条日志</span>
          <button className="management-section__refresh" onClick={loadAllData}>
            🔄 刷新
          </button>
        </div>

        {logs.length > 0 ? (
          <div
            className="management-section__logs-container"
            style={{
              maxHeight: '400px',
              overflowY: 'auto',
            }}
          >
            {logs.slice(0, 50).map((log, index) => (
              <LogItem key={index} index={index} log={log} />
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-4">暂无日志</div>
        )}
      </div>
    </div>
  );

  return (
    <div className="management-dashboard">
      {/* 标签页导航 */}
      <div className="management-dashboard__tabs">
        <button
          className={`management-dashboard__tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Activity size={18} />
          概览
        </button>
        <button
          className={`management-dashboard__tab ${activeTab === 'memory' ? 'active' : ''}`}
          onClick={() => setActiveTab('memory')}
        >
          <Database size={18} />
          记忆
        </button>
        <button
          className={`management-dashboard__tab ${activeTab === 'tools' ? 'active' : ''}`}
          onClick={() => setActiveTab('tools')}
        >
          <Wrench size={18} />
          工具
        </button>
        <button
          className={`management-dashboard__tab ${activeTab === 'personality' ? 'active' : ''}`}
          onClick={() => setActiveTab('personality')}
        >
          <User size={18} />
          人设
        </button>
        <button
          className={`management-dashboard__tab ${activeTab === 'models' ? 'active' : ''}`}
          onClick={() => setActiveTab('models')}
        >
          <Cpu size={18} />
          模型
        </button>
        <button
          className={`management-dashboard__tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <FileText size={18} />
          日志
        </button>
      </div>

      {/* 内容区域 */}
      <div className="management-dashboard__content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'memory' && renderMemory()}
        {activeTab === 'tools' && renderTools()}
        {activeTab === 'personality' && renderPersonality()}
        {activeTab === 'models' && renderModels()}
        {activeTab === 'logs' && renderLogs()}
      </div>
    </div>
  );
};

// 使用 memo 优化日志项组件
const LogItem = memo(({ index, log }: { index: number; log: string }) => (
  <div className="management-section__log-item">
    <span className="management-section__log-index">{index + 1}</span>
    <span className="management-section__log-content">{log}</span>
  </div>
));
