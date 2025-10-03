'use client';

import { useState } from 'react';
import { Bug, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

interface AuthDebugProps {
  authToken: string | null;
}

export default function AuthDebug({ authToken }: AuthDebugProps) {
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const runAuthTest = async () => {
    setIsLoading(true);
    try {
      const url = authToken 
        ? `/api/test-auth?token=${encodeURIComponent(authToken)}`
        : '/api/test-auth';
      
      const response = await fetch(url);
      const result = await response.json();
      setDebugInfo(result);
    } catch (error) {
      setDebugInfo({
        success: false,
        error: error instanceof Error ? error.message : 'Test failed'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <Bug className="w-5 h-5 text-yellow-600" />
        <h3 className="font-medium text-yellow-800">认证调试工具</h3>
        <button
          onClick={runAuthTest}
          disabled={isLoading}
          className="ml-auto bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors disabled:opacity-50"
        >
          {isLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            '测试认证'
          )}
        </button>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-gray-600">当前Token:</span>
          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
            {authToken ? `${authToken.substring(0, 20)}...` : '无'}
          </span>
          {authToken ? (
            <CheckCircle className="w-4 h-4 text-green-600" />
          ) : (
            <XCircle className="w-4 h-4 text-red-600" />
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-gray-600">LocalStorage:</span>
          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
            {typeof window !== 'undefined' && localStorage.getItem('auth-token') ? '存在' : '不存在'}
          </span>
        </div>
      </div>

      {debugInfo && (
        <div className="mt-3 p-3 bg-white rounded border">
          <h4 className="font-medium text-gray-800 mb-2">测试结果:</h4>
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-600">
        💡 如果认证测试失败，请尝试重新登录
      </div>
    </div>
  );
}

