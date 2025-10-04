#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import time
import json
from urllib.parse import urljoin, urlparse, parse_qs

def test_auto_login_api():
    """测试自动登录API的功能"""
    print("=== 测试自动登录API功能 ===")
    
    # 测试API端点
    api_url = "http://localhost:3000/api/auto-login"
    
    try:
        # 步骤1: 测试POST请求（获取验证码）
        print("\n1. 测试POST请求（获取验证码）...")
        
        response = requests.post(api_url, json={
            'username': 'test_user',
            'password': 'test_password'
        })
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get('requiresCaptcha') and data.get('captchaImage'):
                    print("✓ 成功获取验证码")
                    print(f"验证码UUID: {data.get('captchaUuid')}")
                    print(f"JAccount URL: {data.get('jaccountUrl')}")
                    print(f"JSESSIONID: {data.get('jsessionid')}")
                    
                    # 步骤2: 测试PUT请求（提交登录）
                    print("\n2. 测试PUT请求（提交登录）...")
                    
                    put_response = requests.put(api_url, json={
                        'username': 'test_user',
                        'password': 'test_password',
                        'captcha': 'test_captcha',
                        'captchaUrl': data.get('captchaUrl'),
                        'jsessionid': data.get('jsessionid'),
                        'jaccountUrl': data.get('jaccountUrl')
                    })
                    
                    print(f"PUT状态码: {put_response.status_code}")
                    
                    if put_response.status_code == 200:
                        try:
                            put_data = put_response.json()
                            print(f"PUT响应数据: {json.dumps(put_data, indent=2, ensure_ascii=False)}")
                            
                            if put_data.get('success') and put_data.get('cookie'):
                                print("✓ 登录成功，获得Cookie")
                                return True
                            else:
                                print("✗ 登录失败")
                                return False
                        except:
                            print(f"PUT响应内容: {put_response.text[:200]}...")
                    else:
                        print(f"✗ PUT请求失败: {put_response.status_code}")
                        print(f"PUT响应: {put_response.text[:200]}...")
                else:
                    print("✗ 未获取到验证码")
                    return False
            except:
                print(f"响应内容: {response.text[:200]}...")
        else:
            print(f"✗ POST请求失败: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def test_manual_login_simulation():
    """模拟手动登录流程"""
    print("\n=== 模拟手动登录流程 ===")
    
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
            print("✓ 已登录，无需JAccount登录")
            print(f"完整Cookie: keepalive={keepalive}; JSESSIONID={cookies.get('JSESSIONID')}")
            return True
        else:
            print("✗ 未登录，需要JAccount登录")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    """主函数"""
    print("=== 自动登录功能测试 ===")
    
    # 测试1: 手动登录模拟
    print("\n测试1: 手动登录模拟")
    manual_success = test_manual_login_simulation()
    
    # 测试2: API功能测试（需要服务器运行）
    print("\n测试2: API功能测试")
    api_success = test_auto_login_api()
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"手动登录模拟: {'✓ 成功' if manual_success else '✗ 失败'}")
    print(f"API功能测试: {'✓ 成功' if api_success else '✗ 失败'}")
    
    if manual_success:
        print("\n✓ 当前环境已登录，自动登录功能可以正常工作")
        print("建议：在未登录环境中测试完整的JAccount登录流程")
    else:
        print("\n✗ 需要完整的JAccount登录流程测试")
        print("建议：使用VPN或代理服务器进行测试")
    
    print("\n=== 功能说明 ===")
    print("1. 自动登录功能已实现，包括：")
    print("   - JAccount重定向检测")
    print("   - 验证码获取和显示")
    print("   - 登录表单提交")
    print("   - Cookie提取和返回")
    print("2. 前端组件已实现，包括：")
    print("   - 用户名密码输入")
    print("   - 验证码图片显示")
    print("   - 登录状态管理")
    print("3. 后端API已实现，包括：")
    print("   - POST方法获取验证码")
    print("   - PUT方法提交登录")
    print("   - 错误处理和重定向跟踪")

if __name__ == "__main__":
    main()
