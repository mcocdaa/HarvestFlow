# HarvestFlow 改进方向

本文件记录代码审查中发现的潜在改进点，供后续迭代参考。

---

## 1. Schema Migration 方式脆弱

**位置**: `backend/core/database_manager.py` → `_initialize_tables()`

**问题**: 用 `try/except sqlite3.OperationalError` 来判断列是否已存在，会静默掩盖磁盘满、权限错误等真实故障，使所有 `OperationalError` 都被吞掉。

**建议**: 改用 `PRAGMA table_info(sessions)` 先查询列列表，只在列不存在时才执行 `ALTER TABLE`。这样可以精确判断，不会误伤其他错误。

> 已在本次优化中修复。

---

## 2. `import_session` 中的数据自引用

**位置**: `backend/managers/collector_manager.py` → `import_session()`

**问题**: 代码中有一行 `session_data["content"] = session_data`，将 dict 自身赋值给自己的一个字段，导致 `json.dumps` 时产生循环引用，抛出 `ValueError: Circular reference detected`。

**建议**: 在添加元数据字段（`file_path`、`content`）之前先做浅拷贝，将原始解析内容存入 `content`，再向 `session_data` 添加元数据字段。

> 已在本次优化中修复。

---

## 3. SQLite 并发写入无保护

**位置**: `backend/core/database_manager.py`

**问题**: 使用单一共享 `sqlite3.Connection` 并开启 `check_same_thread=False`，但没有任何写锁保护。FastAPI 默认多线程运行，并发写操作可能导致 `database is locked` 错误乃至数据损坏。

**建议**:
- 启用 WAL（Write-Ahead Logging）日志模式，提升并发读性能。
- 添加 `threading.Lock` 保护所有写操作（`execute + commit`）。

> 已在本次优化中修复。

---

## 4. `SessionManager` 是无意义的转发层

**位置**: `backend/managers/session_manager.py`

**问题**: `SessionManager` 几乎所有方法都只是将调用原样转发给 `DatabaseManager`，没有独立的业务逻辑（`get_session_content` 除外）。这增加了调用链长度，却没有带来实际价值。

**建议**: 有两种方向：
- **合并方向**: 将 `SessionManager` 中的逻辑（如 `get_session_content`）迁移到 `DatabaseManager`，让调用方直接使用 `database_manager`。
- **充实方向**: 将业务规则真正放入 `SessionManager`（如状态机校验、导入前去重检查等），让它承担真实职责，而 `DatabaseManager` 保持纯数据访问层。

推荐**充实方向**，将未来的业务逻辑（去重、状态流转校验）放在此层。

> 已在本次优化中实现：`create_session` 加入 session_id 去重检查，`update_session` 加入基于 `VALID_STATUS_TRANSITIONS` 的状态流转合法性校验。

---

## 5. `session_get_for_export` 的 Tags 过滤在应用层

**位置**: `backend/core/database_manager.py` → `session_get_for_export()`

**问题**: `tags` 过滤是在 Python 层逐条遍历实现的。当 `approved` 状态的数据量大时，会将大量数据拉入内存后再丢弃，造成不必要的内存压力和延迟。

**建议**: 利用 SQLite 的 `json_each()` 虚拟表函数将 tags 过滤下推到 SQL 层：

```sql
SELECT DISTINCT s.*
FROM sessions s, json_each(s.tags) t
WHERE s.status = 'approved'
  AND t.value IN (?, ?, ...)
```

或者在数据量尚小时，至少保持当前做法并加注释说明这是已知的性能弱点，待数据规模增长后再优化。

> 已在本次优化中实现：使用 `EXISTS (SELECT 1 FROM json_each(sessions.tags) WHERE value IN (...))` 将 tags 过滤下推到 SQL 层，要求 SQLite ≥ 3.9.0（内置 JSON1 扩展）。

---

## 6. 结构性优化轮（双路径消除 + 样板收敛）

**本轮主题**：消除双路径、做减法、重复代码抽象。

### 6.1 Curator 评分双路径（最严重）

**问题**: `CuratorManager.evaluate_session` 与 `plugins/curators/openclaw/hooks.py` 的
短路钩子逐字重复了整个编排（校验 → 回写 → 自动审批），插件只贡献评分算法。

**修复**: `evaluate_session` 拆为模板（`_validate_for_evaluation` → `_score` → 回写 →
自动审批）；新增窄钩子 `curator_manager_score_before`，插件只接管评分步骤
（hooks.py 75 行 → 33 行）。旧事件名 `evaluate_before/after` 保留。

### 6.2 JSONL 解析双路径

**问题**: `core/parsers.parse_jsonl_file` 与 `plugins/collectors/openclaw/backend.parse`
重复解析逻辑；插件默认启用并短路 `parse_before`，core 版实际是死代码。

**修复**: 删除 core 版及其测试（139 行）；`.jsonl` 解析由采集器插件独占。
**行为变更**: 禁用插件后手工导入 `.jsonl` 不再支持（内置扫描器本就只匹配 `.json`）。

### 6.3 会话更新 API 双路径

**问题**: `PATCH /reviewer/session/{id}` 与 `PATCH /sessions/{id}` 功能重叠，
且仅前者写审计日志。

**修复**: 删除 reviewer PATCH 端点与 `reviewer_manager.update_session` 转发层；
审计上移至 `session_manager.update_session(operator=...)`，API 层传 `operator="user"`。
**行为变更**: `PATCH /sessions/{id}` 现在会写 "modify" 审计日志（行为超集）；
内部流水线调用（如 curator 回写）不传 operator，不产生审计。

### 6.4 状态流转校验双路径

**问题**: `reviewer._review` 手工校验、curator 自动审批绕过校验、
`session_manager.update_session` 又有一套——同一规则三处两种口径。

**修复**: 新增 `SessionManager.apply_review()` 审批落库唯一入口（流转校验 +
委托 `session_review_apply` 原子操作）；reviewer 与 curator 自动审批统一走它。

### 6.5 样板收敛

- `BaseManager` 统一 `__init__` 创建 logger；删除 session/reviewer 空参数组
- `DatabaseManager`：`_ensure()` 替换 12 处连接检查、`_write()` 替换 6 处写锁样板
  （489 行 → 477 行，`session_review_apply` 显式事务保留）
- `setting_manager` 默认值统一为 `DEFAULTS` 常量（修正 PORT 3000/3010、
  HOST 0.0.0.0/127.0.0.1 漂移）；CORS 解析兼容已解析列表
- `secrets_manager._resolve_secret_value` 合并重复的 required 分支
- `collector.import_all` 与 `import_session` 共享 `_import_parsed` 路径
- `exporter.export` filters dict 单次构建后解包传参

### 6.6 已知遗留（后续可做）

- `hook_manager` sync/async 双分发合并（有注释说明理由，风险大于收益）
- `database_manager.session_get_for_export` 状态常量写死在 SQL 字符串中
  （`status = 'approved'`），可用参数化枚举
- `database_manager` 单连接 + 写锁模型在超高并发下仍是瓶颈

---

## 7. 本地部署实测与真实数据回归（Round 8）

以 `backend/data/test_sessions/agents/` 的真实 OpenClaw 导出数据逐功能实测，
发现并修复以下问题：

### 7.1 OpenClaw 采集器：真实格式解析失败（严重）

**问题**: `OpenClawCollector.parse()` 只支持扁平行格式
（`{"role", "content", "sessionId"}`），而真实 OpenClaw v3 导出是嵌套格式
（`{"type": "message", "message": {"role", "content"}}`）。真实文件解析结果为
101 条空消息、无 tools、session_id 取自文件名。

**修复**: `parse()` 兼容两种格式；非 message 事件行不再计入消息；
session_id 优先扁平 `sessionId`，其次 v3 会话头 `{"type":"session","id"}`。
**影响**: 修复前所有真实 .jsonl 导入均为空内容（且因 message_count 虚高被误自动通过）。

### 7.2 OpenClaw 采集器：Windows 路径回退在 POSIX 失效

**问题**: `scan()` 回退分支用 `Path(session_file).name` 取 Windows 路径文件名，
POSIX 上反斜杠不是分隔符，返回整串 → 回退文件永远找不到（本机 6 个真实会话全部扫描为 0）。
`_extract_metadata()` 的 basename 比较同理。

**修复**: 新增 `_path_basename()` 归一化分隔符后取名；`_extract_metadata()`
改用 `os.sep.join` 构造 agent_dir（原 `os.path.join('' , ...)` 会丢绝对路径开头的 `/`）。

### 7.3 Curator 窄钩子回归：tools_used 被写空

**问题**: Round 7 将 openclaw 评分改为窄钩子后，钩子只返回
`{score, is_high_value, tags, score_reasons}`；`evaluate_session` 中
`scored.get("tools_used", [])` 把 content 已有的 tools_used 覆盖为空。
旧插件实现会显式回写 `content["tools_used"]`。

**修复**: `tools_used = scored.get("tools_used", content.get("tools_used", []))`。

### 7.4 本地脚本：VITE 变量泄漏与停止范围过宽

**问题**:
- root `.env` 的 `VITE_API_BASE_URL`（Docker 构建用）经 `start.sh` 的 `load_env`
  导出，覆盖 frontend/.env 的"本地留空走代理"设计，导致本地前端请求到错误端口。
- `stop.sh` 的 `pkill -f "vite"` 会误杀其他项目的 vite；`python backend/main.py`
  模式也可能匹配其他项目。

**修复**:
- `start_frontend_local` 先 `unset VITE_API_BASE_URL VITE_API_KEY`；当 `PORT != 3000`
  时自动导出 `VITE_API_BASE_URL=http://localhost:$PORT`（多项目端口共存）。
- `start_backend_local` 改用绝对路径启动；`stop.sh` 按项目绝对路径精确匹配，
  不再影响其他项目进程。

### 7.5 Reviewer 缺失会话错误码不一致

**问题**: `POST /reviewer/approve|reject` 对不存在会话返回 400 "session not found"，
与 `GET /sessions/{id}`、`POST /curator/evaluate` 的 404 不一致。

**修复**: API 层将 `error == "session not found"` 映射为 404；补 API 测试。

### 7.6 实测覆盖

采集（scan/import/import-all/watch-folder）、会话（list/get/content/patch/delete/stats）、
自动审核（evaluate/evaluate-all/status）、人工审核（pending/approve/reject/batch/audit）、
导出（sharegpt/alpaca/过滤/history/错误路径）、插件（list/by-type）、前端页面与 CORS，
全部通过；新增采集器回归测试 6 例、curator 1 例、API 2 例（共 351 → 360）。
