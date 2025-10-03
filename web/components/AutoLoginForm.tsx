'use client';

import { useState } from 'react';
import { Eye, EyeOff, LogIn, AlertCircle, CheckCircle } from 'lucide-react';

interface AutoLoginFormProps {
  onCookieObtained: (cookie: string) => void;
  disabled?: boolean;
}

export default function AutoLoginForm({ onCookieObtained, disabled }: AutoLoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      setError('请输入用户名和密码');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const authToken = localStorage.getItem('auth-token');
      if (!authToken) {
        throw new Error('请先登录系统');
      }

      const response = await fetch('/api/auto-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success && data.cookie) {
        setSuccess('自动登录成功！Cookie已自动填充');
        onCookieObtained(data.cookie);
        // 清空密码字段
        setPassword('');
      } else {
        setError(data.error || '自动登录失败');
      }
    } catch (error) {
      console.error('Auto login error:', error);
      setError(error instanceof Error ? error.message : '自动登录过程中发生错误');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <LogIn className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">自动获取Cookie</h3>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        输入SJTU账号密码，系统将自动登录并获取Cookie，无需手动复制。
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
            用户名
          </label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="输入SJTU用户名或学号"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={disabled || isLoading}
            required
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            密码
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="输入密码"
              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={disabled || isLoading}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              disabled={disabled || isLoading}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={disabled || isLoading || !username.trim() || !password.trim()}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              正在登录...
            </>
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              自动获取Cookie
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      {success && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-start gap-2">
          <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-green-700">{success}</div>
        </div>
      )}

      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
        <div className="text-sm text-yellow-800">
          <strong>安全提醒：</strong>
          <ul className="mt-1 space-y-1 text-xs">
            <li>• 密码仅用于登录获取Cookie，不会被存储</li>
            <li>• 登录成功后密码字段会自动清空</li>
            <li>• 建议在私人设备上使用此功能</li>
            <li>• 如不放心，仍可使用手动复制Cookie的方式</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
