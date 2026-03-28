# HarvestFlow 后端目录

## 目录结构

```
backend/
├── api/                    # API 路由层
│   ├── v1/                # API v1 版本
│   │   ├── session.py     # 会话管理 API
│   │   ├── collector.py   # 收集器 API
│   │   ├── curator.py     # 审核器 API
│   │   ├── reviewer.py    # 审查器 API
│   │   ├── exporter.py    # 导出器 API
│   │   └── plugins.py     # 插件 API
│   └── __init__.py        # API 路由注册
├── core/                   # 核心模块
│   ├── database_manager.py # 数据库管理
│   ├── setting_manager.py  # 配置管理
│   ├── hook_manager.py     # 钩子管理
│   ├── plugin_manager.py   # 插件管理
│   ├── router_loader.py    # 路由加载器
│   └── secrets_manager.py  # 密钥管理
├── managers/               # 业务逻辑层
│   ├── session_manager.py  # 会话管理
│   ├── collector_manager.py# 收集器管理
│   ├── curator_manager.py  # 审核管理
│   ├── reviewer_manager.py # 审查管理
│   └── exporter_manager.py # 导出管理
├── tests/                  # 测试目录
│   ├── core_tests/        # 核心模块测试
│   ├── managers_tests/    # 管理器测试
│   └── api_tests/         # API 测试
├── data/                   # 数据目录（不提交到 git）
│   ├── db/                # 数据库文件
│   ├── raw_sessions/      # 原始会话数据
│   ├── agent_curated/     # AI 精选会话
│   └── human_approved/    # 人工批准会话
├── main.py                 # 应用入口
├── requirements.txt        # Python 依赖
├── pytest.ini             # 测试配置
├── Dockerfile             # Docker 构建配置
└── .gitignore            # Git 忽略规则
```

## 快速开始

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### Docker 开发

```bash
# 构建镜像
docker build -t harvestflow-backend .

# 启动容器
docker compose -f ../docker/docker-compose.backend.yml up
```

## 清理命令

使用清理脚本清除临时文件和缓存：

```bash
# 从项目根目录运行
bash scripts/cleanup_backend.sh
```

## 主要功能模块

### 1. API 层 (`api/`)
- RESTful API 路由定义
- 版本控制（当前为 v1）
- 请求验证和响应格式化

### 2. 核心层 (`core/`)
- 数据库连接管理
- 配置和密钥管理
- 插件系统支持
- 钩子系统

### 3. 管理层 (`managers/`)
- 会话生命周期管理
- 数据收集和导入
- 质量评估和审核
- 数据导出

### 4. 测试 (`tests/`)
- 单元测试
- 集成测试
- API 测试

## 数据目录说明

`data/` 目录包含以下子目录（不提交到 git）：

- `db/`: SQLite 数据库文件
- `raw_sessions/`: 收集的原始会话数据
- `agent_curated/`: AI 自动审核通过的会话
- `human_approved/`: 人工审核通过的会话

## 环境变量

主要环境变量（在 `.env` 文件中配置）：

- `DATA_DIR`: 数据目录路径
- `DB_PATH`: 数据库文件路径
- `PORT`: 服务端口
- `LOG_LEVEL`: 日志级别

## 开发规范

1. 所有新增 API 路由放在对应的版本目录下
2. 业务逻辑写在 `managers/` 层
3. 数据库操作统一在 `core/database_manager.py` 中封装
4. 使用钩子系统扩展功能时，在 `plugins/` 目录下创建插件
5. 所有新功能必须编写对应的测试用例

## 常用命令

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=backend --cov-report=html

# 检查代码格式
flake8 .

# 清理缓存
bash ../scripts/cleanup_backend.sh
```
