# Round 2 Optimization Plan

**Branch**: `refactor/round2-optimization`
**Base**: `main` (1f093ff)
**Strategy**: 7 sequential commits across phases A-F

---

## Phase 1: Backend Correctness & Data Consistency
**Commit:** `fix(backend): data consistency and atomic review ops`

### P1.1 reviewer update_session silent failure
**File:** `backend/managers/reviewer_manager.py:83-92`
Check `session_manager.update_session()` return value (L89). If None (invalid transition),
return `{"session_id": ..., "error": "invalid status transition"}` — consistent with approve/reject.
API layer `reviewer.py:37-42` currently treats ANY non-empty result as success; must also check
for `"error"` key.

### P1.2 Atomic approve/reject (status + score + audit in one transaction)
**Files:** `backend/managers/reviewer_manager.py`, `backend/core/database_manager.py`
Current approve (L51/57/59) and reject (L70/76/78) split state update, score update, and
audit log into 3 independent DB writes. If score/audit fails after state committed, data
is inconsistent and retry is blocked (already in approved/rejected state).

Add `database_manager.session_review_apply(session_id, status, score, action, notes)`:
single transaction (BEGIN/COMMIT) containing UPDATE status+score AND INSERT audit_log.
Call from manager for both approve and reject paths.

Curator `evaluate_session` also splits score update (L86) from `_mark_as_curated` (L101) —
merge into single `update_session` call with both score+status fields. Verify no plugins
hook into `curator_manager_mark_as_curated` (confirmed: 0 plugin references).

### P1.3 create_session race condition
**Files:** `backend/managers/session_manager.py:64-70`, `backend/core/database_manager.py:147-162`
Check-then-insert pattern: two concurrent threads pass the existence check, second INSERT
triggers sqlite3.IntegrityError. Fix: change `session_create` to use `INSERT OR IGNORE`
(or `INSERT ... ON CONFLICT DO NOTHING`), then return `session_get(session_id)` as the
already-existing record. Keep manager's quick-path existence check as optimization.

### P1.4 Stats semantics fix
**File:** `backend/core/database_manager.py:395-422`
- `total_sessions` missing `curated` status → count all rows
- `curated_sessions` renamed to `reviewed_sessions` (approved+rejected, semantics clear)
- Consolidate 4 COUNT + 1 AVG into single `GROUP BY status` query
- **Frontend:** sync `Dashboard.tsx` field access from `curated_sessions` → `reviewed_sessions`

### P1.5 Export robustness
**Files:** `backend/core/database_manager.py:390-393`, `backend/managers/exporter_manager.py:106-109,127-143,154-221`
- `session_get_for_export` returns rows WITHOUT `_deserialize_session_fields` — content is
  raw JSON string. Add deserialization call.
- `_convert_to_sharegpt` (L158-160) and `_convert_to_alpaca` (L191-193) crash with
  AttributeError when content is None or has no "messages" key. Defensive `continue`.
- `export_record_create` (L137) is outside try/except — if DB write fails after file
  written, API returns 500 but file already exists. Move inside try; on failure log
  warning and still return success with file_path.
- Remove N+1 `get_session_content` loop (L106-109) — content already loaded via `session_get_for_export`.

### P1.6 Secrets logging leak
**File:** `backend/core/setting_manager.py:118-120`
`_log_config()` prints ALL config values including secrets (INFISICAL_CLIENT_SECRET, DB
passwords). Mask keys containing SECRET/KEY/PASSWORD/TOKEN/CREDENTIAL with `***`.

### P1.7 session_delete ordering & audit_log_get limit
**Files:** `backend/core/database_manager.py:270-278,310-314`
- session_delete: delete DB record FIRST, then remove file (file removal failure only
  logs warning — orphan file acceptable, inconsistent DB state is not).
- audit_log_get with session_id: add LIMIT clause (currently unbounded).

### P1.8 evaluate_all error filtering
**File:** `backend/managers/curator_manager.py:181-186`
Results with `"error"` key are counted as low_value — filter them out from statistics.

---

## Phase 2: API Standard HTTP Error Semantics + Frontend Interceptor
**Commit:** `refactor(api): standard 4xx errors with frontend interceptor`

### P2.1 Backend: HTTPException everywhere
**Files:** `backend/api/v1/reviewer.py`, `session.py`, `plugins.py`, `curator.py`, `collector.py`, `exporter.py`
- Not found (session/plugin not found) → `HTTPException(404, detail="...")`
- Invalid transition / bad params → `HTTPException(400, detail="...")`
- `DELETE /sessions/{id}` → return `Response(status_code=204)` on success
- `GET /stats` → move from `database_manager.stats_get()` to `session_manager.get_stats()`
  (fix direct DB access in API layer, violating `CLAUDE.md` layered architecture rule).
- `POST /exporter/export` → add **Pydantic body model** `ExportRequest` (fixes the
  contract bug where frontend sends body params but backend only had query params,
  silently dropping all filter values). Include `format`, `min_score`, `agent_role`,
  `task_type`, `tags`, `version` as Optional fields.

### P2.2 Frontend: unified response interceptor
**Files:** `frontend/src/services/client.ts`, `frontend/src/pages/Review.tsx`, `Plugins.tsx`, `Export.tsx`, `Sessions.tsx`, `Dashboard.tsx`
- Add axios response interceptor: on 4xx/5xx, read `error.response.data.detail` and
  show `message.error(detail)`.
- Remove now-redundant `success:false` checks and local error `message.error` calls from
  all page components (catch blocks become minimal/noop — interceptor handles display).
- ExporterApi no longer needs to check `res.data.success` — HTTP 200 = success, error
  codes handled by interceptor.

---

## Phase 3: Frontend Functional Bugs
**Commit:** `fix(frontend): functional bugs`

### P3.1 Plugins.tsx Switch (uncontrolled → controlled)
**File:** `frontend/src/pages/Plugins.tsx:67-72`
- `<Switch defaultChecked>` → `<Switch checked={record.enabled}>` (current state always ON regardless of actual enabled status)
- Remove `plugin.key!` non-null assertion (key is required in Plugin type)
- Use `pluginApi.getByType(activeTab)` for server-side filtering (replaces client-side filter)
- Improve UX: show enabled/disabled status on toggle

### P3.2 Export.tsx version field type mismatch
**File:** `frontend/src/pages/Export.tsx:101-103`
- `<InputNumber>` with `"v1"` → `<Input defaultValue="v1">` (version is a string)
- Default `initialValue` → `defaultValue` prop
- Add task_type and tags fields to the form (match new backend ExportRequest model)

### P3.3 Review keyboard shortcuts fire in input fields
**File:** `frontend/src/hooks/useKeyboardShortcut.ts:8-19`
- Ignore keydown events when target is input/textarea/contentEditable
- Prevents ⌘Backspace in notes TextArea from triggering reject (which also bypasses Popconfirm)

---

## Phase 4: Infrastructure (Deployment, Scripts, CI)
**Commit:** `fix(infra): routing, docker, scripts, CI`

### P4.1 Local dev API routing
**File:** `frontend/.env`
- `VITE_API_BASE_URL` → empty string (local mode goes through vite proxy `/api` → localhost:3000)
- Add comment explaining Docker deploys inject via ARG

### P4.2 Docker baseURL bake-in
**Files:** `frontend/Dockerfile`, `docker/docker-compose.*.yml`
- Dockerfile: default `VITE_API_BASE_URL` to empty (nginx proxies `/api` → backend:3000)
- nginx.conf already has correct proxy config (verified)
- Delete `docker-compose.full.yml` (not referenced by start.sh or anything else)

### P4.3 Docker compose for swarm
**File:** `docker/docker-compose.base.yml`
- Add `image:` names for prod swarm (stack deploy requires image, ignores build)
- Change relative volume paths to absolute for swarm compatibility
- Add comment noting swarm mode is experimental

### P4.4 start.sh / stop.sh fixes
**Files:** `scripts/start.sh`, `scripts/stop.sh`
- `stop_docker_services`: include all compose files (base+backend+frontend) for down,
  not just base.yml (fixes frontend container not being stopped)
- `local full`: add `trap` to cleanup backend PID on Ctrl+C
- `load_env`: replace `grep | xargs` with `set -a; . .env; set +a` (safer, handles spaces/special chars)
- `stop.sh`: `docker stack rm` add `|| true`; support local mode stop (kill PID from PID file)

### P4.5 fix_and_import_sessions.py
**File:** `scripts/fix_and_import_sessions.py`
- `SESSIONS_DIR` → `backend/data/raw_sessions` (current path doesn't exist)
- Move `import argparse` to top
- Remove unused imports (json, List, Dict, Optional)
- Add `--dry-run` flag

### P4.6 Git tracked build artifacts
**Files:** `.gitignore`, git index
- `git rm --cached frontend/tsconfig.tsbuildinfo frontend/tsconfig.node.tsbuildinfo frontend/vite.config.d.ts`
- `.gitignore` add `vite.config.d.ts`
- Delete stale `backend/backend/data/` directory (nested historical artifact)

### P4.7 CI cleanup
**File:** `.github/workflows/ci.yml`
- Remove duplicate `npx tsc --noEmit` (build already runs `tsc -b`)
- Unify node: 20-alpine in Dockerfile → 24-alpine (match CI); or CI → 22 (LTS) — pick one
- Unify python: Dockerfile 3.11-slim → 3.12-slim (match CI)

---

## Phase 5: Performance
**Commit:** `perf(backend): reduce DB round trips`

### P5.1 session_get_all list projection
**File:** `backend/core/database_manager.py:207-213`
- List query: SELECT explicit columns excluding `content` (verified: SessionTable list
  page only uses task_type, not content field)
- Detail fetch (`session_get`) keeps `SELECT *` with content
- `page_size` validation: clamp to max 100

### P5.2 Read operations without write lock
**File:** `backend/core/database_manager.py`
- Remove `with self._write_lock` from all read methods (session_get, session_get_all,
  session_get_by_status, session_get_for_export, audit_log_get, stats_get)
- SQLite WAL mode supports concurrent reads; writes still serialized by _write_lock
- Effect: read-heavy operations (lists, stats, get) no longer serialized behind writes

### P5.3 curator 8→3 round trips
**File:** `backend/managers/curator_manager.py`
- `evaluate_session`: use `session.get("content")` directly (already deserialized by
  session_get) — remove `get_session_content` call (saves 1 trip)
- `_mark_as_curated` merged into evaluate_session's single update_session call
  (already done in P1.2 — saves 2 trips: get+update)
- Total: 8 trips → 3 trips (get_session + update_session + evaluate return)

### P5.4 secrets_manager dual remote calls
**File:** `backend/core/secrets_manager.py:232-289`
- `_resolve_secret_value` returns tuple `(value, source)`
- `_load_all_secrets` reuses result — removes second `_get_value_source` call
  (both call `client.get_secret` for remote Infisical)

### P5.5 evaluate_session tool_names double traversal
**File:** `backend/managers/curator_manager.py:124-131`
- `_extract_tool_names_from_calls` called by both `_extract_tags` and `_extract_tools`
- Cache result in evaluate_session, pass to both extractors

### P5.6 API sync def (non-blocking)
**Files:** `backend/api/v1/*.py`
- All API endpoints: `async def` → `def` (FastAPI runs sync defs in thread pool)
- No endpoint actually awaits anything (all DB calls are synchronous)
- Prevents event loop blocking during long operations (export, evaluate_all)

---

## Phase 6: Frontend Cleanup + Tests
**Commit:** `chore(frontend): cleanup types, deps, and tests`

### P6.1 Remove unused dependencies
**File:** `frontend/package.json`
- `styled-components` (0 references in src/, confirmed)
- `@testing-library/user-event` (0 references in tests/, confirmed)
- Run `npm uninstall styled-components @testing-library/user-event`

### P6.2 Type safety
**Files:** `frontend/src/pages/Sessions.tsx`, `frontend/src/components/sessions/SessionTable.tsx`, `frontend/src/services/sessionApi.ts`, `frontend/src/types/session.ts`
- Sessions.tsx L27: `const params: any` → typed `SessionListParams`
- sessionApi.ts: use exported `SessionListParams` type (currently redefines inline)
- SessionTable: `getFirstMessageSummary`/`getSessionSummary` use `record` directly
  instead of `sessions.find()` (O(n²) → O(1), render already has the record)
- SessionTable: wrap `columns` in `useMemo`
- `api.get<T>` generic return type
- Remove `any` from `exporterApi.ts`, `SessionTable.tsx L141`

### P6.3 Extract shared MessageBubble component
**Files:** `frontend/src/pages/Review.tsx:27-46`, `frontend/src/components/sessions/SessionDrawer.tsx:28-47`
- Extract identical message rendering into `frontend/src/components/common/MessageBubble.tsx`
- Review.tsx and SessionDrawer.tsx both import and use it

### P6.4 Dead UI: AppHeader
**File:** `frontend/src/components/layout/AppHeader/index.tsx:21-28,30-35`
- Search Input has no onChange handler (dead)
- User menu Dropdown items have no onClick (dead)
- Option: remove both dead sections, keep only header title

### P6.5 Dead code removal
**Files:**
- `frontend/src/constants/index.ts` (barrel, not imported by anyone — delete)
- `frontend/src/types/menu.tsx` MenuItem.key field (SideMenu uses `path`, not `key` — remove)
- `frontend/src/components/sessions/SessionDrawer.tsx` `getFirstMessageSummary` unused
  parameter `_sessionId` — remove

### P6.6 Typescript/eslint tightening
**Files:** `frontend/tsconfig.json`, `frontend/eslint.config.js`
- tsconfig: add `forceConsistentCasingInFileNames`, `noImplicitOverride`, `verbatimModuleSyntax`
- eslint: restore `@typescript-eslint/no-explicit-any` as warn; add `@typescript-eslint/consistent-type-imports` as error; narrow ignores from `'*.config.*'` to `['vite.config.ts', 'eslint.config.js']`

### P6.7 Test coverage
**Files:** `frontend/src/__tests__/`
- Review page: approve/reject flow + keyboard shortcut guard
- Export page: form submission with correct body params (validates exporter contract fix)
- Plugins page: switch toggle calls enable/disable API
- SessionTable: summary rendering
- Dashboard: loading/error states (optional)

---

## Phase 7: Documentation
**Commit:** `docs: sync docs with code`

### P7.1 README API reference table
**File:** `README.md:112-132`
- `collector/import/all` → `import-all`
- `reviewer/batch` → `batch-approve` / `batch-reject`
- `PUT /reviewer/update/{id}` → `PATCH /reviewer/session/{id}`
- `POST /export` → `POST /exporter/export`
- Plugins enable/disable paths → `POST /plugins/enable?key=` / `POST /plugins/disable?key=`
- Add exporter query → body change note

### P7.2 README tech stack
**File:** `README.md:16`
- Remove "React + Redux + Ant Design" → "React + Ant Design" (no Redux)
- Startup instructions → reference `./scripts/start.sh` (per AGENTS.md rule)

### P7.3 README plugin section dedup
**Files:** `README.md:169-202`, `plugins/README.md`
- README plugin API section → brief overview + link to `plugins/README.md`
- plugins/README.md stays as canonical plugin docs

### P7.4 backend/README cleanup
**File:** `backend/README.md`
- Delete reference to `scripts/cleanup_backend.sh` (doesn't exist)
- Delete reference to `tests/api_tests/` (doesn't exist)
- Change flake8 → ruff
- Update test directory reference to `tests/core_tests/`, `tests/managers_tests/`

---

## Verification (after each commit)
- Backend: `pytest` (228 existing + new tests) + `ruff check`
- Frontend: `tsc -b`, `eslint`, `vitest run`, `npm run build`
- **Must not regress** existing test counts or lint results

## Final verification
- `scripts/start.sh local full` full-stack smoke test
- Plugin enable/disable + curator evaluate + reviewer approve/reject + export flow
- Docker build both images
