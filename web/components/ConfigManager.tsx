'use client';

import { useState } from 'react';
import { RunningConfig } from '@/lib/utils';
import { Download, Upload, Save, RotateCcw } from 'lucide-react';

interface ConfigManagerProps {
  config: RunningConfig;
  onConfigChange: (config: RunningConfig) => void;
  disabled?: boolean;
}

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

export default function ConfigManager({ config, onConfigChange, disabled = false }: ConfigManagerProps) {
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleLoadDefault = () => {
    onConfigChange(DEFAULT_CONFIG);
    showMessage('已加载默认配置', 'success');
  };

  const handleExportConfig = () => {
    try {
      const configToExport = { ...config };
      // Remove sensitive information for export
      configToExport.COOKIE = '';
      
      const dataStr = JSON.stringify(configToExport, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = `sjtu-running-config-${new Date().toISOString().split('T')[0]}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      
      showMessage('配置已导出', 'success');
    } catch (error) {
      showMessage('导出配置失败', 'error');
    }
  };

  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedConfig = JSON.parse(e.target?.result as string);
        
        // Validate imported config has required fields
        const requiredFields = ['USER_ID', 'START_LATITUDE', 'START_LONGITUDE', 'END_LATITUDE', 'END_LONGITUDE', 'RUNNING_SPEED_MPS', 'INTERVAL_SECONDS'];
        const missingFields = requiredFields.filter(field => !(field in importedConfig));
        
        if (missingFields.length > 0) {
          showMessage(`配置文件缺少必需字段: ${missingFields.join(', ')}`, 'error');
          return;
        }
        
        // Merge with default config to ensure all fields are present
        const mergedConfig = { ...DEFAULT_CONFIG, ...importedConfig };
        onConfigChange(mergedConfig);
        showMessage('配置已导入', 'success');
      } catch (error) {
        showMessage('导入配置失败：文件格式错误', 'error');
      }
    };
    reader.readAsText(file);
    
    // Reset input value to allow importing the same file again
    event.target.value = '';
  };

  const handleSaveToLocalStorage = () => {
    try {
      localStorage.setItem('sjtu-running-config', JSON.stringify(config));
      showMessage('配置已保存到本地', 'success');
    } catch (error) {
      showMessage('保存配置失败', 'error');
    }
  };

  const handleLoadFromLocalStorage = () => {
    try {
      const savedConfig = localStorage.getItem('sjtu-running-config');
      if (savedConfig) {
        const parsedConfig = JSON.parse(savedConfig);
        const mergedConfig = { ...DEFAULT_CONFIG, ...parsedConfig };
        onConfigChange(mergedConfig);
        showMessage('已从本地加载配置', 'success');
      } else {
        showMessage('未找到本地保存的配置', 'error');
      }
    } catch (error) {
      showMessage('加载本地配置失败', 'error');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">配置管理</h2>
      
      {message && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          {message.text}
        </div>
      )}
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <button
          onClick={handleLoadDefault}
          disabled={disabled}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          加载默认配置
        </button>
        
        <button
          onClick={handleSaveToLocalStorage}
          disabled={disabled}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4" />
          保存到本地
        </button>
        
        <button
          onClick={handleLoadFromLocalStorage}
          disabled={disabled}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <Upload className="w-4 h-4" />
          从本地加载
        </button>
        
        <button
          onClick={handleExportConfig}
          disabled={disabled}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <Download className="w-4 h-4" />
          导出配置
        </button>
      </div>
      
      <div className="mt-4">
        <label className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 cursor-pointer inline-flex items-center gap-2">
          <Upload className="w-4 h-4" />
          导入配置文件
          <input
            type="file"
            accept=".json"
            onChange={handleImportConfig}
            disabled={disabled}
            className="hidden"
          />
        </label>
      </div>
      
      <div className="mt-4 text-sm text-gray-600">
        <p className="mb-2"><strong>提示：</strong></p>
        <ul className="list-disc list-inside space-y-1 text-xs">
          <li>导出的配置文件不包含Cookie信息，需要重新填写</li>
          <li>本地保存的配置包含所有信息，仅在当前浏览器有效</li>
          <li>默认配置使用上海交通大学校园内的示例坐标</li>
        </ul>
      </div>
    </div>
  );
}
