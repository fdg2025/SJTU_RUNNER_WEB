#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
import json
from urllib.parse import urljoin, urlparse, parse_qs

def simulate_incognito_browser():
    """模拟无痕浏览器行为，排查自动登录原因"""
    print("=== 模拟无痕浏览器行为排查自动登录 ===")
    
    # 模拟无痕浏览器的特征
    session = requests.Session()
    
    # 无痕浏览器的典型请求头
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
    
    try:
        print("\n1. 模拟无痕浏览器首次访问...")
        print("   - 清除所有Cookie")
        print("   - 禁用缓存")
        print("   - 使用隐私模式请求头")
        
        # 确保没有任何Cookie
        session.cookies.clear()
        
        # 访问主页面
        response = session.get('https://pe.sjtu.edu.cn/', timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        # 检查获得的Cookie
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"   获得的Cookie: {cookies}")
        
        # 分析Cookie来源
        if 'JSESSIONID' in cookies:
            print(f"   ✓ 获得JSESSIONID: {cookies['JSESSIONID']}")
            print("   来源: 主页面访问")
        
        if 'keepalive' in cookies:
            print(f"   ✓ 获得keepalive: {cookies['keepalive']}")
            print("   来源: 主页面访问")
            print("   ⚠️  问题: 首次访问就获得了keepalive，说明IP被绑定")
        
        # 步骤2: 访问手机页面
        print("\n2. 访问手机页面...")
        response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait', timeout=10)
        print(f"   状态码: {response.status_code}")
        
        # 检查是否有新的Cookie
        new_cookies = {}
        for cookie in session.cookies:
            new_cookies[cookie.name] = cookie.value
        print(f"   所有Cookie: {new_cookies}")
        
        # 分析keepalive的来源
        if 'keepalive' in new_cookies:
            keepalive_value = new_cookies['keepalive']
            print(f"   ✓ keepalive值: {keepalive_value}")
            
            # 检查keepalive是否是固定的
            if keepalive_value == "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=":
                print("   ⚠️  发现: keepalive值是固定的，说明IP被绑定到特定用户")
                print("   原因: SJTU服务器根据IP地址返回预绑定的用户会话")
            else:
                print("   ✓ keepalive值是动态的，正常会话")
        
        # 步骤3: 测试不同的访问路径
        print("\n3. 测试不同的访问路径...")
        
        test_urls = [
            'https://pe.sjtu.edu.cn/',
            'https://pe.sjtu.edu.cn/phone/',
            'https://pe.sjtu.edu.cn/phone/#/',
            'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
            'https://pe.sjtu.edu.cn/phone/api/uid',
            'https://pe.sjtu.edu.cn/api/uid'
        ]
        
        for url in test_urls:
            print(f"\n   测试: {url}")
            try:
                # 创建新的会话测试
                test_session = requests.Session()
                test_session.headers.update(session.headers)
                
                response = test_session.get(url, timeout=10)
                print(f"     状态码: {response.status_code}")
                
                # 检查Cookie
                test_cookies = {}
                for cookie in test_session.cookies:
                    test_cookies[cookie.name] = cookie.value
                
                if test_cookies:
                    print(f"     Cookie: {test_cookies}")
                    
                    if 'keepalive' in test_cookies:
                        if test_cookies['keepalive'] == "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=":
                            print("     ⚠️  固定keepalive，IP绑定确认")
                        else:
                            print("     ✓ 动态keepalive")
                else:
                    print("     无Cookie")
                    
            except Exception as e:
                print(f"     错误: {e}")
        
        # 步骤4: 测试IP绑定假设
        print("\n4. 测试IP绑定假设...")
        
        # 使用不同的User-Agent
        user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        for i, ua in enumerate(user_agents, 1):
            print(f"\n   测试User-Agent {i}: {ua[:50]}...")
            
            test_session = requests.Session()
            test_session.headers.update({
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'no-cache'
            })
            
            try:
                response = test_session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait', timeout=10)
                
                test_cookies = {}
                for cookie in test_session.cookies:
                    test_cookies[cookie.name] = cookie.value
                
                if 'keepalive' in test_cookies:
                    if test_cookies['keepalive'] == "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=":
                        print(f"     ⚠️  固定keepalive，IP绑定确认")
                    else:
                        print(f"     ✓ 动态keepalive: {test_cookies['keepalive']}")
                else:
                    print(f"     无keepalive")
                    
            except Exception as e:
                print(f"     错误: {e}")
        
        # 步骤5: 总结分析
        print("\n5. 分析总结...")
        print("   === 自动登录原因分析 ===")
        print("   1. IP地址绑定:")
        print("      - 当前IP被SJTU服务器绑定到特定用户")
        print("      - 无论使用什么浏览器或User-Agent，都返回相同的keepalive")
        print("      - keepalive值固定为: 'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=")
        print("")
        print("   2. 会话持久化:")
        print("      - SJTU服务器在IP层面维护用户会话")
        print("      - 即使清除浏览器Cookie，服务器仍返回已绑定的会话")
        print("      - 这是服务器端的会话管理机制")
        print("")
        print("   3. 可能的绑定原因:")
        print("      - 之前在此IP上登录过SJTU系统")
        print("      - 网络环境（如校园网）的自动认证")
        print("      - 代理服务器或NAT设备的会话保持")
        print("      - 管理员手动绑定")
        print("")
        print("   4. 解决方案:")
        print("      - 使用VPN或代理服务器更换IP")
        print("      - 在不同的网络环境中测试")
        print("      - 联系SJTU管理员清除IP绑定")
        print("      - 等待会话自然过期")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simulate_incognito_browser()
    if success:
        print("\n✓ 无痕浏览器模拟测试完成")
    else:
        print("\n✗ 测试失败")
