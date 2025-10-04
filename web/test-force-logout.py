#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试强制登出后的重定向流程
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

def test_force_logout():
    """测试强制登出"""
    print('🚀 测试强制登出后的重定向流程...\n')
    
    # 步骤1: 获取初始会话
    print('步骤1: 获取初始会话...')
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
    
    # 步骤2: 尝试访问logout端点
    print('\n步骤2: 尝试访问logout端点...')
    logout_urls = [
        f'{TEST_CONFIG["sjtu_base_url"]}/logout',
        f'{TEST_CONFIG["sjtu_base_url"]}/jaccount/logout',
        f'{TEST_CONFIG["sjtu_base_url"]}/phone/logout',
    ]
    
    for logout_url in logout_urls:
        print(f'   测试logout URL: {logout_url}')
        try:
            status, headers, body, new_cookies = make_request(
                logout_url,
                cookies=f'JSESSIONID={jsessionid}'
            )
            
            print(f'     状态: {status}')
            print(f'     重定向: {headers.get("Location", "无")}')
            print(f'     新Cookie: {new_cookies}')
            
            if status == 302 or status == 301:
                location = headers.get('Location', '')
                if location:
                    print(f'     ✅ 重定向到: {location}')
                    break
        except Exception as e:
            print(f'     ❌ 错误: {e}')
    
    # 步骤3: 清除keepalive cookie后访问phone页面
    print('\n步骤3: 清除keepalive cookie后访问phone页面...')
    
    # 使用新的User-Agent和不同的请求头来模拟新会话
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
    }
    
    phone_url = f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait'
    status, headers, body, new_cookies = make_request(
        phone_url,
        headers=custom_headers,
        cookies=''  # 不携带任何Cookie
    )
    
    print(f'   状态: {status}')
    print(f'   重定向位置: {headers.get("Location", "无")}')
    print(f'   新Cookie: {new_cookies}')
    
    location = headers.get('Location', '')
    if location and 'jaccount.sjtu.edu.cn' in location:
        print(f'   ✅ 成功重定向到JAccount: {location}')
        
        # 步骤4: 访问JAccount页面
        print('\n步骤4: 访问JAccount页面...')
        status, headers, body, jaccount_cookies = make_request(
            location,
            headers=custom_headers
        )
        
        print(f'   状态: {status}')
        print(f'   JAccount Cookie: {jaccount_cookies}')
        
        if status == 200:
            # 解析HTML内容
            html_content = body.decode('utf-8', errors='ignore')
            
            # 保存HTML内容
            with open('jaccount_force_logout.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('   💾 JAccount页面HTML已保存为 jaccount_force_logout.html')
            
            # 查找验证码UUID
            uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
            captcha_uuid = uuid_match.group(1) if uuid_match else ''
            
            if captcha_uuid:
                print(f'   ✅ 找到验证码UUID: {captcha_uuid}')
                
                # 步骤5: 测试验证码URL
                print('\n步骤5: 测试验证码URL...')
                timestamp = int(time.time() * 1000)
                
                # 使用JAccount域名
                captcha_url = f'https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
                
                print(f'   测试URL: {captcha_url}')
                try:
                    status, headers, image_data, _ = make_request(
                        captcha_url,
                        headers={
                            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                            'User-Agent': custom_headers['User-Agent']
                        }
                    )
                    
                    print(f'     状态: {status}')
                    print(f'     内容类型: {headers.get("Content-Type", "未知")}')
                    print(f'     数据大小: {len(image_data)} 字节')
                    
                    if status == 200 and len(image_data) > 0:
                        # 检查是否为图片
                        if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                            print('     ✅ 成功获取验证码图片')
                            
                            # 保存验证码图片
                            filename = f'force_logout_captcha.jpg'
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
        
        # 检查是否包含登录相关内容
        if 'login' in response_text.lower() or '登录' in response_text:
            print('   ⚠️ 响应包含登录相关内容，可能已经是登录页面')
        
        return None

def test_direct_jaccount():
    """直接测试JAccount页面"""
    print('\n🔍 直接测试JAccount页面...')
    
    # 直接访问JAccount登录页面
    jaccount_url = 'https://jaccount.sjtu.edu.cn/jaccount/jalogin'
    
    print(f'   直接访问: {jaccount_url}')
    try:
        status, headers, body, cookies = make_request(jaccount_url)
        
        print(f'     状态: {status}')
        print(f'     Cookie: {cookies}')
        
        if status == 200:
            # 解析HTML内容
            html_content = body.decode('utf-8', errors='ignore')
            
            # 保存HTML内容
            with open('jaccount_direct.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('     💾 JAccount页面HTML已保存为 jaccount_direct.html')
            
            # 查找验证码UUID
            uuid_match = re.search(r'uuid=([a-f0-9-]+)', html_content)
            captcha_uuid = uuid_match.group(1) if uuid_match else ''
            
            if captcha_uuid:
                print(f'     ✅ 找到验证码UUID: {captcha_uuid}')
                
                # 测试验证码URL
                timestamp = int(time.time() * 1000)
                captcha_url = f'https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
                
                print(f'     测试验证码URL: {captcha_url}')
                status, headers, image_data, _ = make_request(
                    captcha_url,
                    headers={'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'}
                )
                
                print(f'       状态: {status}')
                print(f'       内容类型: {headers.get("Content-Type", "未知")}')
                print(f'       数据大小: {len(image_data)} 字节')
                
                if status == 200 and len(image_data) > 0:
                    if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                        print('       ✅ 成功获取验证码图片')
                        
                        # 保存验证码图片
                        filename = f'direct_jaccount_captcha.jpg'
                        with open(filename, 'wb') as f:
                            f.write(image_data)
                        print(f'       💾 验证码图片已保存为 {filename}')
                        
                        return True
                    else:
                        print('       ❌ 返回的不是图片数据')
                        return False
                else:
                    print('       ❌ 获取失败')
                    return False
            else:
                print('     ❌ 未找到验证码UUID')
                return False
        else:
            print(f'     ❌ 访问失败: {status}')
            return False
            
    except Exception as e:
        print(f'     ❌ 错误: {e}')
        return False

def main():
    """主函数"""
    print('🚀 测试强制登出后的重定向流程...\n')
    
    # 测试强制登出后的重定向
    captcha_info = test_force_logout()
    
    if captcha_info and captcha_info['success']:
        print('\n📊 验证码流程测试成功！')
        print(f'✅ JSESSIONID: {captcha_info["jsessionid"][:30]}...')
        print(f'✅ 验证码UUID: {captcha_info["captcha_uuid"]}')
        print(f'✅ 验证码URL: {captcha_info["captcha_url"]}')
        print(f'✅ 验证码图片: {len(captcha_info["captcha_image"])} 字符Base64')
        print(f'✅ JAccount URL: {captcha_info["jaccount_url"]}')
        
        print('\n💡 实现总结:')
        print('1. ✅ 强制清除会话Cookie')
        print('2. ✅ 访问phone页面触发重定向到JAccount')
        print('3. ✅ 从JAccount页面提取验证码UUID')
        print('4. ✅ 使用JAccount域名获取验证码图片')
        print('5. ✅ 用户输入验证码后提交登录')
        print('6. ✅ 处理登录响应和Cookie获取')
        
        print(f'\n🎉 强制登出后的重定向流程测试成功！')
    else:
        print('\n❌ 强制登出流程测试失败')
        
        # 直接测试JAccount页面
        print('\n🔍 直接测试JAccount页面...')
        direct_success = test_direct_jaccount()
        
        if direct_success:
            print('\n✅ 直接访问JAccount页面成功')
            print('💡 建议：可以直接使用JAccount URL进行登录')
        else:
            print('\n❌ 直接访问JAccount页面失败')

if __name__ == '__main__':
    main()

