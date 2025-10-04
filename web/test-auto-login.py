#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SJTU自动登录流程的Python脚本
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import json
from typing import Dict, List, Optional, Tuple

# 测试配置
TEST_CONFIG = {
    'username': 'test_user',
    'password': 'test_password',
    'sjtu_login_url': 'https://pe.sjtu.edu.cn/login',
    'sjtu_phone_url': 'https://pe.sjtu.edu.cn/phone/',
    'timeout': 10
}

# 创建SSL上下文，忽略证书验证（仅用于测试）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def make_request(url: str, method: str = 'GET', data: Optional[Dict] = None, 
                headers: Optional[Dict] = None, follow_redirects: bool = True) -> Tuple[int, Dict, str]:
    """
    发送HTTP请求
    
    Args:
        url: 请求URL
        method: HTTP方法
        data: 请求数据
        headers: 请求头
        follow_redirects: 是否跟随重定向
    
    Returns:
        (status_code, headers_dict, response_body)
    """
    if headers is None:
        headers = {}
    
    # 设置默认请求头
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    default_headers.update(headers)
    
    # 准备请求
    if data and method.upper() == 'POST':
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode('utf-8')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        default_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    
    req = urllib.request.Request(url, data=data, headers=default_headers, method=method.upper())
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=TEST_CONFIG['timeout']) as response:
            status_code = response.getcode()
            response_headers = dict(response.headers)
            response_body = response.read().decode('utf-8', errors='ignore')
            
            return status_code, response_headers, response_body
    except urllib.error.HTTPError as e:
        # 处理HTTP错误（如重定向）
        status_code = e.code
        response_headers = dict(e.headers)
        response_body = e.read().decode('utf-8', errors='ignore') if e.fp else ''
        return status_code, response_headers, response_body
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return 0, {}, str(e)

def test_get_login_page() -> Dict:
    """测试步骤1：获取登录页面"""
    print('🔍 步骤1：获取SJTU登录页面...')
    
    try:
        status, headers, body = make_request(TEST_CONFIG['sjtu_login_url'])
        
        print(f'✅ 登录页面响应状态: {status}')
        print(f'📄 响应内容长度: {len(body)} 字符')
        
        # 检查是否包含登录表单
        has_login_form = any(keyword in body.lower() for keyword in ['login', 'username', 'password', '登录'])
        print(f'🔍 包含登录表单: {"✅" if has_login_form else "❌"}')
        
        # 尝试提取CSRF令牌
        csrf_patterns = [
            r'name="[^"]*token[^"]*"[^>]*value="([^"]*)"',
            r'name="_token"[^>]*value="([^"]*)"',
            r'name="csrf_token"[^>]*value="([^"]*)"',
            r'<meta name="csrf-token" content="([^"]*)"'
        ]
        
        csrf_token = ''
        for pattern in csrf_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                csrf_token = match.group(1)
                break
        
        print(f'🔑 CSRF令牌: {"✅ 找到" if csrf_token else "❌ 未找到"}')
        
        return {
            'success': True,
            'status': status,
            'html': body,
            'csrf_token': csrf_token,
            'headers': headers
        }
    except Exception as e:
        print(f'❌ 获取登录页面失败: {e}')
        return {'success': False, 'error': str(e)}

def test_login_request(csrf_token: str = '') -> Dict:
    """测试步骤2：模拟登录请求"""
    print('\n🔍 步骤2：模拟登录请求...')
    
    # 准备登录数据
    login_data = {
        'username': TEST_CONFIG['username'],
        'password': TEST_CONFIG['password']
    }
    
    if csrf_token:
        login_data['_token'] = csrf_token
    
    headers = {
        'Origin': 'https://pe.sjtu.edu.cn',
        'Referer': 'https://pe.sjtu.edu.cn/login',
    }
    
    try:
        status, headers, body = make_request(
            TEST_CONFIG['sjtu_login_url'], 
            method='POST', 
            data=login_data, 
            headers=headers
        )
        
        print(f'✅ 登录请求响应状态: {status}')
        
        # 检查重定向
        location = headers.get('location', '')
        print(f'📍 重定向位置: {location if location else "无"}')
        
        # 检查Set-Cookie头
        set_cookies = headers.get('Set-Cookie', [])
        if isinstance(set_cookies, str):
            set_cookies = [set_cookies]
        
        if set_cookies:
            print(f'🍪 Set-Cookie头数量: {len(set_cookies)}')
            for i, cookie in enumerate(set_cookies):
                cookie_name = cookie.split('=')[0] if '=' in cookie else cookie.split(';')[0]
                print(f'   Cookie {i + 1}: {cookie_name}')
            
            # 检查是否包含目标Cookie
            all_cookies = '; '.join(set_cookies)
            has_keepalive = 'keepalive=' in all_cookies
            has_jsessionid = 'JSESSIONID=' in all_cookies
            print(f'🔍 包含keepalive: {"✅" if has_keepalive else "❌"}')
            print(f'🔍 包含JSESSIONID: {"✅" if has_jsessionid else "❌"}')
        else:
            print('❌ 未找到Set-Cookie头')
        
        return {
            'success': True,
            'status': status,
            'location': location,
            'cookies': set_cookies,
            'headers': headers
        }
    except Exception as e:
        print(f'❌ 登录请求失败: {e}')
        return {'success': False, 'error': str(e)}

def test_phone_page(cookies: List[str] = None) -> Dict:
    """测试步骤3：访问手机端页面"""
    print('\n🔍 步骤3：访问手机端页面...')
    
    if not cookies:
        cookies = []
    
    cookie_string = '; '.join([cookie.split(';')[0] for cookie in cookies])
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': cookie_string,
    }
    
    try:
        status, headers, body = make_request(
            TEST_CONFIG['sjtu_phone_url'], 
            headers=headers
        )
        
        print(f'✅ 手机端页面响应状态: {status}')
        
        # 检查额外的Cookie
        set_cookies = headers.get('Set-Cookie', [])
        if isinstance(set_cookies, str):
            set_cookies = [set_cookies]
        
        if set_cookies:
            print(f'🍪 额外Cookie数量: {len(set_cookies)}')
            for i, cookie in enumerate(set_cookies):
                cookie_name = cookie.split('=')[0] if '=' in cookie else cookie.split(';')[0]
                print(f'   额外Cookie {i + 1}: {cookie_name}')
        else:
            print('📝 无额外Cookie')
        
        return {
            'success': True,
            'status': status,
            'additional_cookies': set_cookies,
            'headers': headers
        }
    except Exception as e:
        print(f'❌ 访问手机端页面失败: {e}')
        return {'success': False, 'error': str(e)}

def extract_cookies(all_cookies: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """从Cookie列表中提取keepalive和JSESSIONID"""
    keepalive = None
    jsessionid = None
    
    for cookie in all_cookies:
        if cookie.startswith('keepalive='):
            keepalive = cookie.split('=')[1].split(';')[0]
        elif cookie.startswith('JSESSIONID='):
            jsessionid = cookie.split('=')[1].split(';')[0]
    
    return keepalive, jsessionid

def main():
    """主测试函数"""
    print('🚀 开始测试SJTU自动登录流程...\n')
    
    # 步骤1：获取登录页面
    login_page_result = test_get_login_page()
    if not login_page_result['success']:
        print('\n❌ 测试终止：无法获取登录页面')
        return
    
    # 步骤2：模拟登录请求
    login_result = test_login_request(login_page_result.get('csrf_token', ''))
    if not login_result['success']:
        print('\n❌ 测试终止：登录请求失败')
        return
    
    # 步骤3：访问手机端页面
    phone_result = test_phone_page(login_result.get('cookies', []))
    if not phone_result['success']:
        print('\n❌ 测试终止：无法访问手机端页面')
        return
    
    # 总结
    print('\n📊 测试总结:')
    print(f'✅ 登录页面获取: {"成功" if login_page_result["success"] else "失败"}')
    print(f'✅ 登录请求: {"成功" if login_result["success"] else "失败"}')
    print(f'✅ 手机端访问: {"成功" if phone_result["success"] else "失败"}')
    
    # 分析Cookie获取情况
    all_cookies = login_result.get('cookies', []) + phone_result.get('additional_cookies', [])
    
    print(f'\n🍪 Cookie分析 (总共 {len(all_cookies)} 个):')
    for i, cookie in enumerate(all_cookies):
        cookie_name = cookie.split('=')[0] if '=' in cookie else cookie.split(';')[0]
        print(f'   Cookie {i + 1}: {cookie_name}')
    
    keepalive, jsessionid = extract_cookies(all_cookies)
    
    print(f'\n🔍 目标Cookie检查:')
    print(f'keepalive: {"✅ 找到" if keepalive else "❌ 未找到"}')
    print(f'JSESSIONID: {"✅ 找到" if jsessionid else "❌ 未找到"}')
    
    if keepalive and jsessionid:
        final_cookie = f'keepalive={keepalive}; JSESSIONID={jsessionid}'
        print(f'\n🎉 最终Cookie: {final_cookie}')
        print('\n✅ 自动登录流程测试成功！')
        
        # 验证Cookie格式
        print(f'\n🔍 Cookie格式验证:')
        print(f'keepalive长度: {len(keepalive)} 字符')
        print(f'JSESSIONID长度: {len(jsessionid)} 字符')
        print(f'格式正确: {"✅" if len(keepalive) > 10 and len(jsessionid) > 10 else "❌"}')
    else:
        print('\n❌ Cookie获取不完整，需要进一步调试')
        print('\n💡 可能的原因:')
        print('   1. SJTU登录页面结构发生变化')
        print('   2. 需要额外的认证步骤')
        print('   3. 网络连接问题')
        print('   4. 测试账号无效')

if __name__ == '__main__':
    main()

