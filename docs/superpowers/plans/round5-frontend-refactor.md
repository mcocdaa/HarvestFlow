# Round 5 批次 3：前端代码优化与整理 — 实施计划

- 日期：2026-08-10
- 上游 spec：docs/superpowers/specs/2026-08-10-round5-frontend-refactor.md（F1-F6）
- 执行方式：Task 1-6 顺序执行，每个 Task 独立提交

## 概述

统一 API 响应类型、收敛数据加载模式（useAsyncData）、提取快捷键判断工具、清理目录。
行为零变化，tsc/eslint/vitest/build 全绿。

**验收**：tsc 0 error、eslint 0 error、vitest 全绿（既有 66 + 新增）、build 成功。

## Task 1：✅ 已完成F1 types/api.ts

- **新增**：`frontend/src/types/api.ts`（ApiResponse<T>/ListResponse<T>/ErrorDetail，见 spec F1）
- **修改**：`frontend/src/types/index.ts` 增加 `export * from './api';`
- **验证**：`npx tsc --noEmit`；`npx eslint .`
- **提交**：`feat(frontend): F1 统一 API 响应类型（ApiResponse/ListResponse/ErrorDetail）`

## Task 2：✅ 已完成F3 isEditableTarget 工具

- **新增**：`frontend/src/utils/dom.ts`（isEditableTarget，见 spec F3）
- **修改**：`frontend/src/utils/index.ts` 导出；`frontend/src/hooks/useKeyboardShortcut.ts`
  内联判断替换为工具调用（行为逐字等价）
- **验证**：tsc、eslint、既有 api/App 测试
- **提交**：`refactor(frontend): F3 提取 isEditableTarget 工具，快捷键 hook 复用`

## Task 3：✅ 已完成F2 useAsyncData hook

- **新增**：`frontend/src/hooks/useAsyncData.ts`（含竞态保护，见 spec F2）
- **修改**：`frontend/src/hooks/index.ts` 导出
- **验证**：tsc、eslint
- **提交**：`feat(frontend): F2 useAsyncData 通用数据加载 hook（含竞态保护）`

## Task 4：✅ 已完成F5 新增测试

- **新增**：
  - `src/__tests__/dom.test.ts`：isEditableTarget 各分支（input/textarea/button/
    contentEditable/div/body/null）
  - `src/__tests__/useAsyncData.test.tsx`：renderHook 验证加载成功/失败/reload/竞态保护
    （检查现有测试是否已安装 @testing-library/react——已在 devDependencies；
    若 renderHook 未导出则用自写测试组件方式）
- **验证**：`npx vitest run src/__tests__/dom.test.ts src/__tests__/useAsyncData.test.tsx`
- **提交**：`test(frontend): F5 isEditableTarget/useAsyncData 测试`

## Task 5：✅ 已完成F6 页面收敛

- **修改**：
  - `src/pages/Dashboard.tsx`：stats 加载改用 useAsyncData（初始 loading 语义一致）
  - `src/pages/Plugins.tsx`：loadPlugins 改用 useAsyncData(fetcher, [activeTab])；
    `as Plugin[]` 收窄为 `(res.data.plugins as Plugin[] | undefined) ?? []`
  - `src/pages/Sessions.tsx`：仅类型收窄 `(res.data as { sessions?: Session[] }).sessions ?? []`，
    逻辑不动
- **验证**：tsc、eslint、既有 Dashboard/App 测试、全量 vitest
- **提交**：`refactor(frontend): F6 Dashboard/Plugins 收敛 useAsyncData，Sessions 类型收窄`

## Task 6：✅ 已完成F4 目录清理 + 回归

- **删除**：`frontend/src/store/`（确认无引用、空目录）
- **验证**：`npx tsc --noEmit && npx eslint . && npx vitest run && npm run build`
- **提交**：`chore(frontend): F4 移除空 store 目录`

## 风险注意

- useAsyncData 初始 loading：Dashboard 语义为 true（首次自动加载），保持
- Sessions 分页场景不改逻辑，仅类型收窄
- Review/Export 页面不进入重构范围

## 实施记录

- 全部 Task 已完成，commit：e91ceea（F1-F3）、bf27cb0（F5 测试 + reload 稳定性修复）、
  2946717（F6 页面收敛）、store 目录删除（空目录无提交）
- 实现要点/偏差：
  - ApiResponse 无泛型（后端无统一 data 字段，泛型 T 未使用会触发 TS6133）；页面内显式收窄
  - useAsyncData：fetcher 经 latest-ref 模式持有（react-hooks/refs 规则下用 useEffect 更新），
    reload 稳定避免内联 fetcher 引发的 effect 循环
  - Dashboard 错误处理改为 error state（不再 console.error），既有测试同步更新
  - F6 中 Sessions 仅类型收窄，分页联动逻辑未动
- 全量：78 passed（基线 66 + 12），tsc/eslint 0 error，build 成功
