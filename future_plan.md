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
