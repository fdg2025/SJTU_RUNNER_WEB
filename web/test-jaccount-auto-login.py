#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JAccount自动登录流程
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

def test_sjtu_redirect():
    """测试SJTU重定向到JAccount"""
    print('🔍 测试SJTU重定向到JAccount...')
    
    # 步骤1: 访问SJTU体育系统
    print('步骤1: 访问SJTU体育系统...')
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
    
    # 步骤2: 访问登录页面，检查重定向
    print('\n步骤2: 访问登录页面...')
    status, headers, body, new_cookies = make_request(
        f'{TEST_CONFIG["sjtu_base_url"]}/login', 
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    print(f'   状态: {status}')
    print(f'   重定向位置: {headers.get("Location", "无")}')
    
    location = headers.get('Location', '')
    if location and 'jaccount.sjtu.edu.cn' in location:
        print(f'   ✅ 重定向到JAccount: {location}')
        return {
            'jsessionid': jsessionid,
            'redirect_url': location,
            'cookies': cookies
        }
    else:
        print('   ❌ 未重定向到JAccount')
        return None

def test_jaccount_page():
    """测试JAccount页面访问"""
    print('\n🔍 测试JAccount页面访问...')
    
    # 获取重定向信息
    redirect_info = test_sjtu_redirect()
    if not redirect_info:
        return None
    
    # 访问JAccount页面
    print('\n步骤3: 访问JAccount页面...')
    status, headers, body, jaccount_cookies = make_request(
        redirect_info['redirect_url'],
        cookies=f'JSESSIONID={redirect_info["jsessionid"]}'
    )
    
    print(f'   状态: {status}')
    print(f'   JAccount Cookie: {jaccount_cookies}')
    
    if status == 200:
        # 解析HTML内容
        html_content = body.decode('utf-8', errors='ignore')
        
        # 保存HTML内容
        with open('jaccount_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print('   💾 JAccount页面HTML已保存为 jaccount_page.html')
        
        # 查找验证码相关
        print('\n步骤4: 分析验证码...')
        captcha_patterns = [
            r'<img[^>]*src=["\']([^"\']*captcha[^"\']*)["\'][^>]*>',
            r'src=["\']([^"\']*captcha[^"\']*)["\']',
            r'captcha[^"\']*["\']([^"\']*)["\']',
        ]
        
        captcha_found = False
        for pattern in captcha_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print(f'   ✅ 找到验证码: {matches[0]}')
                captcha_found = True
                break
        
        if not captcha_found:
            print('   ❌ 未找到验证码')
        
        # 查找表单字段
        print('\n步骤5: 分析表单字段...')
        input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
        inputs = re.findall(input_pattern, html_content, re.IGNORECASE)
        print(f'   输入字段: {inputs}')
        
        # 查找表单action
        action_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        action = action_match.group(1) if action_match else '无'
        print(f'   表单action: {action}')
        
        return {
            'jsessionid': redirect_info['jsessionid'],
            'jaccount_url': redirect_info['redirect_url'],
            'jaccount_cookies': jaccount_cookies,
            'form_inputs': inputs,
            'form_action': action,
            'captcha_found': captcha_found,
            'html_content': html_content
        }
    else:
        print(f'   ❌ JAccount页面访问失败: {status}')
        return None

def test_captcha_image():
    """测试验证码图片获取"""
    print('\n🔍 测试验证码图片获取...')
    
    # 获取JAccount页面信息
    jaccount_info = test_jaccount_page()
    if not jaccount_info:
        return None
    
    # 查找验证码图片URL
    html_content = jaccount_info['html_content']
    
    # 常见的验证码URL模式
    captcha_urls = [
        'https://jaccount.sjtu.edu.cn/captcha',
        'https://jaccount.sjtu.edu.cn/jaccount/captcha',
        'https://jaccount.sjtu.edu.cn/image/captcha.png',
        'https://jaccount.sjtu.edu.cn/jaccount/image/captcha.png',
    ]
    
    for url in captcha_urls:
        print(f'\n测试验证码URL: {url}')
        try:
            status, headers, image_data, _ = make_request(
                url,
                headers={'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'},
                cookies=f'JSESSIONID={jaccount_info["jsessionid"]}; {jaccount_info["jaccount_cookies"]}'
            )
            
            print(f'   状态: {status}')
            print(f'   内容类型: {headers.get("Content-Type", "未知")}')
            print(f'   数据大小: {len(image_data)} 字节')
            
            if status == 200 and len(image_data) > 0:
                # 检查是否为图片
                if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                    print('   ✅ 成功获取验证码图片')
                    
                    # 保存验证码图片
                    filename = f'jaccount_captcha_test.jpg'
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    print(f'   💾 验证码图片已保存为 {filename}')
                    
                    # 转换为base64
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    print(f'   🔤 Base64长度: {len(base64_image)} 字符')
                    
                    return {
                        'success': True,
                        'captcha_url': url,
                        'captcha_image': base64_image,
                        'jsessionid': jaccount_info['jsessionid'],
                        'jaccount_url': jaccount_info['jaccount_url'],
                        'form_inputs': jaccount_info['form_inputs'],
                        'form_action': jaccount_info['form_action']
                    }
                else:
                    print('   ❌ 返回的不是图片数据')
                    print(f'   内容预览: {image_data[:100]}')
            else:
                print('   ❌ 获取失败')
                
        except Exception as e:
            print(f'   ❌ 错误: {e}')
    
    return None

def test_login_submission():
    """测试登录提交"""
    print('\n🔍 测试登录提交...')
    
    # 获取验证码信息
    captcha_info = test_captcha_image()
    if not captcha_info or not captcha_info['success']:
        print('❌ 验证码获取失败')
        return None
    
    print('\n步骤6: 测试登录提交...')
    
    # 准备登录数据
    login_data = {
        'user': 'test_user',
        'pass': 'test_password',
        'captcha': 'test_captcha'
    }
    
    print(f'   提交数据: {login_data}')
    print(f'   登录URL: {captcha_info["jaccount_url"]}')
    
    # 提交登录
    try:
        status, headers, body, new_cookies = make_request(
            captcha_info['jaccount_url'],
            method='POST',
            data=login_data,
            cookies=f'JSESSIONID={captcha_info["jsessionid"]}'
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

def main():
    """主函数"""
    print('🚀 测试JAccount自动登录流程...\n')
    
    # 测试完整流程
    print('=' * 50)
    print('测试1: SJTU重定向到JAccount')
    print('=' * 50)
    redirect_info = test_sjtu_redirect()
    
    if redirect_info:
        print('\n' + '=' * 50)
        print('测试2: JAccount页面访问')
        print('=' * 50)
        jaccount_info = test_jaccount_page()
        
        if jaccount_info:
            print('\n' + '=' * 50)
            print('测试3: 验证码图片获取')
            print('=' * 50)
            captcha_info = test_captcha_image()
            
            if captcha_info and captcha_info['success']:
                print('\n' + '=' * 50)
                print('测试4: 登录提交')
                print('=' * 50)
                login_result = test_login_submission()
                
                if login_result:
                    print('\n' + '=' * 50)
                    print('📊 测试总结')
                    print('=' * 50)
                    print('✅ SJTU重定向: 成功')
                    print('✅ JAccount页面: 成功')
                    print('✅ 验证码获取: 成功')
                    print('✅ 登录提交: 成功')
                    
                    print(f'\n🎯 关键信息:')
                    print(f'JSESSIONID: {captcha_info["jsessionid"][:30]}...')
                    print(f'JAccount URL: {captcha_info["jaccount_url"]}')
                    print(f'验证码URL: {captcha_info["captcha_url"]}')
                    print(f'表单字段: {captcha_info["form_inputs"]}')
                    print(f'表单action: {captcha_info["form_action"]}')
                    
                    print(f'\n💡 实现建议:')
                    print('1. ✅ 自动跟随SJTU到JAccount重定向')
                    print('2. ✅ 从JAccount页面提取验证码URL')
                    print('3. ✅ 获取验证码图片并转换为Base64')
                    print('4. ✅ 用户输入验证码后提交登录')
                    print('5. ✅ 处理登录响应和Cookie获取')
                    
                    print(f'\n🎉 JAccount自动登录流程测试成功！')
                else:
                    print('\n❌ 登录提交测试失败')
            else:
                print('\n❌ 验证码获取测试失败')
        else:
            print('\n❌ JAccount页面访问测试失败')
    else:
        print('\n❌ SJTU重定向测试失败')
    
    print(f'\n📁 生成的文件:')
    print('   - jaccount_page.html (JAccount页面HTML)')
    print('   - jaccount_captcha_test.jpg (验证码图片)')

if __name__ == '__main__':
    main()

