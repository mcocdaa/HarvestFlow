#!/bin/bash
# ============================================
# HarvestFlow 停止脚本
# 用法:
#   ./stop.sh <mode>
#   mode: dev | prod
# 示例:
#   ./stop.sh dev    # 开发模式停止
#   ./stop.sh prod   # 生产模式停止
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

usage() {
    echo "用法: $0 <mode>"
    echo "  mode: dev | prod"
    echo ""
    echo "示例:"
    echo "  $0 dev   # 开发模式停止"
    echo "  $0 prod  # 生产模式停止"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

MODE="$1"

cd "$DOCKER_DIR"

if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

echo "========================================"
echo "HarvestFlow 停止"
echo "========================================"
echo "模式: $MODE"
echo "========================================"

if [ "$MODE" = "prod" ]; then
    docker stack rm harvestflow
    echo "等待服务移除..."
    sleep 5
else
    docker compose -p harvestflow -f docker-compose.base.yml -f docker-compose.backend.yml -f docker-compose.frontend.yml down 2>/dev/null || true
fi

echo ""
echo "✓ 停止完成"
echo "========================================"
