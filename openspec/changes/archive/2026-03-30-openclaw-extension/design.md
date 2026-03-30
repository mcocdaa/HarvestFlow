# Design: HarvestFlow OpenClaw Extension

## 概述

本设计文档定义了 HarvestFlow OpenClaw Extension 的技术架构、目录结构和实现细节。

## 目录结构

```
openclaw-extension/
├── package.json              # NPM 包配置
├── openclaw.plugin.json      # OpenClaw 插件清单
├── tsconfig.json             # TypeScript 配置
├── src/
│   ├── index.ts              # 插件入口点
│   ├── client.ts             # HarvestFlow API 客户端
│   ├── tools/
│   │   ├── list.ts           # harvestflow_list 工具
│   │   ├── scanImport.ts     # harvestflow_scan_import 工具
│   │   ├── evaluate.ts       # harvestflow_evaluate 工具
│   │   └── review.ts         # harvestflow_review 工具
│   └── types/
│       └── index.ts          # TypeScript 类型定义
└── skills/
    └── harvestflow/
        └── SKILL.md          # 技能文档
```

## 技术栈

- **Runtime**: Node.js 18+
- **Language**: TypeScript 5.x
- **HTTP Client**: axios
- **Build**: tsc

## 核心组件

### 1. package.json

```json
{
  "name": "harvestflow-openclaw-extension",
  "version": "1.0.0",
  "description": "OpenClaw Extension for HarvestFlow - AI Agent session data collection and curation",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "prepublishOnly": "npm run build"
  },
  "keywords": ["openclaw", "harvestflow", "agent", "extension"],
  "dependencies": {
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0"
  }
}
```

### 2. openclaw.plugin.json

```json
{
  "name": "harvestflow",
  "version": "1.0.0",
  "description": "HarvestFlow integration for OpenClaw Agents",
  "entry": "dist/index.js",
  "tools": [
    "harvestflow_list",
    "harvestflow_scan_import",
    "harvestflow_evaluate",
    "harvestflow_review"
  ],
  "config": {
    "HARVESTFLOW_API_URL": {
      "type": "string",
      "default": "http://localhost:3001",
      "description": "HarvestFlow backend API URL"
    },
    "HARVESTFLOW_API_KEY": {
      "type": "string",
      "default": "",
      "description": "API Key for authentication (optional)"
    }
  }
}
```

### 3. src/client.ts

HarvestFlow API 客户端封装：

```typescript
export class HarvestFlowClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(config: { baseUrl: string; apiKey?: string }) {
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;
  }

  async health(): Promise<boolean>;
  async getSessions(params?: ListParams): Promise<SessionListResponse>;
  async getSession(sessionId: string): Promise<Session>;
  async getStats(): Promise<StatsResponse>;
  async scanFolder(folderPath?: string): Promise<ScanResponse>;
  async importSession(filePath: string): Promise<ImportResponse>;
  async importAll(folderPath?: string): Promise<ImportAllResponse>;
  async evaluateSession(sessionId: string): Promise<EvaluateResponse>;
  async evaluateAll(): Promise<EvaluateAllResponse>;
  async getPendingReviews(page?: number, pageSize?: number): Promise<PendingResponse>;
  async approveSession(sessionId: string, notes?: string, score?: number): Promise<ReviewResponse>;
  async rejectSession(sessionId: string, notes?: string, score?: number): Promise<ReviewResponse>;
  async batchApprove(sessionIds: string[]): Promise<BatchReviewResponse>;
  async batchReject(sessionIds: string[]): Promise<BatchReviewResponse>;
}
```

### 4. 工具实现

#### harvestflow_list

**参数:**
- `session_id` (optional): 获取特定会话详情
- `status` (optional): 按状态过滤 (raw, approved, rejected)
- `page` (optional): 页码，默认 1
- `page_size` (optional): 每页数量，默认 20
- `stats` (optional): 是否返回统计信息

**返回:**
- 会话列表或单个会话详情，或统计信息

#### harvestflow_scan_import

**参数:**
- `action` (required): "scan" | "import" | "import_all"
- `folder_path` (optional): 文件夹路径
- `file_path` (optional): 单个文件路径（用于 import）

**返回:**
- 扫描结果或导入结果

#### harvestflow_evaluate

**参数:**
- `session_id` (optional): 评估特定会话
- `scope` (optional): "single" | "all"
- `action` (optional): "evaluate" | "status"

**返回:**
- 评估结果或 Curator 状态

#### harvestflow_review

**参数:**
- `action` (required): "pending" | "approve" | "reject" | "batch_approve" | "batch_reject"
- `session_id` (optional): 单个会话 ID
- `session_ids` (optional): 批量会话 ID 列表
- `notes` (optional): 审核备注
- `score` (optional): 人工评分

**返回:**
- 审核结果或待审核列表

## 错误处理

所有工具 SHALL 实现统一的错误处理：

```typescript
interface ToolResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}
```

错误类型：
- `ConnectionError`: 无法连接到 HarvestFlow 后端
- `NotFoundError`: 会话不存在
- `ValidationError`: 参数无效
- `ServerError`: 后端服务错误

## 配置

插件 SHALL 从以下位置读取配置（优先级从高到低）：

1. 环境变量: `HARVESTFLOW_API_URL`, `HARVESTFLOW_API_KEY`
2. OpenClaw 配置文件中的插件配置
3. 默认值: `http://localhost:3001`

## 安全考虑

1. API Key SHALL 存储在环境变量或安全密钥管理系统中
2. 所有 SHALL 支持 HTTPS 连接
3. 错误消息 SHALL 不暴露敏感信息

## 依赖关系

- HarvestFlow Backend API (端口 3000/3001)
- OpenClaw Framework 2026.x+

## 测试策略

1. 单元测试: 使用 jest 测试每个工具
2. 集成测试: 使用 mock server 测试 API 客户端
3. E2E 测试: 与真实 HarvestFlow 后端测试
