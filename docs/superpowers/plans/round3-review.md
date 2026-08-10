# Round 3 审查修复计划：后端逻辑 + 插件逻辑

- 日期: 2026-08-10
- 基础分支: `main`（4c518d2）
- 新分支: `refactor/round3-review`
- 范围: 全部 A-F（用户决策）
- 用户决策:
  1. 全部发现修复
  2. 插件契约失配 → 改 `plugin-openclaw-to-harvestflow/src/client.ts` 对齐后端（后端路径/参数语义保持不变）
  3. API 鉴权 → Bearer token 全局校验，`HARVESTFLOW_API_KEY` 未配置时默认关闭
  4. 清理空壳插件（collectors/default、curators/default、reviewers/default）+ 实现自动审批

---

## A. 后端核心 Bug（数据容错 / 配置优先级）

### A1. [B1] tags/tools_used 反序列化容错
- **位置**: `backend/core/database_manager.py:455-466`
- **问题**: `_deserialize_session_fields` 中 tags/tools_used 直接 `json.loads` 无 try/except（content 有），一条脏数据使列表/导出/审核全链路 500
- **方案**:
  1. tags/tools_used 的 `json.loads` 与 content 一致包 try/except `json.JSONDecodeError`，失败保留原字符串
  2. API 层堵源头：`backend/api/v1/session.py:40` 的 PATCH `updates: Dict` 改为 Pydantic 模型（`SessionUpdate`，tags/tools_used 类型 `List[str]`，非法时 422）；`backend/api/v1/reviewer.py:38` 同步
- **测试**: 新增 PATCH 脏 tags → 422；DB 层脏数据读取不炸

### A2. [B3] argparse 默认值遮蔽 .env
- **位置**: `collector_manager.py:57`、`curator_manager.py:57,60`、`exporter_manager.py:64`
- **问题**: `--watch-folders` default=""、`--curator-enabled` default="true"、`--auto-approve-threshold` default=4、`--export-default-format` default=sharegpt → `getattr(args, x, fallback)` 永远命中 args，`.env` 中 `WATCH_FOLDERS`/`CURATOR_ENABLED`/`AUTO_APPROVE_THRESHOLD`/`EXPORT_DEFAULT_FORMAT` 静默失效
- **方案**: register_arguments 的 default 全部改为 `None`；init 用 `getattr(args, 'x', None) or setting_manager.get(...)`（与 `export_output_dir` 写法一致）。`--curator-enabled` 的 choices 保留（用户显式传参时仍校验）
- **测试**: 更新 `test_init.py`（现测试手动删属性绕过；补"args 带 None 属性时走 .env fallback"用例）；.env 配置生效验证

### A3. [L6] session_id NULL 孤行
- **位置**: `backend/core/database_manager.py` schema（建表处）+ `session_create:148-163`
- **方案**: 建表 `session_id TEXT PRIMARY KEY NOT NULL`；`session_create` 入口 `if not session_data.get("session_id"): return None`
- **测试**: session_create 无 id → None，不落库

### A4. [L8] 分页 clamp
- **位置**: `database_manager.py:192,201,368-378`
- **方案**: `page_size = max(1, min(page_size, 100))`；`page = max(1, page)`；`audit_log_get`/`export_record_get_history` 的 `limit = max(1, min(limit, 100))`
- **测试**: page_size=-5 / limit=-1 → 不超限

### A5. [L7] 导出文件名冲突
- **位置**: `exporter_manager.py:115-116`
- **方案**: 文件名加毫秒时间戳 + 8 位随机后缀：`{format}_{ts_ms}_{version}_{uuid4().hex[:8]}.jsonl`
- **测试**: 并发两次 export → 不同文件名

### A6. [L5] 重复导入计数
- **位置**: `collector_manager.py:172-228`
- **方案**: `import_session` 在 `parse_session_file` 后先 `session_manager.get_session(session_id)`，已存在 → 返回 `("skip", session_id)` 语义；`import_all` 返回值增加 `skipped` 计数与 `skipped_ids`，`imported` 只统计真正新建
- **测试**: 同文件导入两次 → imported=1, skipped=1

### A7. [D] 死代码清理
- 删 `curator_manager._mark_as_curated`（157-164 行，含其 wrap_hooks 装饰器；grep 确认 hook 名无引用）
- 删 `secrets_manager._get_value_source`（273-276，仅测试引用；同步更新引用它的测试）
- `.env`/`.env.example` 删除 `POLL_INTERVAL`（零引用死配置；watch_folders 保持手动触发语义，README 说明）
- `plugin_manager.init()` 空实现保留（main.py:93 调用 + wrap_hooks 提供生命周期钩子，属设计）

---

## B. API 语义与安全

### B1. [B2] Bearer token 全局鉴权
- **新增**: `backend/core/auth.py` — `HTTPBearer(auto_error=False)` + `require_api_key` 依赖：
  - `HARVESTFLOW_API_KEY` 未配置/为空 → 直接放行（本地默认关闭，向后兼容）
  - 已配置 → 校验 `Authorization: Bearer <key>`，不匹配/缺失 → 401 + `WWW-Authenticate: Bearer`
- **挂载**: `backend/api/__init__.py:28` `include_router(..., dependencies=[Depends(require_api_key)])`（作用于全部 `/api/*`；`/health` 在 main.py 定义不受影响）
- **配置**: `.env`/`.env.example` 新增 `HARVESTFLOW_API_KEY=`（默认空 = 关闭）+ 注释说明
- **前端**: `frontend/.env(.example)` 新增可选 `VITE_API_KEY`；`frontend/src/services/client.ts` axios.create 若配置则带 `Authorization: Bearer`
- **npm 插件**: 已支持（client.ts:20-27），无需改动
- **测试**: 新测试 — key 未配置放行；key 配置后无头 401 / 错 key 401 / 正确 key 200（用 TestClient）

### B2. [L3] PATCH 语义区分
- **位置**: `session_manager.py:111-134` + `session.py:39-44`
- **方案**:
  - `update_session`：会话不存在 → 返回 None（API 404）；非法流转 → 抛 `ValueError("invalid status transition")`；空更新（无 allowed_fields）→ 返回现有会话（幂等 PATCH）
  - `session.py`: catch ValueError → `HTTPException(409, detail="Invalid status transition")`
  - `reviewer_manager.update_session:79-81`: catch ValueError → 返回 error dict（现有契约不变）
- **测试**: PATCH 不存在 → 404；非法流转 → 409；空更新 → 200 返回原 session

### B3. [L4] 导出失败 4xx
- **位置**: `exporter.py:23-33`
- **方案**: `result["success"] is False` → `HTTPException(400, detail=result.get("message", "Export failed"))`（格式不支持 422）
- **前端**: `Export.tsx:42-43` 无需改（拦截器统一 message.error；成功后仍 message.success）
- **测试**: 无会话导出 → 400（TestClient）

### B4. [L9] curator 404 语义
- **位置**: `curator.py:11-18`
- **方案**: `result["error"] == "session not found"` → 404；`session is not in raw status` → 409；其余 400（替换现有死分支 `if not result`）
- **测试**: evaluate 不存在会话 → 404

### B5. [L1] 审核状态机复用流转表
- **位置**: `reviewer_manager.py:51-53,65-67`
- **方案**: 引入 `from managers.session_manager import VALID_STATUS_TRANSITIONS`；approve 前置条件改为 `"approved" in VALID_STATUS_TRANSITIONS.get(current, [])`（即 curated/rejected 可 approve，复审恢复）；reject 同理（curated/approved 可 reject）
- **pending 列表**: 保持只查 `curated`（待审队列语义不变）；rejected 复审走 `POST /reviewer/approve/{id}`
- **测试**: rejected 会话 approve 成功；approved 会话 reject 成功（更新 test_reviewer_manager.py 相关用例）

### B6. [L2] 自动审批落地
- **位置**: `curator_manager.py:80-102`
- **方案**: evaluate 后：
  1. `update_session` 写 `quality_auto_score/tags/tools_used/status="curated"`（保持流转合法）
  2. `is_high_value`（score >= threshold）时：`database_manager.session_review_apply(session_id, "approved", score, "auto_approve", f"score {score} >= threshold {threshold}")`（curated→approved 合法，原子 + 审计）
  3. 返回值增加 `"auto_approved": bool`
- **注意**: 不能直接 update status=approved（raw→approved 非法流转）
- **测试**: 更新 test_evaluate.py / test_bulk_evaluate.py（高分会话 status=approved + 审计日志；低分 status=curated）；evaluate_all 的 high_value/low_value 统计不变

---

## C. 插件系统修复

### C1. [P1] 禁用插件真正注销 hooks
- **位置**: `hook_manager.py` + `plugin_manager.py:234-264`
- **方案**:
  1. `HookManager` 新增 `unregister(hook_name, callback)`（按 (priority, callback) 删除）
  2. 新增 `unregister_by_module(module_name)`：遍历 `_hooks`，移除 `callback.__module__ == module_name` 或以 `module_name + "."` 前缀的条目
  3. `set_enabled(key, False)`：写 yaml 后 → `unregister_by_module(module_name)` → 删除 `sys.modules` 中以 `plugins.{key}` 为前缀的模块 → `plugin_modules.pop(key)` → `loaded_plugins.pop(key)` → 重载 registry（disabled 条目保留在 `self.plugins`）
  4. `set_enabled(key, True)`：写 yaml → 重载 registry → `register_hooks()`（重新导入）
- **测试**: 新测试 — 注册插件 hook → disable → hook 不再被触发 → enable → 恢复

### C2. [P4] get_all 展开 manifest + 含 disabled
- **位置**: `plugin_manager.py:266-278` + `Plugins.tsx`
- **方案**: `get_all()` 遍历 `self.plugins`（含 disabled），每条输出 `{key, plugin_type, enabled, **manifest}`（name/version/description/author 顶层展开）；`plugin_type` 优先 `manifest.get("type")`，兜底 key 前缀
- **前端**: `Plugins.tsx` 无结构改动（getByType 后端过滤，Switch 已受控 `checked={record.enabled}`，disabled 插件重新可见可启用）
- **测试**: get_all 含 disabled + manifest 展开字段

### C3. [P5] plugins.yaml 注释保留 + 并发锁
- **位置**: `plugin_manager.py:249-256`
- **方案**:
  1. 弃用 `yaml.safe_dump` 全量重写 → 行级替换：正则定位 `^\s*{key}:` 块内的 `enabled: \w+` 行，替换为新值（零依赖、保留注释）；插件不存在时新增块
  2. 新增 `threading.Lock` 保护读-改-写
- **测试**: 带注释 plugins.yaml → set_enabled → 注释保留、enabled 更新；并发两次 set_enabled 不互相覆盖

### C4. [P6] manifest hooks 声明清理
- **位置**: `plugins/services/infisical/plugin.yaml:20-21`
- **方案**: 删除 `hooks:` 声明（实际注册靠 `@hook_manager.hook` 装饰器，声明字段从未被读取）；`plugins/README.md` 补充说明 hooks 通过装饰器注册
- **测试**: 无需（非代码）

### C5. [P7] get_plugin_secrets 容错
- **位置**: `plugin_manager.py:224-231`
- **方案**: `secret.get("name")` + 跳过空 name 项（畸形 secret 定义不导致启动崩溃）
- **测试**: 缺 name 的 secret 定义 → 跳过

### C6. [P8] openclaw agents_dir 可配置
- **位置**: `plugins/collectors/openclaw/backend.py:243-258`（on_load）
- **方案**: `agents_dir = os.getenv("OPENCLAW_AGENTS_DIR") or config.get("agents_dir")`；plugin.yaml 默认值保留 `/app/data/test_sessions/agents`（Docker 内可用），本地经 env 覆盖
- **测试**: env 覆盖生效（monkeypatch）

### C7. [P3] 清理空壳插件
- **位置**: `plugins/plugins.yaml` + `plugins/collectors/default/`、`plugins/curators/default/`、`plugins/reviewers/default/`（均无 hooks 注册，backend 未被调用）
- **方案**: `git rm -r` 三个 default 目录 + 从 plugins.yaml 移除对应条目（保留 collectors/openclaw、curators/openclaw、services/infisical + examples）；`plugins/README.md` 插件清单更新
- **测试**: 确认 plugin_manager 测试用临时目录，不受影响（检查 test_plugin_manager 引用）

### C8. [P9] init 类钩子短路告警
- **位置**: `hook_manager.py:138-141,151-153`
- **方案**: 不改短路语义（v2 设计 + 测试覆盖），在短路发生时 `logger.warning("[{before}] 钩子返回非 None，原方法被短路")`
- **测试**: 现有短路测试保持通过

---

## D. npm 插件契约对齐（改 client.ts / types / 文档）

### D1. `src/client.ts` 端点对齐（全部已与后端逐条核对）
| 方法 | 现状 | 改为 |
|---|---|---|
| scanFolder | POST /collector/scan (body) | `GET /collector/scan` + params `{folder_path}` |
| importSession | POST /collector/import (body) | `POST /collector/import` + params `{file_path}`（后端是 query） |
| importAll | POST /collector/import_all (body) | `POST /collector/import-all` + params `{folder_path}` |
| evaluateAll | POST /curator/evaluate_all | `POST /curator/evaluate-all` |
| getStats | GET /sessions/stats | `GET /stats` |
| approveSession | POST ... body {notes,score} | `POST /reviewer/approve/{id}` + params `{notes, score}` |
| rejectSession | 同上 | `POST /reviewer/reject/{id}` + params `{notes, score}` |
| batchApprove | POST /reviewer/batch/approve (body) | `POST /reviewer/batch-approve` + params `{session_ids: ids.join(',')}` |
| batchReject | POST /reviewer/batch/reject (body) | `POST /reviewer/batch-reject` + params 同上 |

### D2. `src/types/` 响应形状对齐（当前与实际后端不符）
- `SessionListResponse`/`PendingResponse`: `sessions` 键（非 `items`）、无 `pages`
- `ImportAllResponse`: `{total, imported, skipped, failed, session_ids, failed_files}`
- `EvaluateResponse`: `{session_id, score, is_high_value, tags, tools_used}`
- `EvaluateAllResponse`: `{total, high_value, low_value, results}`
- `StatsResponse`: 加 `reviewed_sessions`；`avg_auto_score`
- `ScanResponse`: `{folder_path, files_found, files}`
- `ReviewResponse`: `{success, session}`
- `BatchReviewResponse`: `{total, success, failed, results: [{session_id, success}]}`
- `Session`: `session_id` 为 key 的实际字段（id 字段删除/可选）

### D3. 文档
- `README.md`: 安装/构建（`npm run build` 产出 `dist/`）、配置（baseUrl/apiKey）、工作流示例
- 检查 `skills/` 中 SKILL.md 的工作流步骤是否引用错误端点，一并修正

---

## E. 前端适配

### E1. `frontend/src/services/client.ts`
- 可选 `VITE_API_KEY` → axios headers `Authorization: Bearer`（若配置）

### E2. `frontend/src/pages/Plugins.tsx`
- 核对 `Plugin` 类型（types/plugin.ts）含 `enabled`/`version`/`description`/`author`；后端 get_all 展开 manifest 后表格字段自动有值；disabled 插件可见可启用（无需改逻辑，验证即可）

### E3. 其余页面
- Export.tsx / Review.tsx / Sessions.tsx: 验证无回归（B3/B5 变更后）

---

## F. 测试与文档收尾

### F1. 后端测试
- 新增: auth、反序列化容错、PATCH 409、分页 clamp、自动审批（approved+审计）、禁用插件注销 hooks、get_all 展开、yaml 注释保留、agents_dir env 覆盖
- 更新: `test_init.py`（argparse None 默认）、`test_evaluate.py`/`test_bulk_evaluate.py`（status/auto_approved）、`test_reviewer_manager.py`（状态机）、`test_plugin_manager.py`（如受 get_all 结构影响）
- 全量: pytest 238+ 新用例全绿 + ruff clean

### F2. 前端测试
- `frontend` 相关 mock（Plugins 响应形状）核对；tsc 0 error / eslint / vitest / build

### F3. 文档
- `.env.example`: 加 `HARVESTFLOW_API_KEY`、删 `POLL_INTERVAL`、注释更新
- `README.md`: API 表加鉴权说明、自动审批说明、watch_folders 手动触发说明
- `plugins/README.md`: 插件清单（3 个）+ hooks 注册说明
- `docs/rules/api-spec.md`: 核对无契约变更（本次不动后端契约）

---

## Commit 划分（单分支多个 commit，参照 round2 模式）

1. `fix(backend): 数据容错与配置优先级` — A1-A7
2. `feat(api): Bearer 鉴权与 API 语义修正` — B1-B6
3. `fix(plugins): 生命周期与注册表修复` — C1-C6, C8
4. `chore(plugins): 清理空壳插件` — C7
5. `fix(plugin-npm): 契约对齐后端` — D1-D3
6. `feat(frontend): 鉴权头与插件页适配` — E
7. `test+docs: 测试与文档收尾` — F（可并入各 commit）

## 验证方式
- 后端: `pytest`（backend 目录）+ `ruff check`
- 前端: `tsc --noEmit` / `eslint` / `vitest run` / `build`
- npm 插件: `npm run build`（typescript 编译通过）
- 启动验证: `./scripts/start.sh local full`（scripts/start.sh 是唯一启动方式）
