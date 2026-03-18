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
- **前端**: React + Redux + Ant Design + Vite
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
│   │   └── plugin.py           # 插件管理 API
│   ├── config/                 # 配置文件
│   │   └── settings.py         # 项目配置
│   ├── core/                   # 核心组件
│   │   ├── database.py         # SQLite 数据库连接
│   │   ├── router_loader.py    # 路由加载器
│   │   └── plugin_loader.py    # 插件加载器
│   ├── managers/               # 业务逻辑管理器
│   │   ├── db_manager.py       # 数据库管理
│   │   ├── session_manager.py  # 会话管理
│   │   ├── collector_manager.py # 采集管理
│   │   ├── curator_manager.py  # 审核管理
│   │   └── exporter_manager.py # 导出管理
│   ├── data/                   # 数据存储
│   │   ├── raw_sessions/       # 原始会话数据
│   │   ├── agent_curated/      # 自动审核后的数据
│   │   ├── human_approved/     # 人工审核通过的数据
│   │   └── export/             # 导出数据
│   ├── db/                     # SQLite 数据库文件
│   │   └── harvestflow.db
│   ├── main.py                 # 应用入口
│   └── requirements.txt        # Python 依赖
├── frontend/                   # 前端工作域
│   ├── src/
│   │   ├── components/         # 组件
│   │   ├── pages/              # 页面
│   │   ├── services/           # API 服务
│   │   └── store/              # 状态管理
│   ├── package.json
│   └── vite.config.ts
├── plugins/                    # 插件工作域
│   ├── collectors/             # 采集插件
│   ├── curators/               # 自动审核插件
│   └── reviewers/              # 人工审核插件
└── config/
    └── config.yaml             # 全局配置
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
| POST | /api/v1/collector/scan | 触发扫描 |
| POST | /api/v1/collector/import | 导入单个会话 |
| POST | /api/v1/collector/import/all | 批量导入 |
| POST | /api/v1/curator/evaluate/{id} | 评估会话 |
| POST | /api/v1/curator/evaluate/all | 批量评估 |
| POST | /api/v1/reviewer/approve/{id} | 通过审核 |
| POST | /api/v1/reviewer/reject/{id} | 驳回审核 |
| POST | /api/v1/reviewer/batch | 批量审核 |
| PUT | /api/v1/reviewer/update/{id} | 更新会话标注 |
| POST | /api/v1/export | 导出数据 |
| GET | /api/v1/stats | 获取统计信息 |
| GET | /api/v1/plugins | 获取插件列表 |
| GET | /api/v1/plugins/{type} | 获取指定类型插件 |
| POST | /api/v1/plugins/{name}/enable | 启用插件 |
| POST | /api/v1/plugins/{name}/disable | 禁用插件 |

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端服务将在 `http://localhost:3000` 启动。

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器将在 `http://localhost:5173` 启动。

## 插件开发

### 采集插件接口

```python
class CollectorPlugin:
    name: str
    description: str

    def scan() -> List[str]:        # 返回文件路径列表
    def parse(file_path: str) -> dict:  # 解析文件内容
```

### 审核插件接口

```python
class CuratorPlugin:
    name: str
    description: str

    def evaluate(session: dict) -> dict:  # 返回评分结果
    # 必需字段: score, is_high_value, tags
```

### 人工审核插件接口

```python
class ReviewerPlugin:
    name: str
    description: str

    def get_extra_fields() -> List[dict]:  # 返回额外字段定义
    def validate(session: dict) -> bool:   # 验证会话
```

## 配置说明

编辑 `config/config.yaml` 进行配置：

```yaml
app:
  name: HarvestFlow
  version: 1.0.0

backend:
  host: 0.0.0.0
  port: 3000
  db_path: ./backend/db/harvestflow.db
  data_dir: ./backend/data

collector:
  watch_folders: []
  poll_interval: 60

curator:
  default_enabled: true
  auto_approve_threshold: 4

export:
  default_format: sharegpt
  output_dir: ./backend/data/export

plugins:
  dir: ./plugins
```

## 许可证

[LICENSE](LICENSE)
