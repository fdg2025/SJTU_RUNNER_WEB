#!/bin/bash

# SJTU Running Tool Web版本 - 快速设置脚本

echo "🏃 SJTU 体育跑步上传工具 - Web版本设置"
echo "========================================="

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装。请先安装 Node.js (https://nodejs.org/)"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装。请先安装 npm"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 安装依赖
echo "📦 正在安装依赖..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

echo ""

# 创建环境变量文件
if [ ! -f ".env.local" ]; then
    echo "⚙️  创建环境变量文件..."
    cp env.example .env.local
    echo "✅ 已创建 .env.local 文件"
else
    echo "ℹ️  .env.local 文件已存在"
fi

echo ""

# 构建项目
echo "🔨 构建项目..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 项目构建成功"
else
    echo "❌ 项目构建失败"
    exit 1
fi

echo ""
echo "🎉 设置完成！"
echo ""
echo "📋 接下来的步骤："
echo "1. 运行 'npm run dev' 启动开发服务器"
echo "2. 在浏览器中访问 http://localhost:3000"
echo "3. 按照界面提示配置你的跑步参数"
echo ""
echo "🚀 部署到Vercel："
echo "1. 安装 Vercel CLI: npm i -g vercel"
echo "2. 运行 'vercel' 进行部署"
echo ""
echo "📖 更多信息请查看 README.md 和 DEPLOYMENT.md"
