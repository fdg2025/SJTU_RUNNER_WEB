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

    // Store original keepalive for later use
    let originalKeepalive = '';

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
      console.log('[Auto-Login] Set-Cookie header:', setCookieHeader);
      const jsessionidMatch = setCookieHeader.match(/JSESSIONID=([^;]+)/);
      if (jsessionidMatch) {
        jsessionid = jsessionidMatch[1];
        console.log(`[Auto-Login] Retrieved JSESSIONID: ${jsessionid.substring(0, 20)}...`);
      } else {
        console.log('[Auto-Login] No JSESSIONID found in Set-Cookie header');
      }
      
      // Also extract keepalive for later use
      const keepaliveMatch = setCookieHeader.match(/keepalive=([^;]+)/);
      if (keepaliveMatch) {
        originalKeepalive = keepaliveMatch[1].replace(/^'|'$/g, '');
        console.log(`[Auto-Login] Retrieved keepalive: ${originalKeepalive.substring(0, 20)}...`);
      }
    } else {
      console.log('[Auto-Login] No Set-Cookie header found');
    }
    
    // Check if already logged in by looking for keepalive cookie
    if (setCookieHeader && setCookieHeader.includes('keepalive') && jsessionid) {
      const keepaliveMatch = setCookieHeader.match(/keepalive=([^;]+)/);
      const keepalive = keepaliveMatch ? keepaliveMatch[1].replace(/^'|'$/g, '') : '';
      
      if (keepalive) {
        // Already logged in, return cookies directly
        const fullCookie = `keepalive='${keepalive}; JSESSIONID=${jsessionid}`;
        console.log('[Auto-Login] Already logged in, returning cookies directly');
        console.log(`[Auto-Login] keepalive: ${keepalive.substring(0, 20)}...`);
        console.log(`[Auto-Login] JSESSIONID: ${jsessionid.substring(0, 20)}...`);
        
        return NextResponse.json({
          success: true,
          cookie: fullCookie,
          message: '自动登录成功，Cookie已获取'
        });
      }
    }
    
    // Not logged in, proceed to JAccount flow
    console.log('[Auto-Login] Not logged in, proceeding to JAccount flow');
    
    // Check for JAccount redirect to verify actual login status
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

        // Extract login context from JAccount page (based on real browser test)
        // Look for the loginContext object in JavaScript
        const loginContextMatch = jaccountHtml.match(/var loginContext = \{[\s\S]*?\};/);
        let captchaUuid = '';
        let sid = '';
        let client = '';
        let returl = '';
        let se = '';
        let v = '';
        
        if (loginContextMatch) {
          const contextStr = loginContextMatch[1];
          console.log('[Auto-Login] Found loginContext object');
          
          // Extract parameters from loginContext object
          const uuidMatch = contextStr.match(/uuid:\s*"([^"]+)"/);
          const sidMatch = contextStr.match(/sid:\s*"([^"]+)"/);
          const clientMatch = contextStr.match(/client:\s*"([^"]+)"/);
          const returlMatch = contextStr.match(/returl:\s*"([^"]+)"/);
          const seMatch = contextStr.match(/se:\s*"([^"]+)"/);
          const vMatch = contextStr.match(/v:\s*"([^"]*)"/);
          
          captchaUuid = uuidMatch ? uuidMatch[1] : '';
          sid = sidMatch ? sidMatch[1] : '';
          client = clientMatch ? clientMatch[1] : '';
          returl = returlMatch ? returlMatch[1] : '';
          se = seMatch ? seMatch[1] : '';
          v = vMatch ? vMatch[1] : '';
        } else {
          console.log('[Auto-Login] loginContext object not found, trying alternative extraction');
          // Fallback to individual parameter extraction
          const uuidMatch = jaccountHtml.match(/uuid:\s*"([^"]+)"/);
          const sidMatch = jaccountHtml.match(/sid:\s*"([^"]+)"/);
          const clientMatch = jaccountHtml.match(/client:\s*"([^"]+)"/);
          const returlMatch = jaccountHtml.match(/returl:\s*"([^"]+)"/);
          const seMatch = jaccountHtml.match(/se:\s*"([^"]+)"/);
          const vMatch = jaccountHtml.match(/v:\s*"([^"]*)"/);
          
          captchaUuid = uuidMatch ? uuidMatch[1] : '';
          sid = sidMatch ? sidMatch[1] : '';
          client = clientMatch ? clientMatch[1] : '';
          returl = returlMatch ? returlMatch[1] : '';
          se = seMatch ? seMatch[1] : '';
          v = vMatch ? vMatch[1] : '';
        }
        
        
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
      // No redirect detected - this means we're already on the phone page
      // Since keepalive is just an IP binding identifier, we need to check if we can access protected content
      console.log('[Auto-Login] No redirect detected, checking if we can access protected content');
      
      // Try to access a protected endpoint to verify actual login status
      try {
        const protectedResponse = await fetch('https://pe.sjtu.edu.cn/api/user/info', {
          method: 'GET',
          headers: {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': jsessionid ? `JSESSIONID=${jsessionid}` : '',
          },
          redirect: 'manual',
        });
        
        if (protectedResponse.status === 200) {
          // Successfully accessed protected content, we're actually logged in
          console.log('[Auto-Login] Successfully accessed protected content, user is logged in');
          
          if (setCookieHeader) {
            const keepaliveMatch = setCookieHeader.match(/keepalive=([^;]+)/);
            const keepalive = keepaliveMatch ? keepaliveMatch[1].replace(/^'|'$/g, '') : '';
            
            if (keepalive) {
              const fullCookie = `keepalive='${keepalive}; JSESSIONID=${jsessionid}`;
              
              return NextResponse.json({
                success: true,
                cookie: fullCookie,
                message: '自动登录成功，Cookie已获取'
              });
            }
          }
        } else {
          console.log('[Auto-Login] Cannot access protected content, need JAccount login');
          // Instead of throwing error, proceed to JAccount flow
          console.log('[Auto-Login] Proceeding to JAccount flow for captcha');
          // This will fall through to the JAccount flow
        }
      } catch (protectedError) {
        console.log('[Auto-Login] Protected content check failed, proceeding to JAccount flow');
        // Instead of throwing error, proceed to JAccount flow
        console.log('[Auto-Login] Proceeding to JAccount flow for captcha');
        // This will fall through to the JAccount flow
      }
      
      // If we reach here, we need to proceed to JAccount flow
      // Since we're already on the phone page, we need to manually trigger JAccount redirect
      console.log('[Auto-Login] Manually triggering JAccount flow');
      
      // Try to access the JAccount login page directly
      try {
        // Use the real JAccount login URL from the phone page redirect
        const jaccountUrl = 'https://jaccount.sjtu.edu.cn/jaccount/jalogin?sid=jaoauth220160718&client=CN0jz%2FkocIey765dzMbV5erSBBqwiHGWn4qALMErOi5s&returl=COtE5UW1etjDJLkXEkaoRzaW5zZhBiuLHAG9nEzlTVCwSzii6eIJixvQ5yWgZ81%2FCXUMQOFhLS4OZk4%2FCFAepOUJbgjnKnccVLjy9%2FSutOhwMnIyUTfWSauQz3N4pRWQgIPPe8LJ7%2Btk&se=CF8ADlaoySZJ79UPzxGi9tZHFTZ9uVSRvluTmEV5WrXvJ7bb4IPtTWKtI%2FAbYOq48lLXFtDHHHlP';
        const jaccountResponse = await fetch(jaccountUrl, {
          method: 'GET',
          headers: {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cookie': jsessionid ? `JSESSIONID=${jsessionid}` : '',
          },
        });

        if (jaccountResponse.ok) {
          const jaccountHtml = await jaccountResponse.text();
          console.log('[Auto-Login] Retrieved JAccount login page');
          
          // Extract JSESSIONID from JAccount response
          const jaccountSetCookieHeader = jaccountResponse.headers.get('set-cookie');
          if (jaccountSetCookieHeader) {
            console.log('[Auto-Login] JAccount Set-Cookie header:', jaccountSetCookieHeader);
            const jaccountJsessionidMatch = jaccountSetCookieHeader.match(/JSESSIONID=([^;]+)/);
            if (jaccountJsessionidMatch) {
              jsessionid = jaccountJsessionidMatch[1];
              console.log(`[Auto-Login] Retrieved JAccount JSESSIONID: ${jsessionid.substring(0, 20)}...`);
            } else {
              console.log('[Auto-Login] No JSESSIONID found in JAccount Set-Cookie header');
            }
          } else {
            console.log('[Auto-Login] No Set-Cookie header in JAccount response');
          }

          // Extract login context from JAccount page
          const loginContextMatch = jaccountHtml.match(/var loginContext = \{[\s\S]*?\};/);
          let captchaUuid = '';
          let sid = '';
          let client = '';
          let returl = '';
          let se = '';
          let v = '';
          
          if (loginContextMatch) {
            const contextStr = loginContextMatch[0];
            console.log('[Auto-Login] Found loginContext object');
            
            // Extract parameters from loginContext object
            const uuidMatch = contextStr.match(/uuid:\s*"([^"]+)"/);
            const sidMatch = contextStr.match(/sid:\s*"([^"]+)"/);
            const clientMatch = contextStr.match(/client:\s*"([^"]+)"/);
            const returlMatch = contextStr.match(/returl:\s*"([^"]+)"/);
            const seMatch = contextStr.match(/se:\s*"([^"]+)"/);
            const vMatch = contextStr.match(/v:\s*"([^"]*)"/);
            
            captchaUuid = uuidMatch ? uuidMatch[1] : '';
            sid = sidMatch ? sidMatch[1] : '';
            client = clientMatch ? clientMatch[1] : '';
            returl = returlMatch ? returlMatch[1] : '';
            se = seMatch ? seMatch[1] : '';
            v = vMatch ? vMatch[1] : '';
          }
          
          if (captchaUuid) {
            const timestamp = Date.now();
            const fullCaptchaUrl = `https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid=${captchaUuid}&t=${timestamp}`;
            
            console.log(`[Auto-Login] Captcha UUID: ${captchaUuid}`);
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
                'Referer': jaccountUrl,
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

            // 调试信息
            console.log('[Auto-Login] 返回验证码响应:', {
              jsessionid: jsessionid ? jsessionid.substring(0, 20) + '...' : 'empty',
              jaccountUrl: jaccountUrl ? 'exists' : 'empty',
              captchaUuid: captchaUuid ? captchaUuid.substring(0, 8) + '...' : 'empty',
              loginContext: 'exists'
            });
            
            return NextResponse.json({
              success: false,
              requiresCaptcha: true,
              captchaImage: captchaImage,
              captchaUrl: fullCaptchaUrl,
              captchaUuid: captchaUuid,
              jsessionid: jsessionid,
              jaccountUrl: jaccountUrl,
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
          throw new Error(`Failed to get JAccount login page: ${jaccountResponse.status}`);
        }
      } catch (jaccountError) {
        console.error('[Auto-Login] JAccount flow failed:', jaccountError);
        throw new Error('Failed to proceed to JAccount login flow');
      }
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
    
    // Get original keepalive from initial POST request by accessing phone page again
    let originalKeepalive = '';
    try {
      const initialPhoneResponse = await fetch('https://pe.sjtu.edu.cn/phone/#/indexPortrait', {
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
        },
        redirect: 'manual',
      });
      
      const initialSetCookie = initialPhoneResponse.headers.get('set-cookie');
      if (initialSetCookie) {
        const keepaliveMatch = initialSetCookie.match(/keepalive=([^;]+)/);
        if (keepaliveMatch) {
          originalKeepalive = keepaliveMatch[1].replace(/^'|'$/g, '');
          console.log(`[Auto-Login] Retrieved original keepalive: ${originalKeepalive.substring(0, 20)}...`);
        }
      }
    } catch (error) {
      console.log('[Auto-Login] Failed to get original keepalive:', error);
    }
    
    // 调试信息
    console.log('[Auto-Login PUT] 接收到的参数:', {
      username: username ? '***' : 'empty',
      password: password ? '***' : 'empty',
      captcha: captcha ? '***' : 'empty',
      captchaUuid: captchaUuid ? captchaUuid.substring(0, 8) + '...' : 'empty',
      jsessionid: jsessionid ? jsessionid.substring(0, 8) + '...' : 'empty',
      jaccountUrl: jaccountUrl ? 'exists' : 'empty',
      loginContext: loginContext ? 'exists' : 'empty'
    });
    
    if (!username || !password || !captcha || !captchaUuid || !jsessionid || !jaccountUrl || !loginContext) {
      console.log('[Auto-Login PUT] 参数验证失败:', {
        username: !!username,
        password: !!password,
        captcha: !!captcha,
        captchaUuid: !!captchaUuid,
        jsessionid: !!jsessionid,
        jaccountUrl: !!jaccountUrl,
        loginContext: !!loginContext
      });
      
      return NextResponse.json({
        success: false,
        error: '用户名、密码、验证码、验证码UUID、会话ID、JAccount URL和登录上下文不能为空'
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
      
      // Construct full URL if relative
      let redirectUrl = loginResult.url;
      if (redirectUrl.startsWith('/')) {
        redirectUrl = 'https://jaccount.sjtu.edu.cn' + redirectUrl;
      }
      console.log(`[Auto-Login] Full redirect URL: ${redirectUrl}`);
      
      // Initialize variables for cookie extraction
      let keepalive = '';
      let newJsessionid = jsessionid;

      // Follow the complete redirect chain to get the correct cookies
      console.log('[Auto-Login] Following complete redirect chain to get correct cookies');
      
      let currentUrl = redirectUrl;
      let redirectCount = 0;
      const maxRedirects = 5; // Reduce max redirects to speed up
      let accumulatedCookies = '';
      let finalResponse;
      
      // Start with JAccount JSESSIONID and original keepalive if available
      if (jsessionid) {
        accumulatedCookies = `JSESSIONID=${jsessionid}`;
        console.log('[Auto-Login] Starting with JAccount JSESSIONID:', jsessionid.substring(0, 20) + '...');
      }
      if (originalKeepalive) {
        if (accumulatedCookies) {
          accumulatedCookies += '; ';
        }
        accumulatedCookies += `keepalive='${originalKeepalive}`;
        console.log('[Auto-Login] Added original keepalive cookie');
      }
      
      while (redirectCount < maxRedirects) {
        console.log(`[Auto-Login] Following redirect ${redirectCount + 1}: ${currentUrl}`);
        console.log(`[Auto-Login] Using cookies: ${accumulatedCookies}`);
        
        const redirectResponse = await fetch(currentUrl, {
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
            'Cookie': accumulatedCookies,
          },
          redirect: 'manual',
        });
        
        console.log(`[Auto-Login] Redirect response status: ${redirectResponse.status}`);
        
        // Store the response for final processing
        finalResponse = redirectResponse;
        
        // Check for Set-Cookie in redirect response
        const redirectSetCookie = redirectResponse.headers.get('set-cookie');
        if (redirectSetCookie) {
          console.log('[Auto-Login] Redirect Set-Cookie:', redirectSetCookie);
          
          // Accumulate cookies for next request
          // Handle multiple Set-Cookie headers by splitting on comma
          const newCookies = redirectSetCookie.split(',').map(cookie => cookie.trim());
          for (const cookie of newCookies) {
            const cookieNameValue = cookie.split(';')[0].trim();
            if (cookieNameValue) {
              // Check if this cookie already exists in accumulatedCookies
              const cookieName = cookieNameValue.split('=')[0];
              if (accumulatedCookies.includes(cookieName + '=')) {
                // Replace existing cookie
                const cookieRegex = new RegExp(`${cookieName}=[^;]+`, 'g');
                accumulatedCookies = accumulatedCookies.replace(cookieRegex, cookieNameValue);
              } else {
                // Add new cookie
                if (accumulatedCookies) {
                  accumulatedCookies += '; ';
                }
                accumulatedCookies += cookieNameValue;
              }
            }
          }
          
          // Extract keepalive from redirect response
          const redirectKeepaliveMatch = redirectSetCookie.match(/keepalive=([^;]+)/);
          if (redirectKeepaliveMatch) {
            keepalive = redirectKeepaliveMatch[1].replace(/^'|'$/g, '');
            console.log('[Auto-Login] Redirect keepalive:', keepalive.substring(0, 20) + '...');
          }
          
          // Extract JSESSIONID from redirect response
          const redirectJsessionidMatch = redirectSetCookie.match(/JSESSIONID=([^;]+)/);
          if (redirectJsessionidMatch) {
            newJsessionid = redirectJsessionidMatch[1];
            console.log('[Auto-Login] Redirect JSESSIONID:', newJsessionid);
            
            // Check if JSESSIONID is valid (JAccount format is acceptable)
            if (newJsessionid && newJsessionid.length > 10) {
              console.log('[Auto-Login] JSESSIONID is in valid format - SUCCESS!');
              break; // We found a valid JSESSIONID
            } else {
              console.log('[Auto-Login] JSESSIONID format is invalid, continuing...');
            }
          }
        }
        
        // Check if we need to follow another redirect
        if (redirectResponse.status === 302 || redirectResponse.status === 301) {
          const nextLocation = redirectResponse.headers.get('location');
          if (nextLocation) {
            console.log(`[Auto-Login] Following redirect to: ${nextLocation}`);
            // Handle relative URLs
            if (nextLocation.startsWith('http')) {
              currentUrl = nextLocation;
            } else if (nextLocation.startsWith('/')) {
              // Use current domain for absolute paths
              const urlObj = new URL(currentUrl);
              currentUrl = `${urlObj.protocol}//${urlObj.host}${nextLocation}`;
            } else {
              // Relative path, append to current URL
              const urlObj = new URL(currentUrl);
              currentUrl = `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}/${nextLocation}`;
            }
            redirectCount++;
          } else {
            console.log('[Auto-Login] No location header in redirect response');
            break;
          }
        } else if (redirectResponse.status === 200) {
          // Check if this is a login page that needs to be followed
          // For JAccount login, we need to check if there's a redirect in the response body
          try {
            const responseText = await redirectResponse.text();
            console.log('[Auto-Login] Response body length:', responseText.length);
            
            // Look for redirect patterns in the response body
            const redirectPatterns = [
              /window\.location\.href\s*=\s*['"]([^'"]+)['"]/,
              /location\.href\s*=\s*['"]([^'"]+)['"]/,
              /<meta[^>]*http-equiv=['"]refresh['"][^>]*content=['"]\d+;\s*url=([^'"]+)['"]/i,
              /<script[^>]*>[\s\S]*?window\.location\s*=\s*['"]([^'"]+)['"]/i
            ];
            
            for (const pattern of redirectPatterns) {
              const match = responseText.match(pattern);
              if (match && match[1]) {
                let redirectUrl = match[1];
                console.log(`[Auto-Login] Found redirect in response body: ${redirectUrl}`);
                
                // Handle relative URLs
                if (!redirectUrl.startsWith('http')) {
                  const urlObj = new URL(currentUrl);
                  if (redirectUrl.startsWith('/')) {
                    redirectUrl = `${urlObj.protocol}//${urlObj.host}${redirectUrl}`;
                  } else {
                    redirectUrl = `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}/${redirectUrl}`;
                  }
                }
                
                currentUrl = redirectUrl;
                redirectCount++;
                console.log(`[Auto-Login] Following redirect from response body: ${currentUrl}`);
                break;
              }
            }
            
            // If no redirect found in body, check if we should continue to next step
            if (!responseText.includes('window.location') && !responseText.includes('location.href')) {
              console.log('[Auto-Login] No redirect found in response body, checking if we need to continue');
              // For JAccount login page, we might need to continue to the next step
              if (currentUrl.includes('jalogin') && redirectCount < maxRedirects) {
                // Try to construct the next URL based on the login flow
                const nextUrl = currentUrl.replace('/jalogin', '/authorize');
                if (nextUrl !== currentUrl) {
                  currentUrl = nextUrl;
                  redirectCount++;
                  console.log(`[Auto-Login] Constructing next URL: ${currentUrl}`);
                } else {
                  console.log('[Auto-Login] No more redirects needed');
                  break;
                }
              } else {
                console.log('[Auto-Login] No more redirects needed');
                break;
              }
            }
          } catch (error) {
            console.log('[Auto-Login] Could not read response body:', error);
            console.log('[Auto-Login] No more redirects needed');
            break;
          }
        } else {
          console.log('[Auto-Login] No more redirects needed');
          break;
        }
      }
      
      if (redirectCount >= maxRedirects) {
        console.log('[Auto-Login] Maximum redirects reached');
      }
      
      // If we didn't get valid JSESSIONID, make one more request to the final URL
      const hasValidFormat = newJsessionid && newJsessionid.length > 10;
      console.log('[Auto-Login] Format check:', {
        hasKeepalive: !!keepalive,
        hasJsessionid: !!newJsessionid,
        isValidFormat: hasValidFormat,
        jsessionidValue: newJsessionid
      });
      
      if (!hasValidFormat) {
        console.log('[Auto-Login] Making final request to pe.sjtu.edu.cn/phone/ to get correct cookies');
        console.log('[Auto-Login] Current accumulatedCookies:', accumulatedCookies);
        
        // Try final URLs to get the correct cookies (prioritize most likely to succeed)
        const finalUrls = [
          'https://pe.sjtu.edu.cn/phone/#/indexPortrait', // 优先使用正确的目标页面
          'https://pe.sjtu.edu.cn/phone/'
        ];
        
        for (const finalUrl of finalUrls) {
          console.log(`[Auto-Login] Trying final URL: ${finalUrl}`);
          console.log(`[Auto-Login] Using cookies: ${accumulatedCookies}`);
          
          finalResponse = await fetch(finalUrl, {
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
              'Cookie': accumulatedCookies,
            },
            redirect: 'manual',
          });
          
          console.log(`[Auto-Login] Final request response status: ${finalResponse.status}`);
          
          // Extract cookies from final request
          const finalSetCookie = finalResponse.headers.get('set-cookie');
          if (finalSetCookie) {
            console.log('[Auto-Login] Final request Set-Cookie:', finalSetCookie);
            
            // Extract keepalive from final response
            const finalKeepaliveMatch = finalSetCookie.match(/keepalive=([^;]+)/);
            if (finalKeepaliveMatch) {
              keepalive = finalKeepaliveMatch[1].replace(/^'|'$/g, '');
              console.log('[Auto-Login] Final keepalive:', keepalive.substring(0, 20) + '...');
            }
            
            // Extract JSESSIONID from final response
            const finalJsessionidMatch = finalSetCookie.match(/JSESSIONID=([^;]+)/);
            if (finalJsessionidMatch) {
              newJsessionid = finalJsessionidMatch[1];
              console.log('[Auto-Login] Final JSESSIONID:', newJsessionid);
              
              // Check if this is a valid format
              if (newJsessionid && newJsessionid.length > 10) {
                console.log('[Auto-Login] Found valid JSESSIONID in final request - SUCCESS!');
                break; // We found a valid format, stop trying other URLs
              } else {
                console.log('[Auto-Login] JSESSIONID is still not valid format, trying next URL...');
              }
            }
          }
        }
      }
      
      // Ensure finalResponse is defined
      if (!finalResponse) {
        throw new Error('Final response is undefined');
      }
      
      console.log(`[Auto-Login] Final response status: ${finalResponse.status}`);
      
      // 无论前面的重定向结果如何，都要访问正确的目标页面获取最终Cookie
      console.log('[Auto-Login] Making final request to correct target page: https://pe.sjtu.edu.cn/phone/#/indexPortrait');
      console.log('[Auto-Login] Using accumulated cookies for target page:', accumulatedCookies);
      
      const targetPageResponse = await fetch('https://pe.sjtu.edu.cn/phone/#/indexPortrait', {
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
          'Cookie': accumulatedCookies,
        },
        redirect: 'manual',
      });
      
      console.log(`[Auto-Login] Target page response status: ${targetPageResponse.status}`);
      
      // 从目标页面获取最终的Cookie
      const targetSetCookie = targetPageResponse.headers.get('set-cookie');
      let targetJsessionidMatch = null;
      
      if (targetSetCookie) {
        console.log('[Auto-Login] Target page Set-Cookie:', targetSetCookie);
        
        // 提取keepalive从目标页面响应
        const targetKeepaliveMatch = targetSetCookie.match(/keepalive=([^;]+)/);
        if (targetKeepaliveMatch) {
          keepalive = targetKeepaliveMatch[1].replace(/^'|'$/g, '');
          console.log('[Auto-Login] Target page keepalive:', keepalive.substring(0, 20) + '...');
        }
        
        // 提取JSESSIONID从目标页面响应
        targetJsessionidMatch = targetSetCookie.match(/JSESSIONID=([^;]+)/);
        if (targetJsessionidMatch) {
          newJsessionid = targetJsessionidMatch[1];
          console.log('[Auto-Login] Target page JSESSIONID:', newJsessionid);
        }
      }
      
      // 如果目标页面没有返回新的JSESSIONID，我们需要通过其他方式获取
      if (!targetJsessionidMatch || !targetJsessionidMatch[1]) {
        console.log('[Auto-Login] Target page did not return JSESSIONID, making additional request to get it');
        
        // 尝试访问其他可能返回JSESSIONID的端点
        const additionalUrls = [
          'https://pe.sjtu.edu.cn/phone/',
          'https://pe.sjtu.edu.cn/phone/api/uid',
          'https://pe.sjtu.edu.cn/sports/my/uid',
          'https://pe.sjtu.edu.cn/sports/my/data', // 尝试这个端点
          'https://pe.sjtu.edu.cn/api/running/point-rule' // 尝试这个端点
        ];
        
        // 同时尝试不同的Cookie组合
        const cookieVariants = [
          accumulatedCookies, // 使用累积的Cookie
          `keepalive='${keepalive}; JSESSIONID=${newJsessionid}`, // 使用当前的组合
          `JSESSIONID=${newJsessionid}; keepalive='${keepalive}`, // 调换顺序
        ];
        
        for (const url of additionalUrls) {
          for (const cookieVariant of cookieVariants) {
            console.log(`[Auto-Login] Trying additional URL: ${url} with cookie variant: ${cookieVariant.substring(0, 50)}...`);
            
            const additionalResponse = await fetch(url, {
              method: 'GET',
              headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Cookie': cookieVariant,
              },
              redirect: 'manual',
            });
            
            console.log(`[Auto-Login] Additional URL response status: ${additionalResponse.status}`);
            
            const additionalSetCookie = additionalResponse.headers.get('set-cookie');
            if (additionalSetCookie) {
              console.log('[Auto-Login] Additional URL Set-Cookie:', additionalSetCookie);
              
              // 检查是否有JSESSIONID
              const additionalJsessionidMatch = additionalSetCookie.match(/JSESSIONID=([^;]+)/);
              if (additionalJsessionidMatch) {
                const candidateJsessionid = additionalJsessionidMatch[1];
                console.log('[Auto-Login] Found JSESSIONID candidate from additional URL:', candidateJsessionid);
                
                // 检查JSESSIONID格式 - 优先选择UUID格式的JSESSIONID
                const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
                const isUuidFormat = uuidPattern.test(candidateJsessionid);
                const isJaccountFormat = candidateJsessionid.includes('.jaccount');
                
                console.log('[Auto-Login] JSESSIONID format analysis:', {
                  value: candidateJsessionid,
                  isUuidFormat: isUuidFormat,
                  isJaccountFormat: isJaccountFormat
                });
                
                // 优先选择UUID格式的JSESSIONID
                if (isUuidFormat) {
                  newJsessionid = candidateJsessionid;
                  console.log('[Auto-Login] Using UUID format JSESSIONID:', newJsessionid);
                  break; // 找到UUID格式的JSESSIONID就停止
                } else if (!isJaccountFormat && !newJsessionid.includes('.jaccount')) {
                  // 如果不是JAccount格式且当前也不是JAccount格式，则使用这个
                  newJsessionid = candidateJsessionid;
                  console.log('[Auto-Login] Using non-JAccount format JSESSIONID:', newJsessionid);
                } else if (isJaccountFormat && newJsessionid.includes('.jaccount')) {
                  // 如果都是JAccount格式，选择较新的
                  newJsessionid = candidateJsessionid;
                  console.log('[Auto-Login] Using JAccount format JSESSIONID:', newJsessionid);
                }
              }
            }
          }
          // 如果找到了UUID格式的JSESSIONID，立即停止所有搜索
          if (newJsessionid && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(newJsessionid)) {
            console.log('[Auto-Login] Found UUID format JSESSIONID, stopping search:', newJsessionid);
            break;
          }
          if (newJsessionid !== jsessionid) {
            break; // 如果找到了新的JSESSIONID就停止
          }
        }
      }
      
      // 使用目标页面的响应作为最终响应
      finalResponse = targetPageResponse;
      
      // Log all response headers for debugging
      console.log('[Auto-Login] Final response headers:');
      finalResponse.headers.forEach((value, key) => {
        console.log(`  ${key}: ${value}`);
      });
      
      const finalSetCookie = finalResponse.headers.get('set-cookie');
      if (finalSetCookie) {
        console.log('[Auto-Login] Final Set-Cookie:', finalSetCookie);
        
        // Extract keepalive from final response
        const finalKeepaliveMatch = finalSetCookie.match(/keepalive=([^;]+)/);
        if (finalKeepaliveMatch) {
          keepalive = finalKeepaliveMatch[1].replace(/^'|'$/g, '');
          console.log('[Auto-Login] Final keepalive:', keepalive.substring(0, 20) + '...');
        }
        
        // Extract JSESSIONID from final response (should be UUID format)
        const finalJsessionidMatch = finalSetCookie.match(/JSESSIONID=([^;]+)/);
        if (finalJsessionidMatch) {
          newJsessionid = finalJsessionidMatch[1];
          console.log('[Auto-Login] Final JSESSIONID:', newJsessionid);
          
          // Check if JSESSIONID is in valid format
          if (newJsessionid && newJsessionid.length > 10) {
            console.log('[Auto-Login] JSESSIONID is in valid format');
          } else {
            console.log('[Auto-Login] JSESSIONID is NOT in valid format, this might be wrong');
          }
        }
        
        // Log all cookies found in the response
        const allCookies = finalSetCookie.split(',').map(cookie => cookie.trim());
        console.log('[Auto-Login] All cookies in final response:');
        allCookies.forEach((cookie, index) => {
          console.log(`  Cookie ${index + 1}: ${cookie}`);
        });
      } else {
        console.log('[Auto-Login] No Set-Cookie header in final response');
      }
      
      // Also log the response body to see if there are any clues
      try {
        const responseText = await finalResponse.text();
        console.log('[Auto-Login] Final response body length:', responseText.length);
        if (responseText.includes('JSESSIONID') || responseText.includes('keepalive')) {
          console.log('[Auto-Login] Response body contains cookie-related content');
          // Log a small portion of the response body
          console.log('[Auto-Login] Response body sample:', responseText.substring(0, 500));
        }
      } catch (error) {
        console.log('[Auto-Login] Could not read response body:', error);
      }

      // 调试信息
      console.log('[Auto-Login] Cookie 提取结果:', {
        keepalive: keepalive ? keepalive.substring(0, 20) + '...' : 'empty',
        newJsessionid: newJsessionid ? newJsessionid.substring(0, 20) + '...' : 'empty',
        finalResponseStatus: finalResponse ? finalResponse.status : 'undefined'
      });

      // Check if we have valid cookies (JSESSIONID can be in various formats)
      const isValidJsessionid = newJsessionid && newJsessionid.length > 10; // JAccount JSESSIONID is typically longer
      
      if (keepalive && newJsessionid && isValidJsessionid) {
        const finalCookie = `keepalive='${keepalive}; JSESSIONID=${newJsessionid}`;
        console.log(`[Auto-Login] Successfully obtained correct cookie for user: ${username}`);
        console.log(`[Auto-Login] keepalive: ${keepalive.substring(0, 20)}...`);
        console.log(`[Auto-Login] JSESSIONID: ${newJsessionid.substring(0, 20)}...`);
        console.log(`[Auto-Login] JSESSIONID format valid: ${isValidJsessionid}`);
        
        return NextResponse.json({
          success: true,
          cookie: finalCookie,
          message: '自动登录成功，Cookie已获取'
        });
      } else {
        console.log('[Auto-Login] Cookie 提取失败或格式不正确:', {
          hasKeepalive: !!keepalive,
          hasJsessionid: !!newJsessionid,
          isValidFormat: isValidJsessionid,
          jsessionidValue: newJsessionid
        });
        
        throw new Error(`Cookie格式不正确: keepalive=${!!keepalive}, JSESSIONID=${!!newJsessionid}, 格式有效=${isValidJsessionid}`);
      }
    } else {
      // Login failed
      console.log(`[Auto-Login] Login failed for user: ${username}, error: ${loginResult.error}`);
      
      // 检查是否是验证码相关错误
      let errorMessage = loginResult.error || '登录失败，请检查用户名和密码';
      if (loginResult.error && (
        loginResult.error.includes('验证码') || 
        loginResult.error.includes('captcha') ||
        loginResult.error.includes('过期') ||
        loginResult.error.includes('expired')
      )) {
        errorMessage = '验证码已过期或错误，请重新获取验证码';
      }
      
      return NextResponse.json({
        success: false,
        error: errorMessage,
        requiresNewCaptcha: true // 标记需要新的验证码
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
