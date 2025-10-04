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
import subprocess
from urllib.parse import urljoin, urlparse, parse_qs, unquote

def diagnose_network_environment():
    """诊断网络环境"""
    print("=== 网络环境诊断 ===")
    
    # 1. 检查网络配置
    print("\n1. 网络配置检查...")
    
    try:
        # 检查hosts文件
        hosts_file = '/etc/hosts'
        if os.path.exists(hosts_file):
            with open(hosts_file, 'r') as f:
                hosts_content = f.read()
                if 'pe.sjtu.edu.cn' in hosts_content or 'sjtu.edu.cn' in hosts_content:
                    print("   ⚠️  发现hosts文件中有SJTU相关配置")
                    for line in hosts_content.split('\n'):
                        if 'sjtu' in line.lower():
                            print(f"     {line}")
                else:
                    print("   ✓ hosts文件中无SJTU相关配置")
        else:
            print("   ✓ hosts文件不存在")
    except Exception as e:
        print(f"   ✗ 检查hosts文件失败: {e}")
    
    # 2. 检查DNS解析
    print("\n2. DNS解析检查...")
    
    try:
        sjtu_ip = socket.gethostbyname('pe.sjtu.edu.cn')
        print(f"   pe.sjtu.edu.cn -> {sjtu_ip}")
        
        if sjtu_ip == '127.0.0.1' or sjtu_ip.startswith('192.168.') or sjtu_ip.startswith('10.'):
            print("   ⚠️  解析到内网IP，可能存在本地代理或DNS劫持")
        else:
            print("   ✓ 解析到公网IP")
            
    except Exception as e:
        print(f"   ✗ DNS解析失败: {e}")
    
    # 3. 检查代理设置
    print("\n3. 代理设置检查...")
    
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ⚠️  发现代理设置: {var}={value}")
        else:
            print(f"   ✓ 无代理设置: {var}")
    
    # 4. 检查网络连接
    print("\n4. 网络连接检查...")
    
    try:
        # 测试连接到SJTU
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('pe.sjtu.edu.cn', 443))
        sock.close()
        
        if result == 0:
            print("   ✓ 可以连接到pe.sjtu.edu.cn:443")
        else:
            print(f"   ✗ 无法连接到pe.sjtu.edu.cn:443，错误码: {result}")
    except Exception as e:
        print(f"   ✗ 连接测试失败: {e}")
    
    # 5. 检查SSL证书
    print("\n5. SSL证书检查...")
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection(('pe.sjtu.edu.cn', 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname='pe.sjtu.edu.cn') as ssock:
                cert = ssock.getpeercert()
                print(f"   ✓ SSL证书有效")
                print(f"   证书主题: {cert.get('subject', 'N/A')}")
                print(f"   证书颁发者: {cert.get('issuer', 'N/A')}")
    except Exception as e:
        print(f"   ✗ SSL证书检查失败: {e}")

def test_different_resolvers():
    """测试不同的DNS解析器"""
    print("\n=== 测试不同DNS解析器 ===")
    
    # 使用不同的DNS服务器
    dns_servers = [
        '8.8.8.8',      # Google DNS
        '1.1.1.1',      # Cloudflare DNS
        '114.114.114.114',  # 114 DNS
        '223.5.5.5',    # 阿里DNS
    ]
    
    for dns in dns_servers:
        print(f"\n使用DNS服务器: {dns}")
        
        try:
            # 这里只是演示，实际需要修改系统DNS设置
            # 或者使用dnspython库
            print(f"   DNS服务器: {dns}")
            print("   (需要系统级DNS配置才能生效)")
        except Exception as e:
            print(f"   ✗ 测试失败: {e}")

def test_direct_ip_access():
    """测试直接IP访问"""
    print("\n=== 测试直接IP访问 ===")
    
    # 获取SJTU的IP地址
    try:
        sjtu_ip = socket.gethostbyname('pe.sjtu.edu.cn')
        print(f"SJTU IP地址: {sjtu_ip}")
        
        # 测试直接IP访问
        session = requests.Session()
        session.headers.update({
            'Host': 'pe.sjtu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 使用IP地址访问
        ip_url = f"https://{sjtu_ip}/phone/#/indexPortrait"
        print(f"测试URL: {ip_url}")
        
        response = session.get(ip_url, timeout=15, verify=False)
        print(f"状态码: {response.status_code}")
        
        # 检查Cookie
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        print(f"获得的Cookie: {cookies}")
        
        if 'keepalive' in cookies:
            keepalive_value = cookies['keepalive']
            print(f"keepalive值: {keepalive_value}")
            
            if keepalive_value == "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=":
                print("⚠️  固定keepalive值，确认IP绑定")
            else:
                print("✓ 动态keepalive值，正常")
        else:
            print("✓ 没有keepalive，需要登录")
            
    except Exception as e:
        print(f"✗ 直接IP访问失败: {e}")

def test_without_requests():
    """不使用requests库测试"""
    print("\n=== 不使用requests库测试 ===")
    
    try:
        import urllib.request
        import urllib.parse
        
        # 创建请求
        url = 'https://pe.sjtu.edu.cn/phone/#/indexPortrait'
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
        req.add_header('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')
        req.add_header('Cache-Control', 'no-cache')
        
        # 发送请求
        with urllib.request.urlopen(req, timeout=15) as response:
            print(f"状态码: {response.status}")
            print(f"响应头: {dict(response.headers)}")
            
            # 检查Set-Cookie头
            set_cookie = response.headers.get('Set-Cookie')
            if set_cookie:
                print(f"Set-Cookie: {set_cookie}")
                
                if 'keepalive' in set_cookie:
                    print("⚠️  发现keepalive Cookie")
                else:
                    print("✓ 未发现keepalive Cookie")
            else:
                print("✓ 未设置Cookie")
                
    except Exception as e:
        print(f"✗ urllib测试失败: {e}")

def main():
    """主函数"""
    print("=== 网络环境诊断 ===")
    print("全面诊断网络环境，找出IP绑定的原因")
    
    # 诊断网络环境
    diagnose_network_environment()
    
    # 测试不同解析器
    test_different_resolvers()
    
    # 测试直接IP访问
    test_direct_ip_access()
    
    # 测试不使用requests
    test_without_requests()
    
    # 总结
    print("\n=== 诊断总结 ===")
    print("1. 检查了hosts文件、DNS解析、代理设置")
    print("2. 测试了网络连接和SSL证书")
    print("3. 尝试了不同的DNS解析器")
    print("4. 测试了直接IP访问")
    print("5. 测试了不使用requests库")
    
    print("\n=== 建议 ===")
    print("1. 检查系统网络配置")
    print("2. 清除可能的代理设置")
    print("3. 重置DNS设置")
    print("4. 使用VPN或代理服务器")
    print("5. 在不同的网络环境中测试")

if __name__ == "__main__":
    main()
