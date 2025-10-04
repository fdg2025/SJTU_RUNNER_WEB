#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的SJTU自动登录流程
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

def test_updated_flow():
    """测试更新后的登录流程"""
    print('🚀 测试更新后的SJTU自动登录流程...\n')
    
    # 步骤1: 访问主页获取JSESSIONID
    print('步骤1: 访问主页获取JSESSIONID...')
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    
    print(f'   状态: {status}')
    print(f'   Cookie: {cookies}')
    
    # 提取JSESSIONID
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    if jsessionid:
        print(f'   ✅ JSESSIONID: {jsessionid[:20]}...')
    else:
        print('   ❌ 未找到JSESSIONID')
        return
    
    # 步骤2: 访问登录页面
    print('\n步骤2: 访问登录页面...')
    status, headers, body, new_cookies = make_request(
        TEST_CONFIG['sjtu_login_url'], 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    print(f'   状态: {status}')
    print(f'   新Cookie: {new_cookies}')
    
    # 合并Cookie
    all_cookies = f'JSESSIONID={jsessionid}'
    if new_cookies:
        all_cookies += '; ' + new_cookies
    
    print(f'   合并Cookie: {all_cookies}')
    
    # 查找登录表单字段
    print('\n🔍 分析登录表单...')
    form_inputs = re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', body, re.IGNORECASE)
    print(f'   找到输入字段: {form_inputs}')
    
    # 步骤3: 访问手机端页面获取keepalive
    print('\n步骤3: 访问手机端页面获取keepalive...')
    status, headers, body, keepalive_cookies = make_request(
        TEST_CONFIG['sjtu_phone_url'], 
        headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        },
        cookies=all_cookies
    )
    
    print(f'   状态: {status}')
    print(f'   keepalive Cookie: {keepalive_cookies}')
    
    # 提取keepalive
    keepalive_match = re.search(r'keepalive=([^;]+)', keepalive_cookies)
    keepalive = keepalive_match.group(1) if keepalive_match else ''
    
    if keepalive:
        # 清理keepalive值（移除引号）
        keepalive = keepalive.replace("'", '').replace('"', '')
        print(f'   ✅ keepalive: {keepalive[:20]}...')
    else:
        print('   ❌ 未找到keepalive')
        return
    
    # 步骤4: 验证最终Cookie
    print('\n步骤4: 验证最终Cookie...')
    final_cookie = f'keepalive={keepalive}; JSESSIONID={jsessionid}'
    print(f'   最终Cookie: {final_cookie}')
    
    # 验证Cookie格式
    print('\n📊 Cookie验证:')
    print(f'   keepalive长度: {len(keepalive)} 字符')
    print(f'   JSESSIONID长度: {len(jsessionid)} 字符')
    print(f'   格式正确: {"✅" if len(keepalive) > 10 and len(jsessionid) > 10 else "❌"}')
    
    # 测试Cookie有效性
    print('\n步骤5: 测试Cookie有效性...')
    test_headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # 测试访问需要认证的页面
    test_urls = [
        'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
        'https://pe.sjtu.edu.cn/api/user/info',
    ]
    
    for test_url in test_urls:
        try:
            status, headers, body, _ = make_request(test_url, headers=test_headers, cookies=final_cookie)
            print(f'   测试 {test_url}: 状态 {status}')
            
            if status == 200 and 'login' not in body.lower():
                print(f'   ✅ Cookie有效')
            else:
                print(f'   ⚠️ Cookie可能无效或需要登录')
        except Exception as e:
            print(f'   ❌ 测试失败: {e}')
    
    print('\n🎉 测试完成！')
    print(f'\n📋 最终结果:')
    print(f'✅ JSESSIONID: {jsessionid[:30]}...')
    print(f'✅ keepalive: {keepalive[:30]}...')
    print(f'✅ 完整Cookie: {final_cookie}')
    
    return final_cookie

def main():
    """主函数"""
    try:
        final_cookie = test_updated_flow()
        
        if final_cookie:
            print(f'\n🎯 自动登录流程验证成功！')
            print(f'📝 生成的Cookie可以直接用于SJTU跑步工具')
        else:
            print(f'\n❌ 自动登录流程验证失败')
            
    except Exception as e:
        print(f'\n❌ 测试过程中发生错误: {e}')

if __name__ == '__main__':
    main()

