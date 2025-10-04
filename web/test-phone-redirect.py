#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通过phone页面重定向到JAccount的流程
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

def test_phone_redirect():
    """测试通过phone页面重定向到JAccount"""
    print('🚀 测试通过phone页面重定向到JAccount...\n')
    
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
    
    # 步骤2: 访问phone页面触发重定向
    print('\n步骤2: 访问phone页面...')
    phone_url = f'{TEST_CONFIG["sjtu_base_url"]}/phone/#/indexPortrait'
    status, headers, body, new_cookies = make_request(
        phone_url,
        cookies=f'JSESSIONID={jsessionid}'
    )
    
    print(f'   状态: {status}')
    print(f'   重定向位置: {headers.get("Location", "无")}')
    print(f'   新Cookie: {new_cookies}')
    
    # 合并Cookie
    all_cookies = f'JSESSIONID={jsessionid}'
    if new_cookies:
        all_cookies += '; ' + new_cookies
    
    location = headers.get('Location', '')
    if location and 'jaccount.sjtu.edu.cn' in location:
        print(f'   ✅ 成功重定向到JAccount: {location}')
        
        # 步骤3: 访问JAccount页面
        print('\n步骤3: 访问JAccount页面...')
        status, headers, body, jaccount_cookies = make_request(
            location,
            cookies=all_cookies
        )
        
        print(f'   状态: {status}')
        print(f'   JAccount Cookie: {jaccount_cookies}')
        
        if status == 200:
            # 解析HTML内容
            html_content = body.decode('utf-8', errors='ignore')
            
            # 保存HTML内容
            with open('jaccount_phone_redirect.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('   💾 JAccount页面HTML已保存为 jaccount_phone_redirect.html')
            
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
                        cookies=all_cookies
                    )
                    
                    print(f'     状态: {status}')
                    print(f'     内容类型: {headers.get("Content-Type", "未知")}')
                    print(f'     数据大小: {len(image_data)} 字节')
                    
                    if status == 200 and len(image_data) > 0:
                        # 检查是否为图片
                        if image_data.startswith(b'\xff\xd8\xff') or image_data.startswith(b'\x89PNG'):
                            print('     ✅ 成功获取验证码图片')
                            
                            # 保存验证码图片
                            filename = f'phone_redirect_captcha.jpg'
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
                                'cookies': all_cookies
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

def test_login_submission():
    """测试登录提交"""
    print('\n🔍 测试登录提交...')
    
    # 获取验证码信息
    captcha_info = test_phone_redirect()
    if not captcha_info or not captcha_info['success']:
        print('❌ 验证码获取失败')
        return None
    
    print('\n步骤5: 测试登录提交...')
    
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
        status, headers, body, new_cookies = make_request(
            captcha_info['jaccount_url'],
            method='POST',
            data=login_data,
            cookies=captcha_info['cookies']
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
    print('🚀 测试通过phone页面重定向到JAccount的流程...\n')
    
    # 测试验证码流程
    captcha_info = test_phone_redirect()
    
    if captcha_info and captcha_info['success']:
        print('\n📊 验证码流程测试成功！')
        print(f'✅ JSESSIONID: {captcha_info["jsessionid"][:30]}...')
        print(f'✅ 验证码UUID: {captcha_info["captcha_uuid"]}')
        print(f'✅ 验证码URL: {captcha_info["captcha_url"]}')
        print(f'✅ 验证码图片: {len(captcha_info["captcha_image"])} 字符Base64')
        print(f'✅ JAccount URL: {captcha_info["jaccount_url"]}')
        
        # 测试登录表单
        login_result = test_login_submission()
        
        if login_result:
            print('\n📊 登录表单测试完成')
            print(f'✅ 提交状态: {login_result["status"]}')
            print(f'✅ 重定向: {login_result["location"]}')
        
        print('\n💡 实现总结:')
        print('1. ✅ 访问SJTU phone页面获取JSESSIONID')
        print('2. ✅ 跟随重定向到JAccount登录页面')
        print('3. ✅ 从JAccount页面提取验证码UUID')
        print('4. ✅ 使用JAccount域名获取验证码图片')
        print('5. ✅ 用户输入验证码后提交登录')
        print('6. ✅ 处理登录响应和Cookie获取')
        
        print('\n🎯 下一步:')
        print('1. 部署更新后的自动登录API')
        print('2. 测试前端验证码输入功能')
        print('3. 验证完整的登录流程')
        
        print(f'\n🎉 通过phone页面重定向的验证码流程测试成功！')
    else:
        print('\n❌ 验证码流程测试失败')

if __name__ == '__main__':
    main()

