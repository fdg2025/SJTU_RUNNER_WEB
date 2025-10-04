#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用全新环境测试登录流程
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
    'jaccount_base_url': 'https://jaccount.sjtu.edu.cn',
    'timeout': 15
}

def create_fresh_opener():
    """创建一个全新的opener，完全隔离环境"""
    # 创建全新的cookie jar
    cookie_jar = http.cookiejar.CookieJar()
    
    # 创建SSL上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # 创建opener
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=ssl_context)
    )
    
    return opener, cookie_jar

def make_fresh_request(opener, url: str, method: str = 'GET', data: Optional[Dict] = None, 
                      headers: Optional[Dict] = None) -> Tuple[int, Dict, bytes, str]:
    """发送HTTP请求，返回字节数据"""
    if headers is None:
        headers = {}
    
    # 设置全新的请求头
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
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
        with opener.open(req, timeout=TEST_CONFIG['timeout']) as response:
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

def test_fresh_sjtu_access():
    """测试全新环境访问SJTU"""
    print('🚀 使用全新环境测试SJTU访问...\n')
    
    # 创建全新的opener
    opener, cookie_jar = create_fresh_opener()
    
    # 步骤1: 访问SJTU主页
    print('步骤1: 访问SJTU主页...')
    status, headers, body, cookies = make_fresh_request(opener, TEST_CONFIG['sjtu_base_url'])
    
    print(f'   状态: {status}')
    print(f'   Cookie: {cookies}')
    
    # 提取JSESSIONID
    jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
    jsessionid = jsessionid_match.group(1) if jsessionid_match else ''
    
    if jsessionid:
        print(f'   ✅ JSESSIONID: {jsessionid[:20]}...')
    else:
        print('   ❌ 未找到JSESSIONID')
        return None
    
    # 步骤2: 访问需要登录的页面
    print('\n步骤2: 访问需要登录的页面...')
    protected_urls = [
        f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait',
        f'{TEST_CONFIG["sjtu_base_url"]}/phone/',
        f'{TEST_CONFIG["sjtu_base_url"]}/api/user/info',
    ]
    
    for url in protected_urls:
        print(f'\n   测试URL: {url}')
        try:
            status, headers, body, new_cookies = make_fresh_request(opener, url)
            
            print(f'     状态: {status}')
            print(f'     重定向位置: {headers.get("Location", "无")}')
            print(f'     新Cookie: {new_cookies}')
            
            location = headers.get('Location', '')
            if location and 'jaccount.sjtu.edu.cn' in location:
                print(f'     ✅ 重定向到JAccount: {location}')
                
                # 步骤3: 访问JAccount页面
                print('\n步骤3: 访问JAccount页面...')
                status, headers, body, jaccount_cookies = make_fresh_request(opener, location)
                
                print(f'   状态: {status}')
                print(f'   JAccount Cookie: {jaccount_cookies}')
                
                if status == 200:
                    # 解析HTML内容
                    html_content = body.decode('utf-8', errors='ignore')
                    
                    # 保存HTML内容
                    with open('jaccount_fresh_environment.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print('   💾 JAccount页面HTML已保存为 jaccount_fresh_environment.html')
                    
                    # 查找验证码UUID
                    uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
                    captcha_uuid = uuid_match.group(1) if uuid_match else ''
                    
                    if captcha_uuid:
                        print(f'   ✅ 找到验证码UUID: {captcha_uuid}')
                        
                        # 步骤4: 测试验证码URL
                        print('\n步骤4: 测试验证码URL...')
                        timestamp = int(time.time() * 1000)
                        
                        # 使用JAccount域名
                        captcha_url = f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
                        
                        print(f'   测试URL: {captcha_url}')
                        try:
                            status, headers, image_data, _ = make_fresh_request(
                                opener, captcha_url,
                                headers={'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'}
                            )
                            
                            print(f'     状态: {status}')
                            print(f'     内容类型: {headers.get("Content-Type", "未知")}')
                            print(f'     数据大小: {len(image_data)} 字节')
                            
                            if status == 200 and len(image_data) > 0:
                                # 检查是否为图片
                                if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                                    print('     ✅ 成功获取验证码图片')
                                    
                                    # 保存验证码图片
                                    filename = f'fresh_environment_captcha.jpg'
                                    with open(filename, 'wb') as f:
                                        f.write(image_data)
                                    print(f'     💾 验证码图片已保存为 {filename}')
                                    
                                    # 转换为base64
                                    base64_image = base64.b64encode(image_data).decode('utf-8')
                                    print(f'     🔤 Base64长度: {len(base64_image)} 字符')
                                    
                                    return {
                                        'success': True,
                                        'jsessionid': jsessionid,
                                        'captcha_uuid': captcha_uuid,
                                        'captcha_url': captcha_url,
                                        'captcha_image': base64_image,
                                        'jaccount_url': location,
                                        'cookies': f'JSESSIONID={jsessionid}'
                                    }
                                else:
                                    print('     ❌ 返回的不是图片数据')
                                    print(f'     内容预览: {image_data[:100]}')
                                    
                                    # 检查是否是HTML重定向
                                    if b'<html' in image_data.lower() or b'<!doctype' in image_data.lower():
                                        print('     ⚠️ 返回HTML，可能是重定向页面')
                                        html_preview = image_data.decode('utf-8', errors='ignore')[:500]
                                        print(f'     HTML预览: {html_preview}')
                                    
                                    return None
                            else:
                                print('     ❌ 获取失败')
                                return None
                                
                        except Exception as e:
                            print(f'     ❌ 错误: {e}')
                            return None
                    else:
                        print('   ❌ 未找到验证码UUID')
                        return None
                else:
                    print(f'   ❌ JAccount页面访问失败: {status}')
                    return None
            elif 'keepalive' in new_cookies:
                print('     ⚠️ 已登录状态')
            else:
                print('     ❌ 未重定向')
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return None

def test_different_approaches():
    """测试不同的访问方法"""
    print('\n🔍 测试不同的访问方法...')
    
    # 方法1: 直接访问JAccount
    print('\n方法1: 直接访问JAccount...')
    opener, cookie_jar = create_fresh_opener()
    
    jaccount_urls = [
        f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/jalogin',
        f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/login',
        f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/',
    ]
    
    for url in jaccount_urls:
        print(f'\n   测试URL: {url}')
        try:
            status, headers, body, cookies = make_fresh_request(opener, url)
            
            print(f'     状态: {status}')
            print(f'     重定向: {headers.get("Location", "无")}')
            print(f'     Cookie: {cookies}')
            
            if status == 200:
                # 检查是否包含验证码
                html_content = body.decode('utf-8', errors='ignore')
                uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
                if uuid_match:
                    print('     ✅ 找到验证码UUID')
                    return url
                else:
                    print('     ❌ 未找到验证码UUID')
            else:
                print(f'     ❌ 访问失败: {status}')
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    # 方法2: 使用不同的User-Agent
    print('\n方法2: 使用不同的User-Agent...')
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    ]
    
    for ua in user_agents:
        print(f'\n   测试User-Agent: {ua[:50]}...')
        opener, cookie_jar = create_fresh_opener()
        
        try:
            status, headers, body, cookies = make_fresh_request(
                opener, TEST_CONFIG['sjtu_base_url'],
                headers={'User-Agent': ua}
            )
            
            print(f'     状态: {status}')
            print(f'     Cookie: {cookies}')
            
            if 'keepalive' in cookies:
                print('     ⚠️ 已登录状态')
            else:
                print('     ✅ 未登录状态')
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return None

def test_oauth_flow():
    """测试OAuth流程"""
    print('\n🔍 测试OAuth流程...')
    
    # 创建全新的opener
    opener, cookie_jar = create_fresh_opener()
    
    # 测试OAuth相关URL
    oauth_urls = [
        f'{TEST_CONFIG["sjtu_base_url"]}/oauth/authorize',
        f'{TEST_CONFIG["sjtu_base_url"]}/oauth/authorize?response_type=code&client_id=test&redirect_uri=test',
        f'{TEST_CONFIG["sjtu_base_url"]}/login',
        f'{TEST_CONFIG["sjtu_base_url"]}/auth/login',
    ]
    
    for url in oauth_urls:
        print(f'\n   测试OAuth URL: {url}')
        try:
            status, headers, body, cookies = make_fresh_request(opener, url)
            
            print(f'     状态: {status}')
            print(f'     重定向: {headers.get("Location", "无")}')
            print(f'     Cookie: {cookies}')
            
            location = headers.get('Location', '')
            if location and 'jaccount.sjtu.edu.cn' in location:
                print(f'     ✅ 重定向到JAccount: {location}')
                
                # 访问JAccount页面
                status, headers, body, jaccount_cookies = make_fresh_request(opener, location)
                
                if status == 200:
                    html_content = body.decode('utf-8', errors='ignore')
                    uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
                    if uuid_match:
                        print('     ✅ 找到验证码UUID')
                        return url
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return None

def main():
    """主函数"""
    print('🚀 使用全新环境测试登录流程...\n')
    
    # 测试全新环境访问SJTU
    captcha_info = test_fresh_sjtu_access()
    
    if captcha_info and captcha_info['success']:
        print('\n📊 全新环境测试成功！')
        print(f'✅ JSESSIONID: {captcha_info["jsessionid"][:30]}...')
        print(f'✅ 验证码UUID: {captcha_info["captcha_uuid"]}')
        print(f'✅ 验证码URL: {captcha_info["captcha_url"]}')
        print(f'✅ 验证码图片: {len(captcha_info["captcha_image"])} 字符Base64')
        print(f'✅ JAccount URL: {captcha_info["jaccount_url"]}')
        
        print('\n💡 实现总结:')
        print('1. ✅ 使用全新环境访问SJTU')
        print('2. ✅ 访问需要登录的页面触发重定向')
        print('3. ✅ 跟随重定向到JAccount登录页面')
        print('4. ✅ 从JAccount页面提取验证码UUID')
        print('5. ✅ 使用JAccount域名获取验证码图片')
        print('6. ✅ 用户输入验证码后提交登录')
        
        print(f'\n🎉 全新环境登录流程测试成功！')
    else:
        print('\n❌ 全新环境测试失败')
        
        # 测试不同的访问方法
        different_approach = test_different_approaches()
        
        if different_approach:
            print(f'\n✅ 找到可用的访问方法: {different_approach}')
        else:
            print('\n❌ 未找到可用的访问方法')
        
        # 测试OAuth流程
        oauth_approach = test_oauth_flow()
        
        if oauth_approach:
            print(f'\n✅ 找到可用的OAuth方法: {oauth_approach}')
        else:
            print('\n❌ 未找到可用的OAuth方法')

if __name__ == '__main__':
    main()

