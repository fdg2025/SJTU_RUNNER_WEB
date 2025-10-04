#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_correct_api():
    """测试正确的API路径"""
    print("=== 测试正确的API路径 ===")
    
    # 从测试中获得的Cookie
    cookie = "keepalive='ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=; JSESSIONID=71A7C802BB71FFA5743734331013044B.jaccount32"
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://pe.sjtu.edu.cn/phone/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    })
    
    # 设置Cookie
    session.cookies.update({
        'keepalive': "'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=",
        'JSESSIONID': '71A7C802BB71FFA5743734331013044B.jaccount32'
    })
    
    # 测试不同的API路径
    api_paths = [
        'https://pe.sjtu.edu.cn/phone/api/uid',
        'https://pe.sjtu.edu.cn/api/uid',
        'https://pe.sjtu.edu.cn/phone/api/user/uid',
        'https://pe.sjtu.edu.cn/phone/api/user/info',
        'https://pe.sjtu.edu.cn/phone/api/auth/uid',
        'https://pe.sjtu.edu.cn/phone/api/auth/user',
        'https://pe.sjtu.edu.cn/phone/api/currentUser',
        'https://pe.sjtu.edu.cn/phone/api/profile',
        'https://pe.sjtu.edu.cn/phone/api/user/profile',
        'https://pe.sjtu.edu.cn/phone/api/user/current'
    ]
    
    try:
        for i, api_path in enumerate(api_paths, 1):
            print(f"\n{i}. 测试API: {api_path}")
            try:
                response = session.get(api_path)
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✓ 成功获取数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        
                        if data.get('code') == 0 and data.get('data'):
                            print(f"✓ 找到有效数据!")
                            return api_path, data
                    except:
                        print(f"响应内容: {response.text[:200]}...")
                elif response.status_code == 401:
                    print("✗ 需要认证")
                elif response.status_code == 403:
                    print("✗ 禁止访问")
                elif response.status_code == 404:
                    print("✗ 未找到")
                else:
                    print(f"✗ 其他错误: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ 请求失败: {e}")
                
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_correct_api()
