#!/bin/bash
# SJTU 体育跑步上传工具启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖是否已安装
if ! pip show PySide6 > /dev/null 2>&1; then
    echo "正在安装依赖包..."
    pip install -r requirements.txt
fi

# 启动应用
echo "启动 SJTU 体育跑步上传工具..."
python qtui.py
