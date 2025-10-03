import { NextRequest, NextResponse } from 'next/server';
import { validateSessionToken } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const authToken = request.cookies.get('auth-token')?.value || 
                     request.headers.get('authorization')?.replace('Bearer ', '');
    
    if (!authToken || !validateSessionToken(authToken)) {
      return NextResponse.json({
        success: false,
        error: '未授权访问，请重新登录'
      }, { status: 401 });
    }

    const { cookie } = await request.json();
    
    if (!cookie) {
      return NextResponse.json({
        success: false,
        error: 'Cookie不能为空'
      }, { status: 400 });
    }

    // Basic format validation
    if (!cookie.includes('keepalive=') || !cookie.includes('JSESSIONID=')) {
      return NextResponse.json({
        success: false,
        error: 'Cookie格式不正确，必须包含keepalive和JSESSIONID'
      }, { status: 400 });
    }

    // Test Cookie by making a simple request to SJTU API
    const testUrl = 'https://pe.sjtu.edu.cn/phone/api/uid';
    const headers = {
      "Host": "pe.sjtu.edu.cn",
      "Connection": "keep-alive",
      "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0",
      "Accept": "application/json, text/plain, */*",
      "Content-Type": "application/json;charset=utf-8",
      "Cookie": cookie
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const response = await fetch(testUrl, {
        method: 'GET',
        headers,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        if (response.status === 302 || response.status === 401) {
          return NextResponse.json({
            success: false,
            error: 'Cookie已失效，请重新登录获取'
          });
        }
        return NextResponse.json({
          success: false,
          error: `Cookie验证失败: HTTP ${response.status}`
        });
      }
      
      const result = await response.json();
      
      if (result?.code === 0 && result?.data?.uid) {
        return NextResponse.json({
          success: true,
          message: 'Cookie有效',
          data: {
            uid: result.data.uid,
            validatedAt: new Date().toISOString()
          }
        });
      } else {
        return NextResponse.json({
          success: false,
          error: 'Cookie无效或已过期'
        });
      }
      
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return NextResponse.json({
          success: false,
          error: 'Cookie验证超时，请检查网络连接'
        });
      }
      
      return NextResponse.json({
        success: false,
        error: `Cookie验证失败: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
    
  } catch (error) {
    console.error('Cookie validation error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

