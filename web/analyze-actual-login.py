#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析SJTU实际登录流程
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import json
import base64
import time
from typing import Dict, List, Optional, Tuple

# 测试配置
TEST_CONFIG = {
    'sjtu_base_url': 'https://pe.sjtu.edu.cn',
    'sjtu_login_url': 'https://pe.sjtu.edu.cn/login',
    'sjtu_phone_url': 'https://pe.sjtu.edu.cn/phone/',
    'timeout': 15
}

# 创建SSL上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def make_request(url: str, method: str = 'GET', data: Optional[Dict] = None, 
                headers: Optional[Dict] = None, cookies: str = '') -> Tuple[int, Dict, bytes, str]:
    """发送HTTP请求，返回字节数据"""
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
            response_body = response.read()
            
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
        response_body = e.read() if e.fp else b''
        
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
        return 0, {}, b'', ''

def analyze_login_page():
    """分析登录页面内容"""
    print('🔍 分析SJTU登录页面...')
    
    # 步骤1: 获取初始会话
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    print(f'✅ JSESSIONID: {jsessionid[:20]}...')
    
    # 步骤2: 访问登录页面
    status, headers, body, new_cookies = make_request(
        TEST_CONFIG['sjtu_login_url'], 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    print(f'✅ 登录页面状态: {status}')
    
    # 解析HTML内容
    html_content = body.decode('utf-8', errors='ignore')
    
    # 保存HTML内容用于分析
    with open('login_page.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print('💾 登录页面HTML已保存为 login_page.html')
    
    # 查找表单
    print('\n📋 表单分析:')
    form_pattern = r'<form[^>]*>(.*?)</form>'
    forms = re.findall(form_pattern, html_content, re.IGNORECASE | re.DOTALL)
    print(f'   找到表单数量: {len(forms)}')
    
    for i, form in enumerate(forms):
        print(f'\n   表单 {i+1}:')
        
        # 查找action
        action_match = re.search(r'action=["\']([^"\']*)["\']', form, re.IGNORECASE)
        action = action_match.group(1) if action_match else '无'
        print(f'     action: {action}')
        
        # 查找method
        method_match = re.search(r'method=["\']([^"\']*)["\']', form, re.IGNORECASE)
        method = method_match.group(1) if method_match else 'GET'
        print(f'     method: {method}')
        
        # 查找输入字段
        input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
        inputs = re.findall(input_pattern, form, re.IGNORECASE)
        print(f'     输入字段: {inputs}')
        
        # 查找按钮
        button_pattern = r'<button[^>]*>(.*?)</button>'
        buttons = re.findall(button_pattern, form, re.IGNORECASE | re.DOTALL)
        print(f'     按钮: {buttons}')
    
    # 查找验证码相关
    print('\n🔍 验证码分析:')
    captcha_patterns = [
        r'<img[^>]*src=["\']([^"\']*captcha[^"\']*)["\'][^>]*>',
        r'<img[^>]*src=["\']([^"\']*verify[^"\']*)["\'][^>]*>',
        r'<img[^>]*src=["\']([^"\']*image[^"\']*)["\'][^>]*>',
        r'src=["\']([^"\']*captcha[^"\']*)["\']',
        r'captcha[^"\']*["\']([^"\']*)["\']',
    ]
    
    captcha_found = False
    for pattern in captcha_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f'   找到验证码: {matches[0]}')
            captcha_found = True
            break
    
    if not captcha_found:
        print('   ❌ 未找到验证码图片')
    
    # 查找JavaScript
    print('\n🔍 JavaScript分析:')
    js_patterns = [
        r'<script[^>]*>(.*?)</script>',
        r'function[^{]*{[^}]*captcha[^}]*}',
        r'captcha[^"\']*["\']([^"\']*)["\']',
        r'jaccount[^"\']*["\']([^"\']*)["\']',
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f'   JS匹配数量: {len(matches)}')
            if len(matches) > 0:
                print(f'   第一个匹配: {matches[0][:100]}...')
    
    # 查找JAccount相关
    print('\n🔍 JAccount分析:')
    jaccount_patterns = [
        r'jaccount[^"\']*["\']([^"\']*)["\']',
        r'https://jaccount\.sjtu\.edu\.cn[^"\']*',
        r'jaccount\.sjtu\.edu\.cn',
    ]
    
    jaccount_found = False
    for pattern in jaccount_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f'   找到JAccount: {matches[0]}')
            jaccount_found = True
            break
    
    if not jaccount_found:
        print('   ❌ 未找到JAccount相关内容')
    
    return {
        'jsessionid': jsessionid,
        'html_content': html_content,
        'forms_count': len(forms),
        'captcha_found': captcha_found,
        'jaccount_found': jaccount_found
    }

def test_different_login_endpoints():
    """测试不同的登录端点"""
    print('\n🔍 测试不同的登录端点...')
    
    endpoints = [
        'https://pe.sjtu.edu.cn/login',
        'https://pe.sjtu.edu.cn/login.jsp',
        'https://pe.sjtu.edu.cn/login.php',
        'https://pe.sjtu.edu.cn/auth/login',
        'https://pe.sjtu.edu.cn/user/login',
        'https://pe.sjtu.edu.cn/account/login',
    ]
    
    for endpoint in endpoints:
        try:
            status, headers, body, cookies = make_request(endpoint)
            print(f'   {endpoint}: 状态 {status}')
            
            if status == 200:
                html_content = body.decode('utf-8', errors='ignore')
                if 'login' in html_content.lower() or '登录' in html_content:
                    print(f'     ✅ 可能是登录页面')
                    
                    # 查找表单
                    form_count = len(re.findall(r'<form[^>]*>', html_content, re.IGNORECASE))
                    print(f'     表单数量: {form_count}')
                    
                    # 查找验证码
                    captcha_count = len(re.findall(r'captcha', html_content, re.IGNORECASE))
                    print(f'     验证码相关: {captcha_count} 处')
                    
                    # 查找JAccount
                    jaccount_count = len(re.findall(r'jaccount', html_content, re.IGNORECASE))
                    print(f'     JAccount相关: {jaccount_count} 处')
            else:
                print(f'     ❌ 状态码: {status}')
                
        except Exception as e:
            print(f'   ❌ {endpoint}: {e}')

def main():
    """主函数"""
    print('🚀 分析SJTU实际登录流程...\n')
    
    # 分析登录页面
    analysis = analyze_login_page()
    
    # 测试不同端点
    test_different_login_endpoints()
    
    # 总结
    print('\n📊 分析总结:')
    print(f'✅ 表单数量: {analysis["forms_count"]}')
    print(f'✅ 验证码: {"找到" if analysis["captcha_found"] else "未找到"}')
    print(f'✅ JAccount: {"找到" if analysis["jaccount_found"] else "未找到"}')
    
    print('\n💡 建议:')
    print('   1. 查看保存的 login_page.html 文件')
    print('   2. 分析实际的登录表单结构')
    print('   3. 确定验证码获取方式')
    print('   4. 测试真实的登录流程')

if __name__ == '__main__':
    main()

