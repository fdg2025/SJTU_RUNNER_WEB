#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入分析SJTU登录流程，包括验证码处理
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import json
import base64
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
                headers: Optional[Dict] = None, cookies: str = '') -> Tuple[int, Dict, str, str]:
    """发送HTTP请求"""
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

def analyze_login_form():
    """分析登录表单结构"""
    print('🔍 分析SJTU登录表单结构...')
    
    # 步骤1: 获取初始会话
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    print(f'✅ 初始JSESSIONID: {jsessionid[:20]}...')
    
    # 步骤2: 访问登录页面
    status, headers, body, new_cookies = make_request(
        TEST_CONFIG['sjtu_login_url'], 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    print(f'✅ 登录页面状态: {status}')
    
    # 分析表单字段
    print('\n📋 登录表单分析:')
    
    # 查找所有input字段
    input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
    inputs = re.findall(input_pattern, body, re.IGNORECASE)
    print(f'   输入字段: {inputs}')
    
    # 查找表单action
    action_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', body, re.IGNORECASE)
    action = action_match.group(1) if action_match else '/login'
    print(f'   表单action: {action}')
    
    # 查找验证码相关
    captcha_patterns = [
        r'<img[^>]*src=["\']([^"\']*captcha[^"\']*)["\'][^>]*>',
        r'<img[^>]*src=["\']([^"\']*verify[^"\']*)["\'][^>]*>',
        r'<img[^>]*src=["\']([^"\']*code[^"\']*)["\'][^>]*>',
        r'captcha[^"\']*["\']([^"\']*)["\']',
    ]
    
    print('\n🔍 验证码分析:')
    captcha_found = False
    for pattern in captcha_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            print(f'   找到验证码: {matches[0]}')
            captcha_found = True
            break
    
    if not captcha_found:
        print('   ❌ 未找到验证码图片')
    
    # 查找JavaScript中的验证码逻辑
    js_patterns = [
        r'captcha[^"\']*["\']([^"\']*)["\']',
        r'verify[^"\']*["\']([^"\']*)["\']',
        r'code[^"\']*["\']([^"\']*)["\']',
    ]
    
    print('\n🔍 JavaScript验证码:')
    for pattern in js_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            print(f'   JS匹配: {matches[:3]}')
    
    return {
        'jsessionid': jsessionid,
        'inputs': inputs,
        'action': action,
        'body': body,
        'cookies': cookies
    }

def test_captcha_endpoints():
    """测试可能的验证码端点"""
    print('\n🔍 测试验证码端点...')
    
    # 常见的验证码端点
    captcha_endpoints = [
        'https://pe.sjtu.edu.cn/captcha',
        'https://pe.sjtu.edu.cn/captcha.jpg',
        'https://pe.sjtu.edu.cn/captcha.png',
        'https://pe.sjtu.edu.cn/verify',
        'https://pe.sjtu.edu.cn/verify.jpg',
        'https://pe.sjtu.edu.cn/verify.png',
        'https://pe.sjtu.edu.cn/code',
        'https://pe.sjtu.edu.cn/code.jpg',
        'https://pe.sjtu.edu.cn/code.png',
        'https://pe.sjtu.edu.cn/kaptcha',
        'https://pe.sjtu.edu.cn/kaptcha.jpg',
        'https://pe.sjtu.edu.cn/kaptcha.png',
    ]
    
    working_endpoints = []
    
    for endpoint in captcha_endpoints:
        try:
            status, headers, body, cookies = make_request(endpoint)
            content_type = headers.get('Content-Type', '')
            
            print(f'   {endpoint}: 状态 {status}, 类型 {content_type}')
            
            if status == 200 and ('image' in content_type or 'jpeg' in content_type or 'png' in content_type):
                print(f'   ✅ 找到验证码端点: {endpoint}')
                working_endpoints.append(endpoint)
                
                # 尝试保存验证码图片
                try:
                    with open(f'captcha_test_{len(working_endpoints)}.jpg', 'wb') as f:
                        f.write(body.encode('latin1') if isinstance(body, str) else body)
                    print(f'   📷 验证码图片已保存')
                except:
                    pass
                    
        except Exception as e:
            print(f'   ❌ {endpoint}: {e}')
    
    return working_endpoints

def test_login_with_captcha():
    """测试带验证码的登录流程"""
    print('\n🔍 测试带验证码的登录流程...')
    
    # 获取初始会话
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    print(f'✅ JSESSIONID: {jsessionid[:20]}...')
    
    # 访问登录页面
    status, headers, body, new_cookies = make_request(
        TEST_CONFIG['sjtu_login_url'], 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    # 查找验证码字段
    captcha_inputs = [inp for inp in re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', body, re.IGNORECASE) if 'captcha' in inp.lower()]
    print(f'   验证码字段: {captcha_inputs}')
    
    # 尝试获取验证码图片
    captcha_urls = [
        'https://pe.sjtu.edu.cn/captcha',
        'https://pe.sjtu.edu.cn/captcha.jpg',
        'https://pe.sjtu.edu.cn/verify.jpg',
    ]
    
    captcha_image = None
    for url in captcha_urls:
        try:
            status, headers, body, _ = make_request(url, cookies=f'JSESSIONID={jsessionid}')
            if status == 200 and 'image' in headers.get('Content-Type', ''):
                print(f'   ✅ 找到验证码图片: {url}')
                captcha_image = body
                break
        except:
            continue
    
    if captcha_image:
        print(f'   📷 验证码图片大小: {len(captcha_image)} 字节')
        # 保存验证码图片
        try:
            with open('captcha.jpg', 'wb') as f:
                f.write(captcha_image.encode('latin1') if isinstance(captcha_image, str) else captcha_image)
            print(f'   💾 验证码图片已保存为 captcha.jpg')
        except Exception as e:
            print(f'   ❌ 保存验证码图片失败: {e}')
    
    return {
        'jsessionid': jsessionid,
        'captcha_inputs': captcha_inputs,
        'captcha_image': captcha_image
    }

def main():
    """主函数"""
    print('🚀 深入分析SJTU登录流程和验证码...\n')
    
    # 分析登录表单
    form_analysis = analyze_login_form()
    
    # 测试验证码端点
    captcha_endpoints = test_captcha_endpoints()
    
    # 测试带验证码的登录
    captcha_test = test_login_with_captcha()
    
    # 总结
    print('\n📊 分析总结:')
    print(f'✅ 登录表单字段: {form_analysis["inputs"]}')
    print(f'✅ 验证码字段: {captcha_test["captcha_inputs"]}')
    print(f'✅ 找到验证码端点: {len(captcha_endpoints)} 个')
    print(f'✅ 验证码图片: {"有" if captcha_test["captcha_image"] else "无"}')
    
    if captcha_endpoints:
        print(f'\n🎯 可用的验证码端点:')
        for endpoint in captcha_endpoints:
            print(f'   - {endpoint}')
    
    if captcha_test["captcha_image"]:
        print(f'\n💡 建议:')
        print(f'   1. 使用验证码端点获取图片')
        print(f'   2. 将图片显示给用户')
        print(f'   3. 用户输入验证码后提交登录')
        print(f'   4. 验证码字段名: {captcha_test["captcha_inputs"]}')

if __name__ == '__main__':
    main()

