#!/bin/bash
# ============================================
# HarvestFlow 启动脚本
# 用法:
#   ./start.sh <mode> [service]
#   mode: dev | prod | local
#   service: backend | frontend | full (default: full)
#
#   local 模式说明:
#     - frontend-local: 本地启动前端(不通过Docker)
#     - full: 本地启动前后端(不通过Docker)
#
# 示例:
#   ./start.sh dev backend         # 开发模式，仅后端(Docker)
#   ./start.sh dev frontend        # 开发模式，仅前端(Docker)
#   ./start.sh dev frontend-local  # 开发模式，仅前端(本地)
#   ./start.sh local full          # 本地模式，前后端都本地启动
#   ./start.sh prod full           # 生产模式，全栈(Docker)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

usage() {
    echo "用法: $0 <mode> [service]"
    echo "  mode:    dev | prod | local"
    echo "  service: backend | frontend | frontend-local | full (默认: full)"
    echo ""
    echo "模式说明:"
    echo "  dev    - 开发模式，使用 Docker"
    echo "  local  - 本地模式，不使用 Docker"
    echo "  prod   - 生产模式，使用 Docker Swarm"
    echo ""
    echo "服务说明:"
    echo "  backend       - 仅后端"
    echo "  frontend      - 仅前端 (Docker)"
    echo "  frontend-local - 仅前端 (本地，不通过Docker)"
    echo "  full          - 全部服务"
    echo ""
    echo "示例:"
    echo "  $0 dev backend         # 开发模式，仅后端"
    echo "  $0 dev frontend        # 开发模式，仅前端(Docker)"
    echo "  $0 dev frontend-local  # 开发模式，仅前端(本地)"
    echo "  $0 local full          # 本地模式，前后端都本地启动"
    echo "  $0 prod full           # 生产模式，全栈"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

MODE="$1"
SERVICE="${2:-full}"

stop_docker_services() {
    echo "停止已有 Docker 服务..."
    if [ "$MODE" = "prod" ]; then
        docker stack rm harvestflow 2>/dev/null || true
        echo "等待服务移除..."
        sleep 5
    else
        docker compose -p harvestflow -f "$DOCKER_DIR/docker-compose.base.yml" down 2>/dev/null || true
    fi
    echo "✓ Docker 服务已停止"
}

start_frontend_local() {
    echo "检查前端依赖..."
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo "安装前端依赖..."
        cd "$FRONTEND_DIR" && npm install
    fi
    echo "启动本地前端服务..."
    cd "$FRONTEND_DIR" && npm run dev &
    echo "✓ 本地前端已启动 (http://localhost:5173)"
}

load_env() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    fi
}

case "$MODE" in
    dev)
        COMPOSE_COMMAND="docker compose"
        COMPOSE_FILES="-f $DOCKER_DIR/docker-compose.base.yml"
        case "$SERVICE" in
            backend)
                COMPOSE_FILES="$COMPOSE_FILES -f $DOCKER_DIR/docker-compose.backend.yml"
                ;;
            frontend|frontend-local)
                COMPOSE_FILES="$COMPOSE_FILES -f $DOCKER_DIR/docker-compose.frontend.yml"
                ;;
            full)
                COMPOSE_FILES="$COMPOSE_FILES -f $DOCKER_DIR/docker-compose.backend.yml -f $DOCKER_DIR/docker-compose.frontend.yml"
                ;;
            *)
                echo "未知服务: $SERVICE"
                usage
                ;;
        esac
        ;;
    local)
        case "$SERVICE" in
            backend)
                echo "本地模式暂不支持仅后端"
                usage
                ;;
            frontend|frontend-local)
                load_env
                start_frontend_local
                exit 0
                ;;
            full)
                load_env
                start_frontend_local
                exit 0
                ;;
            *)
                echo "未知服务: $SERVICE"
                usage
                ;;
        esac
        ;;
    prod)
        COMPOSE_COMMAND="docker stack"
        STACK_NAME="harvestflow"
        case "$SERVICE" in
            backend)
                COMPOSE_FILES="$DOCKER_DIR/docker-compose.backend.yml"
                ;;
            frontend|frontend-local)
                echo "生产模式暂不支持仅前端部署"
                usage
                ;;
            full)
                COMPOSE_FILES="$DOCKER_DIR/docker-compose.backend.yml -f $DOCKER_DIR/docker-compose.frontend.yml"
                ;;
            *)
                echo "未知服务: $SERVICE"
                usage
                ;;
        esac
        ;;
    *)
        echo "未知模式: $MODE"
        usage
        ;;
esac

cd "$DOCKER_DIR"
load_env
stop_docker_services

echo ""
echo "========================================"
echo "HarvestFlow 启动"
echo "========================================"
echo "模式: $MODE"
echo "服务: $SERVICE"
echo "命令: $COMPOSE_COMMAND"
echo "========================================"

if [ "$MODE" = "prod" ]; then
    $COMPOSE_COMMAND deploy -c "$DOCKER_DIR/docker-compose.base.yml" -c "$COMPOSE_FILES" --composefile "$DOCKER_DIR/docker-compose.backend.yml" "$STACK_NAME"
else
    $COMPOSE_COMMAND -p harvestflow $COMPOSE_FILES up --build -d
fi

echo ""
echo "✓ 启动完成"
echo "========================================"
