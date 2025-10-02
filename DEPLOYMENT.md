# 部署指南

本文档详细说明如何将SJTU体育跑步上传工具的Web版本部署到各种平台。

## 🚀 Vercel 部署（推荐）

Vercel是最简单的部署方式，支持自动构建和部署。

### 方法一：GitHub集成（推荐）

1. **准备代码仓库**
   ```bash
   # 如果还没有Git仓库，先初始化
   git init
   git add .
   git commit -m "Initial commit"
   
   # 推送到GitHub
   git remote add origin https://github.com/your-username/sjtu-running-tool.git
   git push -u origin main
   ```

2. **在Vercel中导入项目**
   - 访问 [vercel.com](https://vercel.com) 并登录
   - 点击 "New Project"
   - 选择 "Import Git Repository"
   - 选择你的GitHub仓库
   - 配置项目设置：
     - **Project Name**: `sjtu-running-tool`
     - **Framework Preset**: `Next.js`
     - **Root Directory**: `web`
     - **Build Command**: `npm run build`
     - **Output Directory**: `.next`

3. **部署**
   - 点击 "Deploy" 按钮
   - 等待构建完成（通常需要1-3分钟）
   - 获得部署URL，如：`https://sjtu-running-tool.vercel.app`

### 方法二：Vercel CLI

1. **安装Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **登录Vercel**
   ```bash
   vercel login
   ```

3. **部署项目**
   ```bash
   cd web
   vercel
   ```

4. **按照提示配置**
   ```
   ? Set up and deploy "~/path/to/web"? [Y/n] y
   ? Which scope do you want to deploy to? Your Name
   ? Link to existing project? [y/N] n
   ? What's your project's name? sjtu-running-tool
   ? In which directory is your code located? ./
   ```

5. **生产部署**
   ```bash
   vercel --prod
   ```

### 方法三：一键部署

点击下面的按钮直接部署：

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/sjtu-running-tool&project-name=sjtu-running-tool&repository-name=sjtu-running-tool&root-directory=web)

## 🌐 Netlify 部署

1. **准备构建**
   ```bash
   cd web
   npm run build
   ```

2. **手动部署**
   - 访问 [netlify.com](https://netlify.com)
   - 拖拽 `web/.next` 文件夹到部署区域

3. **Git集成部署**
   - 在Netlify中选择 "New site from Git"
   - 连接GitHub仓库
   - 配置构建设置：
     - **Base directory**: `web`
     - **Build command**: `npm run build`
     - **Publish directory**: `web/.next`

## ☁️ 其他平台部署

### Railway

1. **连接GitHub**
   - 访问 [railway.app](https://railway.app)
   - 选择 "Deploy from GitHub repo"

2. **配置环境**
   - 设置根目录为 `web`
   - Railway会自动检测Next.js项目

### Heroku

1. **创建应用**
   ```bash
   heroku create sjtu-running-tool
   ```

2. **配置构建包**
   ```bash
   heroku buildpacks:set heroku/nodejs
   ```

3. **部署**
   ```bash
   git subtree push --prefix web heroku main
   ```

## 🔧 环境配置

### 环境变量设置

在部署平台中设置以下环境变量（如需要）：

```env
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com
```

### Vercel环境变量设置

1. 在Vercel项目设置中找到 "Environment Variables"
2. 添加所需的环境变量
3. 重新部署项目

## 📊 性能优化

### 构建优化

1. **启用压缩**
   ```javascript
   // next.config.js
   module.exports = {
     compress: true,
     // ...其他配置
   }
   ```

2. **图片优化**
   ```javascript
   // next.config.js
   module.exports = {
     images: {
       domains: ['your-domain.com'],
       formats: ['image/webp', 'image/avif'],
     },
   }
   ```

### CDN配置

Vercel和Netlify自动提供全球CDN，无需额外配置。

## 🔒 安全配置

### HTTPS强制

大多数现代部署平台默认启用HTTPS。如需手动配置：

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains'
          }
        ]
      }
    ]
  }
}
```

### CORS配置

API路由已包含CORS配置，支持跨域访问。

## 📈 监控和分析

### Vercel Analytics

1. 在Vercel项目设置中启用Analytics
2. 查看访问统计和性能指标

### 自定义监控

可以集成第三方监控服务：
- Google Analytics
- Plausible
- Umami

## 🚨 故障排除

### 常见部署问题

1. **构建失败**
   ```bash
   # 检查依赖
   npm install
   npm run build
   ```

2. **API路由404**
   - 确认API文件路径正确
   - 检查Vercel函数配置

3. **静态资源加载失败**
   - 检查public文件夹路径
   - 确认资源URL正确

### 调试部署

1. **查看构建日志**
   - Vercel: 在部署页面查看Function Logs
   - Netlify: 在Deploy页面查看Deploy log

2. **本地测试生产构建**
   ```bash
   npm run build
   npm start
   ```

## 🔄 持续部署

### 自动部署

当推送代码到主分支时，支持自动部署的平台会自动触发新的部署。

### 部署钩子

可以设置Webhook来触发部署：
```bash
curl -X POST https://api.vercel.com/v1/integrations/deploy/your-hook-id
```

## 📋 部署检查清单

部署前确认以下项目：

- [ ] 代码已推送到Git仓库
- [ ] 所有依赖已正确安装
- [ ] 构建命令可以本地成功执行
- [ ] 环境变量已正确设置
- [ ] API路由功能正常
- [ ] 响应式设计在不同设备上正常显示
- [ ] 所有链接和资源可以正常访问

## 🎯 部署后验证

1. **功能测试**
   - 配置表单可以正常填写
   - API接口响应正常
   - 日志输出功能正常

2. **性能测试**
   - 页面加载速度
   - API响应时间
   - 移动端体验

3. **安全测试**
   - HTTPS正常工作
   - 敏感信息不会泄露
   - CORS配置正确

---

如果在部署过程中遇到问题，请查看相应平台的官方文档或提交Issue。
