# Round 6 后端与插件代码优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-subagent-driven-development (recommended) or superpowers-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对齐 code.md 规范（状态 Enum、魔法数字、文件大小）、收敛重复代码、提升健壮性，并补全 openclaw curator 插件接入——除插件补全外行为零变化。

**Architecture:** 新增 `backend/core/constants.py`（StrEnum + 通用常量）为所有模块提供状态/格式枚举；database_manager 单类内提取 helper 收敛；managers 层合并重复方法并通过 `BaseManager.error_result` 统一错误模式；secrets_manager 忙等待改 threading.Event；`plugins/curators/openclaw/` 新增 hooks.py 通过 `curator_manager_evaluate_before` 短路钩子接入已有评分逻辑。

**Tech Stack:** Python 3.12、FastAPI、sqlite3、pytest、ruff（默认规则集，无配置文件）、pre-commit（已配置）

**上游 spec:** `docs/superpowers/specs/2026-08-11-round6-backend-plugins-optimization.md`

**调研依据（2026-08-11）：**
- Python 官方 enum 文档：`StrEnum`（3.11+）为字符串常量 drop-in replacement；stdlib 存在 `type(x) == str` 检查点 → DB/输出统一 `.value`
- 本地实测（Python 3.12）：`json.dumps(StrEnum)` → `"raw"`、sqlite 绑定存 text、dict 键查找与 `in` 列表天然兼容、`type(S.RAW) == str` 为 False（本项目 grep 无此类检查，无陷阱）
- Python 官方 sqlite3 文档：`check_same_thread=False` 下写操作须用户串行化（`_write_lock` 保留，官方推荐）
- Python 官方 threading 文档：`Event.wait(timeout)` 阻塞至 set 或超时；Event 一次性 → 每次刷新新建
- pytest 配置（backend/pytest.ini）：testpaths=tests、`-v --tb=short`；测试命令统一在 `backend/` 目录下运行

**验证基线：** 后端现有 `pytest` 305 passed；`ruff check backend/ plugins/` 0 error（无配置文件，默认规则）

**常用命令（所有 pytest 在 backend/ 目录执行）：**
```bash
cd backend && python -m pytest            # 全量
cd backend && python -m pytest tests/core_tests/test_constants.py -v   # 单文件
ruff check backend/ plugins/              # 在项目根执行
```

---

### Task 1: 新增 core/constants.py（SessionStatus/ExportFormat/通用常量）

**Files:**
- Create: `backend/core/constants.py`
- Test: `backend/tests/core_tests/test_constants.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/core_tests/test_constants.py`：

```python
# @file backend/tests/core_tests/test_constants.py
# @brief 全局枚举与通用常量测试
# @create 2026-08-11

import json

from core.constants import (
    SessionStatus,
    ExportFormat,
    MAX_PAGE_SIZE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_HISTORY_LIMIT,
)


class TestSessionStatus:
    def test_members_values(self):
        assert SessionStatus.RAW.value == "raw"
        assert SessionStatus.CURATED.value == "curated"
        assert SessionStatus.APPROVED.value == "approved"
        assert SessionStatus.REJECTED.value == "rejected"

    def test_str_equality_and_lookup(self):
        # StrEnum 成员与字符串天然兼容（==、in、dict 键）
        assert SessionStatus.RAW == "raw"
        assert "approved" in [SessionStatus.APPROVED]
        assert {SessionStatus.CURATED: 1}.get("curated") == 1

    def test_unique_values(self):
        values = [s.value for s in SessionStatus]
        assert len(values) == len(set(values))

    def test_json_serialization(self):
        assert json.dumps({"status": SessionStatus.RAW}) == '{"status": "raw"}'

    def test_all_members_str(self):
        for s in SessionStatus:
            assert isinstance(str(s), str)
            assert s.value == str(s)


class TestExportFormat:
    def test_members_values(self):
        assert ExportFormat.SHAREGPT.value == "sharegpt"
        assert ExportFormat.ALPACA.value == "alpaca"

    def test_unique_values(self):
        values = [f.value for f in ExportFormat]
        assert len(values) == len(set(values))


class TestCommonConstants:
    def test_values(self):
        assert MAX_PAGE_SIZE == 100
        assert DEFAULT_PAGE_SIZE == 20
        assert DEFAULT_HISTORY_LIMIT == 20
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && python -m pytest tests/core_tests/test_constants.py -v`
Expected: FAIL 全部（ModuleNotFoundError: No module named 'core.constants'）

- [ ] **Step 3: 实现**

创建 `backend/core/constants.py`：

```python
# @file backend/core/constants.py
# @brief 全局枚举与通用业务常量
# @create 2026-08-11

from enum import StrEnum, unique


@unique
class SessionStatus(StrEnum):
    """会话状态枚举（值即数据库存储字符串，Python 3.11+ StrEnum）"""

    RAW = "raw"
    CURATED = "curated"
    APPROVED = "approved"
    REJECTED = "rejected"


@unique
class ExportFormat(StrEnum):
    """导出格式枚举"""

    SHAREGPT = "sharegpt"
    ALPACA = "alpaca"


# ---- 通用业务常量（收敛重复魔法数字）----

# 分页/历史查询 limit 上限
MAX_PAGE_SIZE = 100
# 默认分页大小
DEFAULT_PAGE_SIZE = 20
# 导出历史默认条数
DEFAULT_HISTORY_LIMIT = 20
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && python -m pytest tests/core_tests/test_constants.py -v`
Expected: PASS 8 passed

- [ ] **Step 5: Commit**

```bash
git add backend/core/constants.py backend/tests/core_tests/test_constants.py
git commit -m "feat: 新增 core/constants.py 状态/格式枚举与通用常量（含测试）"
```

---

### Task 2: exporter_manager 接入 ExportFormat

**Files:**
- Modify: `backend/managers/exporter_manager.py`
- Test: `backend/tests/managers_tests/test_exporter_manager.py`（回归）

- [ ] **Step 1: 运行现有测试确认基线绿**

Run: `cd backend && python -m pytest tests/managers_tests/test_exporter_manager.py -v`
Expected: PASS（基线）

- [ ] **Step 2: 实现**

修改 `backend/managers/exporter_manager.py`：

1. 导入处（第 13 行后）加：

```python
from core.constants import ExportFormat
```

2. 常量区（第 17-25 行）替换为：

```python
DEFAULT_FORMAT = "sharegpt"
FORMAT_SHAREGPT = ExportFormat.SHAREGPT.value
FORMAT_ALPACA = ExportFormat.ALPACA.value
DEFAULT_VERSION = "v1"
DEFAULT_HISTORY_LIMIT = 20
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_GPT = "gpt"
ROLE_SYSTEM = "system"
```

（`FORMAT_SHAREGPT`/`FORMAT_ALPACA` 保持模块常量名与值，调用点零改动，值同源于枚举）

3. `register_arguments` 的 choices（第 54 行）改为：

```python
            choices=[f.value for f in ExportFormat],
```

- [ ] **Step 3: 运行回归确认通过**

Run: `cd backend && python -m pytest tests/managers_tests/test_exporter_manager.py -v`
Expected: PASS（行为不变，全部通过）

- [ ] **Step 4: Commit**

```bash
git add backend/managers/exporter_manager.py
git commit -m "refactor: exporter_manager 格式常量接入 ExportFormat 枚举"
```

---

### Task 3: session_manager 状态枚举化 + 文件删除职责承接

**Files:**
- Modify: `backend/managers/session_manager.py`
- Modify: `backend/core/database_manager.py`（session_delete 简化）
- Test: `backend/tests/managers_tests/test_session_manager.py`（回归 + 新增）

- [ ] **Step 1: 写新增测试**

在 `backend/tests/managers_tests/test_session_manager.py` 末尾追加：

```python
class TestValidStatusTransitionsShape:
    """状态流转表枚举化后形状保持（spec T1 契约测试）"""

    def test_shape_preserved(self):
        from core.constants import SessionStatus
        from managers.session_manager import VALID_STATUS_TRANSITIONS

        assert {
            s.value: [x.value for x in v]
            for s, v in VALID_STATUS_TRANSITIONS.items()
        } == {
            "raw": ["curated"],
            "curated": ["approved", "rejected"],
            "approved": ["rejected"],
            "rejected": ["approved"],
        }


class TestDeleteSessionFileCleanup:
    """delete_session 承接物理文件删除（DB 层不再删文件）"""

    def test_delete_removes_db_record_and_file(self, args_with_db_path, tmp_path):
        import os

        from core import database_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_file = tmp_path / "session.json"
        session_file.write_text("{}", encoding="utf-8")

        created = session_manager.create_session({
            "session_id": "sess-del-1",
            "file_path": str(session_file),
        })
        assert created is not None

        assert session_manager.delete_session("sess-del-1") is True
        assert database_manager.session_get("sess-del-1") is None
        assert not session_file.exists()

    def test_delete_missing_file_returns_true(self, args_with_db_path):
        from core import database_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_manager.create_session({
            "session_id": "sess-del-2",
            "file_path": "/nonexistent/path/session.json",
        })

        assert session_manager.delete_session("sess-del-2") is True

    def test_delete_unknown_session_returns_false(self, args_with_db_path):
        from core import database_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        assert session_manager.delete_session("no-such-id") is False
```

- [ ] **Step 2: 运行确认新测试失败**

Run: `cd backend && python -m pytest tests/managers_tests/test_session_manager.py -k "TestDeleteSessionFileCleanup" -v`
Expected: 既有实现（database_manager.session_delete 已含文件删除）下该 3 用例**全部 PASS**——这是行为保持性回归验证（红绿目标在 Task 4 实现后由全量回归确认），如实记录结果即可。

- [ ] **Step 3: 实现 session_manager**

修改 `backend/managers/session_manager.py`：

1. 导入（第 5-10 行区域）：

```python
import logging
import os
from typing import Optional, Dict, List
import argparse

from core import database_manager, hook_manager
from core.constants import SessionStatus
from managers.base import BaseManager
```

2. 状态流转表（第 13-18 行）替换为：

```python
# 合法的状态流转：{当前状态: [允许转入的状态]}
VALID_STATUS_TRANSITIONS: Dict[SessionStatus, List[SessionStatus]] = {
    SessionStatus.RAW:      [SessionStatus.CURATED],
    SessionStatus.CURATED:  [SessionStatus.APPROVED, SessionStatus.REJECTED],
    SessionStatus.APPROVED: [SessionStatus.REJECTED],
    SessionStatus.REJECTED: [SessionStatus.APPROVED],
}
```

3. `update_session` 中（第 130 行区域）：

```python
            current_status = session.get("status", SessionStatus.RAW.value)
            allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
```

（注释：`current_status` 为 str，dict 键为 StrEnum 成员——哈希/相等天然兼容，无需转换；`new_status not in allowed` 同理）

4. `delete_session`（第 144-154 行）替换为：

```python
    @hook_manager.wrap_hooks("session_manager_delete_before", "session_manager_delete_after")
    def delete_session(self, session_id: str) -> bool:
        """删除会话（DB 记录 + 物理文件，业务层职责）

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        session = database_manager.session_get(session_id)
        if not session:
            return False

        if not database_manager.session_delete(session_id):
            return False

        file_path = session.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"删除会话文件失败 {file_path}: {e}", exc_info=True)

        return True
```

- [ ] **Step 4: 实现 database_manager.session_delete**

修改 `backend/core/database_manager.py`（第 269-288 行）替换为：

```python
    def session_delete(self, session_id: str) -> bool:
        """删除会话记录（物理文件删除由 session_manager.delete_session 负责）

        Args:
            session_id: 会话 ID

        Returns:
            记录是否被删除（不存在返回 False）
        """
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        with self._write_lock:
            cursor = self.connection.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            self.connection.commit()

        return cursor.rowcount > 0
```

（注意：**不要删除 `import os`**——`register_arguments` 第 49 行 `default=os.getenv("DB_PATH", ...)` 仍在使用，删除会导致启动 NameError。`os.path.exists/os.remove` 移出后 `os` 仍在别处使用）

- [ ] **Step 5: 运行全部 session 测试确认通过**

Run: `cd backend && python -m pytest tests/managers_tests/test_session_manager.py -v`
Expected: PASS（既有 + 新增 3 个全绿）

- [ ] **Step 6: Commit**

```bash
git add backend/managers/session_manager.py backend/core/database_manager.py backend/tests/managers_tests/test_session_manager.py
git commit -m "refactor: 会话状态枚举化，文件删除职责移入 session_manager（含测试）"
```

---

### Task 4: database_manager 收敛（helper + 魔法数字 + 日志）

**Files:**
- Modify: `backend/core/database_manager.py`
- Test: `backend/tests/core_tests/database_manager/test_database_manager.py`（新增用例，文件路径以实际为准——见 Step 1）

- [ ] **Step 1: 确认测试目录并新建测试文件**

Run: `cd backend && ls tests/core_tests/database_manager/`
Expected: 现有 5 个文件（test_basic_init.py、test_other_features.py、test_session_queries.py、test_sessions.py、test_transactions_and_errors.py）——**不存在 test_database_manager.py**，需新建。

创建 `backend/tests/core_tests/database_manager/test_database_manager.py`（**文件头必须包含模块级单例导入**，其余测试文件用的是 `from core.database_manager import DatabaseManager`，本文件用单例以便直接调用私有 helper）：

```python
# @file backend/tests/core_tests/database_manager/test_database_manager.py
# @brief database_manager helper 单元测试（_clamp_limit / _deserialize_json_field）
# @create 2026-08-11

from core import database_manager


class TestClampLimit:
    def test_none_uses_default(self):
        dm = database_manager
        assert dm._clamp_limit(None, 20) == 20
        assert dm._clamp_limit(None, 100) == 100

    def test_bounds(self):
        dm = database_manager
        assert dm._clamp_limit(0, 20) == 1          # 下限
        assert dm._clamp_limit(-5, 20) == 1
        assert dm._clamp_limit(1000, 20) == 100     # 上限 MAX_PAGE_SIZE
        assert dm._clamp_limit(50, 20) == 50        # 正常

    def test_custom_max(self):
        dm = database_manager
        assert dm._clamp_limit(50, 10, max_value=30) == 30


class TestDeserializeJsonField:
    def test_valid_json(self):
        dm = database_manager
        data = {"tags": '["a", "b"]'}
        dm._deserialize_json_field(data, "tags")
        assert data["tags"] == ["a", "b"]

    def test_missing_field_keeps_dict(self):
        dm = database_manager
        data = {"other": 1}
        dm._deserialize_json_field(data, "tags")
        assert data == {"other": 1}

    def test_corrupt_json_keeps_raw_and_logs(self, caplog):
        dm = database_manager
        data = {"tags": "{not json"}
        with caplog.at_level("WARNING", logger="core.database_manager"):
            dm._deserialize_json_field(data, "tags")
        assert data["tags"] == "{not json"
        assert "JSON 反序列化失败" in caplog.text
```

（顶部 `from core import database_manager` 已在文件头声明；下方用例直接用 `database_manager` 单例）

- [ ] **Step 2: 运行确认新测试失败**

Run: `cd backend && python -m pytest tests/core_tests/database_manager/ -k "TestClampLimit or TestDeserializeJsonField" -v`
Expected: FAIL（`_clamp_limit` 不存在 / `_deserialize_json_field` 不存在）

- [ ] **Step 3: 实现**

修改 `backend/core/database_manager.py`：

1. 导入区（第 5-15 行区域）加：

```python
from core.constants import (
    MAX_PAGE_SIZE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_HISTORY_LIMIT,
)
```

（**保留 `import os`**——`register_arguments` 中 `os.getenv` 仍在使用）

2. `init` 中连接建立（第 64 行）改为：

```python
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=5.0)
```

3. `session_get_all`（第 194-196 行）替换：

```python
        # clamp page_size and page to prevent unbounded queries
        page_size = self._clamp_limit(page_size, DEFAULT_PAGE_SIZE)
        page = max(1, page)
```

4. `session_get_all` 的 `count_cursor` 行（第 207-210 行）——`total = dict(count_cursor.fetchone())["total"]` 保持不变；`sort_order` 与 `offset` 行保持不变。

5. `audit_log_get`（第 317 行）替换：

```python
        limit = self._clamp_limit(limit, 100)
```

（与 Step 3.6 同类：`limit=None` 由原 TypeError 改为回退默认值 100，属改进非回归）

6. `export_record_get_history`（第 379 行）替换：

```python
        limit = self._clamp_limit(limit, DEFAULT_HISTORY_LIMIT)
```

（原代码 limit 为 None 时 TypeError，现回退默认 20——改进非回归）

7. `session_get_for_export`（第 423-427 行，含 `cursor = self.connection.execute(query, tuple(params))` 行）替换：

```python
        cursor = self.connection.execute(query, tuple(params))
        sessions = [self._deserialize_session_fields(self._row_to_dict(row)) for row in cursor.fetchall()]
        return sessions
```

（消除无效循环赋值 `session = ...`）

8. `_row_to_dict` 之后追加两个 helper，并重构 `_deserialize_session_fields`（第 459-480 行区域）替换为：

```python
    def _clamp_limit(self, limit: Optional[int], default: int,
                     max_value: int = MAX_PAGE_SIZE) -> int:
        """将 limit 限制在 [1, max_value]，None 使用 default"""
        if limit is None:
            return default
        return max(1, min(limit, max_value))

    def _deserialize_json_field(self, data: Dict, key: str) -> None:
        """就地反序列化指定 JSON 字段，失败保留原值并记 warning"""
        raw = data.get(key)
        if not raw:
            return
        try:
            data[key] = json.loads(raw)
        except json.JSONDecodeError as e:
            self.logger.warning(f"字段 {key} JSON 反序列化失败: {e}")

    def _deserialize_session_fields(self, session: Dict) -> Dict:
        """反序列化会话的 JSON 字段"""
        for key in ("tags", "tools_used", "content"):
            self._deserialize_json_field(session, key)
        return session
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && python -m pytest tests/core_tests/database_manager/ tests/managers_tests/test_session_manager.py -v`
Expected: PASS（新增 + 全量回归）

- [ ] **Step 5: Commit**

```bash
git add backend/core/database_manager.py backend/tests/core_tests/database_manager/
git commit -m "refactor: database_manager 提取 clamp/反序列化 helper，收敛魔法数字与日志"
```

---

### Task 5: BaseManager.error_result + reviewer_manager approve/reject 合并

**Files:**
- Modify: `backend/managers/base.py`
- Modify: `backend/managers/reviewer_manager.py`
- Test: `backend/tests/managers_tests/test_base_manager.py`（新增）、`backend/tests/managers_tests/test_reviewer_manager.py`（回归）

- [ ] **Step 1: 写新增测试**

在 `backend/tests/managers_tests/test_base_manager.py` 末尾追加：

```python
class TestErrorResult:
    def test_structure(self):
        from managers.base import BaseManager

        bm = BaseManager()
        assert bm.error_result("s1", "session not found") == {
            "session_id": "s1",
            "error": "session not found",
        }
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && python -m pytest tests/managers_tests/test_base_manager.py -k TestErrorResult -v`
Expected: FAIL（AttributeError: 'BaseManager' object has no attribute 'error_result'）

- [ ] **Step 3: 实现 base.py**

修改 `backend/managers/base.py`（在 `init` 方法后追加）：

```python
    def error_result(self, session_id: str, error: str) -> Dict:
        """构造统一错误结果

        Args:
            session_id: 会话 ID
            error: 错误描述（文案由各调用方提供，保持与既有 API 契约一致）

        Returns:
            {"session_id": ..., "error": ...}
        """
        return {"session_id": session_id, "error": error}
```

（顶部 `from typing import Dict`——检查现有导入，缺则加）

- [ ] **Step 4: 实现 reviewer_manager**

修改 `backend/managers/reviewer_manager.py`：

1. 导入区（第 10-12 行区域）改为：

```python
from core import database_manager, hook_manager
from core.constants import SessionStatus
from managers.base import BaseManager
from managers.session_manager import session_manager, VALID_STATUS_TRANSITIONS
```

2. `approve_session`/`reject_session`（第 45-71 行）替换为：

```python
    def _review(self, session_id: str, target_status: SessionStatus, action: str,
                notes: str = None, score: int = None) -> Dict:
        """审批/拒绝公共逻辑

        Args:
            session_id: 会话 ID
            target_status: 目标状态（APPROVED / REJECTED）
            action: 审计动作名（"approve" / "reject"）
            notes: 备注
            score: 人工评分（缺省沿用现有 quality_manual_score）

        Returns:
            更新后的会话，失败返回 {"session_id", "error"}
        """
        session = session_manager.get_session(session_id)
        if not session:
            return self.error_result(session_id, "session not found")

        current_status = session.get("status", SessionStatus.RAW.value)
        if target_status.value not in VALID_STATUS_TRANSITIONS.get(current_status, []):
            return self.error_result(session_id, "invalid status transition")

        manual_score = score if score is not None else session.get("quality_manual_score", 0)
        return database_manager.session_review_apply(
            session_id, target_status.value, manual_score, action, notes
        )

    @hook_manager.wrap_hooks("reviewer_manager_approve_before", "reviewer_manager_approve_after")
    def approve_session(self, session_id: str, notes: str = None, score: int = None) -> Dict:
        """审批会话"""
        return self._review(session_id, SessionStatus.APPROVED, "approve", notes, score)

    @hook_manager.wrap_hooks("reviewer_manager_reject_before", "reviewer_manager_reject_after")
    def reject_session(self, session_id: str, notes: str = None, score: int = None) -> Dict:
        """拒绝会话"""
        return self._review(session_id, SessionStatus.REJECTED, "reject", notes, score)
```

3. `update_session` 的错误分支（第 78、83、85 行）改用 `error_result`：

```python
        if not session:
            return self.error_result(session_id, "session not found")
        ...
        except ValueError:
            return self.error_result(session_id, "invalid status transition")
        if updated is None:
            return self.error_result(session_id, "invalid status transition")
```

- [ ] **Step 5: 运行确认通过**

Run: `cd backend && python -m pytest tests/managers_tests/test_base_manager.py tests/managers_tests/test_reviewer_manager.py -v`
Expected: PASS（新增 + 回归全绿）

- [ ] **Step 6: Commit**

```bash
git add backend/managers/base.py backend/managers/reviewer_manager.py backend/tests/managers_tests/test_base_manager.py
git commit -m "refactor: BaseManager.error_result 统一错误模式，reviewer approve/reject 合并"
```

---

### Task 6: curator_manager 收敛 + 状态枚举化

**Files:**
- Modify: `backend/managers/curator_manager.py`
- Test: `backend/tests/managers_tests/curator_manager/`（回归；目录文件名以 ls 为准）

- [ ] **Step 1: 运行现有 curator 测试确认基线绿**

Run: `cd backend && python -m pytest tests/managers_tests/curator_manager/ -v`
Expected: PASS（基线）

- [ ] **Step 2: 实现**

修改 `backend/managers/curator_manager.py`：

1. 导入区（第 9-11 行区域）改为：

```python
from core import database_manager, setting_manager, hook_manager
from core.constants import SessionStatus
from managers.base import BaseManager
from managers.session_manager import session_manager
```

2. `evaluate_session` 中：
   - 第 72 行：`return {"session_id": session_id, "error": "curator disabled"}` → `return self.error_result(session_id, "curator disabled")`
   - 第 76 行：`return {"session_id": session_id, "error": "session not found"}` → `return self.error_result(session_id, "session not found")`
   - 第 78 行：`if session.get("status") != "raw":` → `if session.get("status") != SessionStatus.RAW.value:`
   - 第 79 行：`return {"session_id": session_id, "error": "session is not in raw status"}` → `return self.error_result(session_id, "session is not in raw status")`
   - 第 83 行：`return {"session_id": session_id, "error": "content not found"}` → `return self.error_result(session_id, "content not found")`
   - 第 96 行：`"status": "curated",` → `"status": SessionStatus.CURATED.value,`
   - 第 102 行：`session_id, "approved", score, "auto_approve",` → `session_id, SessionStatus.APPROVED.value, score, "auto_approve",`

3. `_extract_tags`/`_extract_tools`（第 147-170 行）替换为：

```python
    @staticmethod
    def _unique_names(names: List[str]) -> List[str]:
        """去重保序（替代 set() 的任意顺序）"""
        seen = set()
        result = []
        for name in names:
            if name not in seen:
                seen.add(name)
                result.append(name)
        return result

    def _extract_tags(self, content: Dict, tool_names: List[str] = None) -> List[str]:
        """提取标签"""
        tags = []

        if content.get("task_type"):
            tags.append(content.get("task_type"))

        if content.get("agent_role"):
            tags.append(content.get("agent_role"))

        tags.extend(tool_names if tool_names is not None else self._extract_tool_names_from_calls(content))

        return self._unique_names(tags)

    def _extract_tools(self, content: Dict, tool_names: List[str] = None) -> List[str]:
        """提取使用的工具"""
        tools = []

        if content.get("tools_used"):
            tools.extend(content.get("tools_used", []))

        tools.extend(tool_names if tool_names is not None else self._extract_tool_names_from_calls(content))

        return self._unique_names(tools)
```

4. `evaluate_all`（第 178 行）：`raw_sessions = database_manager.session_get_by_status("raw")` → `session_get_by_status(SessionStatus.RAW.value)`

（注意：`_unique_names` 保序与旧 `set()` 的任意顺序不同，但元素集合不变——顺序更稳定，属改进；如既有测试断言集合内容则不受影响）

- [ ] **Step 3: 运行确认通过**

Run: `cd backend && python -m pytest tests/managers_tests/curator_manager/ tests/managers_tests/test_session_manager.py -v`
Expected: PASS（全量回归）

- [ ] **Step 4: Commit**

```bash
git add backend/managers/curator_manager.py
git commit -m "refactor: curator 标签/工具提取去重收敛，状态枚举化"
```

---

### Task 7: plugin_manager 收敛

**Files:**
- Modify: `backend/core/plugin_manager.py`
- Test: `backend/tests/core_tests/plugin_manager/`（回归）

- [ ] **Step 1: 运行现有 plugin_manager 测试确认基线绿**

Run: `cd backend && python -m pytest tests/core_tests/plugin_manager/ -v`
Expected: PASS（基线）

- [ ] **Step 2: 实现**

修改 `backend/core/plugin_manager.py`：

1. `_load_registry`（第 234-239 行）替换为：

```python
        data = self._read_yaml(registry_path)
        if data is None:
            return {}
```

（`_read_yaml` 失败已记 error 日志并返回 None；空文件返回 {}——与原 `yaml.safe_load(f) or {}` 等价）

2. `get_all`（第 347-367 行）替换为：

```python
    def _display_name(self, key: str, manifest: Dict) -> str:
        """插件显示名：优先 manifest.name，缺省用 key 最后一段"""
        return manifest.get("name", key.split("/")[-1] if "/" in key else key)

    def _plugin_type(self, key: str, manifest: Dict) -> str:
        """插件类型：key 含 '/' 取首段，否则取 manifest.type"""
        if '/' in key:
            return key.split('/')[0]
        return manifest.get("type", "unknown")

    def get_all(self) -> List[Dict]:
        """获取所有已注册插件的信息（包括禁用插件），展开 manifest 字段"""
        result = []
        for key, info in self.plugins.items():
            manifest = info.get("manifest", {})
            result.append({
                "key": key,
                "plugin_type": self._plugin_type(key, manifest),
                "enabled": info.get("enabled", True),
                "name": self._display_name(key, manifest),
                "version": manifest.get("version", ""),
                "description": manifest.get("description", ""),
                "author": manifest.get("author", ""),
                "type": manifest.get("type", "unknown"),
            })
        return result
```

- [ ] **Step 3: 运行确认通过**

Run: `cd backend && python -m pytest tests/core_tests/plugin_manager/ -v`
Expected: PASS（回归全绿）

- [ ] **Step 4: Commit**

```bash
git add backend/core/plugin_manager.py
git commit -m "refactor: plugin_manager 复用 _read_yaml，get_all 提取名称/类型 helper"
```

---

### Task 8: secrets_manager 忙等待改 Event

**Files:**
- Modify: `backend/core/secrets_manager.py`
- Test: `backend/tests/core_tests/secrets_manager/`（新增用例，追加到既有测试文件）

- [ ] **Step 1: 写新增测试**

在 `backend/tests/core_tests/secrets_manager/` 的既有测试文件末尾追加（文件路径以 ls 为准）：

```python
class TestRefreshConcurrency:
    def test_serial_refresh(self):
        from core.secrets_manager import secrets_manager

        original_client = secrets_manager.client
        try:
            calls = []

            class FakeClient:
                def is_available(self):
                    return True

                def get_secret(self, name):
                    calls.append(name)
                    return "new-value"

            secrets_manager.client = FakeClient()
            secrets_manager._set_cache("KEY", "old-value")

            result = secrets_manager.refresh_secret("KEY")
            assert result == "new-value"
            assert calls == ["KEY"]
        finally:
            secrets_manager.client = original_client

    def test_concurrent_refresh_single_fetch(self):
        import threading
        import time

        from core.secrets_manager import secrets_manager

        original_client = secrets_manager.client
        try:
            calls = []

            class SlowClient:
                def is_available(self):
                    return True

                def get_secret(self, name):
                    calls.append(name)
                    time.sleep(0.2)
                    return "slow-value"

            secrets_manager.client = SlowClient()
            secrets_manager._set_cache("KEY2", "old-value")

            results = []

            def worker():
                results.append(secrets_manager.refresh_secret("KEY2"))

            threads = [threading.Thread(target=worker) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(calls) == 1        # 并发去重：仅一次真实刷新
            assert results == ["slow-value", "slow-value", "slow-value"]
        finally:
            secrets_manager.client = original_client

    def test_waiting_thread_gets_refreshed_cache(self):
        import threading
        import time

        from core.secrets_manager import secrets_manager

        original_client = secrets_manager.client
        try:
            calls = []

            class GateClient:
                def is_available(self):
                    return True

                def get_secret(self, name):
                    calls.append(name)
                    time.sleep(0.1)
                    return "gated-value"

            secrets_manager.client = GateClient()
            secrets_manager._set_cache("KEY3", "old-value")

            results = []
            threads = [threading.Thread(target=lambda: results.append(secrets_manager.refresh_secret("KEY3"))) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 两个线程都拿到刷新后的值（等待者等待完成后读缓存）
            assert set(results) == {"gated-value"}
            assert len(calls) == 1
        finally:
            secrets_manager.client = original_client
```

- [ ] **Step 2: 运行确认新测试通过（回归验证）**

Run: `cd backend && python -m pytest tests/core_tests/secrets_manager/ -k "TestRefreshConcurrency" -v`
Expected: 既有忙等待实现已具备并发去重（`self.refreshing` set + 轮询），3 个用例**全部 PASS**——这是行为保持性回归（Event 改造不可观测差异，最终一致性由实现后复跑确认）。

- [ ] **Step 3: 实现**

修改 `backend/core/secrets_manager.py`：

1. 导入区（第 5-12 行区域）加：

```python
import threading
```

2. `__init__`（第 100-103 行区域）：删除 `self.refreshing = set()`（新实现不再使用，死代码清理），追加：

```python
        self._refresh_events: Dict[str, threading.Event] = {}
        self._refresh_lock = threading.Lock()
```

（`Dict` 需 `from typing import Dict`——检查第 12 行导入，缺则加）

3. `refresh_secret`（第 310-331 行）替换为：

```python
    def refresh_secret(self, name):
        """强制刷新指定密钥（并发去重：同一密钥仅一个线程执行刷新，其余等待结果）

        Args:
            name: 密钥名称

        Returns:
            刷新后的密钥值（或等待期间的超时兜底缓存值）
        """
        with self._refresh_lock:
            event = self._refresh_events.get(name)
            if event is not None:
                # 已有刷新进行中：等待其完成（Event 唤醒即返回；超时兜底返回缓存）
                event.wait(timeout=REFRESH_WAIT_MAX_ITERATIONS * REFRESH_WAIT_INTERVAL)
                return self._get_cache(name)

            event = threading.Event()
            self._refresh_events[name] = event

        try:
            if self.client and self.client.is_available():
                new_value = self.client.get_secret(name)
                if new_value is not None:
                    self._set_cache(name, new_value)
                    self.logger.info(f"密钥 {name} 已刷新")
                    return new_value

            return self._get_cache(name)
        finally:
            with self._refresh_lock:
                self._refresh_events.pop(name, None)
            event.set()
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && python -m pytest tests/core_tests/secrets_manager/ -v`
Expected: PASS（新增 3 + 回归全绿）

- [ ] **Step 5: Commit**

```bash
git add backend/core/secrets_manager.py backend/tests/core_tests/secrets_manager/
git commit -m "refactor: secrets 刷新忙等待改 Event 并发去重（含并发测试）"
```

---

### Task 9: 死代码与占位目录清理

**Files:**
- Delete: `plugins/collectors/default/`、`plugins/curators/default/`、`plugins/reviewers/default/`（三个空占位目录）
- Modify: 无（清理确认后视结果）

- [ ] **Step 1: 确认占位目录无跟踪内容**

Run: `git ls-files plugins/collectors/default plugins/curators/default plugins/reviewers/default`
Expected: 空输出（目录从未被 git 跟踪，仅含 `__pycache__`）

- [ ] **Step 2: 删除目录**

```bash
rm -rf plugins/collectors/default plugins/curators/default plugins/reviewers/default
```

- [ ] **Step 3: 全量静态检查**

Run: `cd /home/mcocdaa/AI_CODE/HarvestFlow && ruff check backend/ plugins/`
Expected: 0 error（如出现未使用导入等提示，一并清理后复跑）

- [ ] **Step 4: 回归**

Run: `cd backend && python -m pytest tests/plugins_tests/ -v`
Expected: PASS（插件冒烟测试不受影响）

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: 删除 default 占位插件目录（死代码清理）"
```

---

### Task 10: openclaw curator 补全（hooks.py + 入口 + 测试）

**Files:**
- Create: `plugins/curators/openclaw/hooks.py`
- Modify: `plugins/curators/openclaw/__init__.py`
- Modify: `plugins/plugins.yaml`
- Test: `backend/tests/plugins_tests/test_openclaw_curator.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/plugins_tests/test_openclaw_curator.py`：

```python
# @file backend/tests/plugins_tests/test_openclaw_curator.py
# @brief OpenClaw 审核器短路钩子测试
# @create 2026-08-11

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core import database_manager  # noqa: E402
from core.hook_manager import hook_manager  # noqa: E402
from managers.curator_manager import curator_manager  # noqa: E402
from managers.session_manager import session_manager  # noqa: E402


@pytest.fixture(autouse=True)
def clean_hooks():
    """每个用例后清理钩子，避免污染其他测试"""
    yield
    hook_manager.clear()


@pytest.fixture
def db(args_with_db_path):
    database_manager.init(args_with_db_path)
    yield database_manager
    database_manager.close()


@pytest.fixture
def curated_setup(db):
    """注册 openclaw curator 钩子并启用 curator"""
    import plugins.curators.openclaw  # noqa: F401

    curator_manager.enabled = True
    curator_manager.auto_approve_threshold = 4
    yield
    curator_manager.enabled = True
    curator_manager.auto_approve_threshold = 4


def make_raw_session(db, session_id="oc-1", **content_extra):
    """创建 raw 状态会话（content 为 OpenClaw collector 输出快照）"""
    content = {
        "session_id": session_id,
        "agent_id": "backend_dev",
        "messages": [
            {"role": "user", "content": "fix the bug"},
            {"role": "assistant", "content": "I will fix it", "tool_calls": [
                {"type": "tool_use", "name": "read_file"},
            ]},
            {"role": "assistant", "content": "```python\nprint(1)\n```", "tool_calls": [
                {"type": "tool_use", "name": "write_file"},
            ]},
            {"role": "assistant", "content": "fixed", "tool_calls": [
                {"type": "tool_use", "name": "run_tests"},
            ]},
        ],
        "tools_used": ["read_file", "write_file", "run_tests"],
        "has_tool_calls": True,
        "message_count": 20,
        **content_extra,
    }
    return session_manager.create_session({
        "session_id": session_id,
        "file_path": f"/tmp/{session_id}.jsonl",
        "content": content,
        "status": "raw",
    })


def make_low_value_session(db, session_id="oc-low"):
    """低价值会话：无工具调用/无代码块/消息少 → OpenClaw 评分 2 分（< 阈值 3，不 auto_approve）"""
    content = {
        "session_id": session_id,
        "agent_id": "backend_dev",
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ],
        "tools_used": [],
        "has_tool_calls": False,
        "message_count": 2,
    }
    return session_manager.create_session({
        "session_id": session_id,
        "file_path": f"/tmp/{session_id}.jsonl",
        "content": content,
        "status": "raw",
    })


class TestOpenClawCuratorHook:
    def test_import_registers_hook(self):
        import plugins.curators.openclaw  # noqa: F401

        assert "curator_manager_evaluate_before" in hook_manager._hooks

    def test_short_circuit_evaluates_and_writes_db(self, db, curated_setup):
        make_low_value_session(db, "oc-1")

        result = curator_manager.evaluate_session("oc-1")

        assert result["session_id"] == "oc-1"
        assert result["score"] == 2                       # openclaw 基础分
        assert "score_reasons" in result                  # openclaw 附加字段
        assert result["auto_approved"] is False
        session = db.session_get("oc-1")
        assert session["status"] == "curated"             # 低分不 auto_approve
        assert session["quality_auto_score"] == 2
        assert session["tags"]

    def test_high_value_auto_approves(self, db, curated_setup):
        make_raw_session(db, "oc-hi", message_count=25)

        result = curator_manager.evaluate_session("oc-hi")

        # 高分内容（工具调用+决策链+代码块+消息数）→ openclaw 评分 ≥ 3 → auto_approve
        assert result["score"] == 5
        assert result["auto_approved"] is True
        assert db.session_get("oc-hi")["status"] == "approved"

    def test_not_raw_returns_error(self, db, curated_setup):
        make_raw_session(db, "oc-2")
        db.session_update("oc-2", {"status": "curated"})

        result = curator_manager.evaluate_session("oc-2")
        assert result == {"session_id": "oc-2", "error": "session is not in raw status"}

    def test_missing_session_returns_error(self, db, curated_setup):
        result = curator_manager.evaluate_session("no-such")
        assert result == {"session_id": "no-such", "error": "session not found"}

    def test_disabled_returns_error(self, db):
        import plugins.curators.openclaw  # noqa: F401
        make_raw_session(db, "oc-3")
        curator_manager.enabled = False

        result = curator_manager.evaluate_session("oc-3")
        assert result == {"session_id": "oc-3", "error": "curator disabled"}

    def test_exception_falls_back_to_builtin(self, db, curated_setup, monkeypatch):
        make_raw_session(db, "oc-fb")
        curator_manager.auto_approve_threshold = 5        # 内置评分 4 分 < 5 → 不 auto_approve，状态停在 curated

        def boom(*a, **k):
            raise RuntimeError("boom")

        # 注意：hooks.py 是 `from ...backend import get_curator` 导入（绑定副本），
        # 必须 patch hooks 模块中的引用，patch backend 模块无效
        monkeypatch.setattr("plugins.curators.openclaw.hooks.get_curator", boom)

        result = curator_manager.evaluate_session("oc-fb")

        # 不短路 → 内置评分执行（返回结构无 score_reasons）
        assert "score_reasons" not in result
        assert "score" in result
        assert result["auto_approved"] is False
        assert db.session_get("oc-fb")["status"] == "curated"
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && python -m pytest tests/plugins_tests/test_openclaw_curator.py -v`
Expected: FAIL 4（test_import_registers_hook——hooks.py 不存在不注册钩子；test_short_circuit——内置评分 3 分 ≠ openclaw 2 分；test_high_value——内置不 auto_approve；test_exception_falls_back——hooks 模块不存在，monkeypatch 目标 AttributeError）。错误路径 3 用例（not_raw/missing/disabled）当前即 PASS（文案与内置一致）。

- [ ] **Step 3: 实现 hooks.py**

创建 `plugins/curators/openclaw/hooks.py`：

```python
# @file plugins/curators/openclaw/hooks.py
# @brief OpenClaw 审核器插件 hooks - 短路接管自动审核评分
# @create 2026-08-11

import logging

from core import database_manager
from core.constants import SessionStatus
from core.hook_manager import hook_manager
from managers.session_manager import session_manager
from plugins.curators.openclaw.backend import OpenClawCurator, get_curator

logger = logging.getLogger(__name__)


@hook_manager.hook("curator_manager_evaluate_before")
def openclaw_curator_evaluate_before(self, session_id):
    """OpenClaw 审核器短路钩子：接管自动审核评分

    前置校验与错误文案与内置 CuratorManager.evaluate_session 逐字一致
    （api/v1/curator.py 依赖这些文案返回 404/409）。
    评分异常时返回 None 不短路，自动回退内置评分。

    Args:
        self: CuratorManager 实例
        session_id: 会话 ID

    Returns:
        评分结果 dict（短路），或 None（回退内置）
    """
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

    try:
        result = get_curator().evaluate(content)
    except Exception as e:
        logger.error(f"[OpenClawCurator] 评分失败: {e}", exc_info=True)
        return None

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
            f"score {result['score']} >= threshold {OpenClawCurator.HIGH_VALUE_SCORE_THRESHOLD}"
        )
        auto_approved = True

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

- [ ] **Step 4: 实现 __init__.py**

`plugins/curators/openclaw/__init__.py`（当前为空文件）写入：

```python
# @file plugins/curators/openclaw/__init__.py
# @brief OpenClaw 审核器插件入口
# @create 2026-08-11

from plugins.curators.openclaw.hooks import *          # noqa: F401,F403
from plugins.curators.openclaw.backend import on_load  # noqa: F401
from plugins.common import call_on_load

call_on_load(on_load, "[OpenClawCurator]")
```

- [ ] **Step 5: 更新 plugins.yaml 注释**

`plugins/plugins.yaml` 中：

```yaml
  curators/openclaw:     # OpenClaw 自动审核（通过 curator_manager_evaluate_before 短路钩子接入）
    enabled: true
```

- [ ] **Step 6: 运行确认通过**

Run: `cd backend && python -m pytest tests/plugins_tests/ -v`
Expected: PASS（新增 7 + 既有冒烟全绿）

- [ ] **Step 7: 全量回归**

Run: `cd backend && python -m pytest`
Expected: PASS（全量：305 基线 + 新增）

- [ ] **Step 8: Commit**

```bash
git add plugins/curators/openclaw/hooks.py plugins/curators/openclaw/__init__.py plugins/plugins.yaml backend/tests/plugins_tests/test_openclaw_curator.py
git commit -m "feat: openclaw curator 短路钩子接入评分逻辑（含测试）"
```

---

### Task 11: 文档同步

**Files:**
- Modify: `docs/project/plugin_development.md`
- Modify: `docs/project/architecture_guide.md`
- Modify: `CLAUDE.md`
- Modify: `docs/project/hook_points.md`（核对该文档是否提及 openclaw curator 状态，按需同步）

- [ ] **Step 1: plugin_development.md**

1. 「注意事项」小节（第 191-197 行区域）改为：

```markdown
### 注意事项

- `plugins/curators/openclaw/` 通过 `curator_manager_evaluate_before` 短路钩子接入
  OpenClaw 评分逻辑（参考 `plugins/collectors/openclaw/hooks.py` 的短路先例）；
  插件异常时自动回退内置评分
- 插件开发以 `plugins/examples/` 为模板
```

2. 「完整示例」后（文末）追加短路钩子说明小节：

```markdown
## 短路钩子（接管内置逻辑）

before 钩子返回非 None 时短路——跳过被包装方法，返回值作为方法结果。
可用于接管内置实现（如 openclaw 采集器接管 jsonl 解析、openclaw 审核器接管评分）。
注意：短路返回结构必须与内置方法返回值契约一致（含错误分支文案）。
```

- [ ] **Step 2: architecture_guide.md**

1. §2 core 层表格（第 41-50 行区域）加一行：

```markdown
| `constants` | 全局枚举与通用常量 | `SessionStatus`/`ExportFormat`（StrEnum）、`MAX_PAGE_SIZE` 等 |
```

2. §5 插件开发入口（第 134-147 行区域）后追加：

```markdown
> `plugins/curators/openclaw/` 已接入：`curator_manager_evaluate_before` 短路钩子
> 接管自动审核评分（参考 `plugin_development.md`「短路钩子」小节）。
```

- [ ] **Step 3: CLAUDE.md**

「插件系统」的「可用钩子点」段（第 106-109 行区域）后追加：

```markdown
- `curators/openclaw` 已接入评分短路钩子（`curator_manager_evaluate_before`）
```

「关键约定」段（第 115-121 行区域）加：

```markdown
- **状态/格式枚举**：会话状态与导出格式使用 `core/constants.py` 的 `SessionStatus`/`ExportFormat`
  （StrEnum）；DB 绑定与输出统一 `.value`。
```

- [ ] **Step 4: hook_points.md 核对**

Run: `cd /home/mcocdaa/AI_CODE/HarvestFlow && grep -n "openclaw\|curator_manager_evaluate_before\|curator" docs/project/hook_points.md`
Expected: 查看结果；若提到"openclaw curator 未实现/无钩子"则更新为已接入；若仅列 hook 名则无需改动。

- [ ] **Step 5: 验证**

Run: `cd /home/mcocdaa/AI_CODE/HarvestFlow && git diff --stat docs/ CLAUDE.md && ruff check backend/ plugins/ && cd backend && python -m pytest -q`
Expected: 文档 diff 符合预期；ruff 0 error；pytest 全量 PASS（305 基线 + 新增 ≈29 = ≈334）

- [ ] **Step 6: Commit**

```bash
git add docs/project/plugin_development.md docs/project/architecture_guide.md docs/project/hook_points.md CLAUDE.md
git commit -m "docs: Round 6 文档同步（openclaw curator 接入、constants 枚举、短路钩子说明）"
```

---

### Task 12: 最终验证与收尾

- [ ] **Step 1: 全量验证**

```bash
cd /home/mcocdaa/AI_CODE/HarvestFlow
ruff check backend/ plugins/
cd backend && python -m pytest
```

Expected: ruff 0 error；pytest 全量 PASS（305 基线 + 新增 ≈29 = ≈334）

- [ ] **Step 2: 行为抽查（响应形状）**

Run: `cd backend && python -c "
import sys
from pathlib import Path
# 依赖 backend/ 为工作目录（python -c 时 sys.path[0]=='' 指向 cwd，与 conftest 一致）
from core.constants import SessionStatus, ExportFormat
from managers.session_manager import VALID_STATUS_TRANSITIONS
assert [s.value for s in SessionStatus] == ['raw', 'curated', 'approved', 'rejected']
assert [f.value for f in ExportFormat] == ['sharegpt', 'alpaca']
assert list(VALID_STATUS_TRANSITIONS.keys()) == [SessionStatus.RAW, SessionStatus.CURATED, SessionStatus.APPROVED, SessionStatus.REJECTED]
assert VALID_STATUS_TRANSITIONS[SessionStatus.RAW] == [SessionStatus.CURATED]
print('OK')
"`
Expected: OK

- [ ] **Step 3: 提交收尾 commit（如需）**

```bash
git status -s
```
Expected: 工作区干净（或仅剩未跟踪临时文件）

- [ ] **Step 4: 汇总报告**

向用户报告：任务完成清单、每任务 commit hash、最终测试/ruff 结果、行为变化说明（仅 openclaw curator 补全）、遗留项（如有）。
