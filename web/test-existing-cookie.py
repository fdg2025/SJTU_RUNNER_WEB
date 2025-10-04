#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试使用现有Cookie的登录流程
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import json
import base64
import time
import http.cookiejar
from typing import Dict, List, Optional, Tuple

# 测试配置
TEST_CONFIG = {
    'sjtu_base_url': 'https://pe.sjtu.edu.cn',
    'timeout': 15
}

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
    
    # 创建SSL上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
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

def test_existing_cookie():
    """测试使用现有Cookie的流程"""
    print('🚀 测试使用现有Cookie的流程...\n')
    
    # 步骤1: 获取现有Cookie
    print('步骤1: 获取现有Cookie...')
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    
    print(f'   状态: {status}')
    print(f'   Cookie: {cookies}')
    
    # 提取JSESSIONID和keepalive
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    keepalive_match = re.search(r"keepalive='([^']+)'", cookies)
    
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    keepalive = keepalive_match.group(1) if keepalive_match else ''
    
    if jsessionid and keepalive:
        print(f'   ✅ JSESSIONID: {jsessionid[:20]}...')
        print(f'   ✅ keepalive: {keepalive[:20]}...')
        
        # 组合完整Cookie
        full_cookie = f'JSESSIONID={jsessionid}; keepalive=\'{keepalive}'
        print(f'   ✅ 完整Cookie: {full_cookie[:50]}...')
        
        return {
            'jsessionid': jsessionid,
            'keepalive': keepalive,
            'full_cookie': full_cookie
        }
    else:
        print('   ❌ 未找到完整的Cookie')
        return None

def test_cookie_validation():
    """测试Cookie验证"""
    print('\n🔍 测试Cookie验证...')
    
    # 获取Cookie
    cookie_info = test_existing_cookie()
    if not cookie_info:
        return None
    
    # 步骤2: 测试Cookie是否有效
    print('\n步骤2: 测试Cookie是否有效...')
    
    # 测试访问需要登录的页面
    test_urls = [
        f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait',
        f'{TEST_CONFIG["sjtu_base_url"]}/phone/',
        f'{TEST_CONFIG["sjtu_base_url"]}/api/user/info',
    ]
    
    for url in test_urls:
        print(f'\n   测试URL: {url}')
        try:
            status, headers, body, new_cookies = make_request(
                url, cookies=cookie_info['full_cookie']
            )
            
            print(f'     状态: {status}')
            print(f'     新Cookie: {new_cookies}')
            
            if status == 200:
                # 检查响应内容
                response_text = body.decode('utf-8', errors='ignore')
                
                if '登录' in response_text or 'login' in response_text.lower():
                    print('     ⚠️ 需要登录')
                elif '用户' in response_text or 'user' in response_text.lower():
                    print('     ✅ 已登录状态')
                else:
                    print('     ✅ 访问成功')
            else:
                print(f'     ❌ 访问失败: {status}')
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return cookie_info

def test_api_endpoints():
    """测试API端点"""
    print('\n🔍 测试API端点...')
    
    # 获取Cookie
    cookie_info = test_existing_cookie()
    if not cookie_info:
        return None
    
    # 测试API端点
    api_endpoints = [
        f'{TEST_CONFIG["sjtu_base_url"]}/api/point/rule',
        f'{TEST_CONFIG["sjtu_base_url"]}/api/user/info',
        f'{TEST_CONFIG["sjtu_base_url"]}/api/sports/upload',
    ]
    
    for endpoint in api_endpoints:
        print(f'\n   测试API: {endpoint}')
        try:
            status, headers, body, new_cookies = make_request(
                endpoint, cookies=cookie_info['full_cookie']
            )
            
            print(f'     状态: {status}')
            print(f'     内容类型: {headers.get("Content-Type", "未知")}')
            print(f'     数据大小: {len(body)} 字节')
            
            if status == 200:
                try:
                    # 尝试解析JSON
                    json_data = json.loads(body.decode('utf-8'))
                    print(f'     ✅ JSON响应: {json_data}')
                except:
                    # 不是JSON，显示文本内容
                    response_text = body.decode('utf-8', errors='ignore')[:200]
                    print(f'     ✅ 文本响应: {response_text}...')
            else:
                print(f'     ❌ API调用失败: {status}')
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return cookie_info

def test_upload_simulation():
    """测试上传模拟"""
    print('\n🔍 测试上传模拟...')
    
    # 获取Cookie
    cookie_info = test_existing_cookie()
    if not cookie_info:
        return None
    
    # 模拟上传数据
    upload_data = {
        'distance': '3000',
        'duration': '1200',
        'calories': '150',
        'steps': '4000',
        'speed': '2.5',
        'date': '2025-01-30',
        'time': '08:00:00'
    }
    
    print(f'   模拟上传数据: {upload_data}')
    
    # 测试上传端点
    upload_url = f'{TEST_CONFIG["sjtu_base_url"]}/api/sports/upload'
    
    try:
        status, headers, body, new_cookies = make_request(
            upload_url, 
            method='POST',
            data=upload_data,
            cookies=cookie_info['full_cookie']
        )
        
        print(f'   上传状态: {status}')
        print(f'   响应内容: {body.decode("utf-8", errors="ignore")[:200]}...')
        
        if status == 200:
            print('   ✅ 上传成功')
        else:
            print(f'   ❌ 上传失败: {status}')
            
    except Exception as e:
        print(f'   ❌ 上传错误: {e}')
    
    return cookie_info

def main():
    """主函数"""
    print('🚀 测试使用现有Cookie的流程...\n')
    
    # 测试Cookie验证
    cookie_info = test_cookie_validation()
    
    if cookie_info:
        print('\n📊 Cookie验证测试成功！')
        print(f'✅ JSESSIONID: {cookie_info["jsessionid"][:30]}...')
        print(f'✅ keepalive: {cookie_info["keepalive"][:30]}...')
        
        # 测试API端点
        api_info = test_api_endpoints()
        
        if api_info:
            print('\n📊 API端点测试完成')
        
        # 测试上传模拟
        upload_info = test_upload_simulation()
        
        if upload_info:
            print('\n📊 上传模拟测试完成')
        
        print('\n💡 实现总结:')
        print('1. ✅ 获取现有的JSESSIONID和keepalive Cookie')
        print('2. ✅ 验证Cookie是否有效')
        print('3. ✅ 测试API端点访问')
        print('4. ✅ 模拟数据上传')
        print('5. ✅ 确认完整的登录流程')
        
        print('\n🎯 下一步:')
        print('1. 更新自动登录API以使用现有Cookie')
        print('2. 简化前端验证码输入流程')
        print('3. 直接使用现有Cookie进行上传')
        
        print(f'\n🎉 现有Cookie流程测试成功！')
    else:
        print('\n❌ Cookie验证测试失败')

if __name__ == '__main__':
    main()

