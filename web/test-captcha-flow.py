#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SJTU验证码获取流程
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
            response_body = response.read()  # 直接读取字节数据
            
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

def test_captcha_image():
    """测试验证码图片获取"""
    print('🔍 测试验证码图片获取...')
    
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
    
    # 查找验证码图片
    captcha_patterns = [
        r'<img[^>]*src=["\']([^"\']*captcha[^"\']*)["\'][^>]*>',
        r'<img[^>]*src=["\']([^"\']*image[^"\']*)["\'][^>]*>',
        r'src=["\']([^"\']*captcha[^"\']*)["\']',
        r'src=["\']([^"\']*image[^"\']*)["\']',
    ]
    
    captcha_url = None
    for pattern in captcha_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            captcha_url = matches[0]
            print(f'   ✅ 找到验证码URL: {captcha_url}')
            break
    
    if not captcha_url:
        print('   ❌ 未找到验证码图片URL')
        return None
    
    # 处理相对URL
    if captcha_url.startswith('/'):
        captcha_url = TEST_CONFIG['sjtu_base_url'] + captcha_url
    elif not captcha_url.startswith('http'):
        captcha_url = TEST_CONFIG['sjtu_base_url'] + '/' + captcha_url
    
    print(f'   🔗 完整验证码URL: {captcha_url}')
    
    # 步骤3: 获取验证码图片
    try:
        status, headers, image_data, _ = make_request(
            captcha_url,
            cookies=f'JSESSIONID={jsessionid}'
        )
        
        print(f'   ✅ 验证码图片状态: {status}')
        print(f'   📷 图片大小: {len(image_data)} 字节')
        print(f'   📋 内容类型: {headers.get("Content-Type", "未知")}')
        
        if status == 200 and len(image_data) > 0:
            # 保存验证码图片
            with open('captcha.jpg', 'wb') as f:
                f.write(image_data)
            print(f'   💾 验证码图片已保存为 captcha.jpg')
            
            # 转换为base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            print(f'   🔤 Base64长度: {len(base64_image)} 字符')
            
            return {
                'url': captcha_url,
                'data': image_data,
                'base64': base64_image,
                'jsessionid': jsessionid
            }
        else:
            print(f'   ❌ 验证码图片获取失败')
            return None
            
    except Exception as e:
        print(f'   ❌ 获取验证码图片失败: {e}')
        return None

def test_login_form_fields():
    """测试登录表单字段"""
    print('\n🔍 测试登录表单字段...')
    
    # 获取登录页面
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    status, headers, body, _ = make_request(
        TEST_CONFIG['sjtu_login_url'], 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    html_content = body.decode('utf-8', errors='ignore')
    
    # 查找表单字段
    form_pattern = r'<form[^>]*>(.*?)</form>'
    form_match = re.search(form_pattern, html_content, re.IGNORECASE | re.DOTALL)
    
    if form_match:
        form_content = form_match.group(1)
        print('   ✅ 找到登录表单')
        
        # 查找所有input字段
        input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
        inputs = re.findall(input_pattern, form_content, re.IGNORECASE)
        print(f'   📋 输入字段: {inputs}')
        
        # 查找表单action
        action_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', form_content, re.IGNORECASE)
        action = action_match.group(1) if action_match else '/login'
        print(f'   🎯 表单action: {action}')
        
        # 查找隐藏字段
        hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*>'
        hidden_inputs = re.findall(hidden_pattern, form_content, re.IGNORECASE)
        print(f'   🔒 隐藏字段数量: {len(hidden_inputs)}')
        
        return {
            'inputs': inputs,
            'action': action,
            'hidden_count': len(hidden_inputs),
            'jsessionid': jsessionid
        }
    else:
        print('   ❌ 未找到登录表单')
        return None

def test_login_submission():
    """测试登录提交"""
    print('\n🔍 测试登录提交...')
    
    # 获取表单信息
    form_info = test_login_form_fields()
    if not form_info:
        return None
    
    jsessionid = form_info['jsessionid']
    
    # 准备登录数据
    login_data = {
        'user': 'test_user',
        'pass': 'test_password',
        'captcha': 'test_captcha'
    }
    
    print(f'   📤 提交数据: {login_data}')
    
    # 提交登录
    try:
        status, headers, body, new_cookies = make_request(
            TEST_CONFIG['sjtu_login_url'],
            method='POST',
            data=login_data,
            cookies=f'JSESSIONID={jsessionid}'
        )
        
        print(f'   ✅ 登录提交状态: {status}')
        print(f'   📍 重定向位置: {headers.get("location", "无")}')
        print(f'   🍪 新Cookie: {new_cookies}')
        
        # 分析响应
        response_text = body.decode('utf-8', errors='ignore')
        
        if '验证码' in response_text or 'captcha' in response_text.lower():
            print('   ⚠️ 响应包含验证码相关错误')
        
        if '用户名' in response_text or '密码' in response_text:
            print('   ⚠️ 响应包含用户名/密码相关错误')
        
        if '成功' in response_text or 'success' in response_text.lower():
            print('   ✅ 登录可能成功')
        
        return {
            'status': status,
            'location': headers.get('location'),
            'cookies': new_cookies,
            'response': response_text[:500]  # 只取前500字符
        }
        
    except Exception as e:
        print(f'   ❌ 登录提交失败: {e}')
        return None

def main():
    """主函数"""
    print('🚀 测试SJTU验证码流程...\n')
    
    # 测试验证码图片获取
    captcha_info = test_captcha_image()
    
    # 测试登录表单字段
    form_info = test_login_form_fields()
    
    # 测试登录提交
    login_result = test_login_submission()
    
    # 总结
    print('\n📊 测试总结:')
    print(f'✅ 验证码图片: {"获取成功" if captcha_info else "获取失败"}')
    print(f'✅ 表单字段: {form_info["inputs"] if form_info else "未找到"}')
    print(f'✅ 登录提交: {"成功" if login_result else "失败"}')
    
    if captcha_info:
        print(f'\n🎯 验证码信息:')
        print(f'   URL: {captcha_info["url"]}')
        print(f'   大小: {len(captcha_info["data"])} 字节')
        print(f'   Base64: {captcha_info["base64"][:50]}...')
        
        print(f'\n💡 实现建议:')
        print(f'   1. 使用验证码URL获取图片')
        print(f'   2. 将Base64图片显示给用户')
        print(f'   3. 用户输入验证码后提交登录')
        print(f'   4. 需要保持JSESSIONID会话')

if __name__ == '__main__':
    main()

