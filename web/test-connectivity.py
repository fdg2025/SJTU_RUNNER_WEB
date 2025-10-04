#!/usr/bin/env python3
import requests
import time

print('=== SJTU 服务器连接测试 ===')

# 测试目标URL
test_urls = [
    'https://pe.sjtu.edu.cn/phone/#/indexPortrait',
    'https://jaccount.sjtu.edu.cn',
    'https://jaccount.sjtu.edu.cn/jaccount/jalogin',
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

for url in test_urls:
    print(f'\n测试 URL: {url}')
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
        end_time = time.time()
        
        print(f'  状态码: {response.status_code}')
        print(f'  响应时间: {end_time - start_time:.2f}秒')
        print(f'  内容长度: {len(response.text)}')
        
        # 检查 Set-Cookie 头
        if 'Set-Cookie' in response.headers:
            print(f'  Set-Cookie: {response.headers["Set-Cookie"][:100]}...')
        else:
            print('  Set-Cookie: 无')
            
        # 检查 Location 头
        if 'Location' in response.headers:
            print(f'  Location: {response.headers["Location"]}')
        else:
            print('  Location: 无')
            
    except requests.exceptions.Timeout:
        print('  ❌ 请求超时')
    except requests.exceptions.ConnectionError as e:
        print(f'  ❌ 连接错误: {e}')
    except requests.exceptions.RequestException as e:
        print(f'  ❌ 请求错误: {e}')
    except Exception as e:
        print(f'  ❌ 未知错误: {e}')

print('\n=== 测试完成 ===')
