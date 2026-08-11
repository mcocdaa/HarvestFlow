# Round 6：后端与插件代码优化 — 设计规格

- 日期：2026-08-11
- 状态：待用户审阅
- 上游：brainstorming 会话（2026-08-11，用户已批准四方向设计）
- 深度：中等重构 + 一处插件功能补全

## 1. 背景与目标

Round 5（2026-08-10，已合并 PR #14/#15）完成后端/插件/前端/文档四批次整理后，代码库仍存在以下可观察问题：

1. 会话状态字符串 `"raw"/"curated"/"approved"/"rejected"` 散落 7+ 处硬编码，未用 Enum（违反 docs/rules/code.md §2.2）
2. `database_manager.py` 483 行（超过 code.md §8.1 建议的 400 行线），含 3 处重复 limit clamp、3 处重复 JSON 反序列化
3. `plugin_manager._load_registry` 手写 yaml 读取，未复用已有 `_read_yaml`；`get_all` 中名称/类型提取重复
4. `reviewer_manager.approve_session`/`reject_session` 结构几乎相同；`curator_manager._extract_tags`/`_extract_tools` 同构重复
5. 各 manager 返回 `{"session_id": ..., "error": ...}` 的 dict 错误模式重复
6. `database_manager.session_delete` 职责混入（DB 层删物理文件）
7. 静默异常（`_deserialize_session_fields` 捕获 JSONDecodeError 后 pass 无日志）；`secrets_manager.refresh_secret` 忙等待（50×0.1s sleep）
8. 死代码/占位：`plugins/curators/openclaw/__init__.py` 为空（评分逻辑 `OpenClawCurator.evaluate` 完整存在但从未接入）；`plugins/collectors/default`、`curators/default`、`reviewers/default` 三个空占位目录
9. 魔法数字散落（limit clamp `100` 等）

**目标**：规范合规（对齐 code.md 审查清单）+ 重复收敛 + 健壮性提升 + 补全 openclaw curator 插件接入。除插件功能补全外，其余改动行为零变化。

## 2. 范围

### In-scope

- `backend/core/constants.py`（新增）：`SessionStatus`/`ExportFormat` 枚举与通用常量
- `backend/core/database_manager.py`：helper 收敛、魔法数字、`session_delete` 职责修正
- `backend/core/plugin_manager.py`：`_read_yaml` 复用、`get_all` helper
- `backend/core/secrets_manager.py`：忙等待改 Event
- `backend/managers/reviewer_manager.py`：approve/reject 合并
- `backend/managers/curator_manager.py`：tags/tools 提取收敛
- `backend/managers/session_manager.py`：状态枚举引用、文件删除职责承接
- `backend/managers/base.py`：`error_result()` helper
- `plugins/curators/openclaw/`：新增 hooks.py 接入评分逻辑、`__init__.py` 补全
- 删除 `plugins/collectors/default`、`plugins/curators/default`、`plugins/reviewers/default` 三个空占位目录
- 测试：新增 constants/Enum、database helper、openclaw curator 测试
- 文档同步：`plugin_development.md`、`architecture_guide.md`、`CLAUDE.md`、`hook_points.md`（如涉及）、`plugins.yaml` 注释

### Out-of-scope（明确不做）

- 前端零改动（含 `api/v1/plugins.py` 的 `{"plugins": [...]}` 响应形状——前端契约，保留）
- 不改 API 路由路径/方法/状态码；错误文案逐字保留（API 层 404/409 依赖）
- 不改 hook 名称与语义（before 短路、after 链式、同步环境警告）
- 不改 CLI 参数名与默认值、不改 `.env` 键名
- 不改数据库 schema 与 SQL 行为（`session_delete` 的 SQL 不变，仅文件删除职责迁移）
- 不改 `plugin.yaml`/`plugins.yaml` 结构与字段（注释可更新）
- 不改 collector 插件行为（openclaw collector 已接入，不动）
- 不做批量导入事务化（行为变化风险大，收益低）
- `main.py`、`api/v1/*`（除注释外）、`core/parsers.py`、`core/hook_manager.py`、`core/setting_manager.py`、`core/router_loader.py` 不改动
- docs/rules/* 规范文档本身不改

## 3. 逐项设计

### T1 状态枚举与常量（新增 `backend/core/constants.py`）

**动机**：状态字符串散落 7+ 处（database/session/curator/reviewer/exporter manager、api/v1/session.py），对齐 code.md §2.2。

**设计**（依据 enum 官方文档：Python 3.11+ `StrEnum` 定位为字符串常量的 drop-in replacement；本地 Python 3.12 支持）：

```python
from enum import StrEnum, unique

@unique
class SessionStatus(StrEnum):
    RAW = "raw"
    CURATED = "curated"
    APPROVED = "approved"
    REJECTED = "rejected"

@unique
class ExportFormat(StrEnum):
    SHAREGPT = "sharegpt"
    ALPACA = "alpaca"

# 通用业务常量（收敛重复魔法数字）
MAX_PAGE_SIZE = 100          # 分页/历史查询 limit 上限
DEFAULT_PAGE_SIZE = 20       # 默认分页大小
DEFAULT_HISTORY_LIMIT = 20   # 导出历史默认条数
```

**使用规则**：
- 枚举值 `StrEnum` 成员：`==` 比较、dict 键查找（hash 同源）与字符串天然兼容（`SessionStatus.RAW == "raw"` 为 True，`"approved" in [SessionStatus.APPROVED]` 为 True），**内部比较与查找无需任何转换**
- **所有 DB 绑定参数与 API 输出统一使用 `.value`**（官方警告：部分 stdlib 检查 `type(x) == str` 而非 `isinstance`；json 序列化、sqlite 绑定以 `.value` 为唯一规范，杜绝隐患）
- API 层（`api/v1/*`）不改动：入参/出参保持 str 透传，枚举仅在 backend 内部（core/managers）使用
- 模块专属常量（curator 评分阈值、exporter 角色名、secrets 刷新参数等）保留原位，不强行搬移
- 替换点：
  - `session_manager.VALID_STATUS_TRANSITIONS`：key/value 均用 `SessionStatus` 成员（外部 str 查询天然命中）；`updates["status"]`（str）与成员列表 `in` 判断天然成立；写入 DB 用 `.value`
  - `database_manager`：SQL 参数（INSERT/UPDATE/WHERE）用 `.value`；`stats_get` 状态名用 `.value`
  - `curator_manager`：`"raw"`/`"curated"`/`"approved"` 状态判断与写库用 `.value`
  - `reviewer_manager`：状态判断与 `session_review_apply` 参数用 `.value`
  - `exporter_manager`：`FORMAT_SHAREGPT`/`FORMAT_ALPACA` 常量改为引用 `ExportFormat`（`DEFAULT_FORMAT` 等模块常量保留，值同源）；`--export-default-format` argparse choices 用 `[f.value for f in ExportFormat]`
- 新增测试：枚举成员值、`.value` 与字符串相等、`VALID_STATUS_TRANSITIONS` 形状不变、`export()` 各格式分支仍走原逻辑

**行为保证**：API 入参/出参全部仍为字符串，`{"success": true, "session": {...}}` 形状逐字不变。

### T2 database_manager 收敛（单类，483 → ~420 行）

**动机**：超过 code.md §8.1 建议线；3 处重复 limit clamp、3 处重复 JSON 反序列化；魔法数字。

**设计**（依据 sqlite3 官方文档：`check_same_thread=False` 下写操作须由用户串行化——保留 `_write_lock` 现状，官方推荐做法）：

- 提取 `_clamp_limit(self, limit: Optional[int], default: int, max_value: int = MAX_PAGE_SIZE) -> int`：
  `session_get_all`（page_size）、`audit_log_get`（limit）、`export_record_get_history`（limit）三处改用
- 提取 `_deserialize_json_field(self, data: Dict, key: str) -> None`（就地反序列化，失败记 warning）：
  `_deserialize_session_fields` 内部 3 个字段循环调用
- 顺手修正 `session_get_for_export` 中的无效循环赋值：`session = self._deserialize_session_fields(session)`（局部变量重新赋值，列表元素靠 dict 就地修改才生效）→ `sessions = [self._deserialize_session_fields(s) for s in sessions]`，行为相同、意图明确
- 魔法数字 `100` → `MAX_PAGE_SIZE`（from core.constants）
- `session_delete` 职责修正：DB 层只删记录（保留 `session_get` 检查与 SQL），**文件删除逻辑移入 `session_manager.delete_session`**（业务层职责；`session_manager` 已能访问 `session["file_path"]`，用 `os.path.exists` + `os.remove` + `logger.warning`，错误文案保留）
- 连接建立处显式 `timeout=5.0`（与默认一致，显式化）
- 新增测试：`_clamp_limit` 边界（None/负值/超上限）、`_deserialize_json_field` 损坏 JSON 不抛异常且有日志、`session_delete` 删 DB 记录后 `session_get` 返回 None

**行为保证**：SQL 语句逐字不变（除参数引用方式）；`session_delete` 返回值与文件删除行为不变（只是执行位置迁移）；API 响应不变。

### T3 managers 重复收敛

#### T3.1 reviewer_manager approve/reject 合并

- 提取私有方法：

```python
def _review(self, session_id: str, target_status: SessionStatus, action: str,
            notes: str = None, score: int = None) -> Dict:
```

内部逻辑 = 原 approve/reject 公共部分（session 校验 → 状态流转校验 → `session_review_apply(session_id, target_status.value, manual_score, action, notes)`）
- `approve_session` → `_review(session_id, SessionStatus.APPROVED, "approve", notes, score)`
- `reject_session` → `_review(session_id, SessionStatus.REJECTED, "reject", notes, score)`
- 错误文案 `"session not found"`/`"invalid status transition"` 逐字保留
- 既有测试覆盖 approve/reject 行为，无需新增（或补 1 个 `_review` 直测）

#### T3.2 curator_manager tags/tools 收敛

- `_extract_tags` 与 `_extract_tools` 共享 `_unique_names(names) -> List[str]`（set 去重保序）helper；各自业务差异保留（tags 加 task_type/agent_role；tools 加 tools_used）
- `DEFAULT_AUTO_APPROVE_THRESHOLD` 等模块常量保留

#### T3.3 plugin_manager 收敛

- `_load_registry` 中 yaml 读取块改为复用 `_read_yaml(registry_path)`（`None` 时返回 `{}`，日志语义不变）
- `get_all` 提取 `_display_name(key, manifest)`、`_plugin_type(key, manifest)` helper（原内联三元逻辑原样搬入）

#### T3.4 错误 dict 模式统一（managers/base.py）

- `BaseManager` 新增：

```python
def error_result(self, session_id: str, error: str) -> Dict:
    """构造统一错误结果 {session_id, error}"""
    return {"session_id": session_id, "error": error}
```

- curator_manager（`"curator disabled"`/`"session not found"`/`"session is not in raw status"`/`"content not found"`）、reviewer_manager 使用；错误文案逐字不变
- 新增测试：`error_result` 返回结构

### T4 健壮性

#### T4.1 异常日志（database_manager）

- `_deserialize_json_field` 失败：`pass` → `logger.warning(f"字段 {key} JSON 反序列化失败: {e}")`（不含 exc_info，避免噪音；与 T2 同处实现）

#### T4.2 secrets_manager.refresh_secret 忙等待 → Event

- 现状：`refreshing` set + 50×0.1s sleep 轮询（约 5s 最坏等待）
- 设计：

```python
self._refresh_events: Dict[str, threading.Event] = {}
self._refresh_lock = threading.Lock()

def refresh_secret(self, name):
    with self._refresh_lock:
        event = self._refresh_events.get(name)
        if event is not None:
            # 已有刷新进行中：等待其完成（等价于原轮询总时长，事件触发即返回）
            event.wait(timeout=REFRESH_WAIT_MAX_ITERATIONS * REFRESH_WAIT_INTERVAL)
            return self._get_cache(name)
        event = threading.Event()
        self._refresh_events[name] = event
    try:
        ...原刷新逻辑（client.get_secret → _set_cache）...
        return 新值或缓存值
    finally:
        with self._refresh_lock:
            self._refresh_events.pop(name, None)
        event.set()
```

- 语义等价：并发刷新同一密钥时仅一个执行、其余等待结果；超时兜底返回缓存；异常路径确保 Event 释放
- `REFRESH_WAIT_MAX_ITERATIONS`/`REFRESH_WAIT_INTERVAL` 常量保留
- 新增测试：串行刷新、并发刷新（两个线程同时 refresh 同一 name，断言最终缓存一致、无死锁）

### T5 死代码与占位清理

- 删除 `plugins/collectors/default`、`plugins/curators/default`、`plugins/reviewers/default`（仅含 `__pycache__` 的空目录；确认无 git 跟踪文件后 `git rm -r` 或直接删除）
- 全量扫描未使用导入/方法（ruff + 手动复核），清理
- `plugin_development.md` 中"default 占位目录"说明同步删除
- `plugins.yaml` 注释更新（`curators/openclaw` 补全后移除"入口未实现"提示）

### T6 openclaw curator 补全（唯一行为变化，已批准）

**现状**：`plugins/curators/openclaw/backend.py` 的 `OpenClawCurator.evaluate()` 评分逻辑完整（239 行），`curator_plugin` 实例存在，但 `__init__.py` 为空、无 hooks.py → 插件加载无效果（plugins.yaml 注释亦注明）。

**设计**（与 `plugins/collectors/openclaw/hooks.py` 的 before 短路先例一致）：

新建 `plugins/curators/openclaw/hooks.py`：

```python
import logging

from core import database_manager
from core.constants import SessionStatus
from core.hook_manager import hook_manager
from managers.session_manager import session_manager
from plugins.curators.openclaw.backend import OpenClawCurator, get_curator

logger = logging.getLogger(__name__)

@hook_manager.hook("curator_manager_evaluate_before")
def openclaw_curator_evaluate_before(self, session_id):
    """OpenClaw 审核器短路钩子：接管自动审核评分"""
    # 1. 前置校验（错误文案与内置 CuratorManager.evaluate_session 逐字一致，
    #    API 层 curator.py 依赖这些文案返回 404/409）
    if not self.enabled:
        return {"session_id": session_id, "error": "curator disabled"}
    session = session_manager.get_session(session_id)
    if not session:
        return {"session_id": session_id, "error": "session not found"}
    if session.get("status") != SessionStatus.RAW.value:
        return {"session_id": session_id, "error": "session is not in raw status"}
    content = session.get("content")
    if not content:
        return {"session_id": session_id, "error": "content not found"}
    # 2. 评分（输入为 content 快照：collector parse 输出含 messages/has_tool_calls/
    #    message_count/tools_used/agent_id，与 OpenClawCurator.evaluate 输入匹配）
    try:
        result = get_curator().evaluate(content)
    except Exception as e:
        logger.error(f"[OpenClawCurator] 评分失败: {e}", exc_info=True)
        return None  # 不短路 → 自动回退内置评分
    # 3. 写库副作用（与内置 evaluate_session 相同的状态流）
    session_manager.update_session(session_id, {
        "quality_auto_score": result["score"],
        "tags": result["tags"],
        "tools_used": content.get("tools_used", []),
        "status": SessionStatus.CURATED.value,
    })
    auto_approved = False
    if result["is_high_value"]:
        database_manager.session_review_apply(
            session_id, SessionStatus.APPROVED.value, result["score"],
            "auto_approve",
            f"score {result['score']} >= threshold {OpenClawCurator.HIGH_VALUE_SCORE_THRESHOLD}")
        auto_approved = True
    # 4. 返回内置契约结构（附加 score_reasons 透传）
    return {
        "session_id": session_id,
        "score": result["score"],
        "is_high_value": result["is_high_value"],
        "tags": result["tags"],
        "tools_used": content.get("tools_used", []),
        "auto_approved": auto_approved,
        "score_reasons": result.get("score_reasons", []),
    }
```

- `__init__.py` 补全为：

```python
from plugins.curators.openclaw.hooks import *
from plugins.curators.openclaw.backend import on_load
from plugins.common import call_on_load

call_on_load(on_load, "[OpenClawCurator]")
```

（on_load 现状仅打日志，保留）
- `plugins.yaml` 注释更新为 `# OpenClaw 自动审核（通过 curator_manager_evaluate_before 短路钩子接入）`
- 新增测试 `backend/tests/plugins_tests/test_openclaw_curator.py`（参考 `test_entries.py` 的 sys.path 注入模式）：
  - 注册表加载后 openclaw curator 钩子已注册
  - 短路生效：raw 会话 evaluate 返回 openclaw 结构（含 score_reasons），状态 → curated、score/tags 写入 DB
  - high_value（score ≥ 3）→ 自动 approved + audit 记录
  - 错误路径：非 raw / 不存在 / 无 content → error dict 文案与内置逐字一致
  - 异常回退：`get_curator()` 抛异常 → 返回 None → 内置评分执行（会话被内置逻辑评分）
  - 禁用场景：curator 未启用 → `"curator disabled"`
- 行为影响（已批准）：openclaw 插件启用时自动审核走 OpenClaw 评分体系（high-value 阈值 3/5 vs 内置 4/5，评分依据不同）；`plugins.yaml` 置 `enabled: false` 即恢复内置逻辑

### T7 文档同步

- `docs/project/plugin_development.md`：移除"curators/openclaw 入口未实现"注意事项；移除 default 占位目录说明；补 openclaw curator 接入示例（可选简短节）
- `docs/project/architecture_guide.md`：core 层表格新增 `constants`（枚举与通用常量）；`plugin_manager` 说明不变
- `CLAUDE.md`：constants 模块一行说明 + openclaw curator 已接入
- `docs/project/hook_points.md`：核对该文档是否提及 curator 相关钩子与 openclaw 状态，按需同步（复用既有 `curator_manager_evaluate_before`，无新钩子点）
- `plugins/plugins.yaml`：注释更新（T5/T6 已含）

## 4. 测试与验证

- 后端全量：`pytest backend/`（基线 305 passed + 新增），`ruff check backend/ plugins/` 0 error
- 新增测试清单：
  - `backend/tests/core_tests/test_constants.py`（新）：枚举值/唯一性/`.value` 兼容
  - database：`_clamp_limit`、`_deserialize_json_field`、`session_delete` 迁移
  - managers：`error_result`、reviewer `_review`（既有测试回归即可）
  - `backend/tests/plugins_tests/test_openclaw_curator.py`（新）：T6 六类场景
- 前端不涉及，不跑（回归风险为零——后端响应形状不变）
- 手动冒烟：`python backend/main.py --help` 参数分组正常；`scripts/start.sh` 可启动（如需要）

## 5. 风险与边界

| 风险 | 缓解 |
|------|------|
| 状态枚举化漏改导致 `.value` 混入 API 响应（StrEnum 序列化为字符串其实兼容，但防 stdlib 陷阱） | 全部 DB/输出点统一 `.value`；测试断言响应仍为 str |
| `session_delete` 职责迁移引入行为偏差 | SQL 不变、删除文件逻辑原样搬运；API 层行为测试回归 |
| openclaw 补全改变自动审核行为（唯一有意变化） | 已批准；错误文案逐字对齐 API 依赖；异常自动回退内置；可经 plugins.yaml 关闭 |
| Event 改造并发死锁 | 锁内 get/del + timeout 兜底；并发测试覆盖 |
| `VALID_STATUS_TRANSITIONS` 枚举化后 shape 变化 | 测试断言形状不变（`{status.value: [s.value ...]}`） |

## 6. 网络调研依据（2026-08-11）

- Python 官方 `enum` 文档（docs.python.org/3/library/enum.html）：`StrEnum`（3.11+）为字符串常量 drop-in replacement；stdlib 存在 `type(x) == str` 检查点 → `.value` 防御
- Python 官方 `sqlite3` 文档（docs.python.org/3/library/sqlite3.html）：`check_same_thread=False` 时写操作须由用户串行化（`_write_lock` 保留为官方推荐做法）；占位符绑定防注入；事务控制 PEP 249 模式（`BEGIN IMMEDIATE` + commit/rollback）符合规范
