'use client';

import { useState } from 'react';
import { RunningConfig } from '@/lib/utils';
import { ExternalLink, MapPin, Clock, Settings, User } from 'lucide-react';

interface ConfigFormProps {
  config: RunningConfig;
  onChange: (config: RunningConfig) => void;
  disabled?: boolean;
}

export default function ConfigForm({ config, onChange, disabled = false }: ConfigFormProps) {
  const [useCurrentTime, setUseCurrentTime] = useState(config.START_TIME_EPOCH_MS === null);

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
                className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 transition-colors"
              >
                获取Cookie
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <input
              type="text"
              className="input-field"
              placeholder="keepalive=...; JSESSIONID=..."
              value={config.COOKIE}
              onChange={(e) => handleInputChange('COOKIE', e.target.value)}
              disabled={disabled}
            />
            <p className="text-xs text-gray-500 mt-1">
              从浏览器开发者工具中复制完整的Cookie字符串
            </p>
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
