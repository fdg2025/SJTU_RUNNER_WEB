# SJTU 体育跑步上传工具 - Web版本

这是上海交通大学体育跑步数据上传工具的现代化Web版本，基于Next.js构建，可以部署到Vercel等平台。

## ✨ 特性

- 🌐 **现代化Web界面** - 响应式设计，支持桌面和移动设备
- 🚀 **一键部署** - 支持Vercel、Netlify等平台部署
- 💾 **配置管理** - 支持配置导入/导出和本地存储
- 📊 **实时日志** - 详细的操作日志和进度显示
- 🎨 **美观UI** - 基于Tailwind CSS的现代化界面设计
- 🔒 **安全性** - 客户端处理敏感信息，不存储Cookie

## 🚀 快速开始

### 本地开发

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd web
   ```

2. **安装依赖**
   ```bash
   npm install
   # 或
   yarn install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   # 或
   yarn dev
   ```

4. **访问应用**
   打开浏览器访问 [http://localhost:3000](http://localhost:3000)

### 部署到Vercel

#### 方法一：通过Vercel CLI

1. **安装Vercel CLI**
   ```bash
   npm i -g vercel
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

4. **按照提示完成部署配置**

#### 方法二：通过GitHub集成

1. **推送代码到GitHub**
   ```bash
   git add .
   git commit -m "Add web version"
   git push origin main
   ```

2. **在Vercel控制台导入项目**
   - 访问 [vercel.com](https://vercel.com)
   - 点击 "New Project"
   - 选择你的GitHub仓库
   - 设置根目录为 `web`
   - 点击 "Deploy"

#### 方法三：一键部署

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/your-repo&project-name=sjtu-running-tool&repository-name=sjtu-running-tool&root-directory=web)

## 📖 使用说明

### 1. 获取Cookie

1. 访问 [交我跑官网](https://pe.sjtu.edu.cn/phone/#/indexPortrait)
2. 使用JAccount登录
3. 按F12打开浏览器开发者工具
4. 切换到"应用程序"(Application)标签页
5. 在左侧找到"存储" → "Cookie" → "https://pe.sjtu.edu.cn"
6. 找到`keepalive`和`JSESSIONID`两个Cookie
7. 复制完整的Cookie字符串，格式如：`keepalive=xxx; JSESSIONID=xxx`

### 2. 配置参数

- **用户ID**: 你的JAccount用户名
- **起点/终点坐标**: 校园内的GPS坐标（纬度/经度）
- **跑步速度**: 建议2.0-3.0米/秒（约7-11公里/小时）
- **采样间隔**: 轨迹点生成间隔，建议3-5秒
- **时间设置**: 可选择使用当前时间或设置历史时间

### 3. 开始上传

1. 填写完所有必要信息
2. 点击"开始上传"按钮
3. 等待系统处理（包括认证、数据生成、上传）
4. 查看日志输出了解详细进度

## 🛠️ 技术栈

- **前端框架**: Next.js 14 (App Router)
- **UI库**: Tailwind CSS
- **图标**: Lucide React
- **语言**: TypeScript
- **部署**: Vercel

## 📁 项目结构

```
web/
├── app/                    # Next.js App Router
│   ├── api/               # API路由
│   │   └── upload/        # 上传接口
│   ├── globals.css        # 全局样式
│   ├── layout.tsx         # 根布局
│   └── page.tsx           # 主页面
├── components/            # React组件
│   ├── ConfigForm.tsx     # 配置表单
│   ├── ConfigManager.tsx  # 配置管理
│   ├── LogOutput.tsx      # 日志输出
│   └── ProgressBar.tsx    # 进度条
├── lib/                   # 工具库
│   ├── api-client.ts      # API客户端
│   ├── data-generator.ts  # 数据生成器
│   └── utils.ts           # 工具函数
├── public/                # 静态资源
├── package.json           # 项目配置
├── tailwind.config.js     # Tailwind配置
├── tsconfig.json          # TypeScript配置
└── vercel.json            # Vercel部署配置
```

## ⚙️ 环境变量

创建 `.env.local` 文件（可选）：

```env
# Node环境
NODE_ENV=production

# 可选：自定义API基础URL
# NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com

# 可选：启用调试日志
# DEBUG=true
```

## 🔧 配置管理

应用支持多种配置管理方式：

1. **本地存储**: 配置自动保存到浏览器本地存储
2. **配置导出**: 将配置导出为JSON文件（不包含敏感信息）
3. **配置导入**: 从JSON文件导入配置
4. **默认配置**: 一键恢复到默认配置

## 🚨 注意事项

### 安全性
- Cookie等敏感信息仅在客户端处理，不会发送到服务器存储
- 导出的配置文件不包含Cookie信息
- 建议定期更新Cookie以确保有效性

### 使用限制
- 本工具仅供学习和研究目的使用
- 请遵守学校相关规定和政策
- 开发者不承担使用本工具产生的任何后果

### 兼容性
- 支持现代浏览器（Chrome、Firefox、Safari、Edge）
- 移动端浏览器支持
- 需要JavaScript启用

## 🐛 故障排除

### 常见问题

1. **Cookie失效**
   - 重新登录交我跑网站获取新的Cookie
   - 确保Cookie格式正确

2. **坐标错误**
   - 确保使用的是校园内的有效坐标
   - 检查纬度经度格式是否正确

3. **网络错误**
   - 检查网络连接
   - 确认交我跑网站可正常访问

4. **部署问题**
   - 检查Vercel部署日志
   - 确认所有依赖正确安装

### 调试模式

在浏览器控制台中设置调试模式：
```javascript
localStorage.setItem('debug', 'true');
```

## 📄 许可证

本项目仅供学习和研究使用。请遵守相关法律法规和学校政策。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📞 支持

如果遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查浏览器控制台错误信息
3. 提交Issue描述具体问题

---

**免责声明**: 本工具仅供学习研究使用，开发者不承担使用后果。请遵守学校相关规定。
