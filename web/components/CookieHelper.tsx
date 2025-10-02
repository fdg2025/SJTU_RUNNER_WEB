'use client';

import { useState, useEffect } from 'react';
import { Globe, Copy, RefreshCw, AlertCircle, CheckCircle, ExternalLink, Clipboard, Eye, EyeOff, ArrowRight, Zap } from 'lucide-react';

interface CookieHelperProps {
  onCookieExtracted: (cookie: string) => void;
}

export default function CookieHelper({ onCookieExtracted }: CookieHelperProps) {
  const [step, setStep] = useState(1);
  const [extractedCookie, setExtractedCookie] = useState('');
  const [tempInput, setTempInput] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [showTempInput, setShowTempInput] = useState(false);

  // 验证Cookie格式是否正确
  const isValidCookie = (cookie: string): boolean => {
    const trimmed = cookie.trim();
    return trimmed.includes('keepalive=') && trimmed.includes('JSESSIONID=');
  };

  // 清理和格式化Cookie
  const cleanCookie = (cookie: string): string => {
    const lines = cookie.split('\n');
    let keepalive = '';
    let jsessionid = '';
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.includes('keepalive=')) {
        const match = trimmed.match(/keepalive=([^;\s]+)/);
        if (match) keepalive = match[1];
      }
      if (trimmed.includes('JSESSIONID=')) {
        const match = trimmed.match(/JSESSIONID=([^;\s]+)/);
        if (match) jsessionid = match[1];
      }
    }
    
    if (keepalive && jsessionid) {
      return `keepalive=${keepalive}; JSESSIONID=${jsessionid}`;
    }
    
    return cookie.trim();
  };

  // 监听剪贴板变化
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isMonitoring) {
      interval = setInterval(async () => {
        try {
          const clipboardText = await navigator.clipboard.readText();
          if (clipboardText && isValidCookie(clipboardText)) {
            const cleanedCookie = cleanCookie(clipboardText);
            setExtractedCookie(cleanedCookie);
            setSuccess('🎉 检测到有效的Cookie！');
            setIsMonitoring(false);
            setStep(3);
            setError('');
          }
        } catch (err) {
          // 剪贴板权限被拒绝或其他错误，静默处理
        }
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isMonitoring]);

  // 开始监听剪贴板
  const startMonitoring = () => {
    setIsMonitoring(true);
    setStep(2);
    setError('');
    setSuccess('');
  };

  // 停止监听
  const stopMonitoring = () => {
    setIsMonitoring(false);
    setStep(1);
  };

  // 手动输入Cookie
  const handleManualInput = () => {
    if (!tempInput.trim()) {
      setError('请输入Cookie内容');
      return;
    }
    
    if (!isValidCookie(tempInput)) {
      setError('Cookie格式不正确，请确保包含keepalive和JSESSIONID');
      return;
    }
    
    const cleanedCookie = cleanCookie(tempInput);
    setExtractedCookie(cleanedCookie);
    setSuccess('Cookie格式验证通过！');
    setStep(3);
    setError('');
  };

  // 使用Cookie
  const useCookie = () => {
    onCookieExtracted(extractedCookie);
    setSuccess('Cookie已应用到配置中！');
  };

  // 重新开始
  const restart = () => {
    setStep(1);
    setExtractedCookie('');
    setTempInput('');
    setError('');
    setSuccess('');
    setIsMonitoring(false);
    setShowTempInput(false);
  };

  // 打开登录页面
  const openLoginPage = () => {
    window.open('https://pe.sjtu.edu.cn/phone/#/indexPortrait', '_blank', 'width=1200,height=800');
  };

  // 复制示例脚本到剪贴板
  const copyScript = async () => {
    const script = `// 在交我跑网站的控制台中运行此脚本
const keepalive = document.cookie.match(/keepalive=([^;]+)/)?.[1];
const jsessionid = document.cookie.match(/JSESSIONID=([^;]+)/)?.[1];
if (keepalive && jsessionid) {
  const cookie = \`keepalive=\${keepalive}; JSESSIONID=\${jsessionid}\`;
  console.log('Cookie:', cookie);
  navigator.clipboard.writeText(cookie).then(() => {
    alert('Cookie已复制到剪贴板！');
  });
} else {
  alert('未找到所需的Cookie，请确保已登录');
}`;
    
    try {
      await navigator.clipboard.writeText(script);
      setSuccess('脚本已复制！请在交我跑网站的控制台中粘贴运行');
    } catch (err) {
      setError('复制失败，请手动复制脚本');
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 space-y-6">
      {/* 标题 */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-blue-900">Cookie获取助手</h3>
          <p className="text-sm text-blue-600">无需扩展，智能检测</p>
        </div>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center justify-center space-x-4">
        {[1, 2, 3].map((num) => (
          <div key={num} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= num 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-500'
            }`}>
              {num}
            </div>
            {num < 3 && (
              <ArrowRight className={`w-4 h-4 mx-2 ${
                step > num ? 'text-blue-600' : 'text-gray-300'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* 步骤1: 选择方式 */}
      {step === 1 && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-800">选择获取方式：</h4>
          
          <div className="grid grid-cols-1 gap-3">
            {/* 智能检测方式 */}
            <div className="bg-white rounded-lg p-4 border-2 border-blue-200 hover:border-blue-300 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Clipboard className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex-1">
                  <h5 className="font-medium text-gray-800 mb-1">智能检测（推荐）</h5>
                  <p className="text-sm text-gray-600 mb-3">
                    自动检测剪贴板中的Cookie，最简单快捷
                  </p>
                  <button
                    onClick={startMonitoring}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    开始智能检测
                  </button>
                </div>
              </div>
            </div>

            {/* 一键脚本方式 */}
            <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Copy className="w-4 h-4 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h5 className="font-medium text-gray-800 mb-1">一键脚本</h5>
                  <p className="text-sm text-gray-600 mb-3">
                    复制脚本到控制台运行，自动提取Cookie
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={openLoginPage}
                      className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                    >
                      <ExternalLink className="w-3 h-3" />
                      打开网站
                    </button>
                    <button
                      onClick={copyScript}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      复制脚本
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* 手动输入方式 */}
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Eye className="w-4 h-4 text-orange-600" />
                </div>
                <div className="flex-1">
                  <h5 className="font-medium text-gray-800 mb-1">手动输入</h5>
                  <p className="text-sm text-gray-600 mb-3">
                    直接粘贴从开发者工具复制的Cookie
                  </p>
                  <button
                    onClick={() => setShowTempInput(!showTempInput)}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    {showTempInput ? '隐藏输入框' : '显示输入框'}
                  </button>
                </div>
              </div>
              
              {showTempInput && (
                <div className="mt-4 space-y-3">
                  <textarea
                    value={tempInput}
                    onChange={(e) => setTempInput(e.target.value)}
                    placeholder="粘贴Cookie内容..."
                    className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm font-mono"
                  />
                  <button
                    onClick={handleManualInput}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    验证Cookie
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 步骤2: 监听中 */}
      {step === 2 && (
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
          <div>
            <h4 className="font-medium text-gray-800 mb-2">正在智能检测...</h4>
            <p className="text-sm text-gray-600 mb-4">
              请按照以下步骤操作，系统会自动检测Cookie：
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-4 text-left space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">1</div>
              <div>
                <p className="text-sm font-medium text-gray-800">打开交我跑网站并登录</p>
                <button
                  onClick={openLoginPage}
                  className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1 mt-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  点击打开网站
                </button>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">2</div>
              <p className="text-sm text-gray-800">按F12打开开发者工具 → 应用程序 → Cookie</p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">3</div>
              <p className="text-sm text-gray-800">复制keepalive和JSESSIONID的值</p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">✓</div>
              <p className="text-sm text-gray-800">系统会自动检测并提取Cookie</p>
            </div>
          </div>
          
          <button
            onClick={stopMonitoring}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            停止检测
          </button>
        </div>
      )}

      {/* 步骤3: 完成 */}
      {step === 3 && extractedCookie && (
        <div className="space-y-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h4 className="font-medium text-green-800 mb-2">Cookie获取成功！</h4>
          </div>
          
          <div className="bg-white rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">获取到的Cookie：</label>
            <div className="bg-gray-50 rounded border p-3 text-xs font-mono break-all max-h-24 overflow-y-auto">
              {extractedCookie}
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={useCookie}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              使用此Cookie
            </button>
            <button
              onClick={restart}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              重新获取
            </button>
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            <span className="text-sm text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* 成功信息 */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
            <span className="text-sm text-green-800">{success}</span>
          </div>
        </div>
      )}

      {/* 帮助提示 */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h5 className="text-sm font-medium text-gray-800 mb-2">💡 使用提示：</h5>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• 推荐使用"智能检测"方式，最简单快捷</li>
          <li>• "一键脚本"适合熟悉控制台操作的用户</li>
          <li>• 如果检测失败，可以尝试手动输入方式</li>
          <li>• Cookie格式：keepalive=值1; JSESSIONID=值2</li>
        </ul>
      </div>
    </div>
  );
}