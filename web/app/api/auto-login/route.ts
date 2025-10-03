import { NextRequest, NextResponse } from 'next/server';
import { validateSessionToken } from '@/lib/auth';

interface LoginCredentials {
  username: string;
  password: string;
}

interface SJTULoginResponse {
  success: boolean;
  cookie?: string;
  error?: string;
  message?: string;
}

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const authToken = request.cookies.get('auth-token')?.value || 
                     request.headers.get('authorization')?.replace('Bearer ', '');
    
    if (!authToken || !validateSessionToken(authToken)) {
      return NextResponse.json({
        success: false,
        error: '认证令牌无效或已过期，请重新登录'
      }, { status: 401 });
    }

    const { username, password }: LoginCredentials = await request.json();
    
    if (!username || !password) {
      return NextResponse.json({
        success: false,
        error: '用户名和密码不能为空'
      }, { status: 400 });
    }

    console.log(`[Auto-Login] Attempting login for user: ${username}`);

    // Step 1: Get initial session by visiting the main page first
    const mainPageResponse = await fetch('https://pe.sjtu.edu.cn/', {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
      },
    });

    if (!mainPageResponse.ok) {
      throw new Error(`Failed to get main page: ${mainPageResponse.status}`);
    }

    // Extract JSESSIONID from main page response
    const mainPageSetCookie = mainPageResponse.headers.get('set-cookie');
    let jsessionid = '';
    if (mainPageSetCookie) {
      const jsessionidMatch = mainPageSetCookie.match(/JSESSIONID=([^;]+)/);
      if (jsessionidMatch) {
        jsessionid = jsessionidMatch[1];
        console.log(`[Auto-Login] Retrieved JSESSIONID: ${jsessionid.substring(0, 20)}...`);
      }
    }

    // Step 2: Get login page with the session cookie
    const loginPageResponse = await fetch('https://pe.sjtu.edu.cn/login', {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Cookie': jsessionid ? `JSESSIONID=${jsessionid}` : '',
      },
    });

    if (!loginPageResponse.ok) {
      throw new Error(`Failed to get login page: ${loginPageResponse.status}`);
    }

    const loginPageHtml = await loginPageResponse.text();
    console.log('[Auto-Login] Retrieved login page');

    // Extract CSRF token or other required fields from the login page
    const csrfTokenMatch = loginPageHtml.match(/name="[^"]*token[^"]*"[^>]*value="([^"]*)"/i);
    const csrfToken = csrfTokenMatch ? csrfTokenMatch[1] : '';

    // Step 3: Perform login with session cookie
    const loginFormData = new URLSearchParams();
    loginFormData.append('user', username);  // SJTU uses 'user' not 'username'
    loginFormData.append('pass', password);  // SJTU uses 'pass' not 'password'
    if (csrfToken) {
      loginFormData.append('_token', csrfToken);
    }

    const loginResponse = await fetch('https://pe.sjtu.edu.cn/login', {
      method: 'POST',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://pe.sjtu.edu.cn',
        'Referer': 'https://pe.sjtu.edu.cn/login',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Cookie': jsessionid ? `JSESSIONID=${jsessionid}` : '',
      },
      body: loginFormData.toString(),
      redirect: 'manual', // Don't follow redirects automatically
    });

    console.log(`[Auto-Login] Login response status: ${loginResponse.status}`);

    // Check if login was successful (usually redirects to dashboard)
    if (loginResponse.status === 302 || loginResponse.status === 301) {
      const location = loginResponse.headers.get('location');
      console.log(`[Auto-Login] Redirect location: ${location}`);
      
      if (location && !location.includes('login')) {
        // Login successful, extract cookies
        const setCookieHeaders = loginResponse.headers.get('set-cookie');
        const cookies: string[] = [];
        
        if (setCookieHeaders) {
          // Parse multiple Set-Cookie headers
          const cookieStrings = setCookieHeaders.split(',');
          for (const cookieString of cookieStrings) {
            const cookie = cookieString.trim().split(';')[0];
            if (cookie.includes('keepalive=') || cookie.includes('JSESSIONID=')) {
              cookies.push(cookie);
            }
          }
        }

        // Follow redirect to get additional cookies (keepalive)
        const dashboardResponse = await fetch('https://pe.sjtu.edu.cn/phone/', {
          method: 'GET',
          headers: {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookies.join('; '),
          },
        });

        const dashboardSetCookie = dashboardResponse.headers.get('set-cookie');
        if (dashboardSetCookie) {
          const dashboardCookies = dashboardSetCookie.split(',');
          for (const cookieString of dashboardCookies) {
            const cookie = cookieString.trim().split(';')[0];
            if (cookie.includes('keepalive=') || cookie.includes('JSESSIONID=')) {
              cookies.push(cookie);
            }
          }
        }

        // Extract keepalive from dashboard cookies
        let keepalive = '';
        for (const cookie of cookies) {
          if (cookie.includes('keepalive=')) {
            keepalive = cookie.split('=')[1];
            // Clean keepalive value (remove quotes if present)
            keepalive = keepalive.replace(/^['"]|['"]$/g, '');
            break;
          }
        }

        // We already have JSESSIONID from the initial session
        if (keepalive && jsessionid) {
          const finalCookie = `keepalive=${keepalive}; JSESSIONID=${jsessionid}`;
          console.log(`[Auto-Login] Successfully obtained cookie for user: ${username}`);
          console.log(`[Auto-Login] keepalive: ${keepalive.substring(0, 20)}...`);
          console.log(`[Auto-Login] JSESSIONID: ${jsessionid.substring(0, 20)}...`);
          
          return NextResponse.json({
            success: true,
            cookie: finalCookie,
            message: '自动登录成功，Cookie已获取'
          });
        }
      }
    }

    // Login failed
    console.log(`[Auto-Login] Login failed for user: ${username}`);
    return NextResponse.json({
      success: false,
      error: '登录失败，请检查用户名和密码'
    }, { status: 401 });

  } catch (error) {
    console.error('[Auto-Login] Error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : '自动登录过程中发生错误'
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
