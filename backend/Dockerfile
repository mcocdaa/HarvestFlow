# ============================================
# HarvestFlow 后端 Dockerfile
# 支持双模式密钥管理
# ============================================

FROM python:3.12-slim

# 安装 uv（官方静态二进制，用于按锁文件安装依赖）
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /uvx /bin/

WORKDIR /app

# 按锁文件安装运行依赖（不安装 dev 组；依赖均有预编译 wheel，无需编译器）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制后端代码
COPY . .

# 使用项目虚拟环境中的 python
ENV PATH="/app/.venv/bin:$PATH"

# 内部端口（固定）
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')" || exit 1

# 默认启动命令（会被 docker-compose 覆盖）
CMD ["python", "main.py"]
