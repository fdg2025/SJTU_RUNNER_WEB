'use client';

import { useState, useEffect } from 'react';
import { RunningConfig, ApiResponse } from '@/lib/utils';
import ConfigForm from '@/components/ConfigForm';
import ConfigManager from '@/components/ConfigManager';
import ProgressBar from '@/components/ProgressBar';
import LogOutput from '@/components/LogOutput';
import LoginForm from '@/components/LoginForm';
import AuthDebug from '@/components/AuthDebug';
import { Play, Square, HelpCircle, Github, ExternalLink, LogOut } from 'lucide-react';

const DEFAULT_CONFIG: RunningConfig = {
  COOKIE: '',
  USER_ID: '',
  START_LATITUDE: 31.031599,
  START_LONGITUDE: 121.442938,
  END_LATITUDE: 31.026400,
  END_LONGITUDE: 121.455100,
  RUNNING_SPEED_MPS: 2.5,
  INTERVAL_SECONDS: 3,
  START_TIME_EPOCH_MS: null,
  HOST: 'pe.sjtu.edu.cn',
  UID_URL: 'https://pe.sjtu.edu.cn/sports/my/uid',
  MY_DATA_URL: 'https://pe.sjtu.edu.cn/sports/my/data',
  POINT_RULE_URL: 'https://pe.sjtu.edu.cn/api/running/point-rule',
  UPLOAD_URL: 'https://pe.sjtu.edu.cn/api/running/result/upload'
};

interface LogEntry {
  message: string;
  level: string;
  timestamp: number;
}

export default function HomePage() {
  const [config, setConfig] = useState<RunningConfig>(DEFAULT_CONFIG);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 100, message: '待命' });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showHelp, setShowHelp] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState<string | null>(null);

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('auth-token');
    if (token) {
      setAuthToken(token);
      setIsAuthenticated(true);
    }
  }, []);

  // Load config from localStorage on mount
  useEffect(() => {
    if (isAuthenticated) {
      const savedConfig = localStorage.getItem('sjtu-running-config');
      if (savedConfig) {
        try {
          const parsedConfig = JSON.parse(savedConfig);
          setConfig({ ...DEFAULT_CONFIG, ...parsedConfig });
        } catch (error) {
          console.error('Failed to load saved config:', error);
        }
      }
    }
  }, [isAuthenticated]);

  const addLog = (message: string, level: string = 'info') => {
    setLogs(prev => [...prev, { message, level, timestamp: Date.now() }]);
  };

  const handleLogin = (token: string) => {
    setAuthToken(token);
    setIsAuthenticated(true);
    localStorage.setItem('auth-token', token);
  };

  const handleLogout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('auth-token');
    localStorage.removeItem('sjtu-running-config');
    setConfig(DEFAULT_CONFIG);
    setLogs([]);
  };

  const validateConfig = (): string | null => {
    if (!config.COOKIE.trim()) {
      return 'Cookie 不能为空';
    }
    if (!config.USER_ID.trim()) {
      return '用户ID 不能为空';
    }
    if (!config.START_LATITUDE || !config.START_LONGITUDE) {
      return '起点坐标不能为空';
    }
    if (!config.END_LATITUDE || !config.END_LONGITUDE) {
      return '终点坐标不能为空';
    }
    if (config.RUNNING_SPEED_MPS <= 0) {
      return '跑步速度必须大于0';
    }
    if (config.INTERVAL_SECONDS <= 0) {
      return '采样间隔必须大于0';
    }
    return null;
  };

  const handleStartUpload = async () => {
    const validationError = validateConfig();
    if (validationError) {
      addLog(`配置错误: ${validationError}`, 'error');
      return;
    }

    // 检查认证状态
    if (!authToken) {
      addLog('认证令牌缺失，请重新登录', 'error');
      handleLogout();
      return;
    }

    setIsUploading(true);
    setLogs([]);
    setProgress({ current: 0, total: 100, message: '准备中...' });
    
    addLog('开始上传跑步数据...', 'info');
    addLog(`使用认证令牌: ${authToken.substring(0, 10)}...`, 'info');

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify(config),
      });

      const result: ApiResponse & { logs?: LogEntry[] } = await response.json();

      // Handle authentication failure
      if (response.status === 401) {
        handleLogout();
        addLog('认证失败，请重新登录', 'error');
        return;
      }

      // Add server logs to client logs
      if (result.logs) {
        result.logs.forEach(log => addLog(log.message, log.level));
      }

      if (result.success) {
        setProgress({ current: 100, total: 100, message: '上传成功！' });
        addLog('上传成功！', 'success');
      } else {
        setProgress({ current: 100, total: 100, message: '上传失败' });
        addLog(`上传失败: ${result.error || '未知错误'}`, 'error');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '网络请求失败';
      addLog(`请求失败: ${errorMessage}`, 'error');
      setProgress({ current: 100, total: 100, message: '请求失败' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleStopUpload = () => {
    setIsUploading(false);
    addLog('用户手动停止上传', 'warning');
    setProgress({ current: 0, total: 100, message: '已停止' });
  };

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Play className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">SJTU 体育跑步上传工具</h1>
                <p className="text-sm text-gray-500">Web版本</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowHelp(!showHelp)}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
              >
                <HelpCircle className="w-4 h-4" />
                帮助
              </button>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
              >
                <Github className="w-4 h-4" />
                GitHub
              </a>
              <button
                onClick={handleLogout}
                className="bg-red-100 hover:bg-red-200 text-red-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                退出
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Help Section */}
      {showHelp && (
        <div className="bg-primary-50 border-b border-primary-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">使用说明</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">1. 获取Cookie</h3>
                  <ul className="list-disc list-inside space-y-1">
                    <li>访问 <a href="https://pe.sjtu.edu.cn/phone/#/indexPortrait" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:text-primary-700">交我跑官网</a></li>
                    <li>登录后按F12打开开发者工具</li>
                    <li>在"应用"或"Application"标签页中找到Cookie</li>
                    <li>复制keepalive和JSESSIONID的完整值</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">2. 配置路线</h3>
                  <ul className="list-disc list-inside space-y-1">
                    <li>设置校园内的起点和终点坐标</li>
                    <li>确保两点之间有足够的距离（1-2公里）</li>
                    <li>可以使用地图工具获取精确坐标</li>
                    <li>默认配置已包含校园内示例坐标</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">3. 参数设置</h3>
                  <ul className="list-disc list-inside space-y-1">
                    <li>跑步速度：建议2.0-3.0米/秒</li>
                    <li>采样间隔：建议3-5秒</li>
                    <li>时间设置：可选择当前时间或历史时间</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">4. 免责声明</h3>
                  <ul className="list-disc list-inside space-y-1">
                    <li>本工具仅供学习和研究目的</li>
                    <li>请遵守学校相关规定</li>
                    <li>开发者不承担使用后果</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Configuration */}
          <div className="lg:col-span-2 space-y-8">
            {/* 调试工具 - 临时添加用于诊断认证问题 */}
            <AuthDebug authToken={authToken} />
            
            <ConfigManager 
              config={config}
              onConfigChange={setConfig}
              disabled={isUploading}
            />
            
            <ConfigForm 
              config={config}
              onChange={setConfig}
              disabled={isUploading}
            />
          </div>

          {/* Right Column - Controls and Status */}
          <div className="space-y-6">
            {/* Control Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">控制面板</h2>
              
              <div className="space-y-4">
                <div className="flex gap-3">
                  {!isUploading ? (
                    <button
                      onClick={handleStartUpload}
                      className="bg-green-600 hover:bg-green-700 text-white font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex-1 flex items-center justify-center gap-2"
                    >
                      <Play className="w-4 h-4" />
                      开始上传
                    </button>
                  ) : (
                    <button
                      onClick={handleStopUpload}
                      className="bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex-1 flex items-center justify-center gap-2"
                    >
                      <Square className="w-4 h-4" />
                      停止上传
                    </button>
                  )}
                </div>
                
                <ProgressBar
                  current={progress.current}
                  total={progress.total}
                  message={progress.message}
                />
              </div>
            </div>

            {/* Status Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">状态信息</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">当前状态:</span>
                  <span className={`font-medium ${
                    isUploading ? 'text-warning-600' : 
                    progress.current === 100 && progress.message.includes('成功') ? 'text-success-600' :
                    progress.current === 100 && progress.message.includes('失败') ? 'text-error-600' :
                    'text-gray-900'
                  }`}>
                    {isUploading ? '上传中...' : progress.message}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">配置状态:</span>
                  <span className={`font-medium ${
                    validateConfig() ? 'text-error-600' : 'text-success-600'
                  }`}>
                    {validateConfig() ? '配置有误' : '配置正常'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">日志条数:</span>
                  <span className="font-medium text-gray-900">{logs.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Log Output */}
        <div className="mt-8">
          <LogOutput logs={logs} />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-600">
            <div>
              <p>© 2024 SJTU 体育跑步上传工具. 仅供学习研究使用.</p>
            </div>
            <div className="flex items-center gap-4">
              <span>版本: 1.0.0</span>
              <span>•</span>
              <a 
                href="https://pe.sjtu.edu.cn" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-700 flex items-center gap-1"
              >
                交我跑官网
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
