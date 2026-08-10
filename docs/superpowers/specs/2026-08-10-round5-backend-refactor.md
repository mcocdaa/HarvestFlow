# Round 5 批次 1：后端代码优化与整理 — 设计规格

- 日期：2026-08-10
- 状态：待用户审阅
- 上游设计：docs/superpowers/specs/2026-08-10-round5-refactor-design.md（第 4 节）
- 深度：中等重构，行为零变化

## 1. 背景与目标

后端（backend/）经多轮迭代功能稳定、测试充分（约 100+ 用例），存在以下可观察问题：

1. 5 个业务 manager 的 `register_arguments(parser)` / `init(args)` 生命周期接口靠文档约定，无代码级统一
2. `collector_manager.parse_session_file` 内嵌约 50 行 jsonl 解析逻辑，与解析职责混在一起
3. `import_session` 与 `import_all` 重复构造会话记录（file_path/content）与错误处理
4. `plugin_manager` 中模块名构造 `f"plugins.{key.replace(os.sep,'.').replace('/','.')}"` 重复 3 次；`_load_registry` 过长（约 130 行）
5. `hook_manager.run` 与 `run_sync` 两套几乎相同的执行循环
6. 每个 API router 手写 `{"success": True, ...}` 与 `HTTPException(...)`
7. `main.py` 常量与生命周期代码混排

**目标**：在不改变任何外部契约的前提下，提取重复、收敛接口、拆分长函数，提升复用性与可维护性。

## 2. 范围

### In-scope

- B1-B8（见第 3 节）
- 新增文件：`backend/managers/base.py`、`backend/core/parsers.py`、`backend/api/v1/common.py`
- 对应新增测试（B8）

### Out-of-scope（明确不做）

- 不改 API 响应 JSON 形状、路由路径/方法/状态码
- 不改 hook 名称与语义（含 before 短路、after 链式、同步环境警告）
- 不改单例实例化方式（`xxx_manager = XxxManager()` 保持）
- 不改 CLI 参数名与默认值、不改 `.env` 键名
- 不改数据库 schema 与 SQL 行为
- 不改 `plugin.yaml`/`plugins.yaml` 结构与字段
- 不改 openclaw 插件的解析短路行为
- core 层单例（setting/secrets/database/hook/plugin manager）暂不强制继承 BaseManager
- 前端、插件目录、docs 目录不属于本批次

## 3. 逐项设计

### B1 Manager 抽象基类（backend/managers/base.py）

**动机**：5 个业务 manager 的生命周期接口（`register_arguments`/`init`）结构完全一致，
引入基类固化契约，便于统一遍历与后续扩展（如统一 hook 包装、统一日志）。

**接口**：

```python
class BaseManager:
    """业务管理器基类。

    所有业务管理器继承本类，实现统一生命周期接口：
    - register_arguments(parser)：注册 argparse 参数
    - init(args)：初始化（args 为 argparse.Namespace）
    子类覆写时按需使用 @hook_manager.wrap_hooks 包装（命名规范
    "{manager_name}_{method}_before/after"），基类不强制包装。
    """

    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数（默认空实现）"""

    def init(self, args: argparse.Namespace):
        """初始化管理器（默认空实现）"""
```

**要点**：
- 使用普通类而非 `abc.ABC`：现有 `session_manager`/`reviewer_manager` 的 `init` 为空实现，
  ABC 无法提供额外约束价值，且避免破坏测试中直接实例化/替换单例的用法
- `__init__` 不放入基类（各 manager 的 `self.logger = logging.getLogger(__name__)`
  与 construct hook 包装各有专属 hook 名，保持现状）
- 子类改动仅为 `class SessionManager(BaseManager):` 等 5 处声明，方法体不变
- `managers/__init__.py` 导出 `BaseManager` 并加入 `__all__`

**测试**（B8）：
- 每个业务 manager 类 `issubclass(X, BaseManager)` 成立
- 基类默认 `register_arguments`/`init` 可调用且不抛异常

### B2 会话解析职责拆分（backend/core/parsers.py）

**动机**：jsonl 逐行解析与 json 兜底解析是通用能力，从 collector 中剥离供复用
（openclaw 插件亦可引用，但不强制改造插件）。

**接口**：

```python
def parse_jsonl_file(file_path: str) -> Optional[Dict]:
    """解析 jsonl 会话文件。

    逐行读取：type == "message" 的行提取 role 与 text content（list 中的
    text 项或字符串）；session_id 取第一个带 id 的行。agent_id 从文件路径
    的 "agents" 段之后提取。messages 为空或 session_id 缺失时返回 None。
    """

def parse_json_file(file_path: str) -> Optional[Dict]:
    """解析普通 json 会话文件。

    返回原字典；缺少 session_id 时生成
    "session_{YYYYmmdd_HHMMSS}_{basename}" 并写回 data["session_id"]。
    读取/解析异常返回 None。
    """
```

**要点**：
- 原 `collector_manager.parse_session_file` 中的 jsonl 分支体原样搬入
  `parse_jsonl_file`（含：空行跳过、`json.JSONDecodeError` 行跳过、
  `if messages and session_id` 前置条件、`agents` 路径段提取）
- 原 json 分支体原样搬入 `parse_json_file`（含 session_id 生成逻辑）
- 日志：parsers 模块使用模块级 `logger = logging.getLogger(__name__)`（即 `core.parsers`），
  函数体顶层 `try/except` 捕获异常后 `logger.error(f"解析文件失败 {file_path}: {e}")`
  并返回 None（文案与现状一致）；`collector_manager.parse_session_file` 不再自带
  try/except，委托调用即可。日志名由 `managers.collector_manager` 变为 `core.parsers`
  （属契约清单第 7 条允许范围）
- `collector_manager.parse_session_file` 收缩为：

```python
@hook_manager.wrap_hooks("collector_manager_parse_before", "collector_manager_parse_after")
def parse_session_file(self, file_path: str) -> Optional[Dict]:
    if file_path.endswith('.jsonl'):
        return parsers.parse_jsonl_file(file_path)
    return parsers.parse_json_file(file_path)
```

- `core/__init__.py` 无需改动（parsers 作为模块直接 import：`from core import parsers`）

**测试**（B8）：tests/core_tests/parsers/ 下
- jsonl：正常多行 message 提取、字符串 content、list content 的 text 拼接、
  坏 JSON 行跳过、无 message 返回 None、无 id 返回 None、
  agents 路径段提取 agent_id（含无 agents 段返回 None）
- json：原样返回、缺 session_id 时生成并写回、非 JSON 文件返回 None
- collector 现有解析测试（managers_tests/collector_manager/test_parsing.py）保持全绿

### B3 import 重复逻辑提取（backend/managers/collector_manager.py）

**动机**：`import_session` 与 `import_all` 中"构造记录 + 创建会话 + 错误处理"重复。

**接口**（私有方法）：

```python
def _build_session_record(self, file_path: str, session_data: Dict) -> Dict:
    """构造入库记录：content 保存原始数据快照，file_path 附加来源路径"""
    record = dict(session_data)
    record["file_path"] = file_path
    record["content"] = dict(session_data)
    return record

def _create_session(self, record: Dict) -> Optional[str]:
    """调用 session_manager 创建会话，返回 session_id，失败记录日志返回 None"""
    try:
        session_manager.create_session(record)
    except Exception as e:
        self.logger.error(f"创建会话记录失败：{e}")
        return None
    return record.get("session_id")
```

**要点**：
- `import_session` 重写为：parse → 空检查 → `_build_session_record` → `_create_session`，
  行为与现状一致（失败返回 None）
- `import_all` 重写为：parse → 空检查（failed）→ skipped 检查（保持现状逻辑）→
  `_build_session_record` → `_create_session` 失败时 failed
- 注意 `import_session` 无 skipped 检查、`import_all` 有，提取后各自行为不得改变

**测试**（B8）：tests/managers_tests/collector_manager/ 下
- `_build_session_record`：content 为原始快照（不含 file_path 键）、file_path 附加
- `_create_session`：成功返回 session_id、session_manager.create_session 抛异常返回 None
- 现有 test_import.py 相关测试保持全绿

### B4 plugin_manager 瘦身（backend/core/plugin_manager.py）

**动机**：模块名构造重复 3 次；`_load_registry` 单函数过长，读 yaml/manifest 逻辑内联。

**接口**（私有方法）：

```python
def _module_name(self, key: str) -> str:
    """插件 key → 模块名：plugins.{key 中的路径分隔符替换为 .}"""
    return f"plugins.{key.replace(os.sep, '.').replace('/', '.')}"

def _read_yaml(self, path: Path) -> Dict:
    """读取 yaml 文件，异常记录错误返回 {}"""

def _read_manifest(self, path: Path) -> Dict:
    """读取插件清单：目录取 plugin.yaml；.py 文件构造
    {"name": stem, "type": "unknown", "backend_entry": name}"""

def _load_entry(self, key: str, cfg: Dict) -> Optional[Dict]:
    """处理注册表单个条目（enabled/path 解析/manifest 读取），
    返回 {enabled, path, name, type, manifest}，失败返回 None"""
```

**要点**：
- `register_hooks` 中 2 处 `module_name = f"plugins.{...}"` 与 `set_enabled` 中 1 处
  全部替换为 `self._module_name(key)`
- `_load_registry` 的循环体改为调用 `_load_entry`；禁用分支（保留注册表项）
  与"路径不存在/清单缺失跳过"逻辑原样搬移
- `_read_yaml` 替换 plugins.yaml 与 plugin.yaml 两处 `open + yaml.safe_load` 块，
  错误日志文案沿用现状
- 日志行为不变

**测试**（B8）：tests/core_tests/plugin_manager/ 下
- `_module_name`：key 含 "/" 与 os.sep 时替换正确
- `_read_yaml`：正常返回 dict、文件缺失/损坏返回 {}（不抛异常）
- `_load_entry`：目录带 plugin.yaml、.py 单文件、禁用、路径缺失、清单缺失各分支
- 现有 test_load_registry.py 等保持全绿

### B5 hook_manager 执行循环去重（backend/core/hook_manager.py）

**动机**：`run`（异步）与 `run_sync`（同步）的遍历/异常收集循环重复，
仅"是否执行异步钩子"不同。

**设计**：提取共享循环，执行策略以可调用对象注入：

```python
def _dispatch(self, hook_name: str, args: Tuple, kwargs: Dict,
              execute: Callable[[Callable], Any]) -> HookResult:
    """共享执行循环：遍历钩子，逐个调用 execute(cb) 收集结果与错误。
    execute 决定单钩子如何执行（await / 直接调用 / 跳过并警告）。"""
    results, errors = [], []
    for _, cb in self._hooks.get(hook_name, []):
        try:
            results.append(execute(cb))
        except Exception as e:
            errors.append((cb.__name__, e))
            logger.error(f"钩子执行失败 [{hook_name}]: {cb.__name__} - {e}", exc_info=True)
    return results, errors
```

`run` 改为：

```python
async def run(self, hook_name: str, *args, **kwargs) -> HookResult:
    async def execute(cb: Callable) -> Any:
        if asyncio.iscoroutinefunction(cb):
            return await cb(*args, **kwargs)
        return cb(*args, **kwargs)
    return self._dispatch(hook_name, args, kwargs, execute)
```

`run_sync` 改为：

```python
def run_sync(self, hook_name: str, *args, **kwargs) -> HookResult:
    def execute(cb: Callable) -> Any:
        if asyncio.iscoroutinefunction(cb):
            logger.warning(
                f"[{hook_name}]: {cb.__name__} - 异步钩子不能在同步环境中执行"
            )
            return None
        return cb(*args, **kwargs)
    return self._dispatch(hook_name, args, kwargs, execute)
```

**要点**：
- 同步环境下异步钩子的 warning 日志行为必须保留（文案逐字一致）
- 异常捕获/错误列表结构 `(cb.__name__, e)` 不变
- 返回值类型 `HookResult` 不变

**测试**（B8）：tests/core_tests/hook_manager/ 下
- 现有 test_run_sync.py、test_error_handling.py、test_basic_registration.py 保持全绿即证明等价
- 补充：`_dispatch` 直接调用场景（execute 抛出异常被收集、结果按注册顺序返回）

### B6 API 统一辅助（backend/api/v1/common.py）

**动机**：`{"success": True, ...}` 与 `HTTPException(status, detail=...)` 在各 router 手写重复。

**接口**：

```python
from fastapi import HTTPException

def ok(**data) -> dict:
    """成功响应：{"success": True, **data}"""
    return {"success": True, **data}

def not_found(detail: str) -> HTTPException:
    """404 异常辅助"""
    return HTTPException(404, detail=detail)

def bad_request(detail: str) -> HTTPException:
    """400 异常辅助"""
    return HTTPException(400, detail=detail)
```

**改造对照表（响应形状逐字不变）**：

| 文件 | 现状 | 改为 |
|------|------|------|
| session.py | `{"success": True, "session": session}` | `ok(session=session)` |
| session.py | `HTTPException(404, detail="Session not found")` 等 | `raise not_found("Session not found")` |
| session.py | `HTTPException(409, detail="Invalid status transition")` | `raise HTTPException(409, detail=...)`（保持，无专用辅助） |
| reviewer.py | `{"success": True, "session": result}` ×3 | `ok(session=result)` |
| reviewer.py | `HTTPException(404/400, detail=...)` | `raise not_found(...)` / `raise bad_request(...)` |
| collector.py | `{"success": True, "session_id": ...}`、`{"success": True, "watch_folders": ...}` ×2 | `ok(session_id=...)` / `ok(watch_folders=...)` |
| collector.py | `HTTPException(400, detail="Failed to import session")` | `raise bad_request(...)` |
| curator.py | `{"success": True, **result}` | `ok(**result)` |
| curator.py | `HTTPException(404/409/400, detail=error)` | `raise not_found(error)` / 409 保持 / `raise bad_request(error)` |
| plugins.py | `{"success": True}` ×2 | `ok()` |
| plugins.py | `HTTPException(404, detail="Plugin not found")` | `raise not_found(...)` |
| exporter.py | `{"exports": records}`、`{"formats": [...]}`、result 原样 | **不改**（无 success 包装，不属于统一范围） |

**要点**：
- 409 Conflict 场景不引入专用辅助（仅 1 处），保持 `HTTPException(409, ...)` 直写
- 仅做表达式替换，不改变控制流与响应内容

**测试**（B8）：tests/core_tests/test_api_common.py
- `ok()` 形状、`ok(session=...)` 键序（success 在前）
- `not_found`/`bad_request` 的 status_code 与 detail

### B7 main.py 整理

**要点**：
- 常量按语义分组并加注释：APP（APP_TITLE/APP_VERSION）、LOG（LOG_SEPARATOR_*）、
  MANAGER 列表（CORE_MANAGERS/BUSINESS_MANAGERS 保持现状，仅加注释说明用途）
- lifespan 中 shutdown 部分提取为模块级 `async def _shutdown(app: FastAPI)`：

```python
async def _shutdown(app: FastAPI):
    logger.info("应用关闭，执行清理...")
    await hook_manager.run("app_lifespan_shutdown", app)
    database_manager.close()
    logger.info("✓ 数据库连接已关闭")
```

- lifespan 主体保持（app_lifespan_start 钩子、日志分隔符、yield）
- `init_app`/`create_app`/`main` 逻辑不动

**测试**：无需新增（现有 core_tests 覆盖各 manager 初始化）；`python -c "import backend.main"` 可导入即验收（不启动服务）。

### B8 测试计划汇总

| 新文件 | 覆盖 |
|--------|------|
| tests/managers_tests/test_base_manager.py | B1 |
| tests/core_tests/parsers/test_jsonl.py、test_json.py | B2 |
| tests/managers_tests/collector_manager/test_import_helpers.py | B3 |
| tests/core_tests/plugin_manager/test_helpers.py | B4 |
| tests/core_tests/hook_manager/test_dispatch.py | B5 |
| tests/core_tests/test_api_common.py | B6 |

风格遵循现有测试（conftest 的 args_with_db_path 等 fixture；核心单例可全局复用）。
全部既有测试必须保持绿色。

## 4. 不改动的契约清单（回归红线）

1. HTTP：所有路由路径、方法、状态码、响应 JSON 键与值逐字不变
2. Hook：hook 名称、before 短路、after 链式、同步环境 warning 文案不变
3. 单例：`xxx_manager = XxxManager()` 模块级实例方式不变，`managers/__init__.py` 导出不变（仅新增 BaseManager）
4. CLI：参数名、默认值、分组不变
5. 数据：database_manager SQL/schema 行为不变
6. 插件：plugins.yaml/plugin.yaml 结构与字段不变；openclaw 插件 parse_before 短路不变
7. 日志：错误文案保持（logger 名称允许因 parsers 模块化而变为 core.parsers）

## 5. 风险与缓解

| 风险 | 缓解 |
|------|------|
| B1 基类化影响测试 mock/单例替换 | 只加继承声明，不改实例化；测试只断言 issubclass 与默认实现 |
| B2 解析提取改变返回语义 | 函数体逐行搬移；现有 parsing 测试全绿为凭据 |
| B5 去重改变同步警告行为 | 警告文案逐字保留；test_run_sync 覆盖 |
| B6 辅助封装遗漏形状 | 对照表逐字核对；api 相关既有测试与前端联调行为不变 |
| 长函数拆分引入回归 | 每项拆分为独立提交，逐步验收 |

## 6. 验收标准

1. `cd backend && pytest` 全部通过（既有 + 新增）
2. `ruff check backend/` 0 error（按项目现有 ruff 配置）
3. 行为对照：API 响应形状抽查与改造前一致
4. 提交记录：按 B1-B8 分 task 提交，每个 task 提交可独立回滚
