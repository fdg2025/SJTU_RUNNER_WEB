#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
import json

def test_with_proxy():
    """使用代理测试登录流程"""
    print("=== 使用代理测试登录流程 ===")
    
    # 方法1: 使用不同的请求头
    print("\n方法1: 使用不同的请求头...")
    
    # 创建全新的会话，使用不同的请求头
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'X-Forwarded-For': '192.168.1.100',
        'X-Real-IP': '192.168.1.100'
    })
    
    try:
        # 步骤1: 直接访问JAccount登录页面
        print("\n1. 直接访问JAccount登录页面...")
        jaccount_url = "https://jaccount.sjtu.edu.cn/jaccount/jalogin"
        response = session.get(jaccount_url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
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
                            
                        return True
                    else:
                        print(f"✗ 验证码返回的不是图片: {content_type}")
                        print(f"内容预览: {captcha_response.text[:200]}...")
                else:
                    print(f"✗ 获取验证码失败: {captcha_response.status_code}")
            else:
                print("✗ 未找到验证码UUID")
        else:
            print(f"✗ 访问JAccount失败: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def test_oauth_flow():
    """测试OAuth流程"""
    print("\n=== 测试OAuth流程 ===")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
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
        # 步骤1: 访问OAuth授权页面
        print("\n1. 访问OAuth授权页面...")
        oauth_url = "https://jaccount.sjtu.edu.cn/oauth2/authorize"
        params = {
            'response_type': 'code',
            'client_id': 'CN0jz/kocIey765dzMbV5erSBBqwiHGWn4qALMErOi5s',
            'redirect_uri': 'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
            'scope': 'basic',
            'state': 'test'
        }
        
        response = session.get(oauth_url, params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
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
                        with open('/tmp/captcha_oauth.png', 'wb') as f:
                            f.write(captcha_response.content)
                        print("✓ 验证码图片已保存到 /tmp/captcha_oauth.png")
                        return True
                    else:
                        print(f"✗ 验证码返回的不是图片: {content_type}")
                        print(f"内容预览: {captcha_response.text[:200]}...")
                else:
                    print(f"✗ 获取验证码失败: {captcha_response.status_code}")
            else:
                print("✗ 未找到验证码UUID")
        else:
            print(f"✗ 访问OAuth失败: {response.status_code}")
            
    except Exception as e:
        print(f"✗ OAuth测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    success1 = test_with_proxy()
    if not success1:
        success2 = test_oauth_flow()
        if not success2:
            print("\n✗ 所有测试方法都失败了")
        else:
            print("\n✓ OAuth流程测试成功")
    else:
        print("\n✓ 直接JAccount访问测试成功")
