#!/bin/bash
# ============================================
# HarvestFlow 停止脚本
# 用法:
#   ./stop.sh <mode>
#   mode: local | dev
# 示例:
#   ./stop.sh local  # 停止本地源码进程
#   ./stop.sh dev    # 停止 Docker Compose 容器
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
COMPOSE_PROJECT="harvestflow"

usage() {
    echo "用法: $0 <mode>"
    echo "  mode: local | dev"
    echo ""
    echo "示例:"
    echo "  $0 local  # 停止本地源码进程"
    echo "  $0 dev    # 停止 Docker Compose 容器"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

MODE="$1"

if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    . "$PROJECT_ROOT/.env"
    set +a
fi

echo "========================================"
echo "HarvestFlow 停止"
echo "========================================"
echo "模式: $MODE"
echo "========================================"

case "$MODE" in
    local)
        echo "停止本地后端进程..."
        # 精确匹配本项目绝对路径，避免误杀其他项目的同名进程
        pkill -f "$PROJECT_ROOT/backend/main.py" 2>/dev/null || true
        echo "停止本地前端进程..."
        # vite 的 node 进程 cmdline 含项目内绝对路径（start.sh 启动时 cwd 为 frontend/）
        pkill -f "$PROJECT_ROOT/frontend/node_modules/.bin/vite" 2>/dev/null || true
        ;;

    dev)
        docker compose -p "$COMPOSE_PROJECT" -f "$COMPOSE_FILE" down 2>/dev/null || true
        ;;

    *)
        echo "未知模式: $MODE"
        usage
        ;;
esac

echo ""
echo "✓ 停止完成"
echo "========================================"
