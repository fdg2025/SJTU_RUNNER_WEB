#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
from urllib.parse import urljoin, urlparse, parse_qs
import json
import time

def test_real_login_flow():
    """测试真实的登录流程"""
    print("=== 测试真实登录流程 ===")
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    try:
        # 步骤1: 访问主页面
        print("\n1. 访问主页面...")
        response = session.get('https://pe.sjtu.edu.cn/')
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 检查是否有JSESSIONID
        jsessionid = None
        for cookie in session.cookies:
            if cookie.name == 'JSESSIONID':
                jsessionid = cookie.value
                print(f"✓ 获得JSESSIONID: {jsessionid}")
                break
        
        if not jsessionid:
            print("✗ 未获得JSESSIONID")
            return
        
        # 步骤2: 访问手机页面
        print("\n2. 访问手机页面...")
        response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait')
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 检查是否有keepalive
        keepalive = None
        for cookie in session.cookies:
            if cookie.name == 'keepalive':
                keepalive = cookie.value
                print(f"✓ 获得keepalive: {keepalive}")
                break
        
        # 步骤3: 检查是否需要登录
        print("\n3. 检查登录状态...")
        if keepalive:
            print("✓ 已登录，无需JAccount登录")
            print(f"完整Cookie: keepalive={keepalive}; JSESSIONID={jsessionid}")
            return
        
        # 步骤4: 尝试访问需要登录的页面
        print("\n4. 访问需要登录的页面...")
        response = session.get('https://pe.sjtu.edu.cn/phone/api/uid')
        print(f"状态码: {response.status_code}")
        
        # 检查是否重定向到JAccount
        if response.status_code == 302:
            location = response.headers.get('Location')
            print(f"重定向到: {location}")
            
            if 'jaccount.sjtu.edu.cn' in location:
                print("✓ 重定向到JAccount登录页面")
                
                # 步骤5: 访问JAccount登录页面
                print("\n5. 访问JAccount登录页面...")
                response = session.get(location)
                print(f"状态码: {response.status_code}")
                
                # 解析登录页面
                html = response.text
                
                # 查找验证码UUID
                uuid_match = re.search(r'uuid=([a-f0-9-]+)', html)
                if uuid_match:
                    captcha_uuid = uuid_match[1]
                    print(f"✓ 找到验证码UUID: {captcha_uuid}")
                    
                    # 构造验证码URL
                    captcha_url = f"https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={int(time.time() * 1000)}"
                    print(f"验证码URL: {captcha_url}")
                    
                    # 获取验证码图片
                    print("\n6. 获取验证码图片...")
                    captcha_response = session.get(captcha_url)
                    print(f"验证码状态码: {captcha_response.status_code}")
                    print(f"验证码Content-Type: {captcha_response.headers.get('Content-Type')}")
                    
                    if captcha_response.status_code == 200:
                        content_type = captcha_response.headers.get('Content-Type', '')
                        if 'image' in content_type:
                            print("✓ 成功获取验证码图片")
                            print(f"图片大小: {len(captcha_response.content)} bytes")
                        else:
                            print(f"✗ 验证码返回的不是图片: {content_type}")
                            print(f"内容预览: {captcha_response.text[:200]}...")
                    else:
                        print(f"✗ 获取验证码失败: {captcha_response.status_code}")
                else:
                    print("✗ 未找到验证码UUID")
                    
                # 查找登录表单
                form_match = re.search(r'<form[^>]*action="([^"]*)"[^>]*>', html)
                if form_match:
                    form_action = form_match.group(1)
                    print(f"✓ 找到登录表单: {form_action}")
                    
                    # 查找隐藏字段
                    hidden_fields = {}
                    for match in re.finditer(r'<input[^>]*type="hidden"[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', html):
                        hidden_fields[match.group(1)] = match.group(2)
                    
                    if hidden_fields:
                        print(f"✓ 找到隐藏字段: {hidden_fields}")
                    else:
                        print("✗ 未找到隐藏字段")
                else:
                    print("✗ 未找到登录表单")
            else:
                print(f"✗ 未重定向到JAccount: {location}")
        else:
            print(f"✗ 未重定向，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_login_flow()
