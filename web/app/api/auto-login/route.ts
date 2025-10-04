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
    
    // The keepalive cookie is a fixed IP binding identifier, not a login status indicator
    // Always proceed to JAccount flow to verify actual login status
    console.log('[Auto-Login] keepalive cookie is IP binding identifier, proceeding to JAccount flow');
    
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
    
    if (!username || !password || !captcha || !captchaUuid || !jsessionid || !jaccountUrl || !loginContext) {
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
        const keepaliveMatch = setCookieHeader.match(/keepalive=([^;]+)/);
        if (keepaliveMatch) {
          keepalive = keepaliveMatch[1].replace(/^'|'$/g, '');
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
          const finalKeepaliveMatch = finalSetCookie.match(/keepalive=([^;]+)/);
          if (finalKeepaliveMatch) {
            keepalive = finalKeepaliveMatch[1].replace(/^'|'$/g, '');
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
