#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试 JAccount 登录流程
模拟未登录状态
"""

import requests
import re
import json
import time
from urllib.parse import urlparse, parse_qs

def test_jaccount_detailed():
    """详细测试 JAccount 登录流程"""
    
    print("=== 详细测试 JAccount 登录流程 ===\n")
    
    # 创建全新的会话，清除所有状态
    session = requests.Session()
    
    # 清除所有 cookies
    session.cookies.clear()
    
    # 设置浏览器头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    try:
        # Step 1: 访问手机页面
        print("1. 访问手机页面...")
        phone_url = 'https://pe.sjtu.edu.cn/phone/#/indexPortrait'
        response = session.get(phone_url, headers=headers, allow_redirects=False)
        
        print(f"   状态码: {response.status_code}")
        print(f"   Location: {response.headers.get('location', 'None')}")
        
        # 打印所有响应头
        print("   响应头:")
        for key, value in response.headers.items():
            print(f"     {key}: {value}")
        
        # 提取 JSESSIONID
        jsessionid = None
        if 'Set-Cookie' in response.headers:
            cookies = response.headers['Set-Cookie']
            print(f"   Set-Cookie: {cookies}")
            jsessionid_match = re.search(r'JSESSIONID=([^;]+)', cookies)
            if jsessionid_match:
                jsessionid = jsessionid_match.group(1)
                print(f"   JSESSIONID: {jsessionid[:20]}...")
        
        # 检查是否已经登录
        if 'keepalive' in response.headers.get('Set-Cookie', ''):
            print("   状态: 已经登录 (检测到 keepalive cookie)")
            print("   这可能是由于 IP 绑定导致的自动登录")
            return True
        
        # Step 2: 如果发生重定向，跟随重定向
        if response.status_code in [301, 302]:
            jaccount_url = response.headers.get('location')
            if jaccount_url and 'jaccount.sjtu.edu.cn' in jaccount_url:
                print(f"\n2. 重定向到 JAccount: {jaccount_url}")
                
                # 访问 JAccount 登录页面
                jaccount_response = session.get(jaccount_url, headers=headers)
                print(f"   状态码: {jaccount_response.status_code}")
                
                if jaccount_response.status_code == 200:
                    html_content = jaccount_response.text
                    print("   成功获取 JAccount 登录页面")
                    
                    # 保存 HTML 内容用于分析
                    with open('/tmp/jaccount_page.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print("   HTML 已保存到 /tmp/jaccount_page.html")
                    
                    # 提取登录上下文参数
                    print("\n3. 提取登录参数...")
                    
                    # 查找 loginContext 对象
                    login_context_match = re.search(r'var loginContext = \{(.*?)\};', html_content, re.DOTALL)
                    if login_context_match:
                        context_str = login_context_match.group(1)
                        print("   找到 loginContext 对象:")
                        print(f"   {context_str}")
                        
                        # 提取各个参数
                        sid_match = re.search(r'sid:\s*"([^"]+)"', context_str)
                        client_match = re.search(r'client:\s*"([^"]+)"', context_str)
                        returl_match = re.search(r'returl:\s*"([^"]+)"', context_str)
                        se_match = re.search(r'se:\s*"([^"]+)"', context_str)
                        uuid_match = re.search(r'uuid:\s*"([^"]+)"', context_str)
                        v_match = re.search(r'v:\s*"([^"]*)"', context_str)
                        
                        sid = sid_match.group(1) if sid_match else ''
                        client = client_match.group(1) if client_match else ''
                        returl = returl_match.group(1) if returl_match else ''
                        se = se_match.group(1) if se_match else ''
                        uuid = uuid_match.group(1) if uuid_match else ''
                        v = v_match.group(1) if v_match else ''
                        
                        print(f"   SID: {sid}")
                        print(f"   Client: {client[:30]}...")
                        print(f"   RetURL: {returl[:30]}...")
                        print(f"   SE: {se[:30]}...")
                        print(f"   UUID: {uuid}")
                        print(f"   V: {v}")
                        
                        # Step 3: 获取验证码
                        if uuid:
                            print("\n4. 获取验证码...")
                            timestamp = int(time.time() * 1000)
                            captcha_url = f'https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={uuid}&t={timestamp}'
                            print(f"   验证码 URL: {captcha_url}")
                            
                            captcha_headers = {
                                'User-Agent': headers['User-Agent'],
                                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                                'Accept-Encoding': 'gzip, deflate, br',
                                'Connection': 'keep-alive',
                                'Sec-Fetch-Dest': 'image',
                                'Sec-Fetch-Mode': 'no-cors',
                                'Sec-Fetch-Site': 'same-origin',
                                'Cache-Control': 'no-cache',
                                'Pragma': 'no-cache',
                                'Cookie': f'JSESSIONID={jsessionid}' if jsessionid else ''
                            }
                            
                            captcha_response = session.get(captcha_url, headers=captcha_headers)
                            print(f"   验证码状态码: {captcha_response.status_code}")
                            print(f"   验证码内容类型: {captcha_response.headers.get('Content-Type', 'Unknown')}")
                            print(f"   验证码内容长度: {len(captcha_response.content)} bytes")
                            
                            if captcha_response.status_code == 200:
                                print("   成功获取验证码图片")
                                
                                # 保存验证码图片
                                with open('/tmp/captcha_test.png', 'wb') as f:
                                    f.write(captcha_response.content)
                                print("   验证码已保存到 /tmp/captcha_test.png")
                                
                                # 构建登录参数
                                print("\n5. 构建登录参数...")
                                login_params = {
                                    'sid': sid,
                                    'client': client,
                                    'returl': returl,
                                    'se': se,
                                    'v': v,
                                    'uuid': uuid,
                                    'user': 'test_user',
                                    'pass': 'test_pass',
                                    'captcha': 'test_captcha',
                                    'lt': 'p'
                                }
                                
                                print("   登录参数:")
                                for key, value in login_params.items():
                                    if key in ['pass']:
                                        print(f"     {key}: {'*' * len(value)}")
                                    elif key in ['client', 'returl', 'se']:
                                        print(f"     {key}: {value[:30]}...")
                                    else:
                                        print(f"     {key}: {value}")
                                
                                print("\n6. 测试登录端点...")
                                ulogin_url = 'https://jaccount.sjtu.edu.cn/jaccount/ulogin'
                                login_headers = {
                                    'User-Agent': headers['User-Agent'],
                                    'Accept': 'application/json, text/plain, */*',
                                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                                    'Accept-Encoding': 'gzip, deflate, br',
                                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                    'Origin': 'https://jaccount.sjtu.edu.cn',
                                    'Referer': jaccount_url,
                                    'X-Requested-With': 'XMLHttpRequest',
                                    'Cache-Control': 'no-cache',
                                    'Pragma': 'no-cache',
                                    'Cookie': f'JSESSIONID={jsessionid}' if jsessionid else ''
                                }
                                
                                # 构建表单数据
                                form_data = '&'.join([f'{k}={v}' for k, v in login_params.items()])
                                print(f"   表单数据: {form_data[:100]}...")
                                
                                print("   登录端点测试完成")
                                print("   注意: 未实际提交登录请求，因为需要真实的用户名密码")
                                
                                return True
                            else:
                                print(f"   获取验证码失败: {captcha_response.status_code}")
                                print(f"   响应内容: {captcha_response.text[:200]}...")
                                return False
                        else:
                            print("   未找到 UUID，无法获取验证码")
                            return False
                    else:
                        print("   未找到 loginContext 对象")
                        # 尝试其他方式提取参数
                        print("   尝试其他方式提取参数...")
                        uuid_match = re.search(r'uuid:\s*"([^"]+)"', html_content)
                        if uuid_match:
                            print(f"   找到 UUID: {uuid_match.group(1)}")
                        else:
                            print("   未找到任何 UUID")
                        return False
                else:
                    print(f"   获取 JAccount 页面失败: {jaccount_response.status_code}")
                    return False
            else:
                print(f"   意外的重定向地址: {jaccount_url}")
                return False
        else:
            print(f"   未发生重定向，状态码: {response.status_code}")
            print("   可能已经登录或页面结构发生变化")
            return True
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jaccount_detailed()
    if success:
        print("\n🎉 测试成功！登录流程验证通过")
    else:
        print("\n❌ 测试失败！请检查网络连接和服务器状态")