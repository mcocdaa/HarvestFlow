# Round 5 批次 1：后端代码优化与整理 — 实施计划

- 日期：2026-08-10
- 上游 spec：docs/superpowers/specs/2026-08-10-round5-backend-refactor.md（已批准）
- 执行方式：Task 0-8 顺序执行，每个 Task 独立提交，可独立回滚

## 概述

中等重构，行为零变化。收敛重复（Manager 生命周期接口、会话解析、import 记录构造、
插件模块名构造、hook 执行循环、API 响应包装），拆分长函数（plugin_manager._load_registry、
main.py lifespan），全部既有测试保持绿色，新抽象补测试。

**验收标准**：
- `cd backend && pytest` 全部通过（既有 + 新增）
- `ruff check backend/` 0 error
- API 响应形状抽查与改造前逐字一致
- 每个 Task 提交可独立回滚

## Task 0：基线验证 ✅ 已完成（249 passed / ruff 0 error）

- **目标**：记录当前测试基线，确认实施起点干净
- **命令**：`cd backend && pytest -q 2>&1 | tail -5`（记录通过数与耗时）；`ruff check .`
- **完成标准**：全部测试通过，基线数字记录于 Task 8 对比

## Task 1：B1 BaseManager 基类 ✅ 已完成（4c520f5）

- **新增**：`backend/managers/base.py`
- **修改**：`backend/managers/{session,collector,curator,reviewer,exporter}_manager.py`
  （类声明加 `(BaseManager)`）、`backend/managers/__init__.py`（导出 BaseManager + __all__）
- **实现要点**：
  ```python
  # backend/managers/base.py
  import argparse
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:  # 或直接 import argparse（简单起见直接 import）
      pass

  class BaseManager:
      """业务管理器基类。统一生命周期接口 register_arguments/init。
      子类覆写时按需使用 @hook_manager.wrap_hooks 包装，基类不强制。"""

      def register_arguments(self, parser: argparse.ArgumentParser):
          """注册 argparse 参数（默认空实现）"""

      def init(self, args: argparse.Namespace):
          """初始化管理器（默认空实现）"""
  ```
- **验证**：
  - 新增 `tests/managers_tests/test_base_manager.py`：
    - `issubclass(SessionManager, BaseManager)` 等 5 个断言
    - 匿名子类调用默认 `register_arguments(None)`/`init(None)` 不抛异常（传 None 需注意——默认实现体内无操作，安全；为稳妥用 `argparse.ArgumentParser()` 与 `argparse.Namespace()`）
  - `pytest tests/managers_tests/test_base_manager.py -q`
- **完成标准**：5 个 manager 继承基类；单例实例化方式未动；新测试通过；既有测试全绿

## Task 2：B2 会话解析职责拆分 ✅ 已完成（b81131f）

- **新增**：`backend/core/parsers.py`
- **修改**：`backend/managers/collector_manager.py`（`parse_session_file` 收缩为委托）
- **实现要点**：
  - `parse_jsonl_file(file_path) -> Optional[Dict]`：原 jsonl 分支体逐行搬移
    （含行级 JSONDecodeError 跳过、`if messages and session_id:` 前置、
    agents 路径段提取、返回键 `session_id/agent_id/messages/message_count/has_tool_calls/tools_used`）
  - `parse_json_file(file_path) -> Optional[Dict]`：原 json 分支体搬移
    （缺 session_id 生成 `session_{YYYYmmdd_HHMMSS}_{basename}` 并写回）
  - 模块级 `logger = logging.getLogger(__name__)`；两函数顶层 try/except：
    `logger.error(f"解析文件失败 {file_path}: {e}")` 返回 None
  - collector 的 `parse_session_file`：
    ```python
    @hook_manager.wrap_hooks("collector_manager_parse_before", "collector_manager_parse_after")
    def parse_session_file(self, file_path: str) -> Optional[Dict]:
        if file_path.endswith('.jsonl'):
            return parsers.parse_jsonl_file(file_path)
        return parsers.parse_json_file(file_path)
    ```
    import：`from core import parsers`（注意 collector 现有 import 列表合并）
  - collector 内不再保留 try/except 与内联解析体
- **验证**：
  - 新增 `tests/core_tests/parsers/test_jsonl.py`：
    - 正常多行 message 提取（role/content 拼接）
    - content 为字符串与 list（text 项拼接）两种形态
    - 坏 JSON 行跳过、空行跳过
    - 无 message 或无 id 返回 None
    - agent_id 从 `agents` 段提取；无 agents 段返回 None
    - 文件不存在返回 None（异常路径）
  - 新增 `tests/core_tests/parsers/test_json.py`：
    - 原样返回 dict
    - 缺 session_id 生成并写回（格式断言）
    - 非 JSON 文件返回 None
  - `pytest tests/core_tests/parsers/ tests/managers_tests/collector_manager/test_parsing.py -q`
- **完成标准**：既有 parsing 测试全绿（等价性证明）；新测试全绿；openclaw 插件短路未动

## Task 3：B3 import 记录构造提取 ✅ 已完成（921cb39）

- **修改**：`backend/managers/collector_manager.py`
- **实现要点**：
  ```python
  def _build_session_record(self, file_path: str, session_data: Dict) -> Dict:
      record = dict(session_data)
      record["file_path"] = file_path
      record["content"] = dict(session_data)
      return record

  def _create_session(self, record: Dict) -> Optional[str]:
      try:
          session_manager.create_session(record)
      except Exception as e:
          self.logger.error(f"创建会话记录失败：{e}")
          return None
      return record.get("session_id")
  ```
  - `import_session` 重写（parse → 空检查 → build → create，保持无 skipped 检查）
  - `import_all` 重写（parse → 空检查 failed → skipped 检查 → build → create 失败 failed），
    skipped/imported/failed 统计语义与现状逐行一致
- **验证**：
  - 新增 `tests/managers_tests/collector_manager/test_import_helpers.py`：
    - `_build_session_record`：content 为原始快照（不含 file_path 键）、file_path 附加、不修改入参 session_data
    - `_create_session`：成功返回 session_id；`session_manager.create_session` 抛异常返回 None 且记录日志
  - `pytest tests/managers_tests/collector_manager/ -q`（含既有 test_import.py）
- **完成标准**：既有 import 测试全绿；新测试全绿

## Task 4：B4 plugin_manager 瘦身 ✅ 已完成（c79cd27）

- **修改**：`backend/core/plugin_manager.py`
- **实现要点**：
  ```python
  def _module_name(self, key: str) -> str:
      return f"plugins.{key.replace(os.sep, '.').replace('/', '.')}"

  def _read_yaml(self, path: Path) -> Dict:
      try:
          with open(path, 'r', encoding='utf-8') as f:
              return yaml.safe_load(f) or {}
      except Exception as e:
          self.logger.error(f"读取 yaml 失败: {path} - {e}", exc_info=True)  # 文案沿用现状各处
          return {}

  def _read_manifest(self, path: Path) -> Dict:
      """目录取 plugin.yaml；.py 单文件构造 {name, type: 'unknown', backend_entry}"""
      if path.is_dir():
          return self._read_yaml(path / "plugin.yaml")
      return {"name": path.stem, "type": "unknown", "backend_entry": path.name}

  def _load_entry(self, key: str, cfg: Dict) -> Optional[Dict]:
      """处理单个注册表条目。返回 {enabled, path, name, type, manifest}；失败返回 None。"""
  ```
  - `register_hooks` 中 2 处与 `set_enabled` 中 1 处模块名构造替换为 `self._module_name(key)`
  - `_load_registry` 循环体改为 `entry = self._load_entry(key, cfg)`；禁用分支（保留注册表项）原样
  - 注意：禁用分支返回结构 `{enabled: False, path: "", name: key.split("/")[-1], type: "unknown", manifest: {}}`
    与启用分支不同，`_load_entry` 需保持这两个分支的差异化结构
  - 错误日志文案沿用现状（如 "插件路径不存在: {path}，跳过插件 {key}" 等）
- **验证**：
  - 新增 `tests/core_tests/plugin_manager/test_helpers.py`：
    - `_module_name`：`"collectors/openclaw"` → `"plugins.collectors.openclaw"`；含 os.sep 场景
    - `_read_yaml`：正常 dict、文件缺失返回 {}、坏 yaml 返回 {}
    - `_load_entry`：目录带 plugin.yaml（manifest 字段透传）、.py 单文件（构造 manifest）、
      enabled=False 禁用结构、路径不存在返回 None、清单缺失返回 None
  - `pytest tests/core_tests/plugin_manager/ -q`
- **完成标准**：既有 plugin_manager 测试全绿；新测试全绿；3 处模块名构造收敛

## Task 5：B5 hook_manager 执行循环去重 ✅ 已完成（8d9954e）

- **修改**：`backend/core/hook_manager.py`
- **实现要点**：
  ```python
  def _dispatch(self, hook_name: str, args: Tuple, kwargs: Dict,
                execute: Callable[[Callable], Any]) -> HookResult:
      results, errors = [], []
      for _, cb in self._hooks.get(hook_name, []):
          try:
              results.append(execute(cb))
          except Exception as e:
              errors.append((cb.__name__, e))
              logger.error(f"钩子执行失败 [{hook_name}]: {cb.__name__} - {e}", exc_info=True)
      return results, errors
  ```
  - `run`（async）：execute 中 `asyncio.iscoroutinefunction(cb)` → `await cb(*args, **kwargs)`，否则 `cb(*args, **kwargs)`
  - `run_sync`：execute 中异步钩子 `logger.warning(f"[{hook_name}]: {cb.__name__} - 异步钩子不能在同步环境中执行")` 返回 None，同步钩子直接调用
  - 注意：execute 闭包捕获 args/kwargs，`_dispatch` 仅传 `(hook_name, args, kwargs, execute)`
- **验证**：
  - 新增 `tests/core_tests/hook_manager/test_dispatch.py`：
    - `_dispatch` 直接调用：结果按注册顺序、execute 抛异常被收集为 errors
    - 间接验证：run/run_sync 走 `_dispatch` 后行为不变（同步钩子结果、异步钩子在 run 中被 await、run_sync 中跳过并 warning——可用 `caplog` 断言 warning 文案）
  - `pytest tests/core_tests/hook_manager/ -q`（既有 test_run_sync/test_error_handling/test_wrap_hooks 全绿为等价证明）
- **完成标准**：既有 hook 测试全绿；warning 文案逐字未变；新测试全绿

## Task 6：B6 API 统一辅助 ✅ 已完成（529d605）

- **新增**：`backend/api/v1/common.py`
- **修改**：`backend/api/v1/{session,reviewer,collector,curator,plugins}.py`（exporter.py 不动）
- **实现要点**：
  ```python
  # backend/api/v1/common.py
  from fastapi import HTTPException

  def ok(**data) -> dict:
      """成功响应：{"success": True, **data}"""
      return {"success": True, **data}

  def not_found(detail: str) -> HTTPException:
      return HTTPException(404, detail=detail)

  def bad_request(detail: str) -> HTTPException:
      return HTTPException(400, detail=detail)
  ```
  - 按 spec 第 3 节 B6 对照表逐项替换（session.py 5 处、reviewer.py 6 处、collector.py 4 处、
    curator.py 4 处、plugins.py 4 处）；409 Conflict 保持 `HTTPException(409, ...)` 直写
  - curator.py 的 `{"success": True, **result}` → `ok(**result)`（键序一致）
  - 删除替换后不再使用的 `HTTPException` 导入（仅保留需要的）
- **验证**：
  - 新增 `tests/core_tests/test_api_common.py`：
    - `ok()` == `{"success": True}`；`ok(session=1)` 键序 success 在前
    - `not_found("x").status_code == 404` 且 `.detail == "x"`；`bad_request` 同理 400
  - 手工抽查：`python -c` 导入各 router 模块确认无 ImportError
  - `pytest tests/core_tests/test_api_common.py -q`；既有测试全绿
- **完成标准**：对照表全部落实；exporter.py 未动；无残留未使用导入（ruff 检查）

## Task 7：B7 main.py 整理 ✅ 已完成（23f8b7b）

- **修改**：`backend/main.py`
- **实现要点**：
  - 常量分组加注释：APP（APP_TITLE/APP_VERSION）、LOG（LOG_SEPARATOR_LENGTH/CHAR）
  - 提取 `async def _shutdown(app: FastAPI)`（shutdown 日志 + app_lifespan_shutdown 钩子 + database_manager.close()）
  - `lifespan` 的 shutdown 段改为调用 `_shutdown(app)`
  - `init_app`/`create_app`/`register_all_arguments`/`main` 逻辑不动；CORE/BUSINESS_MANAGERS 仅加注释
- **验证**：`python -c "import sys; sys.path.insert(0, 'backend'); import main"` 无错误（在 backend 目录下 `python -c "import main"`）；`pytest -q` 全绿
- **完成标准**：main.py 可导入；既有测试全绿

## Task 8：全量回归 ✅ 已完成（299 passed / ruff 0 error / 响应形状逐字一致）

- **命令**：`cd backend && pytest -q 2>&1 | tail -5`；`ruff check backend/`；git status 干净
- **抽查**：改造前后响应形状对照（读改造后代码确认 `ok()` 展开 == 原 dict）
- **完成标准**：全部测试通过（数量 ≥ 基线 + 新增）、ruff 0 error、无未提交变更

## 实施记录

- 全部 Task 已完成，commit：4c520f5（B1）、b81131f（B2）、921cb39（B3）、c79cd27（B4）、
  8d9954e（B5）、529d605（B6）、23f8b7b（B7）
- B5 实现偏差说明：spec 原设计为同步 `_dispatch` 注入 execute，但同步循环无法 await
  异步钩子（Python 语义限制），且 `run_sync` 改用 `asyncio.run` 会破坏同步/异步上下文
  混合场景（running loop 中抛 RuntimeError）。最终实现：`_dispatch` 为 async（run 共享），
  `run_sync` 保留独立同步循环（warning 语义逐字保留）。行为经既有 hook 测试全部验证等价。
- B4 实现偏差说明：`_read_yaml` 读取失败返回 None（而非 {}），`_load_entry` 见 None 跳过
  插件——保持原"坏 yaml 跳过插件"语义（既有 test_edge_cases 验证）。
- 全量：299 passed（基线 249 + 新增 50），ruff 0 error。
