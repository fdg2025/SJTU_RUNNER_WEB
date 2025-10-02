import { RunningConfig, LogCallback } from './utils';

export class SportsUploaderError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SportsUploaderError';
  }
}

export async function makeRequest(
  method: 'GET' | 'POST',
  url: string,
  headers: Record<string, string>,
  params?: Record<string, string>,
  data?: string,
  logCb?: LogCallback
): Promise<any> {
  try {
    const timeoutValue = 15000;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutValue);
    
    let requestUrl = url;
    if (method === 'GET' && params) {
      const searchParams = new URLSearchParams(params);
      requestUrl += '?' + searchParams.toString();
    }
    
    const requestOptions: RequestInit = {
      method,
      headers,
      signal: controller.signal,
    };
    
    if (method === 'POST' && data) {
      requestOptions.body = data;
    }
    
    const response = await fetch(requestUrl, requestOptions);
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      logCb?.(`HTTP error occurred: ${response.status} ${response.statusText}`, 'error');
      logCb?.(`URL: ${url}`, 'error');
      logCb?.(`Response text: ${errorText}`, 'error');
      throw new SportsUploaderError(`HTTP Error: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    if (error instanceof SportsUploaderError) {
      throw error;
    }
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        logCb?.('Request timeout occurred', 'error');
        throw new SportsUploaderError('Request timeout');
      }
      
      logCb?.(`An unexpected error occurred: ${error.message}`, 'error');
      throw new SportsUploaderError(`Request Error: ${error.message}`);
    }
    
    throw new SportsUploaderError('Unknown error occurred');
  }
}

export async function getAuthorizationTokenAndRules(
  config: RunningConfig,
  logCb?: LogCallback
): Promise<[string, any]> {
  const commonAppHeaders = {
    "Host": config.HOST,
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "\"Android\"",
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-S9080 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.67 Safari/537.36 TaskCenterApp/3.5.0",
    "Accept": "application/json, text/plain, */*",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Android WebView\";v=\"138\"",
    "Content-Type": "application/json;charset=utf-8",
    "sec-ch-ua-mobile": "?0",
    "X-Requested-With": "edu.sjtu.infoplus.taskcenter",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://pe.sjtu.edu.cn/phone/",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cookie": config.COOKIE
  };

  logCb?.(`Attempting to get Authorization Token from: ${config.UID_URL}`);
  const uidResponseData = await makeRequest('GET', config.UID_URL, commonAppHeaders, undefined, undefined, logCb);

  let authToken: string;
  if (uidResponseData?.code === 0 && uidResponseData?.data?.uid) {
    authToken = uidResponseData.data.uid;
    logCb?.(`Successfully retrieved Authorization Token: ${authToken}`);
  } else {
    throw new SportsUploaderError(`Failed to get Authorization Token: ${JSON.stringify(uidResponseData)}`);
  }

  logCb?.(`Attempting to get MyData from: ${config.MY_DATA_URL}`);
  try {
    await makeRequest('GET', config.MY_DATA_URL, commonAppHeaders, undefined, undefined, logCb);
    logCb?.('Successfully sent MyData request.');
  } catch (error) {
    logCb?.(`Warning: Failed to get MyData (this might be expected or ignorable): ${error}`, 'warning');
  }

  const formattedLon = config.START_LONGITUDE.toFixed(14);
  const formattedLat = config.START_LATITUDE.toFixed(14);
  const currentLocationParam = `${formattedLon},${formattedLat}`;

  const refererUrlForPointRule = `${config.POINT_RULE_URL}?location=${encodeURIComponent(currentLocationParam)}`;

  const pointRuleHeaders = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "authorization": authToken,
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "referer": refererUrlForPointRule,
    "Host": config.HOST,
  };

  const params = { location: currentLocationParam };
  
  logCb?.(`Getting point rules from: ${config.POINT_RULE_URL} with location: ${currentLocationParam}`);
  const pointRuleResponseData = await makeRequest('GET', config.POINT_RULE_URL, pointRuleHeaders, params, undefined, logCb);

  return [authToken, pointRuleResponseData?.data || {}];
}

export async function uploadRunningData(
  config: RunningConfig,
  authToken: string,
  runningData: any[],
  logCb?: LogCallback
): Promise<any> {
  const headers = {
    "Authorization": authToken,
    "Content-Type": "application/json; charset=utf-8",
    "Host": config.HOST,
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/4.10.0"
  };

  const response = await makeRequest(
    'POST',
    config.UPLOAD_URL,
    headers,
    undefined,
    JSON.stringify(runningData),
    logCb
  );
  
  logCb?.(`Upload Response: ${JSON.stringify(response, null, 2)}`);
  return response;
}
