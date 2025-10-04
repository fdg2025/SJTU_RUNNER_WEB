#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
import json
import os
import tempfile
import socket
import ssl
from urllib.parse import urljoin, urlparse, parse_qs, unquote

def get_network_info():
    """获取网络信息"""
    print("=== 网络信息 ===")
    
    try:
        # 获取外网IP
        response = requests.get('https://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            data = response.json()
            external_ip = data.get('origin')
            print(f"外网IP: {external_ip}")
        else:
            print("无法获取外网IP")
    except Exception as e:
        print(f"获取外网IP失败: {e}")
    
    try:
        # 获取本地IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"本地IP: {local_ip}")
    except Exception as e:
        print(f"获取本地IP失败: {e}")
    
    try:
        # 获取DNS信息
        sjtu_ip = socket.gethostbyname('pe.sjtu.edu.cn')
        print(f"pe.sjtu.edu.cn IP: {sjtu_ip}")
    except Exception as e:
        print(f"获取SJTU IP失败: {e}")

def create_fresh_session():
    """创建全新的会话，完全重置"""
    print("\n=== 创建全新会话 ===")
    
    # 创建全新的会话
    session = requests.Session()
    
    # 重置所有配置
    session.cookies.clear()
    session.headers.clear()
    session.auth = None
    session.proxies.clear()
    session.stream = False
    session.verify = True
    session.cert = None
    
    # 设置全新的请求头
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
    
    print("✓ 创建全新会话完成")
    print(f"  User-Agent: {session.headers['User-Agent'][:50]}...")
    print(f"  Cookie数量: {len(session.cookies)}")
    print(f"  代理设置: {session.proxies}")
    
    return session

def test_direct_access():
    """测试直接访问，绕过所有缓存"""
    print("\n=== 测试直接访问 ===")
    
    session = create_fresh_session()
    
    try:
        # 测试1: 直接访问手机页面，不使用重定向
        print("\n1. 直接访问手机页面...")
        url = 'https://pe.sjtu.edu.cn/phone/#/indexPortrait'
        
        # 添加随机参数避免缓存
        timestamp = int(time.time() * 1000)
        url_with_timestamp = f"{url}?t={timestamp}"
        
        response = session.get(url_with_timestamp, timeout=15, allow_redirects=False)
        print(f"   状态码: {response.status_code}")
        print(f"   响应URL: {response.url}")
        
        if response.status_code == 302:
            location = response.headers.get('Location')
            print(f"   重定向到: {location}")
            
            if 'jaccount.sjtu.edu.cn' in location:
                print("   ✓ 重定向到JAccount，需要登录")
                
                # 跟随重定向
                response = session.get(location, timeout=15)
                print(f"   JAccount状态码: {response.status_code}")
                
                # 检查Cookie
                cookies = {}
                for cookie in session.cookies:
                    cookies[cookie.name] = cookie.value
                print(f"   获得的Cookie: {cookies}")
                
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
            else:
                print(f"   ✗ 未重定向到JAccount: {location}")
                return False
        else:
            print(f"   ✗ 未重定向，状态码: {response.status_code}")
            
            # 检查Cookie
            cookies = {}
            for cookie in session.cookies:
                cookies[cookie.name] = cookie.value
            print(f"   获得的Cookie: {cookies}")
            
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

def test_with_different_ports():
    """测试不同的端口和协议"""
    print("\n=== 测试不同端口和协议 ===")
    
    test_urls = [
        'https://pe.sjtu.edu.cn:443/phone/#/indexPortrait',
        'https://pe.sjtu.edu.cn:80/phone/#/indexPortrait',
        'http://pe.sjtu.edu.cn/phone/#/indexPortrait',
        'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
    ]
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n测试 {i}: {url}")
        
        session = create_fresh_session()
        
        try:
            response = session.get(url, timeout=15, allow_redirects=False)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('Location')
                print(f"   重定向到: {location}")
                
                if 'jaccount.sjtu.edu.cn' in location:
                    print("   ✓ 重定向到JAccount")
                    results.append(True)
                else:
                    print("   ✗ 未重定向到JAccount")
                    results.append(False)
            else:
                print("   ✗ 未重定向")
                results.append(False)
                
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")
            results.append(False)
    
    success_count = sum(results)
    print(f"\n端口测试结果: {success_count}/{len(results)} 成功")
    
    return success_count > 0

def test_ssl_verification():
    """测试SSL验证"""
    print("\n=== 测试SSL验证 ===")
    
    session = create_fresh_session()
    
    # 测试1: 启用SSL验证
    print("\n1. 启用SSL验证...")
    session.verify = True
    
    try:
        response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait', timeout=15)
        print(f"   SSL验证状态码: {response.status_code}")
        
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"   Cookie: {cookies}")
        
    except Exception as e:
        print(f"   SSL验证失败: {e}")
    
    # 测试2: 禁用SSL验证
    print("\n2. 禁用SSL验证...")
    session.verify = False
    
    try:
        response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait', timeout=15)
        print(f"   无SSL验证状态码: {response.status_code}")
        
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"   Cookie: {cookies}")
        
    except Exception as e:
        print(f"   无SSL验证失败: {e}")

def main():
    """主函数"""
    print("=== 全新网络环境测试 ===")
    print("完全重置网络环境，测试SJTU登录流程")
    
    # 获取网络信息
    get_network_info()
    
    # 测试1: 直接访问
    direct_success = test_direct_access()
    
    # 测试2: 不同端口
    port_success = test_with_different_ports()
    
    # 测试3: SSL验证
    test_ssl_verification()
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"直接访问测试: {'✓ 成功' if direct_success else '✗ 失败'}")
    print(f"端口测试: {'✓ 成功' if port_success else '✗ 失败'}")
    
    if direct_success or port_success:
        print("\n✓ 找到可用的访问方式")
        print("建议: 可以继续测试完整的登录流程")
    else:
        print("\n✗ 所有测试都失败")
        print("建议: 使用VPN或代理服务器更换IP地址")
        print("      或在不同的网络环境中测试")

if __name__ == "__main__":
    main()
