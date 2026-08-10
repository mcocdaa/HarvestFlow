# HarvestFlow

HarvestFlow 是一个本地化的 Agent 会话数据采集与审核系统，用于收集、筛选、审核 Agent 会话数据并导出为训练格式。

## 功能特性

- **数据采集 (Collector)**: 扫描指定文件夹，自动导入 JSON 格式的会话数据
- **自动审核 (Curator)**: 基于插件的自动质量评估和筛选
- **人工审核 (Reviewer)**: 提供可视化界面进行人工审核和标注
- **数据导出 (Exporter)**: 支持多种格式导出（ShareGPT、Alpaca 等）
- **插件系统**: 可扩展的插件架构，支持自定义采集器、审核器和审核界面

## 技术栈

- **后端**: Python + FastAPI + SQLite
- **前端**: React + Ant Design + Vite
- **数据库**: SQLite (元数据) + 本地文件 (JSON)

## 项目结构

```
HarvestFlow/
├── backend/                    # 后端工作域
│   ├── api/v1/                 # API 路由
│   │   ├── session.py          # 会话管理 API
│   │   ├── collector.py        # 采集模块 API
│   │   ├── curator.py          # 自动审核 API
│   │   ├── reviewer.py         # 人工审核 API
│   │   ├── exporter.py         # 导出模块 API
│   │   └── plugins.py          # 插件管理 API
│   ├── core/                   # 核心组件
│   │   ├── setting_manager.py  # 配置管理（.env + 命令行）
│   │   ├── database_manager.py # SQLite 数据库封装
│   │   ├── hook_manager.py     # 钩子系统
│   │   ├── plugin_manager.py   # 插件加载器
│   │   ├── secrets_manager.py  # 密钥管理
│   │   └── router_loader.py    # 路由加载器
│   ├── managers/               # 业务逻辑管理器
│   │   ├── session_manager.py  # 会话管理
│   │   ├── collector_manager.py # 采集管理
│   │   ├── curator_manager.py  # 审核管理
│   │   ├── reviewer_manager.py # 人工审核管理
│   │   └── exporter_manager.py # 导出管理
│   ├── data/                   # 数据存储（不提交 git）
│   │   └── db/harvestflow.db   # SQLite 数据库
│   ├── tests/                  # 测试
│   ├── main.py                 # 应用入口
│   ├── requirements.txt        # 生产依赖
│   └── requirements-dev.txt    # 开发/测试依赖
├── frontend/                   # 前端工作域
│   ├── src/
│   │   ├── components/         # 组件
│   │   ├── pages/              # 页面
│   │   ├── services/           # API 服务
│   │   └── types/              # 类型定义
│   ├── package.json
│   └── vite.config.ts
├── plugins/                    # 插件工作域
│   ├── collectors/             # 采集插件
│   ├── curators/               # 自动审核插件
│   └── reviewers/              # 人工审核插件
```

## 数据库设计

### sessions 表
| 字段 | 类型 | 描述 |
|------|------|------|
| session_id | TEXT PRIMARY KEY | 唯一会话 ID |
| file_path | TEXT | JSON 文件路径 |
| status | TEXT | raw/curated/approved/rejected |
| quality_auto_score | INTEGER | 自动评分 (1-5) |
| quality_manual_score | INTEGER | 人工评分 (1-5) |
| agent_role | TEXT | Agent 角色 |
| task_type | TEXT | 任务类型 |
| tools_used | TEXT | 使用的工具 |
| tags | TEXT | 标签 (JSON 数组) |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### audit_logs 表
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 日志 ID |
| session_id | TEXT | 会话 ID |
| action | TEXT | 操作类型 (approve/reject/modify) |
| operator | TEXT | 操作者 (system/user) |
| details | TEXT | 详情 (JSON) |
| created_at | DATETIME | 操作时间 |

### export_records 表
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 记录 ID |
| export_format | TEXT | 导出格式 |
| file_path | TEXT | 导出文件路径 |
| filters | TEXT | 筛选条件 (JSON) |
| record_count | INTEGER | 导出数量 |
| version | TEXT | 版本号 |
| created_at | DATETIME | 导出时间 |

### plugins 表
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 插件 ID |
| name | TEXT | 插件名称 |
| plugin_type | TEXT | 插件类型 (collector/curator/reviewer) |
| is_enabled | BOOLEAN | 是否启用 |
| config | TEXT | 插件配置 (JSON) |
| created_at | DATETIME | 安装时间 |

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/sessions | 获取会话列表 |
| GET | /api/v1/sessions/{id} | 获取会话详情 |
| GET | /api/v1/sessions/{id}/content | 获取会话原始内容 |
| DELETE | /api/v1/sessions/{id} | 删除会话 |
| GET | /api/v1/collector/scan | 触发扫描 |
| POST | /api/v1/collector/import | 导入单个会话 |
| POST | /api/v1/collector/import-all | 批量导入 |
| POST | /api/v1/curator/evaluate/{id} | 评估会话 |
| POST | /api/v1/curator/evaluate-all | 批量评估 |
| POST | /api/v1/reviewer/approve/{id} | 通过审核 |
| POST | /api/v1/reviewer/reject/{id} | 驳回审核 |
| POST | /api/v1/reviewer/batch-approve | 批量审核通过 |
| POST | /api/v1/reviewer/batch-reject | 批量审核驳回 |
| PATCH | /api/v1/reviewer/session/{id} | 更新会话标注 |
| GET | /api/v1/reviewer/audit-logs | 获取审核日志 |
| POST | /api/v1/exporter/export | 导出数据 (JSON body) |
| GET | /api/v1/exporter/formats | 获取支持的导出格式 |
| GET | /api/v1/exporter/history | 获取导出历史 |
| GET | /api/v1/stats | 获取统计信息 |
| GET | /api/v1/plugins | 获取插件列表 |
| GET | /api/v1/plugins/{type} | 获取指定类型插件 |
| POST | /api/v1/plugins/enable?key= | 启用插件 |
| POST | /api/v1/plugins/disable?key= | 禁用插件 |

## 快速开始

### 本地开发

**启动方式必须通过 `scripts/start.sh` 脚本（项目规范要求）：**

```bash
./scripts/start.sh local full     # 本地模式启动前后端
./scripts/start.sh local backend  # 仅后端
./scripts/start.sh local frontend # 仅前端
```

后端服务在 `http://localhost:3000`，前端开发服务器在 `http://localhost:5173`。

### Docker 开发

使用 `scripts/start.sh` 管理前后端（本地/开发/生产模式）：

```bash
./scripts/start.sh dev full     # Docker Compose 前后端
./scripts/start.sh dev backend  # Docker Compose 后端
```

## 插件开发

HarvestFlow 支持可扩展的插件架构，包含 Collector（采集）、Curator（自动审核）、Reviewer（人工审核）和 Service 四种插件类型。完整的接口定义、开发指南和配置说明请参见 [plugins/README.md](plugins/README.md)。

## 配置说明

配置通过根目录 `.env` 文件进行（参考 `.env.example`），主要项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` / `PORT` | `0.0.0.0` / `3000` | 后端监听地址与端口 |
| `DATA_DIR` | `./backend/data` | 数据目录 |
| `DB_PATH` | `./backend/data/db/harvestflow.db` | SQLite 数据库路径 |
| `PLUGINS_DIR` | `./plugins` | 插件目录（相对项目根） |
| `WATCH_FOLDERS` | 空 | 监控文件夹列表，逗号分隔 |
| `CURATOR_ENABLED` | `true` | 是否启用自动审核 |
| `AUTO_APPROVE_THRESHOLD` | `4` | 自动审批阈值 |
| `CORS_ORIGINS` | `*` | 允许的 CORS 源，逗号分隔 |
| `SECRETS_YAML` | `./secrets/backend.yaml` | 密钥定义文件 |

所有配置也可通过命令行参数覆盖，例如：

```bash
python backend/main.py --port 3001 --log-level DEBUG --watch-folders /path/to/sessions
```

## 许可证

[LICENSE](LICENSE)
