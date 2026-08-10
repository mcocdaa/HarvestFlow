#!/bin/bash
# ============================================
# HarvestFlow 停止脚本
# 用法:
#   ./stop.sh <mode>
#   mode: dev | local | prod
# 示例:
#   ./stop.sh dev    # 开发模式停止 (Docker Compose)
#   ./stop.sh local  # 本地模式停止 (kill processes)
#   ./stop.sh prod   # 生产模式停止 (Docker Swarm)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

usage() {
    echo "用法: $0 <mode>"
    echo "  mode: dev | local | prod"
    echo ""
    echo "示例:"
    echo "  $0 dev    # 开发模式停止"
    echo "  $0 local  # 本地模式停止"
    echo "  $0 prod   # 生产模式停止"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

MODE="$1"

load_env() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        . "$PROJECT_ROOT/.env"
        set +a
    fi
}

echo "========================================"
echo "HarvestFlow 停止"
echo "========================================"
echo "模式: $MODE"
echo "========================================"

case "$MODE" in
    dev)
        cd "$DOCKER_DIR"
        load_env
        docker compose -p harvestflow \
            -f docker-compose.base.yml \
            -f docker-compose.backend.yml \
            -f docker-compose.frontend.yml \
            down 2>/dev/null || true
        ;;

    local)
        load_env
        echo "停止本地后端进程..."
        pkill -f "python backend/main.py" 2>/dev/null || true
        echo "停止本地前端进程..."
        pkill -f "vite" 2>/dev/null || true
        ;;

    prod)
        cd "$DOCKER_DIR"
        load_env
        docker stack rm harvestflow 2>/dev/null || true
        echo "等待服务移除..."
        sleep 5
        ;;

    *)
        echo "未知模式: $MODE"
        usage
        ;;
esac

echo ""
echo "✓ 停止完成"
echo "========================================"
