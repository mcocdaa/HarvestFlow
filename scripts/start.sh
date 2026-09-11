#!/bin/bash
# ============================================
# HarvestFlow 启动脚本
# 用法:
#   ./start.sh <mode> [service]
#   mode:    local | dev
#   service: backend | frontend | full (default: full)
#
# 模式说明:
#   local  - 本地源码模式（不使用 Docker，开发用）
#   dev    - Docker Compose 模式（部署用，自动创建 .env）
#
# 示例:
#   ./start.sh local full      # 本地源码启动前后端
#   ./start.sh local backend   # 仅后端 (uv)
#   ./start.sh local frontend  # 仅前端 (vite)
#   ./start.sh dev full        # Docker Compose 启动前后端
#   ./start.sh dev backend     # Docker Compose 仅后端
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
COMPOSE_PROJECT="harvestflow"

usage() {
    echo "用法：$0 <mode> [service]"
    echo "  mode:    local | dev"
    echo "  service: backend | frontend | full (默认：full)"
    echo ""
    echo "模式说明:"
    echo "  local  - 本地源码模式（不使用 Docker，开发用）"
    echo "  dev    - Docker Compose 模式（部署用，自动创建 .env）"
    echo ""
    echo "示例:"
    echo "  $0 local full      # 本地源码启动前后端"
    echo "  $0 local backend   # 仅后端 (uv)"
    echo "  $0 local frontend  # 仅前端 (vite)"
    echo "  $0 dev full        # Docker Compose 启动前后端"
    echo "  $0 dev backend     # Docker Compose 仅后端"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

MODE="$1"
SERVICE="${2:-full}"

case "$MODE" in
    local|dev) ;;
    *) echo "未知模式：$MODE"; usage ;;
esac

case "$SERVICE" in
    backend|frontend|full) ;;
    *) echo "未知服务：$SERVICE"; usage ;;
esac

# 无 .env 时从模板自动创建，保证 cp .env.example .env 的等价体验
ensure_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ] && [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "✓ 已从 .env.example 创建 .env（可按需修改）"
    fi
}

load_env() {
    ensure_env
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        . "$PROJECT_ROOT/.env"
        set +a
    fi
}

start_frontend_local() {
    echo "检查前端依赖..."
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo "安装前端依赖..."
        cd "$FRONTEND_DIR" && npm install
    fi
    echo "启动本地前端服务..."
    # 本地模式默认走 Vite 代理（/api → localhost:3000）：
    # 清除 .env 中供 Docker 构建使用的 VITE_* 变量，避免覆盖 frontend/.env 的留空设计
    unset VITE_API_BASE_URL VITE_API_KEY
    # 后端端口非默认 3000 时（多项目共存场景），前端直连对应端口；默认仍走代理
    if [ -n "$PORT" ] && [ "$PORT" != "3000" ]; then
        export VITE_API_BASE_URL="http://localhost:$PORT"
    fi
    echo "✓ 前端服务将启动 (http://localhost:5173)"
    echo "按 Ctrl+C 停止服务"
    cd "$FRONTEND_DIR" && npm run dev
}

start_backend_local() {
    echo "启动本地后端服务..."
    if ! command -v uv >/dev/null 2>&1; then
        echo "✗ 未找到 uv。请先安装：curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    # 从项目根启动，保证 .env 相对路径（DATA_DIR/DB_PATH/PLUGINS_DIR）正确解析
    # uv 按 backend/uv.lock 自动创建/同步 backend/.venv 后运行
    # 使用绝对路径便于 stop.sh 精确匹配本项目进程（避免误杀其他项目）
    cd "$PROJECT_ROOT"
    uv run --project backend --frozen --no-dev python "$PROJECT_ROOT/backend/main.py" &
    echo "✓ 本地后端已启动 (http://localhost:${PORT:-3000})"
}

start_docker() {
    command -v docker >/dev/null 2>&1 || { echo "✗ 未找到 docker"; exit 1; }
    load_env
    echo "停止已有容器..."
    docker compose -p "$COMPOSE_PROJECT" -f "$COMPOSE_FILE" down 2>/dev/null || true

    local target="$SERVICE"
    [ "$target" = "full" ] && target=""
    echo "构建并启动容器（首次构建需要几分钟）..."
    docker compose -p "$COMPOSE_PROJECT" -f "$COMPOSE_FILE" up --build -d $target

    echo ""
    echo "✓ Docker 服务已启动"
    echo "  前端: http://localhost:${FRONTEND_EXTERNAL_PORT:-8001}"
    echo "  后端: http://localhost:${BACKEND_EXTERNAL_PORT:-3001}"
}

case "$MODE" in
    dev)
        start_docker
        ;;
    local)
        load_env
        case "$SERVICE" in
            backend)
                start_backend_local
                ;;
            frontend)
                start_frontend_local
                ;;
            full)
                trap 'kill $(jobs -p) 2>/dev/null' EXIT
                echo "启动本地后端..."
                start_backend_local
                sleep 2
                echo "启动本地前端..."
                start_frontend_local
                ;;
        esac
        echo ""
        echo "✓ HarvestFlow 已启动 (本地模式)"
        ;;
esac
