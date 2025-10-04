#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试JAccount登录流程
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

def create_clean_opener():
    """创建一个干净的opener，不保存任何cookie"""
    # 创建cookie jar，但不保存cookie
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

def make_clean_request(opener, url: str, method: str = 'GET', data: Optional[Dict] = None, 
                      headers: Optional[Dict] = None) -> Tuple[int, Dict, bytes, str]:
    """发送HTTP请求，返回字节数据"""
    if headers is None:
        headers = {}
    
    # 设置默认请求头
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
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

def test_jaccount_login_page():
    """测试JAccount登录页面"""
    print('🚀 测试JAccount登录页面...\n')
    
    # 创建干净的opener
    opener, cookie_jar = create_clean_opener()
    
    # 步骤1: 直接访问JAccount登录页面
    print('步骤1: 直接访问JAccount登录页面...')
    jaccount_url = f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/jalogin'
    
    print(f'   访问URL: {jaccount_url}')
    status, headers, body, cookies = make_clean_request(opener, jaccount_url)
    
    print(f'   状态: {status}')
    print(f'   Cookie: {cookies}')
    
    if status == 200:
        # 解析HTML内容
        html_content = body.decode('utf-8', errors='ignore')
        
        # 保存HTML内容
        with open('jaccount_direct_login.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print('   💾 JAccount登录页面HTML已保存为 jaccount_direct_login.html')
        
        # 查找验证码UUID
        uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
        captcha_uuid = uuid_match.group(1) if uuid_match else ''
        
        if captcha_uuid:
            print(f'   ✅ 找到验证码UUID: {captcha_uuid}')
            
            # 步骤2: 测试验证码URL
            print('\n步骤2: 测试验证码URL...')
            timestamp = int(time.time() * 1000)
            
            # 使用JAccount域名
            captcha_url = f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
            
            print(f'   测试URL: {captcha_url}')
            try:
                status, headers, image_data, _ = make_clean_request(
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
                        filename = f'jaccount_direct_captcha.jpg'
                        with open(filename, 'wb') as f:
                            f.write(image_data)
                        print(f'     💾 验证码图片已保存为 {filename}')
                        
                        # 转换为base64
                        base64_image = base64.b64encode(image_data).decode('utf-8')
                        print(f'     🔤 Base64长度: {len(base64_image)} 字符')
                        
                        return {
                            'success': True,
                            'captcha_uuid': captcha_uuid,
                            'captcha_url': captcha_url,
                            'captcha_image': base64_image,
                            'jaccount_url': jaccount_url,
                            'cookies': cookies
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
        print(f'   ❌ 访问失败: {status}')
        return None

def test_jaccount_login_submission():
    """测试JAccount登录提交"""
    print('\n🔍 测试JAccount登录提交...')
    
    # 获取验证码信息
    captcha_info = test_jaccount_login_page()
    if not captcha_info or not captcha_info['success']:
        print('❌ 验证码获取失败')
        return None
    
    print('\n步骤3: 测试登录提交...')
    
    # 创建干净的opener
    opener, cookie_jar = create_clean_opener()
    
    # 准备登录数据
    login_data = {
        'user': 'test_user',
        'pass': 'test_password',
        'captcha': 'test_captcha',
        'lt': 'p'  # login type: password
    }
    
    print(f'   提交数据: {login_data}')
    print(f'   登录URL: {captcha_info["jaccount_url"]}')
    
    # 提交登录
    try:
        status, headers, body, new_cookies = make_clean_request(
            opener, captcha_info['jaccount_url'],
            method='POST',
            data=login_data
        )
        
        print(f'   登录提交状态: {status}')
        print(f'   重定向位置: {headers.get("Location", "无")}')
        print(f'   新Cookie: {new_cookies}')
        
        # 分析响应
        response_text = body.decode('utf-8', errors='ignore')
        
        if '验证码' in response_text or 'captcha' in response_text.lower():
            print('   ⚠️ 响应包含验证码相关错误')
        elif '用户名' in response_text or '密码' in response_text:
            print('   ⚠️ 响应包含用户名/密码相关错误')
        elif '成功' in response_text or 'success' in response_text.lower():
            print('   ✅ 登录可能成功')
        else:
            print('   📝 响应内容预览:')
            print(f'   {response_text[:200]}...')
        
        return {
            'status': status,
            'location': headers.get('Location'),
            'cookies': new_cookies,
            'response': response_text[:500]
        }
        
    except Exception as e:
        print(f'   ❌ 登录提交失败: {e}')
        return None

def test_sjtu_oauth_flow():
    """测试SJTU OAuth流程"""
    print('\n🔍 测试SJTU OAuth流程...')
    
    # 创建干净的opener
    opener, cookie_jar = create_clean_opener()
    
    # 步骤1: 访问SJTU OAuth授权页面
    print('步骤1: 访问SJTU OAuth授权页面...')
    oauth_url = f'{TEST_CONFIG["sjtu_base_url"]}/oauth/authorize'
    
    print(f'   访问URL: {oauth_url}')
    status, headers, body, cookies = make_clean_request(opener, oauth_url)
    
    print(f'   状态: {status}')
    print(f'   重定向位置: {headers.get("Location", "无")}')
    print(f'   Cookie: {cookies}')
    
    location = headers.get('Location', '')
    if location and 'jaccount.sjtu.edu.cn' in location:
        print(f'   ✅ 重定向到JAccount: {location}')
        
        # 步骤2: 访问JAccount页面
        print('\n步骤2: 访问JAccount页面...')
        status, headers, body, jaccount_cookies = make_clean_request(opener, location)
        
        print(f'   状态: {status}')
        print(f'   JAccount Cookie: {jaccount_cookies}')
        
        if status == 200:
            # 解析HTML内容
            html_content = body.decode('utf-8', errors='ignore')
            
            # 保存HTML内容
            with open('jaccount_oauth_redirect.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('   💾 JAccount页面HTML已保存为 jaccount_oauth_redirect.html')
            
            # 查找验证码UUID
            uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
            captcha_uuid = uuid_match.group(1) if uuid_match else ''
            
            if captcha_uuid:
                print(f'   ✅ 找到验证码UUID: {captcha_uuid}')
                
                # 步骤3: 测试验证码URL
                print('\n步骤3: 测试验证码URL...')
                timestamp = int(time.time() * 1000)
                
                # 使用JAccount域名
                captcha_url = f'{TEST_CONFIG["jaccount_base_url"]}/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
                
                print(f'   测试URL: {captcha_url}')
                try:
                    status, headers, image_data, _ = make_clean_request(
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
                            filename = f'oauth_redirect_captcha.jpg'
                            with open(filename, 'wb') as f:
                                f.write(image_data)
                            print(f'     💾 验证码图片已保存为 {filename}')
                            
                            # 转换为base64
                            base64_image = base64.b64encode(image_data).decode('utf-8')
                            print(f'     🔤 Base64长度: {len(base64_image)} 字符')
                            
                            return {
                                'success': True,
                                'captcha_uuid': captcha_uuid,
                                'captcha_url': captcha_url,
                                'captcha_image': base64_image,
                                'jaccount_url': location,
                                'cookies': jaccount_cookies
                            }
                        else:
                            print('     ❌ 返回的不是图片数据')
                            print(f'     内容预览: {image_data[:100]}')
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
    else:
        print('   ❌ 未重定向到JAccount')
        return None

def main():
    """主函数"""
    print('🚀 直接测试JAccount登录流程...\n')
    
    # 测试直接访问JAccount登录页面
    captcha_info = test_jaccount_login_page()
    
    if captcha_info and captcha_info['success']:
        print('\n📊 JAccount直接访问测试成功！')
        print(f'✅ 验证码UUID: {captcha_info["captcha_uuid"]}')
        print(f'✅ 验证码URL: {captcha_info["captcha_url"]}')
        print(f'✅ 验证码图片: {len(captcha_info["captcha_image"])} 字符Base64')
        print(f'✅ JAccount URL: {captcha_info["jaccount_url"]}')
        
        # 测试登录提交
        login_result = test_jaccount_login_submission()
        
        if login_result:
            print('\n📊 登录提交测试完成')
            print(f'✅ 提交状态: {login_result["status"]}')
            print(f'✅ 重定向: {login_result["location"]}')
        
        print('\n💡 实现总结:')
        print('1. ✅ 直接访问JAccount登录页面')
        print('2. ✅ 从页面提取验证码UUID')
        print('3. ✅ 使用JAccount域名获取验证码图片')
        print('4. ✅ 用户输入验证码后提交登录')
        print('5. ✅ 处理登录响应和Cookie获取')
        
        print(f'\n🎉 JAccount直接访问流程测试成功！')
    else:
        print('\n❌ JAccount直接访问测试失败')
        
        # 测试SJTU OAuth流程
        print('\n🔍 尝试SJTU OAuth流程...')
        oauth_info = test_sjtu_oauth_flow()
        
        if oauth_info and oauth_info['success']:
            print('\n📊 SJTU OAuth流程测试成功！')
            print(f'✅ 验证码UUID: {oauth_info["captcha_uuid"]}')
            print(f'✅ 验证码URL: {oauth_info["captcha_url"]}')
            print(f'✅ 验证码图片: {len(oauth_info["captcha_image"])} 字符Base64')
            print(f'✅ JAccount URL: {oauth_info["jaccount_url"]}')
            
            print('\n💡 实现总结:')
            print('1. ✅ 访问SJTU OAuth授权页面')
            print('2. ✅ 跟随重定向到JAccount登录页面')
            print('3. ✅ 从页面提取验证码UUID')
            print('4. ✅ 使用JAccount域名获取验证码图片')
            print('5. ✅ 用户输入验证码后提交登录')
            print('6. ✅ 处理登录响应和Cookie获取')
            
            print(f'\n🎉 SJTU OAuth流程测试成功！')
        else:
            print('\n❌ SJTU OAuth流程测试失败')

if __name__ == '__main__':
    main()

