// 测试自动登录功能的脚本
const https = require('https');
const http = require('http');

// 测试配置
const TEST_CONFIG = {
  username: 'test_user',
  password: 'test_password',
  sjtuLoginUrl: 'https://pe.sjtu.edu.cn/login',
  sjtuPhoneUrl: 'https://pe.sjtu.edu.cn/phone/',
  timeout: 10000
};

// 模拟fetch函数
function mockFetch(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        ...options.headers
      }
    };

    const req = client.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          ok: res.statusCode >= 200 && res.statusCode < 300,
          status: res.statusCode,
          statusText: res.statusMessage,
          headers: res.headers,
          text: () => Promise.resolve(data),
          json: () => Promise.resolve(JSON.parse(data))
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.setTimeout(TEST_CONFIG.timeout);

    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
}

// 测试步骤1：获取登录页面
async function testGetLoginPage() {
  console.log('🔍 步骤1：获取SJTU登录页面...');
  
  try {
    const response = await mockFetch(TEST_CONFIG.sjtuLoginUrl, {
      method: 'GET'
    });
    
    console.log(`✅ 登录页面响应状态: ${response.status}`);
    console.log(`📄 响应内容长度: ${(await response.text()).length} 字符`);
    
    // 检查是否包含登录表单
    const html = await response.text();
    const hasLoginForm = html.includes('login') || html.includes('username') || html.includes('password');
    console.log(`🔍 包含登录表单: ${hasLoginForm ? '✅' : '❌'}`);
    
    // 尝试提取CSRF令牌
    const csrfMatch = html.match(/name="[^"]*token[^"]*"[^>]*value="([^"]*)"/i);
    const csrfToken = csrfMatch ? csrfMatch[1] : '';
    console.log(`🔑 CSRF令牌: ${csrfToken ? '✅ 找到' : '❌ 未找到'}`);
    
    return { success: true, html, csrfToken };
  } catch (error) {
    console.log(`❌ 获取登录页面失败: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// 测试步骤2：模拟登录请求
async function testLoginRequest(csrfToken = '') {
  console.log('\n🔍 步骤2：模拟登录请求...');
  
  const formData = new URLSearchParams();
  formData.append('username', TEST_CONFIG.username);
  formData.append('password', TEST_CONFIG.password);
  if (csrfToken) {
    formData.append('_token', csrfToken);
  }
  
  try {
    const response = await mockFetch(TEST_CONFIG.sjtuLoginUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://pe.sjtu.edu.cn',
        'Referer': 'https://pe.sjtu.edu.cn/login',
      },
      body: formData.toString()
    });
    
    console.log(`✅ 登录请求响应状态: ${response.status}`);
    console.log(`📍 重定向位置: ${response.headers.location || '无'}`);
    
    // 检查Set-Cookie头
    const setCookie = response.headers['set-cookie'];
    if (setCookie) {
      console.log(`🍪 Set-Cookie头数量: ${setCookie.length}`);
      setCookie.forEach((cookie, index) => {
        console.log(`   Cookie ${index + 1}: ${cookie.split(';')[0]}`);
      });
      
      // 检查是否包含目标Cookie
      const allCookies = setCookie.join('; ');
      const hasKeepalive = allCookies.includes('keepalive=');
      const hasJSessionId = allCookies.includes('JSESSIONID=');
      console.log(`🔍 包含keepalive: ${hasKeepalive ? '✅' : '❌'}`);
      console.log(`🔍 包含JSESSIONID: ${hasJSessionId ? '✅' : '❌'}`);
    } else {
      console.log('❌ 未找到Set-Cookie头');
    }
    
    return { 
      success: true, 
      status: response.status, 
      location: response.headers.location,
      cookies: setCookie || []
    };
  } catch (error) {
    console.log(`❌ 登录请求失败: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// 测试步骤3：访问手机端页面
async function testPhonePage(cookies = []) {
  console.log('\n🔍 步骤3：访问手机端页面...');
  
  const cookieString = cookies.map(c => c.split(';')[0]).join('; ');
  
  try {
    const response = await mockFetch(TEST_CONFIG.sjtuPhoneUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': cookieString,
      }
    });
    
    console.log(`✅ 手机端页面响应状态: ${response.status}`);
    
    // 检查额外的Cookie
    const setCookie = response.headers['set-cookie'];
    if (setCookie) {
      console.log(`🍪 额外Cookie数量: ${setCookie.length}`);
      setCookie.forEach((cookie, index) => {
        console.log(`   额外Cookie ${index + 1}: ${cookie.split(';')[0]}`);
      });
    }
    
    return { success: true, status: response.status, additionalCookies: setCookie || [] };
  } catch (error) {
    console.log(`❌ 访问手机端页面失败: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// 主测试函数
async function runAutoLoginTest() {
  console.log('🚀 开始测试SJTU自动登录流程...\n');
  
  // 步骤1：获取登录页面
  const loginPageResult = await testGetLoginPage();
  if (!loginPageResult.success) {
    console.log('\n❌ 测试终止：无法获取登录页面');
    return;
  }
  
  // 步骤2：模拟登录请求
  const loginResult = await testLoginRequest(loginPageResult.csrfToken);
  if (!loginResult.success) {
    console.log('\n❌ 测试终止：登录请求失败');
    return;
  }
  
  // 步骤3：访问手机端页面
  const phoneResult = await testPhonePage(loginResult.cookies);
  if (!phoneResult.success) {
    console.log('\n❌ 测试终止：无法访问手机端页面');
    return;
  }
  
  // 总结
  console.log('\n📊 测试总结:');
  console.log(`✅ 登录页面获取: ${loginPageResult.success ? '成功' : '失败'}`);
  console.log(`✅ 登录请求: ${loginResult.success ? '成功' : '失败'}`);
  console.log(`✅ 手机端访问: ${phoneResult.success ? '成功' : '失败'}`);
  
  // 分析Cookie获取情况
  const allCookies = [...(loginResult.cookies || []), ...(phoneResult.additionalCookies || [])];
  const cookieString = allCookies.map(c => c.split(';')[0]).join('; ');
  
  const keepaliveMatch = cookieString.match(/keepalive=([^;]+)/);
  const jsessionidMatch = cookieString.match(/JSESSIONID=([^;]+)/);
  
  console.log('\n🍪 Cookie分析:');
  console.log(`keepalive: ${keepaliveMatch ? '✅ 找到' : '❌ 未找到'}`);
  console.log(`JSESSIONID: ${jsessionidMatch ? '✅ 找到' : '❌ 未找到'}`);
  
  if (keepaliveMatch && jsessionidMatch) {
    const finalCookie = `keepalive=${keepaliveMatch[1]}; JSESSIONID=${jsessionidMatch[1]}`;
    console.log(`\n🎉 最终Cookie: ${finalCookie}`);
    console.log('\n✅ 自动登录流程测试成功！');
  } else {
    console.log('\n❌ Cookie获取不完整，需要进一步调试');
  }
}

// 运行测试
runAutoLoginTest().catch(error => {
  console.error('测试过程中发生错误:', error);
});
