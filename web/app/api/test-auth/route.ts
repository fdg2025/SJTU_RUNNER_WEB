import { NextRequest, NextResponse } from 'next/server';
import { generateSessionToken, validateSessionToken } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    // 生成一个新token
    const newToken = generateSessionToken();
    
    // 立即验证这个token
    const isValid = validateSessionToken(newToken);
    
    // 从请求中获取token（如果有的话）
    const providedToken = request.nextUrl.searchParams.get('token');
    let providedTokenValid = false;
    
    if (providedToken) {
      providedTokenValid = validateSessionToken(providedToken);
    }
    
    return NextResponse.json({
      success: true,
      data: {
        newToken,
        newTokenValid: isValid,
        providedToken,
        providedTokenValid,
        timestamp: Date.now(),
        message: 'Token测试完成'
      }
    });
    
  } catch (error) {
    console.error('Auth test error:', error);
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
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
