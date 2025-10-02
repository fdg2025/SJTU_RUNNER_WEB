import { promises as fs } from 'fs';
import path from 'path';

// 读取密码文件
export async function getValidPasswords(): Promise<string[]> {
  try {
    const passwordsPath = path.join(process.cwd(), 'passwords.txt');
    const content = await fs.readFile(passwordsPath, 'utf-8');
    
    return content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#')) // 过滤空行和注释
      .map(line => line.toLowerCase()); // 转换为小写进行比较
  } catch (error) {
    console.error('Error reading passwords file:', error);
    // 如果文件不存在或读取失败，返回默认密码
    return ['sjtu2024', 'running123'];
  }
}

// 验证密码
export async function validatePassword(password: string): Promise<boolean> {
  if (!password || typeof password !== 'string') {
    return false;
  }
  
  const validPasswords = await getValidPasswords();
  return validPasswords.includes(password.toLowerCase().trim());
}

// 生成简单的会话token
export function generateSessionToken(): string {
  const randomPart = Math.random().toString(36).substring(2);
  const timestamp = Date.now();
  // 使用分隔符，便于解析
  return `${randomPart}_${timestamp}`;
}

// 验证会话token（简单实现，生产环境建议使用更安全的方式）
export function validateSessionToken(token: string): boolean {
  if (!token || typeof token !== 'string') {
    console.log('Token validation failed: invalid token format');
    return false;
  }
  
  try {
    // Token格式：随机字符串_时间戳
    const parts = token.split('_');
    if (parts.length !== 2) {
      console.log('Token validation failed: invalid token structure');
      return false;
    }
    
    const timestamp = parseInt(parts[1], 10);
    
    // 验证时间戳是否有效
    if (isNaN(timestamp) || timestamp <= 0) {
      console.log('Token validation failed: invalid timestamp');
      return false;
    }
    
    const now = Date.now();
    
    // Token有效期：24小时
    const validDuration = 24 * 60 * 60 * 1000;
    const tokenAge = now - timestamp;
    
    // 检查token是否在有效期内，并且不是未来的时间戳
    const isValid = tokenAge >= 0 && tokenAge < validDuration;
    
    if (!isValid) {
      console.log(`Token validation failed: token age ${tokenAge}ms, valid duration ${validDuration}ms`);
    }
    
    return isValid;
  } catch (error) {
    console.error('Token validation error:', error);
    return false;
  }
}
