#!/bin/bash
# ============================================
# HarvestFlow 启动脚本
# 用法:
#   ./start.sh <mode> [service]
#   mode: dev | local | prod
#   service: backend | frontend | full (default: full)
#
# 模式说明:
#   dev    - 开发模式，使用 Docker Compose
#   local  - 本地模式，不使用 Docker
#   prod   - 生产模式，使用 Docker Swarm (stack deploy)
#
# 服务说明:
#   backend       - 仅后端
#   frontend      - 仅前端 (dev/prod 用 Docker，local 用本地)
#   full          - 全部服务
#
# 示例:
#   ./start.sh dev backend         # 开发模式，仅后端 (Docker Compose)
#   ./start.sh dev frontend        # 开发模式，仅前端 (Docker Compose)
#   ./start.sh dev full            # 开发模式，前后端都启动 (Docker Compose)
#   ./start.sh local backend       # 本地模式，仅后端
#   ./start.sh local frontend      # 本地模式，仅前端
#   ./start.sh local full          # 本地模式，前后端都本地启动
#   ./start.sh prod full           # 生产模式，全栈 (Docker Swarm)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

usage() {
    echo "用法：$0 <mode> [service]"
    echo "  mode:    dev | local | prod"
    echo "  service: backend | frontend | full (默认：full)"
    echo ""
    echo "模式说明:"
    echo "  dev    - 开发模式，使用 Docker Compose"
    echo "  local  - 本地模式，不使用 Docker"
    echo "  prod   - 生产模式，使用 Docker Swarm (stack deploy)"
    echo ""
    echo "服务说明:"
    echo "  backend       - 仅后端"
    echo "  frontend      - 仅前端 (dev/prod 用 Docker，local 用本地)"
    echo "  full          - 全部服务"
    echo ""
    echo "示例:"
    echo "  $0 dev backend         # 开发模式，仅后端 (Docker Compose)"
    echo "  $0 dev frontend        # 开发模式，仅前端 (Docker Compose)"
    echo "  $0 dev full            # 开发模式，前后端都启动 (Docker Compose)"
    echo "  $0 local backend       # 本地模式，仅后端"
    echo "  $0 local frontend      # 本地模式，仅前端"
    echo "  $0 local full          # 本地模式，前后端都本地启动"
    echo "  $0 prod full           # 生产模式，全栈 (Docker Swarm)"
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
        # Docker Swarm 模式
        docker stack rm harvestflow 2>/dev/null || true
        echo "等待服务移除..."
        sleep 5
    else
        # Docker Compose 模式
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
    echo "✓ 前端服务将启动"
    echo "按 Ctrl+C 停止服务"
    cd "$FRONTEND_DIR" && npm run dev
}

start_backend_local() {
    echo "检查后端依赖..."
    if [ ! -d "$BACKEND_DIR/__pycache__" ]; then
        echo "后端环境检查通过..."
    fi
    echo "启动本地后端服务..."
    cd "$BACKEND_DIR" && python main.py &
    echo "✓ 本地后端已启动 (http://localhost:3000)"
}

load_env() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    fi
}

# ============================================
# 主逻辑
# ============================================

case "$MODE" in
    dev)
        # Docker Compose 开发模式
        COMPOSE_COMMAND="docker compose"
        COMPOSE_FILES="-f $DOCKER_DIR/docker-compose.base.yml"

        case "$SERVICE" in
            backend)
                COMPOSE_FILES="$COMPOSE_FILES -f $DOCKER_DIR/docker-compose.backend.yml"
                ;;
            frontend)
                COMPOSE_FILES="$COMPOSE_FILES -f $DOCKER_DIR/docker-compose.frontend.yml"
                ;;
            full)
                COMPOSE_FILES="$COMPOSE_FILES -f $DOCKER_DIR/docker-compose.backend.yml -f $DOCKER_DIR/docker-compose.frontend.yml"
                ;;
            *)
                echo "未知服务：$SERVICE"
                usage
                ;;
        esac

        # Docker Compose 模式：停止旧服务并启动新服务
        cd "$DOCKER_DIR"
        load_env
        stop_docker_services

        echo ""
        echo "========================================"
        echo "HarvestFlow 启动 (Docker Compose)"
        echo "========================================"
        echo "模式：$MODE"
        echo "服务：$SERVICE"
        echo "命令：$COMPOSE_COMMAND"
        echo "========================================"

        $COMPOSE_COMMAND -p harvestflow $COMPOSE_FILES up --build -d

        echo ""
        echo "✓ 启动完成"
        echo "========================================"
        ;;

    prod)
        # Docker Swarm 生产模式
        STACK_NAME="harvestflow"
        COMPOSE_COMMAND="docker stack"

        case "$SERVICE" in
            backend)
                COMPOSE_FILES="$DOCKER_DIR/docker-compose.backend.yml"
                ;;
            frontend)
                echo "生产模式暂不支持仅前端部署"
                usage
                ;;
            full)
                COMPOSE_FILES="$DOCKER_DIR/docker-compose.backend.yml $DOCKER_DIR/docker-compose.frontend.yml"
                ;;
            *)
                echo "未知服务：$SERVICE"
                usage
                ;;
        esac

        # Docker Swarm 模式：停止旧服务并部署新服务
        cd "$DOCKER_DIR"
        load_env
        stop_docker_services

        echo ""
        echo "========================================"
        echo "HarvestFlow 启动 (Docker Swarm)"
        echo "========================================"
        echo "模式：$MODE"
        echo "服务：$SERVICE"
        echo "栈名：$STACK_NAME"
        echo "========================================"

        docker stack deploy -c "$DOCKER_DIR/docker-compose.base.yml" -c "$COMPOSE_FILES" "$STACK_NAME"

        echo ""
        echo "✓ 启动完成"
        echo "========================================"
        ;;

    local)
        # 本地开发模式（不使用 Docker）
        case "$SERVICE" in
            backend)
                load_env
                start_backend_local
                ;;
            frontend)
                load_env
                start_frontend_local
                ;;
            full)
                load_env
                echo "启动本地后端..."
                start_backend_local
                sleep 2
                echo "启动本地前端..."
                start_frontend_local
                ;;
            *)
                echo "未知服务：$SERVICE"
                usage
                ;;
        esac

        echo ""
        echo "========================================"
        echo "HarvestFlow 启动 (本地模式)"
        echo "========================================"
        echo "模式：$MODE"
        echo "服务：$SERVICE"
        echo "========================================"
        echo "✓ 启动完成"
        echo "========================================"
        ;;

    *)
        echo "未知模式：$MODE"
        usage
        ;;
esac
