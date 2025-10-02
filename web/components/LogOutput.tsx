'use client';

import { useEffect, useRef } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

interface LogEntry {
  message: string;
  level: string;
  timestamp: number;
}

interface LogOutputProps {
  logs: LogEntry[];
  className?: string;
}

export default function LogOutput({ logs, className = '' }: LogOutputProps) {
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-error-500 flex-shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-warning-500 flex-shrink-0 mt-0.5" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-success-500 flex-shrink-0 mt-0.5" />;
      default:
        return <Info className="w-4 h-4 text-primary-500 flex-shrink-0 mt-0.5" />;
    }
  };

  const getLogTextColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'text-error-700';
      case 'warning':
        return 'text-warning-700';
      case 'success':
        return 'text-success-700';
      default:
        return 'text-gray-700';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (logs.length === 0) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">日志输出</h3>
        <div className="text-center text-gray-500 py-8">
          <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>暂无日志信息</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">日志输出</h3>
      <div 
        ref={logContainerRef}
        className="bg-gray-50 rounded-lg p-4 h-64 overflow-y-auto border border-gray-200 font-mono text-sm space-y-2"
      >
        {logs.map((log, index) => (
          <div key={index} className="flex items-start gap-2">
            {getLogIcon(log.level)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-gray-500 font-sans">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={`text-xs font-sans font-medium uppercase px-1.5 py-0.5 rounded ${
                  log.level.toLowerCase() === 'error' ? 'bg-error-100 text-error-700' :
                  log.level.toLowerCase() === 'warning' ? 'bg-warning-100 text-warning-700' :
                  log.level.toLowerCase() === 'success' ? 'bg-success-100 text-success-700' :
                  'bg-primary-100 text-primary-700'
                }`}>
                  {log.level}
                </span>
              </div>
              <p className={`${getLogTextColor(log.level)} break-words`}>
                {log.message}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
