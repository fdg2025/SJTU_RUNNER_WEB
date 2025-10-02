# 项目结构说明

本项目包含两个版本的SJTU体育跑步上传工具：桌面版和Web版。

## 📁 项目目录结构

```
SJTURunningMan5-master/
├── 📁 assets/                 # 桌面版资源文件
│   ├── help.md               # 帮助文档
│   ├── help0.png             # 帮助图片
│   ├── help1.png
│   ├── help3.png
│   └── SJTURM.png            # 应用图标
├── 📁 configs/               # 桌面版配置文件
│   └── default.json          # 默认配置
├── 📁 src/                   # 桌面版源代码
│   ├── __pycache__/          # Python缓存
│   ├── api_client.py         # API客户端
│   ├── config_manager.py     # 配置管理器
│   ├── data_generator.py     # 数据生成器
│   ├── help_dialog.py        # 帮助对话框
│   ├── main.py               # 主逻辑
│   └── utils.py              # 工具函数
├── 📁 web/                   # Web版本目录 🌟
│   ├── 📁 app/               # Next.js App Router
│   │   ├── 📁 api/           # API路由
│   │   │   └── 📁 upload/    # 上传接口
│   │   │       └── route.ts
│   │   ├── globals.css       # 全局样式
│   │   ├── layout.tsx        # 根布局
│   │   └── page.tsx          # 主页面
│   ├── 📁 components/        # React组件
│   │   ├── ConfigForm.tsx    # 配置表单
│   │   ├── ConfigManager.tsx # 配置管理
│   │   ├── LogOutput.tsx     # 日志输出
│   │   └── ProgressBar.tsx   # 进度条
│   ├── 📁 lib/               # 工具库
│   │   ├── api-client.ts     # API客户端
│   │   ├── data-generator.ts # 数据生成器
│   │   └── utils.ts          # 工具函数
│   ├── 📁 scripts/           # 脚本文件
│   │   └── setup.sh          # 设置脚本
│   ├── package.json          # 项目配置
│   ├── tailwind.config.js    # Tailwind配置
│   ├── tsconfig.json         # TypeScript配置
│   ├── vercel.json           # Vercel部署配置
│   └── README.md             # Web版说明文档
├── 📁 venv/                  # Python虚拟环境
├── qtui.py                   # 桌面版主程序
├── requirements.txt          # Python依赖
├── README.md                 # 项目主说明
├── DEPLOYMENT.md             # 部署指南
├── PROJECT_STRUCTURE.md      # 本文件
└── 启动脚本.sh               # 桌面版启动脚本
```

## 🔍 核心文件说明

### 桌面版核心文件

| 文件 | 说明 |
|------|------|
| `qtui.py` | 桌面版主程序入口，包含Qt界面 |
| `src/main.py` | 核心业务逻辑，处理跑步数据生成和上传 |
| `src/api_client.py` | 处理与SJTU体育网站的API交互 |
| `src/data_generator.py` | 生成模拟跑步轨迹数据 |
| `src/config_manager.py` | 配置文件管理 |
| `src/utils.py` | 通用工具函数 |

### Web版核心文件

| 文件 | 说明 |
|------|------|
| `web/app/page.tsx` | Web版主页面，包含完整的用户界面 |
| `web/app/api/upload/route.ts` | 处理上传请求的API端点 |
| `web/lib/api-client.ts` | Web版API客户端，移植自Python版本 |
| `web/lib/data-generator.ts` | Web版数据生成器，移植自Python版本 |
| `web/components/ConfigForm.tsx` | 配置表单组件 |
| `web/components/LogOutput.tsx` | 日志输出组件 |

## 🔄 代码复用

Web版本是基于桌面版的核心逻辑移植而来：

- **API交互逻辑**: `src/api_client.py` → `web/lib/api-client.ts`
- **数据生成逻辑**: `src/data_generator.py` → `web/lib/data-generator.ts`
- **工具函数**: `src/utils.py` → `web/lib/utils.ts`
- **业务流程**: `src/main.py` → `web/app/api/upload/route.ts`

## 🎨 技术栈对比

### 桌面版技术栈
- **语言**: Python 3.9+
- **GUI框架**: PySide6 (Qt)
- **HTTP客户端**: requests
- **配置管理**: JSON文件
- **打包**: 可执行文件

### Web版技术栈
- **语言**: TypeScript
- **前端框架**: Next.js 14 (React)
- **样式**: Tailwind CSS
- **HTTP客户端**: Fetch API
- **状态管理**: React Hooks
- **部署**: Vercel/Netlify

## 🚀 开发建议

### 新功能开发
1. **桌面版**: 在`src/`目录下添加新模块
2. **Web版**: 在`web/lib/`或`web/components/`下添加新功能

### 代码同步
- 核心业务逻辑更新时，需要同时更新两个版本
- 建议先在Python版本中测试，再移植到TypeScript版本

### 测试
- **桌面版**: 直接运行`python qtui.py`测试
- **Web版**: 使用`npm run dev`启动开发服务器测试

## 📦 部署选项

### 桌面版部署
- 直接分发Python脚本
- 使用PyInstaller打包为可执行文件
- 提供虚拟环境和依赖列表

### Web版部署
- **开发环境**: `npm run dev`
- **生产构建**: `npm run build`
- **云端部署**: Vercel、Netlify、Railway等
- **自托管**: Docker容器或传统服务器

## 🔧 维护建议

1. **定期更新依赖**: 检查并更新Python和Node.js依赖
2. **API兼容性**: 关注SJTU体育网站API变化
3. **安全性**: 定期检查安全漏洞
4. **文档更新**: 保持文档与代码同步
5. **用户反馈**: 收集并处理用户问题和建议

---

这个项目结构设计旨在提供灵活的使用方式，用户可以根据自己的需求选择合适的版本。
