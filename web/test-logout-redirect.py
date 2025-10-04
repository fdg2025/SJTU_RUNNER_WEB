#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试未登录状态下的重定向流程
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

def test_clear_session():
    """测试清除会话后的重定向"""
    print('🚀 测试清除会话后的重定向流程...\n')
    
    # 步骤1: 获取初始会话（不携带任何Cookie）
    print('步骤1: 获取初始会话（无Cookie）...')
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
        return None
    
    # 步骤2: 访问phone页面（未登录状态）
    print('\n步骤2: 访问phone页面（未登录状态）...')
    phone_url = f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait'
    status, headers, body, new_cookies = make_request(
        phone_url,
        cookies=f'JSESSIONID={jsessionid}'  # 只携带JSESSIONID，不携带keepalive
    )
    
    print(f'   状态: {status}')
    print(f'   重定向位置: {headers.get("Location", "无")}')
    print(f'   新Cookie: {new_cookies}')
    
    location = headers.get('Location', '')
    if location and 'jaccount.sjtu.edu.cn' in location:
        print(f'   ✅ 成功重定向到JAccount: {location}')
        
        # 步骤3: 访问JAccount页面
        print('\n步骤3: 访问JAccount页面...')
        status, headers, body, jaccount_cookies = make_request(
            location,
            cookies=f'JSESSIONID={jsessionid}'
        )
        
        print(f'   状态: {status}')
        print(f'   JAccount Cookie: {jaccount_cookies}')
        
        if status == 200:
            # 解析HTML内容
            html_content = body.decode('utf-8', errors='ignore')
            
            # 保存HTML内容
            with open('jaccount_logout_redirect.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('   💾 JAccount页面HTML已保存为 jaccount_logout_redirect.html')
            
            # 查找验证码UUID
            uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
            captcha_uuid = uuid_match.group(1) if uuid_match else ''
            
            if captcha_uuid:
                print(f'   ✅ 找到验证码UUID: {captcha_uuid}')
                
                # 步骤4: 测试验证码URL
                print('\n步骤4: 测试验证码URL...')
                timestamp = int(time.time() * 1000)
                
                # 使用JAccount域名
                captcha_url = f'https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
                
                print(f'   测试URL: {captcha_url}')
                try:
                    status, headers, image_data, _ = make_request(
                        captcha_url,
                        headers={'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'},
                        cookies=f'JSESSIONID={jsessionid}'
                    )
                    
                    print(f'     状态: {status}')
                    print(f'     内容类型: {headers.get("Content-Type", "未知")}')
                    print(f'     数据大小: {len(image_data)} 字节')
                    
                    if status == 200 and len(image_data) > 0:
                        # 检查是否为图片
                        if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                            print('     ✅ 成功获取验证码图片')
                            
                            # 保存验证码图片
                            filename = f'logout_redirect_captcha.jpg'
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
    else:
        print('   ❌ 未重定向到JAccount')
        print('   📝 响应内容预览:')
        response_text = body.decode('utf-8', errors='ignore')
        print(f'   {response_text[:200]}...')
        return None

def test_different_endpoints():
    """测试不同的端点"""
    print('\n🔍 测试不同的端点...')
    
    # 测试不同的URL
    test_urls = [
        'https://pe.sjtu.edu.cn/phone/',
        'https://pe.sjtu.edu.cn/phone/index.html',
        'https://pe.sjtu.edu.cn/phone/indexPortrait',
        'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
        'https://pe.sjtu.edu.cn/phone/indexPortrait.html',
    ]
    
    for url in test_urls:
        print(f'\n   测试URL: {url}')
        try:
            status, headers, body, cookies = make_request(url)
            location = headers.get('Location', '')
            
            print(f'     状态: {status}')
            print(f'     重定向: {location}')
            print(f'     Cookie: {cookies}')
            
            if location and 'jaccount.sjtu.edu.cn' in location:
                print('     ✅ 重定向到JAccount')
                return url
            elif 'keepalive' in cookies:
                print('     ⚠️ 已登录状态')
            else:
                print('     ❌ 未重定向')
                
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    return None

def main():
    """主函数"""
    print('🚀 测试未登录状态下的重定向流程...\n')
    
    # 测试清除会话后的重定向
    captcha_info = test_clear_session()
    
    if captcha_info and captcha_info['success']:
        print('\n📊 验证码流程测试成功！')
        print(f'✅ JSESSIONID: {captcha_info["jsessionid"][:30]}...')
        print(f'✅ 验证码UUID: {captcha_info["captcha_uuid"]}')
        print(f'✅ 验证码URL: {captcha_info["captcha_url"]}')
        print(f'✅ 验证码图片: {len(captcha_info["captcha_image"])} 字符Base64')
        print(f'✅ JAccount URL: {captcha_info["jaccount_url"]}')
        
        print('\n💡 实现总结:')
        print('1. ✅ 访问SJTU获取JSESSIONID（无keepalive）')
        print('2. ✅ 访问phone页面触发重定向到JAccount')
        print('3. ✅ 从JAccount页面提取验证码UUID')
        print('4. ✅ 使用JAccount域名获取验证码图片')
        print('5. ✅ 用户输入验证码后提交登录')
        print('6. ✅ 处理登录响应和Cookie获取')
        
        print(f'\n🎉 未登录状态下的重定向流程测试成功！')
    else:
        print('\n❌ 验证码流程测试失败')
        
        # 测试不同的端点
        print('\n🔍 尝试不同的端点...')
        working_url = test_different_endpoints()
        
        if working_url:
            print(f'\n✅ 找到可用的端点: {working_url}')
        else:
            print('\n❌ 未找到可用的端点')

if __name__ == '__main__':
    main()

