'use client';

import { useState, useEffect } from 'react';
import { Eye, EyeOff, LogIn, AlertCircle, CheckCircle } from 'lucide-react';

interface AutoLoginFormProps {
  onCookieObtained: (cookie: string) => void;
  disabled?: boolean;
}

export default function AutoLoginForm({ onCookieObtained, disabled }: AutoLoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [captcha, setCaptcha] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [captchaImage, setCaptchaImage] = useState('');
  const [captchaUrl, setCaptchaUrl] = useState('');
  const [captchaUuid, setCaptchaUuid] = useState('');
  const [jsessionid, setJsessionid] = useState('');
  const [jaccountUrl, setJaccountUrl] = useState('');
  const [loginContext, setLoginContext] = useState<any>(null);
  const [requiresCaptcha, setRequiresCaptcha] = useState(false);
  const [captchaTimestamp, setCaptchaTimestamp] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);

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

      // 如果还没有验证码，先获取验证码
      if (!requiresCaptcha) {
        const response = await fetch('/api/auto-login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (data.requiresCaptcha && data.captchaImage) {
          setCaptchaImage(data.captchaImage);
          setCaptchaUrl(data.captchaUrl);
          setCaptchaUuid(data.captchaUuid);
          setJsessionid(data.jsessionid);
          setJaccountUrl(data.jaccountUrl);
          setLoginContext(data.loginContext);
          setRequiresCaptcha(true);
          setCaptchaTimestamp(Date.now());
          setError('请输入验证码');
          return;
        } else {
          setError(data.error || '获取验证码失败');
          return;
        }
      }

      // 如果有验证码，提交登录
      if (requiresCaptcha && captcha.trim()) {
        // 调试信息
        console.log('提交登录参数:', {
          username,
          password: password ? '***' : 'empty',
          captcha,
          captchaUuid,
          jsessionid,
          jaccountUrl,
          loginContext
        });
        
        const response = await fetch('/api/auto-login', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify({ 
            username, 
            password, 
            captcha, 
            captchaUuid, 
            jsessionid,
            jaccountUrl,
            loginContext
          }),
        });

        const data = await response.json();

        if (data.success && data.cookie) {
          setSuccess('自动登录成功！Cookie已自动填充');
          onCookieObtained(data.cookie);
          // 清空所有字段
          setPassword('');
          setCaptcha('');
          setRequiresCaptcha(false);
          setCaptchaImage('');
          setCaptchaUrl('');
          setCaptchaUuid('');
          setJsessionid('');
          setJaccountUrl('');
          setLoginContext(null);
          setCaptchaTimestamp(null);
        } else {
          setError(data.error || '自动登录失败');
          // 如果验证码错误，重新获取验证码
          if (data.error && (data.error.includes('验证码') || data.error.includes('keepalive')) || data.requiresNewCaptcha) {
            setRequiresCaptcha(false);
            setCaptcha('');
            setCaptchaImage('');
            setCaptchaUrl('');
            setCaptchaUuid('');
            setJsessionid('');
            setJaccountUrl('');
            setLoginContext(null);
            setCaptchaTimestamp(null);
            setError('验证码已过期，请重新获取验证码');
          }
        }
      } else {
        setError('请输入验证码');
      }
    } catch (error) {
      console.error('Auto login error:', error);
      setError(error instanceof Error ? error.message : '自动登录过程中发生错误');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCaptcha = async () => {
    if (!username.trim() || !password.trim()) {
      setError('请输入用户名和密码');
      return;
    }

    setIsLoading(true);
    setError('');

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

      if (data.requiresCaptcha && data.captchaImage) {
        setCaptchaImage(data.captchaImage);
        setCaptchaUrl(data.captchaUrl);
        setCaptchaUuid(data.captchaUuid);
        setJsessionid(data.jsessionid);
        setJaccountUrl(data.jaccountUrl);
        setLoginContext(data.loginContext);
        setCaptchaTimestamp(Date.now());
        setCaptcha('');
        setError('验证码已刷新，请重新输入');
      } else {
        setError(data.error || '刷新验证码失败');
      }
    } catch (error) {
      console.error('Refresh captcha error:', error);
      setError(error instanceof Error ? error.message : '刷新验证码时发生错误');
    } finally {
      setIsLoading(false);
    }
  };

  // 检查验证码是否过期（5分钟）
  const isCaptchaExpired = captchaTimestamp ? (Date.now() - captchaTimestamp > 5 * 60 * 1000) : false;

  // 验证码倒计时
  useEffect(() => {
    if (!captchaTimestamp || !requiresCaptcha) {
      setTimeLeft(null);
      return;
    }

    const updateTimeLeft = () => {
      const elapsed = Date.now() - captchaTimestamp;
      const remaining = Math.max(0, 5 * 60 * 1000 - elapsed);
      setTimeLeft(remaining);
      
      if (remaining <= 0) {
        setTimeLeft(null);
      }
    };

    updateTimeLeft();
    const interval = setInterval(updateTimeLeft, 1000);

    return () => clearInterval(interval);
  }, [captchaTimestamp, requiresCaptcha]);

  // 自动刷新验证码（当验证码即将过期时）
  useEffect(() => {
    if (!captchaTimestamp || !requiresCaptcha) return;

    const timeUntilExpiry = 5 * 60 * 1000 - (Date.now() - captchaTimestamp);
    const warningTime = 4 * 60 * 1000; // 4分钟后开始警告

    if (timeUntilExpiry > warningTime) {
      const timer = setTimeout(() => {
        setError('验证码即将过期，建议刷新验证码');
      }, warningTime);

      return () => clearTimeout(timer);
    }
  }, [captchaTimestamp, requiresCaptcha]);

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

        {/* 验证码输入 */}
        {requiresCaptcha && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">
                验证码
              </label>
              <div className="flex items-center gap-2">
                {timeLeft && !isCaptchaExpired && (
                  <span className={`text-xs font-medium ${
                    timeLeft < 60000 ? 'text-red-600' : 
                    timeLeft < 120000 ? 'text-orange-600' : 'text-gray-600'
                  }`}>
                    {Math.floor(timeLeft / 60000)}:{(Math.floor(timeLeft / 1000) % 60).toString().padStart(2, '0')}
                  </span>
                )}
                {isCaptchaExpired && (
                  <span className="text-xs text-red-600 font-medium">
                    验证码已过期，请刷新
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={captcha}
                onChange={(e) => setCaptcha(e.target.value)}
                placeholder={isCaptchaExpired ? "验证码已过期，请点击刷新" : "请输入验证码"}
                className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  isCaptchaExpired ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
                disabled={disabled || isLoading}
                required
              />
              {captchaImage && (
                <div className="flex flex-col gap-1">
                  <img
                    src={captchaImage}
                    alt="验证码"
                    className="w-24 h-10 border border-gray-300 rounded cursor-pointer hover:border-blue-500 transition-colors"
                    onClick={refreshCaptcha}
                    title="点击刷新验证码"
                  />
                  <button
                    type="button"
                    onClick={refreshCaptcha}
                    disabled={disabled || isLoading}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:text-gray-400 transition-colors"
                  >
                    刷新
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={disabled || isLoading || !username.trim() || !password.trim() || (requiresCaptcha && (!captcha.trim() || isCaptchaExpired))}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              {requiresCaptcha ? '正在登录...' : '获取验证码...'}
            </>
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              {requiresCaptcha ? (isCaptchaExpired ? '请先刷新验证码' : '提交登录') : '获取验证码'}
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
