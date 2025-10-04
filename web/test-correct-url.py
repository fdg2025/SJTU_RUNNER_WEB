#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试正确的JAccount URL
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

def test_captcha_urls():
    """测试验证码URL"""
    print('🔍 测试验证码URL...')
    
    # 获取初始会话
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    print(f'✅ JSESSIONID: {jsessionid[:20]}...')
    
    # 访问登录页面
    status, headers, body, _ = make_request(
        f'{TEST_CONFIG["sjtu_base_url"]}/login', 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    # 解析HTML内容
    html_content = body.decode('utf-8', errors='ignore')
    
    # 查找验证码UUID
    uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
    captcha_uuid = uuid_match.group(1) if uuid_match else ''
    
    if captcha_uuid:
        print(f'✅ 找到验证码UUID: {captcha_uuid}')
    else:
        print('❌ 未找到验证码UUID')
        return
    
    # 测试不同的验证码URL
    captcha_urls = [
        f'https://pe.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={int(time.time() * 1000)}',
        f'https://pe.sjtu.edu.cn/captcha?uuid={captcha_uuid}&t={int(time.time() * 1000)}',
        f'https://pe.sjtu.edu.cn/image/captcha.png?uuid={captcha_uuid}&t={int(time.time() * 1000)}',
        f'https://pe.sjtu.edu.cn/jaccount/image/captcha.png?uuid={captcha_uuid}&t={int(time.time() * 1000)}',
    ]
    
    for url in captcha_urls:
        print(f'\n测试URL: {url}')
        try:
            status, headers, image_data, _ = make_request(
                url,
                headers={'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'},
                cookies=f'JSESSIONID={jsessionid}'
            )
            
            print(f'   状态: {status}')
            print(f'   内容类型: {headers.get("Content-Type", "未知")}')
            print(f'   数据大小: {len(image_data)} 字节')
            
            if status == 200 and len(image_data) > 0:
                # 检查是否为图片
                if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                    print('   ✅ 成功获取验证码图片')
                    
                    # 保存验证码图片
                    filename = f'captcha_test_{len(captcha_urls)}.jpg'
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    print(f'   💾 验证码图片已保存为 {filename}')
                    
                    return url
                else:
                    print('   ❌ 返回的不是图片数据')
                    print(f'   内容预览: {image_data[:100]}')
            else:
                print('   ❌ 获取失败')
                
        except Exception as e:
            print(f'   ❌ 错误: {e}')
    
    return None

def test_login_urls():
    """测试登录URL"""
    print('\n🔍 测试登录URL...')
    
    # 获取初始会话
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    # 访问登录页面
    status, headers, body, _ = make_request(
        f'{TEST_CONFIG["sjtu_base_url"]}/login', 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    # 解析HTML内容
    html_content = body.decode('utf-8', errors='ignore')
    
    # 查找验证码UUID
    uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
    captcha_uuid = uuid_match.group(1) if uuid_match else ''
    
    # 测试不同的登录URL
    login_urls = [
        f'https://pe.sjtu.edu.cn/jaccount/login',
        f'https://pe.sjtu.edu.cn/login',
        f'https://pe.sjtu.edu.cn/jaccount/',
    ]
    
    for url in login_urls:
        print(f'\n测试登录URL: {url}')
        try:
            # 准备登录数据
            login_data = {
                'user': 'test_user',
                'pass': 'test_password',
                'captcha': 'test_captcha',
                'uuid': captcha_uuid,
                'lt': 'p'
            }
            
            status, headers, body, _ = make_request(
                url,
                method='POST',
                data=login_data,
                cookies=f'JSESSIONID={jsessionid}'
            )
            
            print(f'   状态: {status}')
            print(f'   重定向: {headers.get("Location", "无")}')
            
            if status == 200:
                response_text = body.decode('utf-8', errors='ignore')
                if '验证码' in response_text or 'captcha' in response_text.lower():
                    print('   ⚠️ 响应包含验证码相关错误')
                elif '用户名' in response_text or '密码' in response_text:
                    print('   ⚠️ 响应包含用户名/密码相关错误')
                else:
                    print('   ✅ 可能成功')
            
        except Exception as e:
            print(f'   ❌ 错误: {e}')

def main():
    """主函数"""
    print('🚀 测试正确的JAccount URL...\n')
    
    # 测试验证码URL
    captcha_url = test_captcha_urls()
    
    # 测试登录URL
    test_login_urls()
    
    if captcha_url:
        print(f'\n🎯 找到可用的验证码URL: {captcha_url}')
    else:
        print('\n❌ 未找到可用的验证码URL')

if __name__ == '__main__':
    main()

