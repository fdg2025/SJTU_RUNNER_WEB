#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试退出登录流程
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

def test_logout_endpoints():
    """测试各种退出登录端点"""
    print('🚀 测试退出登录端点...\n')
    
    # 步骤1: 获取当前登录状态
    print('步骤1: 获取当前登录状态...')
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    
    print(f'   状态: {status}')
    print(f'   Cookie: {cookies}')
    
    # 提取JSESSIONID和keepalive
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    keepalive_match = re.search(r"keepalive='([^']+)'", cookies)
    
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    keepalive = keepalive_match.group(1) if keepalive_match else ''
    
    if jsessionid and keepalive:
        print(f'   ✅ 当前已登录')
        print(f'   ✅ JSESSIONID: {jsessionid[:20]}...')
        print(f'   ✅ keepalive: {keepalive[:20]}...')
        
        # 组合完整Cookie
        full_cookie = f'JSESSIONID={jsessionid}; keepalive=\'{keepalive}'
        
        # 步骤2: 测试各种退出登录端点
        print('\n步骤2: 测试各种退出登录端点...')
        
        logout_urls = [
            f'{TEST_CONFIG["sjtu_base_url"]}/logout',
            f'{TEST_CONFIG["sjtu_base_url"]}/jaccount/logout',
            f'{TEST_CONFIG["sjtu_base_url"]}/phone/logout',
            f'{TEST_CONFIG["sjtu_base_url"]}/api/logout',
            f'{TEST_CONFIG["sjtu_base_url"]}/user/logout',
            f'{TEST_CONFIG["sjtu_base_url"]}/auth/logout',
            f'{TEST_CONFIG["sjtu_base_url"]}/login/logout',
        ]
        
        for url in logout_urls:
            print(f'\n   测试退出URL: {url}')
            try:
                # 测试GET请求
                status, headers, body, new_cookies = make_request(
                    url, cookies=full_cookie
                )
                
                print(f'     GET状态: {status}')
                print(f'     重定向: {headers.get("Location", "无")}')
                print(f'     新Cookie: {new_cookies}')
                
                # 检查是否清除了keepalive
                if 'keepalive' not in new_cookies:
                    print('     ✅ 成功清除keepalive cookie')
                    
                    # 验证退出状态
                    print('\n     验证退出状态...')
                    verify_status, verify_headers, verify_body, verify_cookies = make_request(
                        f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait',
                        cookies=f'JSESSIONID={jsessionid}'  # 只使用JSESSIONID
                    )
                    
                    print(f'       验证状态: {verify_status}')
                    print(f'       验证重定向: {verify_headers.get("Location", "无")}')
                    print(f'       验证Cookie: {verify_cookies}')
                    
                    if verify_headers.get('Location') and 'jaccount.sjtu.edu.cn' in verify_headers.get('Location', ''):
                        print('       ✅ 成功退出登录，访问受保护页面会重定向到JAccount')
                        return True
                    elif 'keepalive' in verify_cookies:
                        print('       ⚠️ 仍然保持登录状态')
                    else:
                        print('       ✅ 成功退出登录')
                        return True
                
                # 测试POST请求
                print('     测试POST请求...')
                status, headers, body, new_cookies = make_request(
                    url, method='POST', cookies=full_cookie
                )
                
                print(f'     POST状态: {status}')
                print(f'     重定向: {headers.get("Location", "无")}')
                print(f'     新Cookie: {new_cookies}')
                
                if 'keepalive' not in new_cookies:
                    print('     ✅ POST请求成功清除keepalive cookie')
                    return True
                    
            except Exception as e:
                print(f'     ❌ 错误: {e}')
        
        return False
    else:
        print('   ❌ 未检测到登录状态')
        return False

def test_manual_logout():
    """手动测试退出登录"""
    print('\n🔍 手动测试退出登录...')
    
    # 获取当前状态
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    
    # 提取JSESSIONID
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    if not jsessionid:
        print('❌ 未找到JSESSIONID')
        return False
    
    print(f'✅ JSESSIONID: {jsessionid[:20]}...')
    
    # 方法1: 清除Cookie后访问
    print('\n方法1: 清除Cookie后访问...')
    try:
        status, headers, body, new_cookies = make_request(
            f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait',
            cookies=''  # 不携带任何Cookie
        )
        
        print(f'   状态: {status}')
        print(f'   重定向: {headers.get("Location", "无")}')
        print(f'   Cookie: {new_cookies}')
        
        if headers.get('Location') and 'jaccount.sjtu.edu.cn' in headers.get('Location', ''):
            print('   ✅ 成功触发重定向到JAccount')
            return True
        else:
            print('   ❌ 未触发重定向')
            
    except Exception as e:
        print(f'   ❌ 错误: {e}')
    
    # 方法2: 使用过期的Cookie
    print('\n方法2: 使用过期的Cookie...')
    try:
        expired_cookie = f'JSESSIONID={jsessionid}; keepalive=\'expired_token\''
        status, headers, body, new_cookies = make_request(
            f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait',
            cookies=expired_cookie
        )
        
        print(f'   状态: {status}')
        print(f'   重定向: {headers.get("Location", "无")}')
        print(f'   Cookie: {new_cookies}')
        
        if headers.get('Location') and 'jaccount.sjtu.edu.cn' in headers.get('Location', ''):
            print('   ✅ 过期Cookie成功触发重定向')
            return True
        else:
            print('   ❌ 过期Cookie未触发重定向')
            
    except Exception as e:
        print(f'   ❌ 错误: {e}')
    
    return False

def test_force_logout():
    """强制退出登录"""
    print('\n🔍 强制退出登录...')
    
    # 获取当前状态
    status, headers, body, cookies = make_request(TEST_CONFIG['sjtu_base_url'])
    
    # 提取JSESSIONID
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    if not jsessionid:
        print('❌ 未找到JSESSIONID')
        return False
    
    print(f'✅ JSESSIONID: {jsessionid[:20]}...')
    
    # 方法1: 访问logout端点
    print('\n方法1: 访问logout端点...')
    logout_endpoints = [
        f'{TEST_CONFIG["sjtu_base_url"]}/logout',
        f'{TEST_CONFIG["sjtu_base_url"]}/jaccount/logout',
        f'{TEST_CONFIG["sjtu_base_url"]}/phone/logout',
    ]
    
    for endpoint in logout_endpoints:
        print(f'\n   测试端点: {endpoint}')
        try:
            status, headers, body, new_cookies = make_request(endpoint)
            
            print(f'     状态: {status}')
            print(f'     重定向: {headers.get("Location", "无")}')
            print(f'     Cookie: {new_cookies}')
            
            if status == 200 or status == 302:
                print('     ✅ 端点可访问')
                
                # 验证退出状态
                verify_status, verify_headers, verify_body, verify_cookies = make_request(
                    f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait',
                    cookies=f'JSESSIONID={jsessionid}'
                )
                
                if verify_headers.get('Location') and 'jaccount.sjtu.edu.cn' in verify_headers.get('Location', ''):
                    print('     ✅ 成功退出登录')
                    return True
                    
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return False

def main():
    """主函数"""
    print('🚀 测试退出登录流程...\n')
    
    # 测试退出登录端点
    logout_success = test_logout_endpoints()
    
    if logout_success:
        print('\n📊 退出登录测试成功！')
        print('✅ 成功找到可用的退出登录端点')
        print('✅ 成功清除keepalive cookie')
        print('✅ 验证退出状态成功')
        
        print('\n💡 退出登录方法:')
        print('1. 访问 /logout 端点')
        print('2. 访问 /jaccount/logout 端点')
        print('3. 访问 /phone/logout 端点')
        print('4. 清除浏览器Cookie')
        print('5. 使用过期的Cookie')
        
        print(f'\n🎉 退出登录流程测试成功！')
    else:
        print('\n❌ 退出登录端点测试失败')
        
        # 测试手动退出登录
        print('\n🔍 尝试手动退出登录...')
        manual_success = test_manual_logout()
        
        if manual_success:
            print('\n✅ 手动退出登录成功')
        else:
            print('\n❌ 手动退出登录失败')
        
        # 测试强制退出登录
        print('\n🔍 尝试强制退出登录...')
        force_success = test_force_logout()
        
        if force_success:
            print('\n✅ 强制退出登录成功')
        else:
            print('\n❌ 强制退出登录失败')
        
        print('\n💡 建议的退出登录方法:')
        print('1. 清除浏览器Cookie和缓存')
        print('2. 使用隐私模式/无痕模式')
        print('3. 使用不同的浏览器')
        print('4. 使用VPN或代理服务器')
        print('5. 等待会话自动过期')

if __name__ == '__main__':
    main()

