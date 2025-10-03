#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入分析SJTU登录流程，找出JSESSIONID的获取方式
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
    'sjtu_base_url': 'https://pe.sjtu.edu.cn',
    'sjtu_login_url': 'https://pe.sjtu.edu.cn/login',
    'sjtu_phone_url': 'https://pe.sjtu.edu.cn/phone/',
    'sjtu_phone_index': 'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
    'timeout': 15
}

# 创建SSL上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def make_request(url: str, method: str = 'GET', data: Optional[Dict] = None, 
                headers: Optional[Dict] = None, cookies: str = '') -> Tuple[int, Dict, str, str]:
    """
    发送HTTP请求
    
    Returns:
        (status_code, headers_dict, response_body, new_cookies)
    """
    if headers is None:
        headers = {}
    
    # 添加Cookie
    if cookies:
        headers['Cookie'] = cookies
    
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
            
            # 提取新的Cookie
            set_cookies = response_headers.get('Set-Cookie', [])
            if isinstance(set_cookies, str):
                set_cookies = [set_cookies]
            
            new_cookies = []
            for cookie in set_cookies:
                cookie_name_value = cookie.split(';')[0]
                new_cookies.append(cookie_name_value)
            
            return status_code, response_headers, response_body, '; '.join(new_cookies)
    except urllib.error.HTTPError as e:
        # 处理HTTP错误（如重定向）
        status_code = e.code
        response_headers = dict(e.headers)
        response_body = e.read().decode('utf-8', errors='ignore') if e.fp else ''
        
        # 提取新的Cookie
        set_cookies = response_headers.get('Set-Cookie', [])
        if isinstance(set_cookies, str):
            set_cookies = [set_cookies]
        
        new_cookies = []
        for cookie in set_cookies:
            cookie_name_value = cookie.split(';')[0]
            new_cookies.append(cookie_name_value)
        
        return status_code, response_headers, response_body, '; '.join(new_cookies)
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return 0, {}, str(e), ''

def analyze_login_page():
    """分析登录页面结构"""
    print('🔍 分析SJTU登录页面结构...')
    
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_login_url'])
    
    print(f'✅ 响应状态: {status}')
    print(f'📄 页面大小: {len(body)} 字符')
    print(f'🍪 初始Cookie: {cookies if cookies else "无"}')
    
    # 查找登录表单
    form_patterns = [
        r'<form[^>]*>(.*?)</form>',
        r'<input[^>]*type=["\']password["\'][^>]*>',
        r'<input[^>]*name=["\'][^"\']*user[^"\']*["\'][^>]*>',
        r'<input[^>]*name=["\'][^"\']*pass[^"\']*["\'][^>]*>'
    ]
    
    print('\n📋 登录表单分析:')
    for i, pattern in enumerate(form_patterns):
        matches = re.findall(pattern, body, re.IGNORECASE | re.DOTALL)
        print(f'   模式 {i+1}: {len(matches)} 个匹配')
    
    # 查找所有input字段
    input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
    inputs = re.findall(input_pattern, body, re.IGNORECASE)
    
    print(f'\n🔍 找到的输入字段:')
    for input_name in inputs:
        print(f'   - {input_name}')
    
    # 查找JavaScript中的登录逻辑
    js_patterns = [
        r'login[^"\']*["\']([^"\']*)["\']',
        r'action[^"\']*["\']([^"\']*)["\']',
        r'url[^"\']*["\']([^"\']*login[^"\']*)["\']'
    ]
    
    print(f'\n🔍 JavaScript登录相关:')
    for pattern in js_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            print(f'   匹配: {matches[:3]}')  # 只显示前3个
    
    return {
        'status': status,
        'body': body,
        'cookies': cookies,
        'inputs': inputs
    }

def test_different_endpoints():
    """测试不同的端点，寻找JSESSIONID"""
    print('\n🔍 测试不同端点寻找JSESSIONID...')
    
    endpoints = [
        'https://pe.sjtu.edu.cn/',
        'https://pe.sjtu.edu.cn/index',
        'https://pe.sjtu.edu.cn/phone/',
        'https://pe.sjtu.edu.cn/api/user/info',
        'https://pe.sjtu.edu.cn/api/auth/status',
        'https://pe.sjtu.edu.cn/login',
    ]
    
    all_cookies = {}
    
    for endpoint in endpoints:
        print(f'\n📡 测试端点: {endpoint}')
        try:
            status, headers, body, cookies = make_request(endpoint)
            print(f'   状态: {status}')
            print(f'   Cookie: {cookies if cookies else "无"}')
            
            if cookies:
                all_cookies[endpoint] = cookies
                
                # 检查是否包含JSESSIONID
                if 'JSESSIONID=' in cookies:
                    print(f'   🎉 找到JSESSIONID!')
                    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
                    if jsessionid_match:
                        print(f'   JSESSIONID值: {jsessionid_match.group(1)}')
        
        except Exception as e:
            print(f'   ❌ 错误: {e}')
    
    return all_cookies

def test_session_creation():
    """测试会话创建流程"""
    print('\n🔍 测试会话创建流程...')
    
    # 步骤1: 访问主页，获取初始会话
    print('步骤1: 访问主页...')
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    print(f'   状态: {status}')
    print(f'   Cookie: {cookies}')
    
    # 步骤2: 访问登录页面，保持会话
    print('\n步骤2: 访问登录页面...')
    status, headers, body, new_cookies = make_request(TEST_CONFIG['sjtu_login_url'], cookies=cookies)
    print(f'   状态: {status}')
    print(f'   新Cookie: {new_cookies}')
    
    # 合并Cookie
    all_cookies = cookies
    if new_cookies:
        if all_cookies:
            all_cookies += '; ' + new_cookies
        else:
            all_cookies = new_cookies
    
    print(f'   合并Cookie: {all_cookies}')
    
    # 步骤3: 访问手机端页面
    print('\n步骤3: 访问手机端页面...')
    status, headers, body, final_cookies = make_request(TEST_CONFIG['sjtu_phone_url'], cookies=all_cookies)
    print(f'   状态: {status}')
    print(f'   最终Cookie: {final_cookies}')
    
    # 分析最终Cookie
    print(f'\n🍪 Cookie分析:')
    if final_cookies:
        cookie_parts = final_cookies.split('; ')
        for part in cookie_parts:
            if '=' in part:
                name, value = part.split('=', 1)
                print(f'   {name}: {value[:20]}{"..." if len(value) > 20 else ""}')
                
                if name == 'JSESSIONID':
                    print(f'   🎉 JSESSIONID找到! 长度: {len(value)}')
                elif name == 'keepalive':
                    print(f'   🔑 keepalive找到! 长度: {len(value)}')
    
    return final_cookies

def main():
    """主函数"""
    print('🚀 深入分析SJTU登录流程...\n')
    
    # 分析登录页面
    login_analysis = analyze_login_page()
    
    # 测试不同端点
    endpoint_cookies = test_different_endpoints()
    
    # 测试会话创建
    final_cookies = test_session_creation()
    
    # 总结
    print('\n📊 分析总结:')
    print(f'✅ 登录页面可访问: {"是" if login_analysis["status"] == 200 else "否"}')
    print(f'✅ 找到输入字段: {len(login_analysis["inputs"])} 个')
    print(f'✅ 测试端点数量: {len(endpoint_cookies)} 个')
    print(f'✅ 最终Cookie: {"有" if final_cookies else "无"}')
    
    if final_cookies:
        has_keepalive = 'keepalive=' in final_cookies
        has_jsessionid = 'JSESSIONID=' in final_cookies
        
        print(f'\n🎯 目标Cookie状态:')
        print(f'keepalive: {"✅ 找到" if has_keepalive else "❌ 未找到"}')
        print(f'JSESSIONID: {"✅ 找到" if has_jsessionid else "❌ 未找到"}')
        
        if has_keepalive and has_jsessionid:
            print('\n🎉 成功！找到了完整的Cookie！')
            
            # 提取Cookie值
            keepalive_match = re.search(r'keepalive=([^;]+)', final_cookies)
            jsessionid_match = re.search(r'JSESSIONID=([^;]+)', final_cookies)
            
            if keepalive_match and jsessionid_match:
                keepalive = keepalive_match.group(1)
                jsessionid = jsessionid_match.group(1)
                final_cookie = f'keepalive={keepalive}; JSESSIONID={jsessionid}'
                print(f'\n📋 最终Cookie格式:')
                print(f'keepalive={keepalive[:30]}...')
                print(f'JSESSIONID={jsessionid}')
                print(f'\n完整Cookie: {final_cookie}')
        else:
            print('\n❌ 仍然缺少必要的Cookie')
            print('\n💡 建议:')
            print('   1. 检查SJTU系统是否需要特殊的认证流程')
            print('   2. 可能需要先访问特定的页面来初始化会话')
            print('   3. 考虑使用真实的用户凭据进行测试')

if __name__ == '__main__':
    main()
