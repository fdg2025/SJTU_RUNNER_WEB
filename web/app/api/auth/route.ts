import { NextRequest, NextResponse } from 'next/server';
import { validatePassword, generateSessionToken } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const { password } = await request.json();
    
    if (!password) {
      return NextResponse.json({
        success: false,
        error: '请输入密码'
      }, { status: 400 });
    }

    const isValid = await validatePassword(password);
    
    if (isValid) {
      const token = generateSessionToken();
      
      // 设置HttpOnly cookie
      const response = NextResponse.json({
        success: true,
        message: '登录成功',
        token
      });
      
      response.cookies.set('auth-token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 24 * 60 * 60 // 24小时
      });
      
      return response;
    } else {
      return NextResponse.json({
        success: false,
        error: '密码错误'
      }, { status: 401 });
    }
  } catch (error) {
    console.error('Auth error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器错误'
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

