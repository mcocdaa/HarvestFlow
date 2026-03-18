#!/bin/bash

ROOT_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. &>/dev/null && pwd)
pushd $ROOT_PATH
# 启动开发环境

# 启动前端开发服务器
echo "Starting frontend development server..."
pushd frontend
    npm run dev &
popd

# 启动后端服务
echo "Starting backend server..."
pushd backend
    docker-compose up -d &
popd

echo "Development environment started!"
popd
