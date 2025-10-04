#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
import json

def test_fresh_session():
    """使用全新的会话测试登录流程"""
    print("=== 使用全新会话测试登录流程 ===")
    
    # 方法1: 使用不同的User-Agent和IP模拟
    print("\n方法1: 使用移动端User-Agent...")
    
    # 创建全新的会话，使用移动端User-Agent
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
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
        
        # 检查Cookie
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"获得的Cookie: {cookies}")
        
        # 步骤2: 访问手机页面
        print("\n2. 访问手机页面...")
        response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait')
        print(f"状态码: {response.status_code}")
        
        # 检查是否有keepalive
        keepalive = None
        for cookie in session.cookies:
            if cookie.name == 'keepalive':
                keepalive = cookie.value
                print(f"获得keepalive: {keepalive}")
                break
        
        if keepalive:
            print("✗ 仍然有keepalive，可能IP被绑定")
        else:
            print("✓ 没有keepalive，可以测试登录流程")
            
            # 步骤3: 尝试访问需要登录的页面
            print("\n3. 访问需要登录的页面...")
            response = session.get('https://pe.sjtu.edu.cn/phone/api/uid')
            print(f"状态码: {response.status_code}")
            
            # 检查是否重定向
            if response.status_code == 302:
                location = response.headers.get('Location')
                print(f"重定向到: {location}")
                
                if 'jaccount.sjtu.edu.cn' in location:
                    print("✓ 重定向到JAccount登录页面")
                    test_jaccount_login(session, location)
                else:
                    print(f"✗ 未重定向到JAccount: {location}")
            else:
                print(f"✗ 未重定向，状态码: {response.status_code}")
                
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_jaccount_login(session, jaccount_url):
    """测试JAccount登录流程"""
    print("\n=== 测试JAccount登录流程 ===")
    
    try:
        # 访问JAccount登录页面
        print("\n1. 访问JAccount登录页面...")
        response = session.get(jaccount_url)
        print(f"状态码: {response.status_code}")
        
        html = response.text
        print(f"页面大小: {len(html)} 字符")
        
        # 查找验证码UUID
        uuid_match = re.search(r'uuid=([a-f0-9-]+)', html)
        if uuid_match:
            captcha_uuid = uuid_match[1]
            print(f"✓ 找到验证码UUID: {captcha_uuid}")
            
            # 构造验证码URL
            captcha_url = f"https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={int(time.time() * 1000)}"
            print(f"验证码URL: {captcha_url}")
            
            # 获取验证码图片
            print("\n2. 获取验证码图片...")
            captcha_response = session.get(captcha_url)
            print(f"验证码状态码: {captcha_response.status_code}")
            print(f"验证码Content-Type: {captcha_response.headers.get('Content-Type')}")
            
            if captcha_response.status_code == 200:
                content_type = captcha_response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    print("✓ 成功获取验证码图片")
                    print(f"图片大小: {len(captcha_response.content)} bytes")
                    
                    # 保存验证码图片
                    with open('/tmp/captcha.png', 'wb') as f:
                        f.write(captcha_response.content)
                    print("✓ 验证码图片已保存到 /tmp/captcha.png")
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
            
    except Exception as e:
        print(f"✗ JAccount测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fresh_session()
