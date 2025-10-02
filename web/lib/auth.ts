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
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

// 验证会话token（简单实现，生产环境建议使用更安全的方式）
export function validateSessionToken(token: string): boolean {
  if (!token || typeof token !== 'string') {
    return false;
  }
  
  // 简单验证：检查token格式和时间戳
  const parts = token.split(/[a-z]/);
  if (parts.length < 2) return false;
  
  const timestamp = parseInt(parts[parts.length - 1], 36);
  const now = Date.now();
  
  // Token有效期：24小时
  const validDuration = 24 * 60 * 60 * 1000;
  return (now - timestamp) < validDuration;
}
