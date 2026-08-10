# Round 4 审查修复计划：前端代码

- 日期: 2026-08-10
- 基础分支: `main`（764f48b）
- 新分支: `refactor/round4-frontend-review`
- 范围: 全部 B+C+Q（用户决策）
- 用户决策:
  1. 全部修复 B1-B3 功能 bug + C1-C3 一致性 + Q1-Q7 质量项

---

## B. 功能 Bug（高优先级）

### B1. [Review 页评审后内容不刷新/越界] `frontend/src/pages/Review.tsx`
- **位置**: `handleApprove`/`handleReject`（71-97）、`loadPendingSessions`（43-56）、`useEffect [selectedIndex]`（37-41）
- **问题**: 评审成功后 `loadPendingSessions()` 重拉列表，但 `selectedIndex` 不重置；`loadPendingSessions` 内 `!sessionContent` 读旧闭包值，不触发 `loadSessionContent`；列表变短后 `sessions[selectedIndex]` 为 undefined → 空白/内容滞留
- **方案**:
  1. `loadPendingSessions` 改为无参、不依赖 `sessionContent` 闭包：拉取后若有数据且 `selectedIndex` 越界 → 重置 `selectedIndex=0` 并加载该条内容
  2. 抽取 `selectSession(index)` 统一处理 index 越界 clamp + 加载内容；approve/reject 后调用它定位下一条
- **测试**: 新增/更新组件测试：mock 列表 3 条 → approve 第 1 条 → 断言仍显示有效会话且内容重载

### B2. [快捷键与按钮焦点冲突] `frontend/src/hooks/useKeyboardShortcut.ts` + `Review.tsx`
- **位置**: `useKeyboardShortcut.ts:10-16`
- **问题**: 排除列表不含 `button`；焦点在"通过/确认拒绝"按钮时 Enter 同时触发按钮 click 与全局 handler（Popconfirm 确认场景会跳过确认直接拒绝）
- **方案**: `tagName === 'button'` 加入跳过条件；Review 页给快捷键增加 `document.activeElement` 为按钮时的防御
- **测试**: `useKeyboardShortcut.test.ts` 补 button 聚焦场景用例

### B3. [连续按键竞态] `frontend/src/pages/Review.tsx`
- **方案**: 增加 `submitting` state，`handleApprove/Reject` 进入时置 true、finally 置 false；按钮 `disabled={!currentSession || !score || submitting}`；快捷键 handler 内也检查 `submitting`
- **测试**: 双击 Enter 只发一次请求（mock reviewerApi 断言调用次数）

---

## C. 一致性 / 契约（中）

### C1. [Export version 默认值不生效] `frontend/src/pages/Export.tsx:98`
- antd Form.Item 内 `defaultValue` 对受控 Input 无效 → 改 `Form initialValues={{ version: 'v1' }}`，删除 Input 的 defaultValue
- **测试**: Export.test.tsx 断言提交 payload 含 `version: 'v1'`

### C2. [SessionDrawer 元数据误显示] `frontend/src/components/sessions/SessionDrawer.tsx:43-68`
- `Object.keys(content)` 会把 `session_id` 等顶层字段当技术详情展示
- **方案**: 白名单过滤：仅展示明确字段集（`agent_role`、`task_type`、`created_at`、`tools_used`、`tags`）+ `metadata` 对象展开，其余忽略
- **测试**: 补 SessionDrawer 渲染断言

### C3. [Plugins 页 reviewers tab 已空] `frontend/src/pages/Plugins.tsx:74-78`
- **方案**: 移除 reviewers tab（后端已无该类型插件）
- **测试**: 更新 Plugins.test.tsx 断言 tabs 数量

---

## Q. 工程质量（低）

### Q1. [eslint error] `frontend/eslint.config.js:8`
- `vite.config.d.ts`（tsc -b 构建产物）被扫描 → ignores 加 `'**/*.d.ts'`
- **验证**: `npm run lint` 0 error

### Q2. [14 warnings 清理]
- **exhaustive-deps ×5**: Export/Plugins/Review×2/Sessions 的 `loadX` 函数包 `useCallback` 并加入依赖数组
- **no-explicit-any ×9**: `types/session.ts` 的 `content: string | any` → `string | object | null`；`SessionContent` 索引签名 `[key: string]: unknown`；`__tests__/api.test.ts` 等 mock 处的 any → 精确类型
- **验证**: `npm run lint` 0 error 0 warning

### Q3. [错误拦截器动态 import + detail 数组] `frontend/src/services/client.ts:20-30`
- **方案**: 顶部静态 `import { message } from 'antd'`；`detail` 为数组时 `join('; ')` 再展示；无 detail 时按 status 给通用文案（401 → "认证失败"）
- **测试**: api.test.ts 补 interceptor 行为测试

### Q4. [destroyOnClose 弃用] `frontend/src/components/sessions/SessionDrawer.tsx:78`
- antd 5.29 已弃用 → 改 `destroyOnHidden`
- **验证**: console 无 antd 弃用警告

### Q5. [Bearer 头注入未测] `frontend/src/__tests__/api.test.ts`
- 补测试：`vi.stubEnv` 设置 `VITE_API_KEY` 后断言 Authorization 头；未设置时无头

### Q6. [Dashboard 无 loading] `frontend/src/pages/Dashboard.tsx:18-29`
- 加 `loading` state，`Statistic` 加 loading 属性
- **测试**: Dashboard.test.tsx 补 loading 断言

### Q7. [无 404 路由] `frontend/src/routes/index.tsx`
- 追加 `{ path: '*', element: <NotFound/> }`，新建轻量 `NotFound` 页（antd Result 404 + 返回首页按钮）
- **测试**: App.test.tsx 补未知路径渲染 404

---

## 提交计划（6 个 commit，遵循既有 style）

1. `fix(frontend): Review 评审后刷新定位下一条（B1+B3，含测试）`
2. `fix(frontend): 快捷键排除按钮焦点（B2，含测试）`
3. `fix(frontend): Export 默认值/SessionDrawer 元数据/Plugins tab（C1-C3，含测试）`
4. `chore(frontend): eslint 清理（Q1-Q2，0 error 0 warning）`
5. `fix(frontend): 拦截器与 antd 弃用项（Q3-Q4，含测试）`
6. `test+feat(frontend): Bearer 头测试/Dashboard loading/404 页（Q5-Q7，含测试）`

## 验证
- `npm run lint`：0 error 0 warning
- `npx tsc --noEmit`：0 error
- `npx vitest run`：全部通过（现有 50 + 新增约 10-15）
- `npm run build` 成功
