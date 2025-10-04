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

    // Step 1: Access the phone page to trigger JAccount redirect
    const phoneResponse = await fetch('https://pe.sjtu.edu.cn/phone/#/indexPortrait', {
      method: 'GET',
      headers: {
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
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      },
      redirect: 'manual',
    });

    console.log(`[Auto-Login] Phone page response status: ${phoneResponse.status}`);
    
    // Extract JSESSIONID from response
    const setCookieHeader = phoneResponse.headers.get('set-cookie');
    let jsessionid = '';
    if (setCookieHeader) {
      const jsessionidMatch = setCookieHeader.match(/JSESSIONID=([^;]+)/);
      if (jsessionidMatch) {
        jsessionid = jsessionidMatch[1];
        console.log(`[Auto-Login] Retrieved JSESSIONID: ${jsessionid.substring(0, 20)}...`);
      }
    }
    
    // Check if already logged in by looking for keepalive cookie
    const isLoggedIn = setCookieHeader && setCookieHeader.includes('keepalive');
    
    if (isLoggedIn) {
      console.log('[Auto-Login] Already logged in, extracting cookies');
      
      // Extract keepalive cookie
      const keepaliveMatch = setCookieHeader.match(/keepalive='([^']+)'/);
      const keepalive = keepaliveMatch ? keepaliveMatch[1] : '';
      
      if (keepalive) {
        const fullCookie = `keepalive='${keepalive}; JSESSIONID=${jsessionid}`;
        console.log('[Auto-Login] Successfully extracted cookies');
        
        return NextResponse.json({
          success: true,
          cookie: fullCookie,
          message: '自动登录成功，Cookie已获取'
        });
      }
    }
    
    // If not logged in, check for JAccount redirect
    if (phoneResponse.status === 302 || phoneResponse.status === 301) {
      const location = phoneResponse.headers.get('location');
      console.log(`[Auto-Login] Redirect to: ${location}`);
      
      if (location && location.includes('jaccount.sjtu.edu.cn')) {
        // Follow redirect to JAccount
        const jaccountResponse = await fetch(location, {
          method: 'GET',
          headers: {
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
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Cookie': jsessionid ? `JSESSIONID=${jsessionid}` : '',
          },
        });

        if (!jaccountResponse.ok) {
          throw new Error(`Failed to get JAccount login page: ${jaccountResponse.status}`);
        }

        const jaccountHtml = await jaccountResponse.text();
        console.log('[Auto-Login] Retrieved JAccount login page');

        // Extract login context from JAccount page (based on saved HTML analysis)
        // Look for the loginContext object in JavaScript
        const loginContextMatch = jaccountHtml.match(/var loginContext = \{[^}]*uuid:\s*"([a-f0-9-]+)"[^}]*\}/);
        const uuidMatch = loginContextMatch ? loginContextMatch[1] : jaccountHtml.match(/uuid:\s*"([a-f0-9-]+)"/)?.[1];
        
        const sidMatch = jaccountHtml.match(/sid:\s*"([^"]+)"/);
        const clientMatch = jaccountHtml.match(/client:\s*"([^"]+)"/);
        const returlMatch = jaccountHtml.match(/returl:\s*"([^"]+)"/);
        const seMatch = jaccountHtml.match(/se:\s*"([^"]+)"/);
        const vMatch = jaccountHtml.match(/v:\s*"([^"]*)"/);
        
        const captchaUuid = uuidMatch || '';
        const sid = sidMatch ? sidMatch[1] : '';
        const client = clientMatch ? clientMatch[1] : '';
        const returl = returlMatch ? returlMatch[1] : '';
        const se = seMatch ? seMatch[1] : '';
        const v = vMatch ? vMatch[1] : '';
        
        if (captchaUuid) {
          const timestamp = Date.now();
          const fullCaptchaUrl = `https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid=${captchaUuid}&t=${timestamp}`;
          
          console.log(`[Auto-Login] Captcha UUID: ${captchaUuid}`);
          console.log(`[Auto-Login] SID: ${sid}`);
          console.log(`[Auto-Login] Client: ${client.substring(0, 20)}...`);
          console.log(`[Auto-Login] Captcha URL: ${fullCaptchaUrl}`);
          
          // Get captcha image
          const captchaResponse = await fetch(fullCaptchaUrl, {
            method: 'GET',
            headers: {
              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
              'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
              'Accept-Encoding': 'gzip, deflate, br',
              'Connection': 'keep-alive',
              'Sec-Fetch-Dest': 'image',
              'Sec-Fetch-Mode': 'no-cors',
              'Sec-Fetch-Site': 'same-origin',
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache',
              'Cookie': jsessionid ? `JSESSIONID=${jsessionid}` : '',
            },
          });

          let captchaImage = null;
          if (captchaResponse.ok) {
            const captchaBuffer = await captchaResponse.arrayBuffer();
            const captchaBase64 = Buffer.from(captchaBuffer).toString('base64');
            captchaImage = `data:image/png;base64,${captchaBase64}`;
            console.log('[Auto-Login] Captcha image retrieved successfully');
          } else {
            console.log(`[Auto-Login] Failed to get captcha image: ${captchaResponse.status}`);
          }

          return NextResponse.json({
            success: false,
            requiresCaptcha: true,
            captchaImage: captchaImage,
            captchaUrl: fullCaptchaUrl,
            captchaUuid: captchaUuid,
            jsessionid: jsessionid,
            jaccountUrl: location,
            loginContext: {
              sid: sid,
              client: client,
              returl: returl,
              se: se,
              v: v,
              uuid: captchaUuid
            },
            message: '请输入验证码'
          });
        } else {
          throw new Error('Failed to extract captcha UUID from JAccount page');
        }
      } else {
        throw new Error('Unexpected redirect location');
      }
    } else {
      // No redirect, check if we have keepalive cookie
      console.log('[Auto-Login] No redirect detected, checking for existing session');
      
      if (setCookieHeader) {
        const keepaliveMatch = setCookieHeader.match(/keepalive='([^']+)'/);
        const keepalive = keepaliveMatch ? keepaliveMatch[1] : '';
        
        if (keepalive) {
          const fullCookie = `keepalive='${keepalive}; JSESSIONID=${jsessionid}`;
          console.log('[Auto-Login] Successfully extracted cookies from phone page');
          
          return NextResponse.json({
            success: true,
            cookie: fullCookie,
            message: '自动登录成功，Cookie已获取'
          });
        }
      }
      
      throw new Error('Unable to extract keepalive cookie');
    }
  } catch (error) {
    console.error('[Auto-Login] Error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : '自动登录过程中发生错误'
    }, { status: 500 });
  }
}

// New endpoint for submitting login with captcha
export async function PUT(request: NextRequest) {
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

    const { username, password, captcha, captchaUuid, jsessionid, jaccountUrl, loginContext } = await request.json();
    
    if (!username || !password || !captcha || !captchaUuid || !jsessionid || !jaccountUrl) {
      return NextResponse.json({
        success: false,
        error: '用户名、密码、验证码、验证码UUID、会话ID和JAccount URL不能为空'
      }, { status: 400 });
    }

    console.log(`[Auto-Login] Attempting login with captcha for user: ${username}`);

    // Step 1: Perform login with captcha to JAccount using ulogin endpoint (based on saved HTML analysis)
    const loginFormData = new URLSearchParams();
    
    // Add login context parameters (based on saved HTML analysis)
    if (loginContext) {
      loginFormData.append('sid', loginContext.sid || '');
      loginFormData.append('client', loginContext.client || '');
      loginFormData.append('returl', loginContext.returl || '');
      loginFormData.append('se', loginContext.se || '');
      loginFormData.append('v', loginContext.v || '');
      loginFormData.append('uuid', loginContext.uuid || captchaUuid);
    }
    
    // Add login credentials
    loginFormData.append('user', username);
    loginFormData.append('pass', password);
    loginFormData.append('captcha', captcha);
    loginFormData.append('lt', 'p'); // login type: password

    // Use ulogin endpoint as found in the saved HTML
    const uloginUrl = 'https://jaccount.sjtu.edu.cn/jaccount/ulogin';
    
    const loginResponse = await fetch(uloginUrl, {
      method: 'POST',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://jaccount.sjtu.edu.cn',
        'Referer': jaccountUrl,
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Cookie': `JSESSIONID=${jsessionid}`,
      },
      body: loginFormData.toString(),
      redirect: 'manual',
    });

    console.log(`[Auto-Login] Login response status: ${loginResponse.status}`);

    // Parse JSON response (based on saved HTML analysis)
    let loginResult;
    try {
      const responseText = await loginResponse.text();
      console.log(`[Auto-Login] Login response: ${responseText}`);
      loginResult = JSON.parse(responseText);
    } catch (parseError) {
      console.error('[Auto-Login] Failed to parse login response:', parseError);
      throw new Error('登录响应解析失败');
    }

    // Check login result (based on saved HTML analysis)
    if (loginResult.errno === 0 && loginResult.url) {
      console.log(`[Auto-Login] Login successful, redirecting to: ${loginResult.url}`);
      
      // Follow redirect to get cookies
      const redirectResponse = await fetch(loginResult.url, {
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
          'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'cross-site',
          'Sec-Fetch-User': '?1',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'Cookie': `JSESSIONID=${jsessionid}`,
        },
        redirect: 'manual',
      });

      console.log(`[Auto-Login] Redirect response status: ${redirectResponse.status}`);

      // Extract cookies from redirect response
      const setCookieHeader = redirectResponse.headers.get('set-cookie');
      let keepalive = '';
      let newJsessionid = jsessionid;

      if (setCookieHeader) {
        // Extract keepalive cookie
        const keepaliveMatch = setCookieHeader.match(/keepalive='([^']+)'/);
        if (keepaliveMatch) {
          keepalive = keepaliveMatch[1];
        }

        // Extract new JSESSIONID if present
        const jsessionidMatch = setCookieHeader.match(/JSESSIONID=([^;]+)/);
        if (jsessionidMatch) {
          newJsessionid = jsessionidMatch[1];
        }
      }

      // Follow final redirect to phone page to get keepalive
      if (redirectResponse.status === 302 || redirectResponse.status === 301) {
        const finalLocation = redirectResponse.headers.get('location');
        console.log(`[Auto-Login] Final redirect to: ${finalLocation}`);
        
        const finalResponse = await fetch(finalLocation || 'https://pe.sjtu.edu.cn/phone/#/indexPortrait', {
          method: 'GET',
          headers: {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Cookie': `JSESSIONID=${newJsessionid}`,
          },
        });

        const finalSetCookie = finalResponse.headers.get('set-cookie');
        if (finalSetCookie) {
          const finalKeepaliveMatch = finalSetCookie.match(/keepalive='([^']+)'/);
          if (finalKeepaliveMatch) {
            keepalive = finalKeepaliveMatch[1];
          }
        }
      }

      if (keepalive && newJsessionid) {
        const finalCookie = `keepalive='${keepalive}; JSESSIONID=${newJsessionid}`;
        console.log(`[Auto-Login] Successfully obtained cookie for user: ${username}`);
        console.log(`[Auto-Login] keepalive: ${keepalive.substring(0, 20)}...`);
        console.log(`[Auto-Login] JSESSIONID: ${newJsessionid.substring(0, 20)}...`);
        
        return NextResponse.json({
          success: true,
          cookie: finalCookie,
          message: '自动登录成功，Cookie已获取'
        });
      } else {
        throw new Error('无法获取keepalive Cookie');
      }
    } else {
      // Login failed
      console.log(`[Auto-Login] Login failed for user: ${username}, error: ${loginResult.error}`);
      return NextResponse.json({
        success: false,
        error: loginResult.error || '登录失败，请检查用户名和密码'
      }, { status: 401 });
    }

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
