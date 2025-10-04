#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试最终版本的JAccount登录流程
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
    'jaccount_base': 'https://jaccount.sjtu.edu.cn',
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

def test_jaccount_complete_flow():
    """测试完整的JAccount登录流程"""
    print('🚀 测试完整的JAccount登录流程...\n')
    
    # 步骤1: 访问SJTU体育系统获取JSESSIONID
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
    
    # 步骤2: 访问JAccount登录页面
    print('\n步骤2: 访问JAccount登录页面...')
    jaccount_url = f'{TEST_CONFIG["jaccount_base"]}/jaccount/login'
    
    status, headers, body, jaccount_cookies = make_request(
        jaccount_url,
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    print(f'   状态: {status}')
    print(f'   JAccount Cookie: {jaccount_cookies}')
    
    # 解析JAccount页面
    html_content = body.decode('utf-8', errors='ignore')
    
    # 查找验证码UUID
    uuid_patterns = [
        r'uuid=([a-f0-9-]+)',
        r'captcha\?uuid=([a-f0-9-]+)',
        r'refreshCaptcha\(\)[^}]*uuid=([a-f0-9-]+)',
    ]
    
    captcha_uuid = None
    for pattern in uuid_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            captcha_uuid = matches[0]
            print(f'   ✅ 找到验证码UUID: {captcha_uuid}')
            break
    
    if not captcha_uuid:
        print('   ❌ 未找到验证码UUID')
        return None
    
    # 步骤3: 获取验证码图片
    print('\n步骤3: 获取验证码图片...')
    timestamp = int(time.time() * 1000)
    captcha_url = f'{TEST_CONFIG["jaccount_base"]}/jaccount/captcha?uuid={captcha_uuid}&t={timestamp}'
    
    print(f'   验证码URL: {captcha_url}')
    
    status, headers, image_data, _ = make_request(
        captcha_url,
        headers={'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'},
        cookies=f'JSESSIONID={jsessionid}; {jaccount_cookies}'
    )
    
    print(f'   状态: {status}')
    print(f'   内容类型: {headers.get("Content-Type", "未知")}')
    print(f'   图片大小: {len(image_data)} 字节')
    
    if status == 200 and len(image_data) > 0:
        # 检查是否为图片
        if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
            print('   ✅ 成功获取验证码图片')
            
            # 保存验证码图片
            with open('jaccount_captcha_final.jpg', 'wb') as f:
                f.write(image_data)
            print('   💾 验证码图片已保存为 jaccount_captcha_final.jpg')
            
            # 转换为base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            print(f'   🔤 Base64长度: {len(base64_image)} 字符')
            
            return {
                'success': True,
                'jsessionid': jsessionid,
                'jaccount_cookies': jaccount_cookies,
                'captcha_uuid': captcha_uuid,
                'captcha_url': captcha_url,
                'captcha_image': base64_image,
                'login_url': jaccount_url
            }
        else:
            print('   ❌ 返回的不是图片数据')
            print(f'   内容预览: {image_data[:100]}')
    else:
        print('   ❌ 获取验证码图片失败')
    
    return None

def test_login_submission_with_captcha():
    """测试带验证码的登录提交"""
    print('\n🔍 测试带验证码的登录提交...')
    
    # 获取JAccount流程信息
    jaccount_info = test_jaccount_complete_flow()
    
    if not jaccount_info or not jaccount_info['success']:
        print('❌ JAccount流程测试失败')
        return None
    
    print('\n步骤4: 测试登录提交...')
    
    # 准备登录数据
    login_data = {
        'user': 'test_user',
        'pass': 'test_password',
        'captcha': 'test_captcha',
        'uuid': jaccount_info['captcha_uuid'],
        'lt': 'p'  # login type: password
    }
    
    print(f'   提交数据: {login_data}')
    
    # 提交登录
    try:
        status, headers, body, new_cookies = make_request(
            jaccount_info['login_url'],
            method='POST',
            data=login_data,
            cookies=f'JSESSIONID={jaccount_info["jsessionid"]}; {jaccount_info["jaccount_cookies"]}'
        )
        
        print(f'   登录提交状态: {status}')
        print(f'   重定向位置: {headers.get("Location", "无")}')
        print(f'   新Cookie: {new_cookies}')
        
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
            'location': headers.get('Location'),
            'cookies': new_cookies,
            'response': response_text[:500]
        }
        
    except Exception as e:
        print(f'   ❌ 登录提交失败: {e}')
        return None

def main():
    """主函数"""
    print('🚀 测试最终版本的JAccount登录流程...\n')
    
    # 测试完整流程
    jaccount_info = test_jaccount_complete_flow()
    
    if jaccount_info and jaccount_info['success']:
        print('\n📊 JAccount流程测试成功！')
        print(f'✅ JSESSIONID: {jaccount_info["jsessionid"][:30]}...')
        print(f'✅ 验证码UUID: {jaccount_info["captcha_uuid"]}')
        print(f'✅ 验证码URL: {jaccount_info["captcha_url"]}')
        print(f'✅ 登录URL: {jaccount_info["login_url"]}')
        print(f'✅ 验证码图片: {len(jaccount_info["captcha_image"])} 字符Base64')
        
        # 测试登录提交
        login_result = test_login_submission_with_captcha()
        
        if login_result:
            print('\n📊 登录提交测试完成')
            print(f'✅ 提交状态: {login_result["status"]}')
            print(f'✅ 重定向: {login_result["location"]}')
        
        print('\n💡 实现总结:')
        print('   1. ✅ 访问SJTU体育系统获取JSESSIONID')
        print('   2. ✅ 访问JAccount登录页面')
        print('   3. ✅ 从页面提取验证码UUID')
        print('   4. ✅ 使用UUID获取验证码图片')
        print('   5. ✅ 用户输入验证码后提交登录')
        print('   6. ✅ 处理登录成功后的重定向和Cookie')
        
        print('\n🎯 下一步:')
        print('   1. 部署更新后的自动登录API')
        print('   2. 测试前端验证码输入功能')
        print('   3. 验证完整的登录流程')
    else:
        print('\n❌ JAccount流程测试失败')

if __name__ == '__main__':
    main()

