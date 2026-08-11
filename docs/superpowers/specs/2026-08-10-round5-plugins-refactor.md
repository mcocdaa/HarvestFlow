# Round 5 批次 2：插件代码优化与整理 — 设计规格

- 日期：2026-08-10
- 状态：待用户审阅
- 上游设计：docs/superpowers/specs/2026-08-10-round5-refactor-design.md（第 5 节）
- 深度：中等重构，行为零变化（例外见第 3 节 P1 说明）

## 1. 背景与目标

插件目录（plugins/）结构基本成型，但存在以下问题：

1. **入口样板重复且不一致**：`__init__.py` 的写法有 4 种变体——
   - openclaw collector：`from hooks import *` + try/except 调用 backend.on_load()（唯一完整样板）
   - infisical：`from hooks import *` + `from backend import ...`（无 on_load）
   - examples×4：仅 `from hooks import *`（on_load 定义于 hooks.py 但从不调用）
   - **openclaw curator：`__init__.py` 完全为空**（只有文件头注释）
2. **发现项（不改，仅记录）**：
   - `curators/openclaw` 的 `__init__.py` 为空 → backend.on_load() 从未被调用，
     该插件无任何钩子注册，backend.py 是"死代码"（全仓库无外部引用）
   - `collectors/default`、`curators/default`、`reviewers/default` 三个目录仅含
     `__pycache__`，是空占位目录（plugins.yaml 未注册，不影响运行）
3. **文档与结构不一致**：`docs/project/plugin_structure.md` 描述的目录树与实际不符
   （default 目录实际为空、examples 未收录、插件清单示例字段与实际 plugin.yaml 不同）

**目标**：统一插件入口样板（消除 4 种变体）、补齐注册表注释、文档对齐；
不改变任何插件钩子语义与加载行为。

## 2. 范围

### In-scope

- P1 `plugins/common.py`：on_load 安全调用辅助
- P2 入口样板统一（collectors/openclaw、services/infisical、examples×4 的 `__init__.py`）
- P3 plugins.yaml 注释补充
- P4 新增测试：`plugins/common.py` 单元测试 + 插件入口导入冒烟测试
- P5 文档对齐：`docs/project/plugin_structure.md` 修正（本批次只修正该文件，
  plugins 其余文档更新归批次 4）

### Out-of-scope（明确不做）

- 不改任何插件的 hooks 注册、hook 名称、钩子函数体
- 不修复 `curators/openclaw` 空 `__init__.py`（修复=启用死代码=行为变化，仅文档记录；
  是否激活该插件由用户另行决定）
- 不删除 default 空占位目录（删除可能影响未来插件约定；仅文档记录）
- 不改 plugin.yaml 字段结构与内容
- 不改 plugin_manager 加载逻辑（backend 批次 B4 已完成，不重复）
- 不新增/删除插件

## 3. 逐项设计

### P1 plugins/common.py（新增）

**动机**：on_load 安全调用样板（try/except + 错误日志）在 openclaw collector 中手写，
未来插件开发需要复用。

```python
# @file plugins/common.py
# @brief 插件公共辅助 - 统一的插件生命周期样板
# @create 2026-08-10

import logging


def call_on_load(on_load_func, log_prefix: str) -> None:
    """安全调用插件 on_load：失败记录错误但不中断插件导入

    Args:
        on_load_func: 插件的 on_load 可调用对象（不存在时跳过）
        log_prefix: 日志前缀，如 "[OpenClaw]"
    """
    if on_load_func is None:
        return
    try:
        on_load_func()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"{log_prefix} 调用 on_load 失败：{e}")
```

**行为对齐说明**：openclaw collector 现状为
`try: on_load() except Exception as e: logger.error(f"[OpenClaw] 调用 on_load 失败：{e}")`。
P1 的日志文案 `{log_prefix} 调用 on_load 失败：{e}` 与其逐字一致（log_prefix="[OpenClaw]"）。
这是本批次唯一的"行为"接触点，且仅日志名从 `plugins.collectors.openclaw` 变为 `plugins.common`
（可接受，同批次 1 契约清单第 7 条精神）。

### P2 入口样板统一（__init__.py）

统一模板（4 行模式）：

```python
# @file plugins/{path}/__init__.py
# @brief {插件名}插件入口
# @create 2026-08-10

from plugins.{path}.hooks import *          # 注册钩子（hooks.py 负责 @hook_manager.hook）
from plugins.{path}.backend import on_load  # 插件初始化入口（可选）
from plugins.common import call_on_load     # 安全调用样板
call_on_load(on_load, "[{Name}]")
```

各插件落点：

| 插件 | 现状 | 改为 |
|------|------|------|
| collectors/openclaw | 内联 try/except + 单独 import | 模板（行为等价，见 P1） |
| services/infisical | `from hooks import *` + `from backend import InfisicalSDKClient, get_client` | **保持 backend 具名导出**（get_client 被 hooks.py 使用；on_load 不存在则跳过 call_on_load）。模板改为：hooks 导入 + backend 具名导入 + `from plugins.common import call_on_load; call_on_load(None, "[Infisical]")`——不调用时跳过。实际写法：`call_on_load(getattr(backend, 'on_load', None), ...)` 或简化：仅当 backend 有 on_load 时调用。为避免引入 getattr 复杂度，infisical 采用：`try: from plugins.services.infisical.backend import InfisicalSDKClient, get_client, on_load except ImportError: ...` 不优雅。**决定**：infisical 保持现状不动（其样板已是规范形态：hooks 导入 + 具名导出；无 on_load 需要调用） |
| examples×4 | `from hooks import *` | 保持（on_load 定义于 hooks.py 由 hooks 导入，无 backend on_load 需要调用）。仅统一文件头注释格式（若不一致） |

**最终统一标准**（写入文档，批次 4 落文档）：
1. 有 hooks.py 的插件：`__init__.py` 必须 `from plugins.{path}.hooks import *`
2. 有 on_load 的插件：`from plugins.{path}.backend import on_load` + `call_on_load(on_load, "[{Name}]")`
3. 无 on_load 的插件：不调用 call_on_load

因此本批次实际改动：
- `collectors/openclaw/__init__.py`：改为模板（行为等价）
- `infisical/__init__.py`、`examples×4`：不改动（已是规范形态）
- `curators/openclaw/__init__.py`：**不改动**（发现项，out-of-scope）

### P3 plugins.yaml 注释补充

```yaml
# HarvestFlow 插件注册表
# 插件 key 为相对 plugins/ 的路径；enabled 控制是否加载
# 插件类型：collector（采集）/ curator（自动审核）/ reviewer（人工审核）/ service（服务）
plugins:
  collectors/openclaw:   # OpenClaw 会话采集（默认启用）
    enabled: true
  curators/openclaw:     # OpenClaw 自动审核（注：入口未实现，加载无效果）
    enabled: true
  services/infisical:    # Infisical 密钥服务
    enabled: true
```

### P4 测试

- `backend/tests/plugins_tests/test_common.py`（新建目录，或放 core_tests？插件辅助属 plugins/，
  建 `backend/tests/plugins_tests/`）：
  - call_on_load：on_load 被调用；on_load 抛异常时记录日志不抛出（caplog 断言文案）；
    on_load 为 None 时静默跳过
- 入口冒烟测试 `backend/tests/plugins_tests/test_entries.py`：
  - import plugins.collectors.openclaw / plugins.services.infisical / plugins.examples.* 成功
    （需 sys.path 含项目根；现有 plugin_manager 测试已有此惯例）
  - openclaw collector 加载后 hooks 已注册（hook_manager._hooks 含 collector_manager_scan_after）

### P5 文档对齐（docs/project/plugin_structure.md）

- 目录树更新：default 目录标注"占位（空）"、examples 收录、curators/openclaw 标注"入口待实现"
- 新增"插件入口约定"小节（上述统一标准）
- 说明 plugins/common.py 辅助

## 4. 不改动的契约清单

1. 插件钩子注册与语义（hook 名称、before/after 语义）不变
2. plugin.yaml / plugins.yaml 结构字段不变（仅 plugins.yaml 加注释）
3. plugin_manager 加载逻辑不变（B4 已重构，行为经测试验证）
4. 插件 backend/hooks 函数体不变
5. `curators/openclaw` 空入口保持现状（不激活死代码）

## 5. 风险与缓解

| 风险 | 缓解 |
|------|------|
| openclaw collector __init__ 改造引入加载回归 | 行为逐字等价（P1 对齐说明）；P4 冒烟测试锁定 |
| 测试导入插件引发全局单例副作用 | 现有 plugin_manager 测试已演示安全加载模式；测试内清理 hook_manager |
| 文档描述与实现不符 | P5 以实际代码为准修订 |

## 6. 验收标准

1. `cd backend && pytest -q` 全部通过（既有 + 新增）
2. `ruff check backend/ plugins/` 0 error（插件目录若有 py 文件一并检查）
3. 冒烟：`python -c "import plugins.collectors.openclaw, plugins.services.infisical, plugins.examples.collector_example"` 成功
4. 提交记录按 P1-P5 分 task 提交
