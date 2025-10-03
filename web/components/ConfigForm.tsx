'use client';

import { useState } from 'react';
import { RunningConfig } from '@/lib/utils';
import { ExternalLink, MapPin, Clock, Settings, User } from 'lucide-react';
import CookieHelper from './CookieHelper';
import AutoLoginForm from './AutoLoginForm';

interface ConfigFormProps {
  config: RunningConfig;
  onChange: (config: RunningConfig) => void;
  disabled?: boolean;
}

export default function ConfigForm({ config, onChange, disabled = false }: ConfigFormProps) {
  const [useCurrentTime, setUseCurrentTime] = useState(config.START_TIME_EPOCH_MS === null);
  const [showCookieHelper, setShowCookieHelper] = useState(false);
  const [showAutoLogin, setShowAutoLogin] = useState(false);

  const handleInputChange = (field: keyof RunningConfig, value: string | number | null) => {
    onChange({
      ...config,
      [field]: value
    });
  };

  const handleTimeToggle = (checked: boolean) => {
    setUseCurrentTime(checked);
    handleInputChange('START_TIME_EPOCH_MS', checked ? null : Date.now());
  };

  const handleDateTimeChange = (value: string) => {
    const timestamp = new Date(value).getTime();
    handleInputChange('START_TIME_EPOCH_MS', timestamp);
  };

  const formatDateTimeLocal = (timestamp: number | null | undefined) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toISOString().slice(0, 16);
  };

  const [cookieValidation, setCookieValidation] = useState<{
    isValidating: boolean;
    isValid: boolean | null;
    message: string;
  }>({
    isValidating: false,
    isValid: null,
    message: ''
  });

  const validateCookie = async (cookie: string) => {
    if (!cookie.trim()) {
      setCookieValidation({
        isValidating: false,
        isValid: null,
        message: ''
      });
      return;
    }

    setCookieValidation({
      isValidating: true,
      isValid: null,
      message: '验证中...'
    });

    try {
      // 基本格式验证
      if (!cookie.includes('keepalive=') || !cookie.includes('JSESSIONID=')) {
        setCookieValidation({
          isValidating: false,
          isValid: false,
          message: '❌ Cookie格式不正确，必须包含keepalive和JSESSIONID'
        });
        return;
      }

      // 提取Cookie值进行基本验证
      const keepaliveMatch = cookie.match(/keepalive=([^;]+)/);
      const jsessionidMatch = cookie.match(/JSESSIONID=([^;]+)/);
      
      if (!keepaliveMatch || !jsessionidMatch) {
        setCookieValidation({
          isValidating: false,
          isValid: false,
          message: '❌ 无法解析Cookie值'
        });
        return;
      }

      const keepaliveValue = keepaliveMatch[1].trim();
      const jsessionidValue = jsessionidMatch[1].trim();

      // 基本长度和格式检查
      if (keepaliveValue.length < 10 || jsessionidValue.length < 10) {
        setCookieValidation({
          isValidating: false,
          isValid: false,
          message: '❌ Cookie值长度不足，可能无效'
        });
        return;
      }

      // 检查是否包含明显的无效字符
      if (keepaliveValue.includes(' ') || jsessionidValue.includes(' ')) {
        setCookieValidation({
          isValidating: false,
          isValid: false,
          message: '❌ Cookie值包含无效字符'
        });
        return;
      }

      // 尝试直接验证Cookie（简化版本，不通过API）
      try {
        const testUrl = 'https://pe.sjtu.edu.cn/phone/api/uid';
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);
        
        const response = await fetch(testUrl, {
          method: 'GET',
          headers: {
            "Host": "pe.sjtu.edu.cn",
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0",
            "Accept": "application/json, text/plain, */*",
            "Cookie": cookie
          },
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const result = await response.json();
          if (result?.code === 0 && result?.data?.uid) {
            setCookieValidation({
              isValidating: false,
              isValid: true,
              message: `✅ Cookie有效 (UID: ${result.data.uid})`
            });
            return;
          }
        }
        
        // 如果直接验证失败，但格式正确，给出警告而不是错误
        setCookieValidation({
          isValidating: false,
          isValid: null,
          message: '⚠️ Cookie格式正确，但无法验证有效性。请确保已登录SJTU系统'
        });
        
      } catch (fetchError) {
        // 网络错误或CORS问题，但Cookie格式正确
        setCookieValidation({
          isValidating: false,
          isValid: null,
          message: '⚠️ Cookie格式正确，但验证受限。建议直接尝试上传'
        });
      }
      
    } catch (error) {
      setCookieValidation({
        isValidating: false,
        isValid: false,
        message: '❌ 验证过程出错，请检查Cookie格式'
      });
    }
  };

  const handleCookieChange = (cookie: string) => {
    handleInputChange('COOKIE', cookie);
    // Debounce validation
    const timeoutId = setTimeout(() => {
      validateCookie(cookie);
    }, 1000);
    return () => clearTimeout(timeoutId);
  };

  const handleCookieExtracted = (cookie: string) => {
    handleInputChange('COOKIE', cookie);
    setShowCookieHelper(false);
    validateCookie(cookie);
  };

  const handleCookieFromAutoLogin = (cookie: string) => {
    handleInputChange('COOKIE', cookie);
    setShowAutoLogin(false);
    validateCookie(cookie);
  };

  return (
    <div className="space-y-8">
      {/* User Configuration */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <User className="w-5 h-5 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">用户配置</h2>
        </div>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">Cookie</label>
              <a
                href="https://pe.sjtu.edu.cn/phone/#/indexPortrait"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 transition-colors"
              >
                打开SJTU体育系统
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
                     <div className="relative">
                     <input
                       type="text"
                       className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:border-transparent transition-all duration-200 ${
                         cookieValidation.isValid === true 
                           ? 'border-green-300 focus:ring-green-500' 
                           : cookieValidation.isValid === false 
                           ? 'border-red-300 focus:ring-red-500'
                           : cookieValidation.isValid === null && cookieValidation.message.includes('⚠️')
                           ? 'border-yellow-300 focus:ring-yellow-500'
                           : 'border-gray-300 focus:ring-blue-500'
                       }`}
                       placeholder="keepalive=...; JSESSIONID=..."
                       value={config.COOKIE}
                       onChange={(e) => handleCookieChange(e.target.value)}
                       disabled={disabled}
                     />
                     {cookieValidation.isValidating && (
                       <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                         <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                       </div>
                     )}
                     {cookieValidation.isValid === true && (
                       <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                         <div className="w-4 h-4 text-green-600">✓</div>
                       </div>
                     )}
                     {cookieValidation.isValid === false && (
                       <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                         <div className="w-4 h-4 text-red-600">✗</div>
                       </div>
                     )}
                     {cookieValidation.isValid === null && cookieValidation.message.includes('⚠️') && (
                       <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                         <div className="w-4 h-4 text-yellow-600">⚠</div>
                       </div>
                     )}
                   </div>
                   
                   {cookieValidation.message && (
                     <p className={`text-xs mt-1 ${
                       cookieValidation.isValid === true 
                         ? 'text-green-600' 
                         : cookieValidation.isValid === false 
                         ? 'text-red-600'
                         : cookieValidation.message.includes('⚠️')
                         ? 'text-yellow-600'
                         : 'text-blue-600'
                     }`}>
                       {cookieValidation.message}
                     </p>
                   )}
                   
                   <div className="flex gap-2 mt-2">
                     <button
                       type="button"
                       onClick={() => setShowCookieHelper(!showCookieHelper)}
                       className="flex-1 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors"
                       disabled={disabled}
                     >
                       {showCookieHelper ? '隐藏助手' : '手动获取'}
                     </button>
                     <button
                       type="button"
                       onClick={() => setShowAutoLogin(!showAutoLogin)}
                       className="flex-1 px-3 py-1.5 text-sm bg-green-50 text-green-600 border border-green-200 rounded-md hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 transition-colors"
                       disabled={disabled}
                     >
                       {showAutoLogin ? '隐藏登录' : '自动登录'}
                     </button>
                   </div>
                   
                   <p className="text-xs text-gray-500 mt-1">
                     选择"自动登录"输入账号密码自动获取，或选择"手动获取"复制粘贴Cookie。
                   </p>
            
            {/* Cookie助手 */}
            {showCookieHelper && (
              <div className="mt-3">
                <CookieHelper onCookieExtracted={handleCookieExtracted} />
              </div>
            )}
            
            {/* 自动登录表单 */}
            {showAutoLogin && (
              <div className="mt-3">
                <AutoLoginForm onCookieObtained={handleCookieFromAutoLogin} disabled={disabled} />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">用户ID</label>
            <input
              type="text"
              className="input-field"
              placeholder="你的JAccount用户名"
              value={config.USER_ID}
              onChange={(e) => handleInputChange('USER_ID', e.target.value)}
              disabled={disabled}
            />
          </div>
        </div>
      </div>

      {/* Route Configuration */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <MapPin className="w-5 h-5 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">跑步路线配置</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">起点纬度 (LAT)</label>
            <input
              type="number"
              step="0.000001"
              className="input-field"
              placeholder="31.031599"
              value={config.START_LATITUDE}
              onChange={(e) => handleInputChange('START_LATITUDE', parseFloat(e.target.value) || 0)}
              disabled={disabled}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">起点经度 (LON)</label>
            <input
              type="number"
              step="0.000001"
              className="input-field"
              placeholder="121.442938"
              value={config.START_LONGITUDE}
              onChange={(e) => handleInputChange('START_LONGITUDE', parseFloat(e.target.value) || 0)}
              disabled={disabled}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">终点纬度 (LAT)</label>
            <input
              type="number"
              step="0.000001"
              className="input-field"
              placeholder="31.026400"
              value={config.END_LATITUDE}
              onChange={(e) => handleInputChange('END_LATITUDE', parseFloat(e.target.value) || 0)}
              disabled={disabled}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">终点经度 (LON)</label>
            <input
              type="number"
              step="0.000001"
              className="input-field"
              placeholder="121.455100"
              value={config.END_LONGITUDE}
              onChange={(e) => handleInputChange('END_LONGITUDE', parseFloat(e.target.value) || 0)}
              disabled={disabled}
            />
          </div>
        </div>
      </div>

      {/* Running Parameters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <Settings className="w-5 h-5 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">跑步参数配置</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">跑步速度 (米/秒)</label>
            <input
              type="number"
              step="0.1"
              className="input-field"
              placeholder="2.5"
              value={config.RUNNING_SPEED_MPS}
              onChange={(e) => handleInputChange('RUNNING_SPEED_MPS', parseFloat(e.target.value) || 0)}
              disabled={disabled}
            />
            <p className="text-xs text-gray-500 mt-1">
              例如: 2.5 米/秒 ≈ 9 公里/小时
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">轨迹点采样间隔 (秒)</label>
            <input
              type="number"
              className="input-field"
              placeholder="3"
              value={config.INTERVAL_SECONDS}
              onChange={(e) => handleInputChange('INTERVAL_SECONDS', parseInt(e.target.value) || 0)}
              disabled={disabled}
            />
            <p className="text-xs text-gray-500 mt-1">
              生成轨迹点的时间间隔
            </p>
          </div>
        </div>
      </div>

      {/* Time Configuration */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-6">
          <Clock className="w-5 h-5 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">跑步时间配置</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="useCurrentTime"
              checked={useCurrentTime}
              onChange={(e) => handleTimeToggle(e.target.checked)}
              disabled={disabled}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 focus:ring-2"
            />
            <label htmlFor="useCurrentTime" className="text-sm font-medium text-gray-700">
              使用当前时间
            </label>
          </div>

          {!useCurrentTime && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">手动设置开始时间</label>
              <input
                type="datetime-local"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                value={formatDateTimeLocal(config.START_TIME_EPOCH_MS)}
                onChange={(e) => handleDateTimeChange(e.target.value)}
                disabled={disabled}
              />
              <p className="text-xs text-gray-500 mt-1">
                设置过去的时间可用于补签历史跑步记录
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
