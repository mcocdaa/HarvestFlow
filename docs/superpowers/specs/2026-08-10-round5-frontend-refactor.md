# Round 5 批次 3：前端代码优化与整理 — 设计规格

- 日期：2026-08-10
- 状态：待用户审阅
- 上游设计：docs/superpowers/specs/2026-08-10-round5-refactor-design.md（第 6 节）
- 深度：中等重构，行为零变化

## 1. 背景与目标

前端（frontend/src/）已具备 utils/hooks/components/services 分层，存在以下可优化点：

1. **API 返回无类型化**：5 个 service 文件直接返回 axios promise，页面内 `res.data.plugins || []`
   或 `as Plugin[]` 断言（Plugins.tsx:15），无统一响应类型
2. **数据加载模式重复**：Dashboard/Plugins/Sessions 各自手写 loading 状态 +
   `try/catch/finally` + 重载逻辑（3 份相似代码）
3. **快捷键判断内联**：`useKeyboardShortcut` 内联 input/textarea/button/可编辑判断
4. **types 无统一出口**：`types/index.ts` 有 `export *`，但缺 api 响应类型；
   `store/` 空目录无内容

**目标**：统一 API 响应类型、收敛数据加载模式、提取快捷键判断工具、清理目录结构。
行为零变化（不改 API 契约、不改任何页面交互）。

## 2. 范围

### In-scope

- F1 `types/api.ts`：`ApiResponse<T>`、`ListResponse<T>`、`ErrorDetail`
- F2 `hooks/useAsyncData.ts`：通用数据加载 hook（loading/data/error/reload）
- F3 `useKeyboardShortcut` 提取 `isEditableTarget` 判断为导出工具
- F4 `types/index.ts` 统一出口；删除空 `store/` 目录
- F5 补测试：useAsyncData、isEditableTarget、api 类型编译验证
- F6 页面收敛（使用 useAsyncData）：Dashboard、Plugins（Sessions 分页场景保留原模式，
  其逻辑含分页参数联动，提取收益低且有回归风险）

### Out-of-scope（明确不做）

- 不改后端 API 契约与响应字段
- 不改 antd 版本与组件用法
- 不引入状态管理库（zustand/redux 等）
- 不改 Review/Export 页面逻辑（除非纯类型替换）
- 不改 useKeyboardShortcut 的注册/卸载行为
- 不新增全局 API 错误处理层（拦截器已处理，保持）

## 3. 逐项设计

### F1 types/api.ts（新增）

```ts
/** API 统一响应包装（success 字段由后端 ok() 辅助返回） */
export interface ApiResponse<T = unknown> {
  success: boolean;
  [key: string]: unknown;
}

/** 列表响应：{ sessions: Session[]; total: number } 类结构 */
export interface ListResponse<T> {
  items?: T[];
  total?: number;
  [key: string]: unknown;
}
```

设计考量：
- 后端响应形状多样（`{success, session}`、`{sessions, total}`、`{plugins}`、`{logs}`、
  `{formats}`、`{exports}`），统一精确类型需 per-endpoint 定义，收益低。
  采用**宽松包装 + 页面内收窄**策略：
  - `ApiResponse<T>`：仅标注 success 字段 + 索引签名，`T` 用于常见单对象场景
  - 页面读取时用泛型收窄，**移除 `as Plugin[]` 硬断言**，改为
    `res.data.plugins as Plugin[] | undefined ?? []` 或经 helper 收窄
- `ErrorDetail`：`string | { msg: string }[]`（拦截器已处理展示，此类型供测试/文档引用）

### F2 hooks/useAsyncData.ts（新增）

```ts
export interface UseAsyncDataResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  reload: () => Promise<void>;
}

export const useAsyncData = <T>(
  fetcher: () => Promise<{ data: T }>,
  deps: React.DependencyList = []
): UseAsyncDataResult<T> => {
  // 实现：useState(data/loading/error) + useCallback(reload 带竞态保护)
  // + useEffect(deps 变化自动 reload)
  // 竞态保护：reload 内部请求序号比对，过期响应丢弃
};
```

设计要点：
- fetcher 返回 `{ data: T }`（axios 响应形状），hook 负责提取 `data`
- 竞态保护：序号 ref，请求返回时序号不匹配则忽略（防止快速切换 tab 时旧数据覆盖）
- reload 返回 Promise 供调用方 await（如 Plugins 的 handleToggle 后刷新）
- 错误处理：捕获后 setError，**不重复弹 message**（拦截器已处理），仅 console.error 可省略
- 行为对齐现状：Dashboard 初始 loading=true；Plugins/Sessions 初始 loading=false——
  统一为 `loading` 初始值由 fetcher 首次调用前为 true（Dashboard 语义），
  Plugins 的 Table 仅用 loading 控制 spinner，初始 true 不改变用户可见行为

### F3 useKeyboardShortcut 整理

`src/utils/dom.ts`（或 utils/string 同风格新文件）：

```ts
/** 判断事件目标是否为可编辑元素（输入框/文本域/按钮/可编辑容器） */
export const isEditableTarget = (target: EventTarget | null): boolean => {
  const el = target as HTMLElement | null;
  if (!el?.tagName) return false;
  const tagName = el.tagName.toLowerCase();
  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'button' ||
    el.isContentEditable ||
    el.contentEditable === 'true'
  );
};
```

`useKeyboardShortcut` 改用该工具（行为逐字等价，含 `!target?.tagName` 短路）。

### F4 类型出口与目录清理

- `types/index.ts` 增加 `export * from './api';`
- 删除 `frontend/src/store/`（空目录，无 git 跟踪内容则直接删）
- `types/menu.ts` 确认已导出（现 index.ts 已 `export * from './menu'`）✓

### F5 测试

- `src/__tests__/hooks.test.tsx`（或按现有测试组织）：
  - useAsyncData：加载成功（data/loading 流转）、失败（error 设置）、reload 触发重新请求、
    竞态保护（两次 reload 乱序返回取最新）
  - 用 @testing-library/react renderHook（检查现有测试是否已装 @testing-library/react）
- `src/__tests__/dom.test.ts`：
  - isEditableTarget：input/textarea/button/contentEditable → true；div/body/null → false
- `src/__tests__/api.test.ts` 补充：types/api 编译验证（`satisfies` 或简单对象赋值断言）

### F6 页面收敛

- **Dashboard**：替换自写 loading 逻辑为 useAsyncData（stats 加载；初始 loading=true 语义一致）
- **Plugins**：loadPlugins → useAsyncData(fetcher, [activeTab])；
  `(res.data.plugins || []) as Plugin[]` → `(res.data.plugins as Plugin[] | undefined) ?? []`
- **Sessions**：**不改**（分页参数联动 + 独立 content 加载，提取收益低、回归风险高，
  仅将 `res.data.sessions` 类型化：`(res.data as { sessions?: Session[] }).sessions ?? []`）
- **Review**：不改逻辑，仅若存在 `as any` 则收窄（检查确认无）

## 4. 不改动的契约清单

1. API 请求/响应字段与 HTTP 行为不变
2. 页面交互（表格/分页/抽屉/切换）不变
3. useKeyboardShortcut 对外签名与行为不变
4. antd/axios 版本与用法不变
5. 快捷键行为、错误提示（拦截器 message）不变

## 5. 风险与缓解

| 风险 | 缓解 |
|------|------|
| useAsyncData 竞态/初始 loading 语义偏差 | 序号竞态保护；Dashboard 初始 true 对齐；既有页面测试锁定 |
| Plugins 重构引入表格行为变化 | 收敛仅限数据加载部分；Table 属性不变 |
| 类型宽松化失去类型安全 | 页面内显式收窄替代硬断言；tsc 全量校验 |
| 删除 store 目录影响导入 | 确认无任何 import store 引用 |

## 6. 验收标准

1. `cd frontend && npx tsc --noEmit` 0 error
2. `npx eslint .` 0 error 0 warning
3. `npx vitest run` 全部通过（既有 66 + 新增）
4. `npm run build` 成功
5. 提交记录按 F1-F6 分 task 提交
