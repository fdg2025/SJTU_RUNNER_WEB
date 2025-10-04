#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 JAccount 登录页面 HTML，提取关键信息
"""

import re
import json
from urllib.parse import urlparse, parse_qs

def analyze_jaccount_html():
    """分析 JAccount 登录页面 HTML"""
    
    # 读取保存的 HTML 文件
    with open('/Users/xin/Downloads/上海交通大学统一身份认证.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("=== JAccount 登录页面分析 ===\n")
    
    # 1. 提取 loginContext 对象
    login_context_match = re.search(r'var loginContext = \{(.*?)\};', html_content, re.DOTALL)
    if login_context_match:
        print("1. 登录上下文参数 (loginContext):")
        context_str = login_context_match.group(1)
        print(context_str)
        print()
        
        # 提取各个参数
        sid_match = re.search(r'sid:\s*"([^"]+)"', context_str)
        client_match = re.search(r'client:\s*"([^"]+)"', context_str)
        returl_match = re.search(r'returl:\s*"([^"]+)"', context_str)
        se_match = re.search(r'se:\s*"([^"]+)"', context_str)
        uuid_match = re.search(r'uuid:\s*"([^"]+)"', context_str)
        
        if sid_match:
            print(f"   sid: {sid_match.group(1)}")
        if client_match:
            print(f"   client: {client_match.group(1)}")
        if returl_match:
            print(f"   returl: {returl_match.group(1)}")
        if se_match:
            print(f"   se: {se_match.group(1)}")
        if uuid_match:
            print(f"   uuid: {uuid_match.group(1)}")
        print()
    
    # 2. 分析验证码相关
    captcha_img_match = re.search(r'<img id="captcha-img"[^>]*src="([^"]*)"', html_content)
    if captcha_img_match:
        print("2. 验证码图片 URL:")
        print(f"   {captcha_img_match.group(1)}")
        print()
    
    # 3. 分析验证码刷新函数
    refresh_captcha_match = re.search(r'function refreshCaptcha\(\)\s*\{[^}]*img\.src = \'([^\']+)\'[^}]*\}', html_content, re.DOTALL)
    if refresh_captcha_match:
        print("3. 验证码刷新 URL 模板:")
        print(f"   {refresh_captcha_match.group(1)}")
        print()
    
    # 4. 分析登录表单提交
    ajax_match = re.search(r'\$\.ajax\(\{[^}]*url:\s*"([^"]+)"[^}]*data:\s*params[^}]*\}', html_content, re.DOTALL)
    if ajax_match:
        print("4. 登录提交端点:")
        print(f"   {ajax_match.group(1)}")
        print()
    
    # 5. 分析表单字段
    print("5. 登录表单字段:")
    user_input = re.search(r'<input[^>]*id="input-login-user"[^>]*>', html_content)
    pass_input = re.search(r'<input[^>]*id="input-login-pass"[^>]*>', html_content)
    captcha_input = re.search(r'<input[^>]*id="input-login-captcha"[^>]*>', html_content)
    
    if user_input:
        print(f"   用户名输入框: {user_input.group(0)}")
    if pass_input:
        print(f"   密码输入框: {pass_input.group(0)}")
    if captcha_input:
        print(f"   验证码输入框: {captcha_input.group(0)}")
    print()
    
    # 6. 分析 checkForm 函数中的参数构建
    params_match = re.search(r'var params = \{(.*?)\};', html_content, re.DOTALL)
    if params_match:
        print("6. 登录参数构建:")
        print(params_match.group(1))
        print()
    
    # 7. 分析 WebSocket 连接
    websocket_match = re.search(r'socketUrl \+= "/jaccount/sub/([^"]+)"', html_content)
    if websocket_match:
        print("7. WebSocket 连接 UUID:")
        print(f"   {websocket_match.group(1)}")
        print()
    
    # 8. 分析登录类型
    login_type_match = re.search(r'loginType:\s*"([^"]+)"', html_content)
    if login_type_match:
        print("8. 登录类型:")
        print(f"   {login_type_match.group(1)}")
        print()
    
    # 9. 分析验证码预填值
    captcha_value_match = re.search(r'value="([^"]*)"[^>]*id="input-login-captcha"', html_content)
    if captcha_value_match:
        print("9. 验证码预填值:")
        print(f"   {captcha_value_match.group(1)}")
        print()
    
    # 10. 分析登录成功后的重定向
    redirect_match = re.search(r'window\.location\.href = "([^"]+)"', html_content)
    if redirect_match:
        print("10. 登录成功后重定向:")
        print(f"    {redirect_match.group(1)}")
        print()
    
    print("=== 分析完成 ===")
    
    # 返回关键信息
    return {
        'loginContext': {
            'sid': sid_match.group(1) if sid_match else None,
            'client': client_match.group(1) if client_match else None,
            'returl': returl_match.group(1) if returl_match else None,
            'se': se_match.group(1) if se_match else None,
            'uuid': uuid_match.group(1) if uuid_match else None,
            'loginType': login_type_match.group(1) if login_type_match else None
        },
        'captchaUrl': refresh_captcha_match.group(1) if refresh_captcha_match else None,
        'loginEndpoint': ajax_match.group(1) if ajax_match else None,
        'websocketUuid': websocket_match.group(1) if websocket_match else None,
        'captchaPrefilled': captcha_value_match.group(1) if captcha_value_match else None
    }

if __name__ == "__main__":
    result = analyze_jaccount_html()
    print("\n=== 提取的关键信息 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
