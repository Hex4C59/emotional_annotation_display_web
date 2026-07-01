#!/bin/bash

set -e

PROJECT_DIR="/home/aimsl/code/Python/CCSEMO_dataset_and_annotation_tool"

cd "$PROJECT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "错误: 未找到 uv，请先安装 uv"
    exit 1
fi

echo "启动情感标注系统（本地反代模式）..."
echo "Flask 将监听 127.0.0.1:5001，供 nginx 反向代理到 10.10.16.135:5000"

if pgrep -f "start_server_local.py" >/dev/null 2>&1; then
    echo "检测到已有旧的本地反代实例，正在停止..."
    pkill -f "start_server_local.py" || true
    sleep 1
fi

uv run python start_server_local.py
