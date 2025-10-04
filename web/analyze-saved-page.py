#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import base64
from urllib.parse import urlparse, parse_qs, unquote

def analyze_saved_page():
    """分析保存的JAccount登录页面"""
    print("=== 分析保存的JAccount登录页面 ===")
    
    # 读取保存的HTML文件
    try:
        with open('/Users/xin/Downloads/上海交通大学统一身份认证.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"✓ 成功读取HTML文件，大小: {len(html_content)} 字符")
    except Exception as e:
        print(f"✗ 读取HTML文件失败: {e}")
        return
    
    # 1. 分析页面基本信息
    print("\n1. 页面基本信息分析...")
    
    # 提取title
    title_match = re.search(r'<title>(.*?)</title>', html_content)
    if title_match:
        print(f"   页面标题: {title_match.group(1)}")
    
    # 提取base href
    base_match = re.search(r'<base href="([^"]*)"', html_content)
    if base_match:
        print(f"   Base URL: {base_match.group(1)}")
    
    # 2. 分析loginContext对象
    print("\n2. 分析loginContext对象...")
    
    # 提取loginContext
    context_match = re.search(r'var loginContext = ({.*?});', html_content, re.DOTALL)
    if context_match:
        context_str = context_match.group(1)
        print(f"   loginContext: {context_str}")
        
        # 解析各个参数
        sid_match = re.search(r'sid:\s*"([^"]*)"', context_str)
        if sid_match:
            print(f"   SID: {sid_match.group(1)}")
        
        client_match = re.search(r'client:\s*"([^"]*)"', context_str)
        if client_match:
            print(f"   Client: {client_match.group(1)}")
        
        returl_match = re.search(r'returl:\s*"([^"]*)"', context_str)
        if returl_match:
            returl = returl_match.group(1)
            print(f"   Return URL: {returl}")
            # 尝试解码
            try:
                decoded_returl = unquote(returl)
                print(f"   解码后: {decoded_returl}")
            except:
                pass
        
        se_match = re.search(r'se:\s*"([^"]*)"', context_str)
        if se_match:
            print(f"   SE: {se_match.group(1)}")
        
        uuid_match = re.search(r'uuid:\s*"([^"]*)"', context_str)
        if uuid_match:
            uuid = uuid_match.group(1)
            print(f"   UUID: {uuid}")
    
    # 3. 分析验证码机制
    print("\n3. 分析验证码机制...")
    
    # 查找验证码相关函数
    captcha_functions = [
        'setCaptchaCheckStatus',
        'showCaptcha', 
        'refreshCaptcha',
        'checkForm'
    ]
    
    for func in captcha_functions:
        if func in html_content:
            print(f"   ✓ 找到函数: {func}")
            
            # 查找函数定义
            func_match = re.search(rf'function {func}\s*\([^)]*\)\s*{{(.*?)}}', html_content, re.DOTALL)
            if func_match:
                func_body = func_match.group(1).strip()
                print(f"     函数体: {func_body[:100]}...")
    
    # 查找验证码URL
    captcha_url_match = re.search(r"img\.src = 'captcha\?uuid=([^']*)&t='", html_content)
    if captcha_url_match:
        captcha_uuid = captcha_url_match.group(1)
        print(f"   验证码UUID: {captcha_uuid}")
        print(f"   验证码URL: https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid={captcha_uuid}&t=timestamp")
    
    # 4. 分析登录表单
    print("\n4. 分析登录表单...")
    
    # 查找表单字段
    form_fields = [
        ('用户名', 'input-login-user'),
        ('密码', 'input-login-pass'), 
        ('验证码', 'input-login-captcha'),
        ('手机号', 'input-login-mobile'),
        ('短信验证码', 'input-login-sms')
    ]
    
    for field_name, field_id in form_fields:
        if f'id="{field_id}"' in html_content:
            print(f"   ✓ 找到字段: {field_name} ({field_id})")
            
            # 查找字段的默认值
            field_match = re.search(rf'id="{field_id}"[^>]*value="([^"]*)"', html_content)
            if field_match:
                default_value = field_match.group(1)
                print(f"     默认值: {default_value}")
    
    # 5. 分析WebSocket连接
    print("\n5. 分析WebSocket连接...")
    
    if 'WebSocket' in html_content:
        print("   ✓ 页面使用WebSocket")
        
        # 查找WebSocket URL
        ws_match = re.search(r'socketUrl \+= "/jaccount/sub/([^"]*)"', html_content)
        if ws_match:
            ws_uuid = ws_match.group(1)
            print(f"   WebSocket UUID: {ws_uuid}")
            print(f"   WebSocket URL: wss://jaccount.sjtu.edu.cn/jaccount/sub/{ws_uuid}")
        
        # 查找WebSocket消息处理
        ws_events = ['onmessage', 'onopen', 'onerror', 'onclose']
        for event in ws_events:
            if event in html_content:
                print(f"   ✓ WebSocket事件: {event}")
    
    # 6. 分析登录提交逻辑
    print("\n6. 分析登录提交逻辑...")
    
    # 查找checkForm函数
    checkform_match = re.search(r'var checkForm = function \(button\) {(.*?)}', html_content, re.DOTALL)
    if checkform_match:
        print("   ✓ 找到checkForm函数")
        
        # 分析登录参数
        params_match = re.search(r'var params = {(.*?)}', checkform_match.group(1), re.DOTALL)
        if params_match:
            print("   登录参数:")
            params_str = params_match.group(1)
            
            # 提取参数
            param_matches = re.findall(r'(\w+):\s*([^,\n]+)', params_str)
            for param_name, param_value in param_matches:
                print(f"     {param_name}: {param_value.strip()}")
        
        # 查找AJAX请求
        ajax_match = re.search(r'\$\.ajax\({(.*?)}\)', checkform_match.group(1), re.DOTALL)
        if ajax_match:
            print("   AJAX请求配置:")
            ajax_config = ajax_match.group(1)
            
            url_match = re.search(r'url:\s*"([^"]*)"', ajax_config)
            if url_match:
                print(f"     请求URL: {url_match.group(1)}")
            
            method_match = re.search(r'type:\s*[\'"]([^\'"]*)[\'"]', ajax_config)
            if method_match:
                print(f"     请求方法: {method_match.group(1)}")
    
    # 7. 分析自动登录机制
    print("\n7. 分析自动登录机制...")
    
    # 查找setCaptchaCheckStatus调用
    captcha_status_match = re.search(r'setCaptchaCheckStatus\([\'"]([^\'"]*)[\'"]\)', html_content)
    if captcha_status_match:
        status = captcha_status_match.group(1)
        print(f"   验证码检查状态: {status}")
        
        if status == 'failed':
            print("   ⚠️  验证码检查失败，需要显示验证码")
        elif status == 'passed':
            print("   ✓ 验证码检查通过，可能自动登录")
        elif status == 'waiting':
            print("   ⏳ 验证码检查等待中")
    
    # 查找可能的自动登录逻辑
    auto_login_indicators = [
        'expresslogin',
        'window.location.href',
        'navigating = true',
        'LOGIN'
    ]
    
    for indicator in auto_login_indicators:
        if indicator in html_content:
            print(f"   ✓ 找到自动登录指示器: {indicator}")
            
            # 查找相关代码
            if indicator == 'expresslogin':
                express_match = re.search(r'window\.location\.href = "expresslogin\?uuid=([^"]*)"', html_content)
                if express_match:
                    print(f"     快速登录UUID: {express_match.group(1)}")
    
    # 8. 分析页面状态
    print("\n8. 分析页面状态...")
    
    # 查找隐藏元素
    hidden_elements = [
        'captcha-box',
        'operate-buttons', 
        'captcha-verify',
        'login-with-sms',
        'login-with-password'
    ]
    
    for element in hidden_elements:
        element_match = re.search(rf'id="{element}"[^>]*style="[^"]*display:\s*none[^"]*"', html_content)
        if element_match:
            print(f"   ⚠️  元素隐藏: {element}")
        else:
            print(f"   ✓ 元素可见: {element}")
    
    # 9. 总结分析结果
    print("\n9. 分析总结...")
    print("   === 关键发现 ===")
    
    # 检查是否有预填充的验证码
    captcha_value_match = re.search(r'id="input-login-captcha"[^>]*value="([^"]*)"', html_content)
    if captcha_value_match:
        captcha_value = captcha_value_match.group(1)
        print(f"   ⚠️  验证码字段有预填充值: {captcha_value}")
        print("      这可能表明验证码已被自动处理")
    
    # 检查验证码检查状态
    if 'setCaptchaCheckStatus(\'failed\')' in html_content:
        print("   ⚠️  验证码检查状态为'failed'")
        print("      这表明需要用户输入验证码")
    elif 'setCaptchaCheckStatus(\'passed\')' in html_content:
        print("   ✓ 验证码检查状态为'passed'")
        print("      这可能表明验证码已通过，可以自动登录")
    
    # 检查是否有快速登录逻辑
    if 'expresslogin' in html_content:
        print("   ✓ 发现快速登录逻辑")
        print("      这表明存在自动登录机制")
    
    print("\n   === 建议 ===")
    print("   1. 检查验证码检查状态")
    print("   2. 分析WebSocket连接状态")
    print("   3. 检查是否有预填充的验证码")
    print("   4. 分析快速登录逻辑")

def analyze_captcha_mechanism():
    """分析验证码机制"""
    print("\n=== 验证码机制分析 ===")
    
    try:
        with open('/Users/xin/Downloads/上海交通大学统一身份认证.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"✗ 读取文件失败: {e}")
        return
    
    # 查找验证码相关代码
    captcha_patterns = [
        r'setCaptchaCheckStatus\([\'"]([^\'"]*)[\'"]\)',
        r'refreshCaptcha\(\)',
        r'captcha\?uuid=([^&]+)',
        r'input-login-captcha.*?value="([^"]*)"'
    ]
    
    for i, pattern in enumerate(captcha_patterns, 1):
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\n{i}. 验证码模式 {pattern}:")
            for match in matches:
                print(f"   匹配: {match}")

if __name__ == "__main__":
    analyze_saved_page()
    analyze_captcha_mechanism()
