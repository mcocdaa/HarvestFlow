# Round 5 批次 2：插件代码优化与整理 — 实施计划

- 日期：2026-08-10
- 上游 spec：docs/superpowers/specs/2026-08-10-round5-plugins-refactor.md（P1-P5）
- 执行方式：Task 1-5 顺序执行，每个 Task 独立提交

## 概述

统一插件入口样板、补充注册表注释、修正插件结构文档、新增插件辅助测试。
行为零变化（openclaw collector 入口改造与现状逐字等价）。

**验收**：pytest 全绿（既有 + 新增）、ruff 0 error、插件可正常导入加载。

## Task 1：✅ 已完成P1 plugins/common.py

- **新增**：`plugins/common.py`（call_on_load，见 spec P1 代码）
- **验证**：`python -c "from plugins.common import call_on_load"`（从项目根）
- **提交**：`feat(plugins): P1 新增 common.call_on_load 插件生命周期辅助`

## Task 2：✅ 已完成P2 openclaw collector 入口统一

- **修改**：`plugins/collectors/openclaw/__init__.py` → 模板（hooks 导入 + backend on_load + call_on_load）
- **关键**：日志文案 `[OpenClaw] 调用 on_load 失败：{e}` 逐字保留
- **验证**：
  - `python -c "import plugins.collectors.openclaw"`（项目根）成功
  - 钩子已注册：python -c 检查 hook_manager._hooks 含 collector_manager_scan_after
- **提交**：`refactor(plugins): P2 openclaw 采集器入口统一为 call_on_load 样板`

## Task 3：✅ 已完成P3 plugins.yaml 注释

- **修改**：`plugins/plugins.yaml` 加注释（见 spec P3）
- **验证**：`python -c "import yaml; yaml.safe_load(open('plugins/plugins.yaml'))"` 解析正常
- **提交**：`docs(plugins): P3 plugins.yaml 注册表注释补充`

## Task 4：✅ 已完成P4 测试

- **新增**：`backend/tests/plugins_tests/__init__.py`、`test_common.py`、`test_entries.py`
  - test_common：call_on_load 被调用 / 异常记录不抛出（caplog 断言 "[OpenClaw] 调用 on_load 失败：" 文案）/ None 跳过
  - test_entries：import 各插件成功；openclaw collector 加载后 collector_manager_scan_after 钩子已注册；
    测试后清理 hook_manager（clear + unregister_by_module）
  - 注意 conftest：sys.path 需含项目根（backend 的 conftest 只加了 backend/ 自身；插件导入需项目根
    在 sys.path——pytest 的 rootdir 为 backend/ 时，需要 conftest 或 test 内 sys.path.insert 项目根；
    查看 backend/tests 现有测试是否有引用 plugins 的先例，没有则在 test_entries.py 顶部插入
    `PROJECT_ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(PROJECT_ROOT))`）
- **验证**：`cd backend && python -m pytest tests/plugins_tests/ -q`；全量 pytest
- **提交**：`test(plugins): P4 插件辅助与入口冒烟测试`

## Task 5：✅ 已完成P5 文档对齐

- **修改**：`docs/project/plugin_structure.md`
  - 目录树更新：default 标注"占位（空）"、examples 收录、curators/openclaw 标注"入口待实现"
  - 新增"插件入口约定"小节（统一标准：hooks 导入 / on_load 调用 / 无 on_load 不调用）
  - 补充 plugins/common.py 说明
- **提交**：`docs(plugins): P5 插件结构文档与实现对齐`

## 发现项（不处理，记录于文档）

- `curators/openclaw` 空 `__init__.py`：on_load 从未调用，插件无钩子注册（死代码）
- `collectors/default` 等 3 个空占位目录

## 实施记录

- 全部 Task 已完成，commit：3b8b7f8（P1-P3）、6da5ee3（P4）、1eca91c（P5）
- P4 执行中顺带修复 plugins/ 既有 ruff 问题（此前未纳入检查）：examples 未用导入/F541 空占位
  f-string、infisical __init__ re-export、插件入口 star import noqa（F403 为插件约定）
- 发现项记录：curators/openclaw 空入口（死代码）、default 占位目录
- 全量：305 passed（批次1 后 299 + 6）
