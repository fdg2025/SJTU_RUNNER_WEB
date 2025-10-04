#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_cookie_validity():
    """测试Cookie的有效性"""
    print("=== 测试Cookie有效性 ===")
    
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
    
    try:
        # 测试UID接口
        print("\n1. 测试UID接口...")
        response = session.get('https://pe.sjtu.edu.cn/phone/api/uid')
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✓ 成功获取UID数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get('code') == 0 and data.get('data', {}).get('uid'):
                    uid = data['data']['uid']
                    print(f"✓ 获得UID: {uid}")
                    
                    # 测试规则接口
                    print("\n2. 测试规则接口...")
                    rule_response = session.get('https://pe.sjtu.edu.cn/phone/api/pointRule', 
                                              headers={'authorization': uid})
                    print(f"规则接口状态码: {rule_response.status_code}")
                    
                    if rule_response.status_code == 200:
                        try:
                            rule_data = rule_response.json()
                            print(f"✓ 成功获取规则数据: {json.dumps(rule_data, indent=2, ensure_ascii=False)}")
                        except:
                            print(f"规则接口响应: {rule_response.text[:200]}...")
                    else:
                        print(f"✗ 规则接口失败: {rule_response.status_code}")
                        print(f"响应: {rule_response.text[:200]}...")
                else:
                    print(f"✗ UID数据格式不正确: {data}")
            except Exception as e:
                print(f"✗ 解析UID响应失败: {e}")
                print(f"响应内容: {response.text[:200]}...")
        else:
            print(f"✗ UID接口失败: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cookie_validity()
