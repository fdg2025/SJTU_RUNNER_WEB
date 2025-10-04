#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
import json
import os
import tempfile
from urllib.parse import urljoin, urlparse, parse_qs, unquote

def create_clean_session():
    """创建一个完全干净的会话，模拟无痕浏览器"""
    print("=== 创建干净会话 ===")
    
    # 创建全新的会话
    session = requests.Session()
    
    # 模拟无痕浏览器的请求头
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
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    })
    
    # 确保没有任何Cookie
    session.cookies.clear()
    
    print("✓ 创建干净会话完成")
    print(f"  User-Agent: {session.headers['User-Agent'][:50]}...")
    print(f"  Cookie数量: {len(session.cookies)}")
    
    return session

def test_clean_access(session):
    """测试干净访问"""
    print("\n=== 测试干净访问 ===")
    
    try:
        # 测试1: 访问主页面
        print("\n1. 访问SJTU主页面...")
        response = session.get('https://pe.sjtu.edu.cn/', timeout=15)
        print(f"   状态码: {response.status_code}")
        print(f"   响应URL: {response.url}")
        
        # 检查Cookie
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"   获得的Cookie: {cookies}")
        
        if cookies:
            print("   ⚠️  获得了Cookie，可能不是完全干净的环境")
        else:
            print("   ✓ 没有Cookie，环境干净")
        
        # 测试2: 访问手机页面
        print("\n2. 访问手机页面...")
        response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait', timeout=15)
        print(f"   状态码: {response.status_code}")
        print(f"   响应URL: {response.url}")
        
        # 检查Cookie
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"   获得的Cookie: {cookies}")
        
        # 分析Cookie
        if 'keepalive' in cookies:
            keepalive_value = cookies['keepalive']
            print(f"   ⚠️  获得keepalive: {keepalive_value}")
            
            if keepalive_value == "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=":
                print("   ⚠️  固定keepalive值，确认IP绑定")
                return False
            else:
                print("   ✓ 动态keepalive值，正常")
                return True
        else:
            print("   ✓ 没有keepalive，需要登录")
            return True
            
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_jaccount_redirect(session):
    """测试JAccount重定向"""
    print("\n=== 测试JAccount重定向 ===")
    
    try:
        # 访问需要登录的API
        print("\n1. 访问需要登录的API...")
        response = session.get('https://pe.sjtu.edu.cn/phone/api/uid', timeout=15)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location')
            print(f"   ✓ 重定向到: {location}")
            
            if 'jaccount.sjtu.edu.cn' in location:
                print("   ✓ 重定向到JAccount登录页面")
                
                # 访问JAccount登录页面
                print("\n2. 访问JAccount登录页面...")
                response = session.get(location, timeout=15)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    html = response.text
                    print(f"   页面大小: {len(html)} 字符")
                    
                    # 查找验证码UUID
                    uuid_matches = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', html, re.IGNORECASE)
                    if uuid_matches:
                        captcha_uuid = uuid_matches[0]
                        print(f"   ✓ 找到验证码UUID: {captcha_uuid}")
                        
                        # 测试验证码获取
                        print("\n3. 测试验证码获取...")
                        captcha_url = f"https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t={int(time.time() * 1000)}"
                        print(f"   验证码URL: {captcha_url}")
                        
                        captcha_response = session.get(captcha_url, timeout=10)
                        print(f"   验证码状态码: {captcha_response.status_code}")
                        print(f"   验证码Content-Type: {captcha_response.headers.get('Content-Type')}")
                        
                        if captcha_response.status_code == 200:
                            content_type = captcha_response.headers.get('Content-Type', '')
                            if 'image' in content_type:
                                print("   ✓ 成功获取验证码图片")
                                print(f"   图片大小: {len(captcha_response.content)} bytes")
                                
                                # 保存验证码图片
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                                    f.write(captcha_response.content)
                                    captcha_file = f.name
                                print(f"   ✓ 验证码图片已保存到: {captcha_file}")
                                return True
                            else:
                                print(f"   ✗ 返回的不是图片: {content_type}")
                                return False
                        else:
                            print(f"   ✗ 获取验证码失败: {captcha_response.status_code}")
                            return False
                    else:
                        print("   ✗ 未找到验证码UUID")
                        return False
                else:
                    print(f"   ✗ 访问JAccount失败: {response.status_code}")
                    return False
            else:
                print(f"   ✗ 未重定向到JAccount: {location}")
                return False
        else:
            print(f"   ✗ 未重定向，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_different_networks():
    """测试不同网络环境"""
    print("\n=== 测试不同网络环境 ===")
    
    # 测试不同的User-Agent
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    results = []
    
    for i, ua in enumerate(user_agents, 1):
        print(f"\n测试 {i}: {ua[:50]}...")
        
        session = create_clean_session()
        session.headers['User-Agent'] = ua
        
        # 测试访问
        success = test_clean_access(session)
        results.append((i, success))
        
        if success:
            print(f"   ✓ 测试 {i} 成功")
        else:
            print(f"   ✗ 测试 {i} 失败")
    
    return results

def main():
    """主函数"""
    print("=== 干净环境测试 ===")
    print("模拟无痕浏览器行为，测试SJTU登录流程")
    
    # 测试1: 创建干净会话
    session = create_clean_session()
    
    # 测试2: 测试干净访问
    clean_success = test_clean_access(session)
    
    if clean_success:
        print("\n✓ 环境干净，可以测试登录流程")
        
        # 测试3: 测试JAccount重定向
        redirect_success = test_jaccount_redirect(session)
        
        if redirect_success:
            print("\n✓ JAccount重定向和验证码获取成功")
        else:
            print("\n✗ JAccount重定向或验证码获取失败")
    else:
        print("\n✗ 环境不干净，存在IP绑定")
        
        # 测试4: 测试不同网络环境
        print("\n测试不同网络环境...")
        network_results = test_different_networks()
        
        success_count = sum(1 for _, success in network_results if success)
        print(f"\n网络环境测试结果: {success_count}/{len(network_results)} 成功")
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"干净环境测试: {'✓ 成功' if clean_success else '✗ 失败'}")
    
    if clean_success:
        print("建议: 可以继续测试完整的登录流程")
    else:
        print("建议: 使用VPN或代理服务器更换IP地址")
        print("      或在不同的网络环境中测试")

if __name__ == "__main__":
    main()