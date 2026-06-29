#!/bin/bash

# 情感标注系统一键启动脚本
# 自动配置环境变量并启动服务器

set -e  # 遇到错误立即退出

echo "🚀 情感标注系统一键启动脚本"
echo "================================"

# 检查 Python 版本
echo "📋 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python 版本: $PYTHON_VERSION"

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查并创建 .env 文件
echo "🔧 配置环境变量..."
DEFAULT_LANSYS_TOMCAT_URL="http://10.10.16.133:8080"
if [ ! -f ".env" ]; then
    echo "📝 创建 .env 文件..."
    
    # 生成强随机 SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # 创建 .env 文件
    cat > .env << EOF
# Flask 应用配置
FLASK_ENV=development
FLASK_DEBUG=False

# 安全配置
SECRET_KEY='$SECRET_KEY'

# Lansys Java 后端反向代理配置
LANSYS_PROXY_ENABLED=true
LANSYS_TOMCAT_URL=$DEFAULT_LANSYS_TOMCAT_URL
LANSYS_PROXY_TIMEOUT=120
EOF
    
    # 设置文件权限
    chmod 600 .env
    echo "✅ .env 文件已创建并设置权限"
else
    echo "✅ .env 文件已存在"
    
    # 检查 SECRET_KEY 是否已设置
    if ! grep -q "^SECRET_KEY=" .env || grep -q "your-very-secure-secret-key-here" .env; then
        echo "🔑 更新 SECRET_KEY..."
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        
        # 更新或添加 SECRET_KEY
        if grep -q "^SECRET_KEY=" .env; then
            sed -i "s/^SECRET_KEY=.*/SECRET_KEY='$SECRET_KEY'/" .env
        else
            echo "SECRET_KEY='$SECRET_KEY'" >> .env
        fi
        echo "✅ SECRET_KEY 已更新"
    fi
fi

# 确保 Lansys Java 后端反向代理配置存在；如需换 Java 地址，只改 .env 中的 LANSYS_TOMCAT_URL。
if ! grep -q "^LANSYS_PROXY_ENABLED=" .env; then
    echo "LANSYS_PROXY_ENABLED=true" >> .env
fi
if ! grep -q "^LANSYS_TOMCAT_URL=" .env; then
    echo "LANSYS_TOMCAT_URL=$DEFAULT_LANSYS_TOMCAT_URL" >> .env
fi
if ! grep -q "^LANSYS_PROXY_TIMEOUT=" .env; then
    echo "LANSYS_PROXY_TIMEOUT=120" >> .env
fi

echo "✅ Lansys 代理配置: $(grep '^LANSYS_TOMCAT_URL=' .env | tail -n 1 | cut -d= -f2-)"

# 检查依赖
echo "📦 检查项目依赖..."
if [ ! -f "uv.lock" ] && [ ! -d "venv" ]; then
    echo "⚠️  建议先安装项目依赖:"
    echo "   pip install -e ."
    echo "   或使用 uv: uv sync"
    echo ""
fi

# 运行安全检查
echo "🔒 运行安全检查..."
if [ -f "scripts/security_check.py" ]; then
    if command -v uv &> /dev/null; then
        uv run python scripts/security_check.py
    else
        python3 scripts/security_check.py
    fi
    if [ $? -ne 0 ]; then
        echo "⚠️  安全检查发现问题，但继续启动服务器..."
    fi
else
    echo "⚠️  未找到安全检查脚本"
fi

echo ""
echo "🎯 启动服务器..."
echo "================================"

# 启动服务器
if [ -f "start_server.py" ]; then
    echo "🌐 使用 start_server.py 启动..."
    if command -v uv &> /dev/null; then
        uv run python start_server.py
    else
        python3 start_server.py
    fi
elif [ -f "app.py" ]; then
    echo "🌐 使用 app.py 启动..."
    if command -v uv &> /dev/null; then
        uv run python app.py
    else
        python3 app.py
    fi
else
    echo "❌ 错误: 未找到启动文件 (start_server.py 或 app.py)"
    exit 1
fi
