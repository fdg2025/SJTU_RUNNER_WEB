#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
import json
import hashlib
import base64
from urllib.parse import urljoin, urlparse, parse_qs

def analyze_keepalive_mechanism():
    """深入分析keepalive的生成机制"""
    print("=== 深入分析keepalive生成机制 ===")
    
    # 固定值分析
    fixed_keepalive = "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY="
    print(f"固定keepalive值: {fixed_keepalive}")
    
    # 分析keepalive的结构
    print("\n1. keepalive结构分析...")
    
    # 移除首尾的单引号
    clean_keepalive = fixed_keepalive.strip("'")
    print(f"清理后的值: {clean_keepalive}")
    
    # 尝试Base64解码
    try:
        decoded = base64.b64decode(clean_keepalive)
        print(f"Base64解码: {decoded}")
        print(f"解码长度: {len(decoded)} bytes")
        
        # 尝试分析内容
        if len(decoded) == 32:
            print("✓ 32字节长度，可能是MD5哈希")
            print(f"十六进制: {decoded.hex()}")
        elif len(decoded) == 64:
            print("✓ 64字节长度，可能是SHA256哈希")
            print(f"十六进制: {decoded.hex()}")
        else:
            print(f"未知长度: {len(decoded)} bytes")
            
    except Exception as e:
        print(f"Base64解码失败: {e}")
    
    # 分析可能的生成方式
    print("\n2. 可能的生成方式分析...")
    
    # 测试IP地址哈希
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"本地IP: {local_ip}")
        
        # 尝试用IP生成哈希
        ip_hash_md5 = hashlib.md5(local_ip.encode()).digest()
        ip_hash_b64 = base64.b64encode(ip_hash_md5).decode()
        print(f"IP MD5 Base64: {ip_hash_b64}")
        
        if ip_hash_b64 == clean_keepalive:
            print("✓ 匹配！keepalive可能是基于IP地址的MD5哈希")
        else:
            print("✗ 不匹配")
            
    except Exception as e:
        print(f"IP分析失败: {e}")
    
    # 测试时间戳相关
    print("\n3. 时间戳分析...")
    current_time = int(time.time())
    print(f"当前时间戳: {current_time}")
    
    # 尝试不同的时间戳
    test_timestamps = [
        current_time,
        current_time - 3600,  # 1小时前
        current_time - 86400,  # 1天前
        current_time - 604800,  # 1周前
        1640995200,  # 2022-01-01
        1609459200,  # 2021-01-01
    ]
    
    for ts in test_timestamps:
        ts_hash = hashlib.md5(str(ts).encode()).digest()
        ts_b64 = base64.b64encode(ts_hash).decode()
        print(f"时间戳 {ts}: {ts_b64}")
        
        if ts_b64 == clean_keepalive:
            print("✓ 匹配！keepalive可能是基于时间戳的MD5哈希")
            break
    else:
        print("✗ 时间戳分析无匹配")
    
    # 测试用户名相关
    print("\n4. 用户名分析...")
    test_usernames = [
        'admin',
        'user',
        'sjtu',
        'student',
        'teacher',
        'guest',
        'test',
        'default'
    ]
    
    for username in test_usernames:
        user_hash = hashlib.md5(username.encode()).digest()
        user_b64 = base64.b64encode(user_hash).decode()
        print(f"用户名 {username}: {user_b64}")
        
        if user_b64 == clean_keepalive:
            print("✓ 匹配！keepalive可能是基于用户名的MD5哈希")
            break
    else:
        print("✗ 用户名分析无匹配")
    
    # 测试组合哈希
    print("\n5. 组合哈希分析...")
    
    # IP + 时间戳
    try:
        combined_ip_time = f"{local_ip}_{current_time}"
        combined_hash = hashlib.md5(combined_ip_time.encode()).digest()
        combined_b64 = base64.b64encode(combined_hash).decode()
        print(f"IP+时间戳: {combined_b64}")
        
        if combined_b64 == clean_keepalive:
            print("✓ 匹配！keepalive可能是基于IP+时间戳的MD5哈希")
    except:
        pass
    
    # 测试网络信息
    print("\n6. 网络信息分析...")
    
    try:
        # 获取外网IP
        response = requests.get('https://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            data = response.json()
            external_ip = data.get('origin')
            print(f"外网IP: {external_ip}")
            
            # 用外网IP生成哈希
            ext_ip_hash = hashlib.md5(external_ip.encode()).digest()
            ext_ip_b64 = base64.b64encode(ext_ip_hash).decode()
            print(f"外网IP MD5 Base64: {ext_ip_b64}")
            
            if ext_ip_b64 == clean_keepalive:
                print("✓ 匹配！keepalive可能是基于外网IP的MD5哈希")
            else:
                print("✗ 不匹配")
                
    except Exception as e:
        print(f"外网IP获取失败: {e}")
    
    # 测试SJTU特定信息
    print("\n7. SJTU特定信息分析...")
    
    sjtu_info = [
        'sjtu.edu.cn',
        'pe.sjtu.edu.cn',
        'jaccount.sjtu.edu.cn',
        'SJTU',
        'Shanghai Jiao Tong University',
        '交大',
        '上海交通大学'
    ]
    
    for info in sjtu_info:
        info_hash = hashlib.md5(info.encode()).digest()
        info_b64 = base64.b64encode(info_hash).decode()
        print(f"SJTU信息 {info}: {info_b64}")
        
        if info_b64 == clean_keepalive:
            print("✓ 匹配！keepalive可能是基于SJTU信息的MD5哈希")
            break
    else:
        print("✗ SJTU信息分析无匹配")
    
    # 总结
    print("\n8. 分析总结...")
    print("   === keepalive生成机制分析 ===")
    print("   1. 固定值特征:")
    print(f"      - 值: {fixed_keepalive}")
    print(f"      - 长度: {len(clean_keepalive)} 字符")
    print(f"      - 类型: Base64编码")
    print("")
    print("   2. 可能来源:")
    print("      - 服务器端预生成的固定值")
    print("      - 基于IP地址的哈希")
    print("      - 基于用户ID的哈希")
    print("      - 基于时间戳的哈希")
    print("      - 组合信息的哈希")
    print("")
    print("   3. 绑定机制:")
    print("      - 服务器根据IP地址返回固定的keepalive")
    print("      - 这是服务器端的会话管理策略")
    print("      - 可能与网络环境或用户绑定相关")
    print("")
    print("   4. 影响:")
    print("      - 无法通过清除Cookie来重置会话")
    print("      - 需要更换IP或网络环境")
    print("      - 这是SJTU系统的安全机制")

def test_keepalive_validation():
    """测试keepalive的验证机制"""
    print("\n=== 测试keepalive验证机制 ===")
    
    # 测试不同的keepalive值
    test_values = [
        "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=",  # 固定值
        "test_keepalive_value",
        "invalid_keepalive",
        "",
        "random_string_12345"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    })
    
    for i, keepalive_value in enumerate(test_values, 1):
        print(f"\n{i}. 测试keepalive值: {keepalive_value}")
        
        # 清除Cookie
        session.cookies.clear()
        
        # 手动设置keepalive
        if keepalive_value:
            session.cookies.set('keepalive', keepalive_value)
        
        try:
            response = session.get('https://pe.sjtu.edu.cn/phone/#/indexPortrait', timeout=10)
            print(f"   状态码: {response.status_code}")
            
            # 检查服务器返回的Cookie
            server_cookies = {}
            for cookie in session.cookies:
                server_cookies[cookie.name] = cookie.value
            
            print(f"   服务器返回的Cookie: {server_cookies}")
            
            if 'keepalive' in server_cookies:
                if server_cookies['keepalive'] == keepalive_value:
                    print("   ✓ 服务器接受此keepalive值")
                else:
                    print(f"   ⚠️  服务器替换了keepalive值: {server_cookies['keepalive']}")
            else:
                print("   ✗ 服务器未返回keepalive")
                
        except Exception as e:
            print(f"   错误: {e}")

if __name__ == "__main__":
    analyze_keepalive_mechanism()
    test_keepalive_validation()
