# Vercel Analytics 集成指南

## 🎯 已完成的集成步骤

### ✅ 步骤1：添加依赖包
已在 `package.json` 中添加：
```json
"@vercel/analytics": "^1.1.1"
```

### ✅ 步骤2：添加Analytics组件
已在 `app/layout.tsx` 中集成：
```typescript
import { Analytics } from '@vercel/analytics/next'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">
        <div className="min-h-screen">
          {children}
        </div>
        <Analytics />
      </body>
    </html>
  )
}
```

## 🚀 部署和使用

### 第3步：安装依赖并部署

1. **安装新的依赖包**：
   ```bash
   npm install
   # 或
   yarn install
   # 或
   pnpm install
   ```

2. **构建项目**：
   ```bash
   npm run build
   ```

3. **部署到Vercel**：
   - 推送代码到GitHub
   - Vercel会自动检测到Analytics并开始收集数据

### 📊 数据收集

部署完成后：
- 访问你的网站
- 在页面间导航
- 等待30秒后查看Vercel Dashboard
- 数据会出现在 Vercel 项目的 Analytics 标签页

### 🔍 故障排除

如果30秒后仍未看到数据：

1. **检查广告拦截器**：
   - 禁用浏览器的广告拦截扩展
   - 检查是否有内容拦截器

2. **确认页面导航**：
   - 在网站的不同页面间导航
   - 刷新页面
   - 确保JavaScript已启用

3. **检查控制台错误**：
   - 打开浏览器开发者工具
   - 查看是否有JavaScript错误
   - 确认Analytics脚本已加载

### 📈 Analytics功能

Vercel Analytics 提供：
- **页面浏览量**：每个页面的访问次数
- **独立访客**：唯一访客数量
- **热门页面**：最受欢迎的页面
- **引荐来源**：访客来源统计
- **设备信息**：桌面/移动端统计
- **地理位置**：访客地理分布

### 🎛️ 高级配置（可选）

如需更多控制，可以使用自定义配置：

```typescript
import { Analytics } from '@vercel/analytics/next'

// 在layout.tsx中
<Analytics 
  beforeSend={(event) => {
    // 自定义事件处理
    return event
  }}
/>
```

### 🔐 隐私设置

Analytics默认遵循隐私最佳实践：
- 不收集个人身份信息
- 符合GDPR规范
- 数据匿名化处理

## 📝 注意事项

1. **仅在生产环境工作**：Analytics只在部署到Vercel的生产环境中收集数据
2. **数据延迟**：数据可能有几分钟的延迟
3. **免费额度**：Vercel提供一定的免费Analytics额度
4. **团队项目**：确保你有项目的Analytics访问权限

## 🎉 完成

现在你的SJTU跑步工具网站已经集成了Vercel Analytics！

部署后可以在以下位置查看数据：
- Vercel Dashboard → 你的项目 → Analytics 标签页
- 实时访客统计
- 页面性能指标

