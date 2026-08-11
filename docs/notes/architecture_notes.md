---
title: 架构设计笔记
description: 系统架构设计与实现细节记录
keywords: [架构, architecture, 设计决策]
version: "2.0"
---

# 架构设计笔记

> 本文为开发过程的设计决策记录。当前架构的完整说明见
> [架构指南](../project/architecture_guide.md)；与实现不一致的历史描述已修正。

## 初始化流程

整个流程具有鲜明的流程化，init 阶段会执行：
1. args 参数解析（`register_all_arguments`：核心管理器 + 业务管理器逐个注册）
2. 插件注册（`plugin_manager.register_hooks()`，import 插件 `__init__.py` 注册钩子）
3. 环境变量注册（`setting_manager.init`）
4. 密钥注册（`secrets_manager.init`，此时检查 Infisical 服务是否启动）
5. 密钥检查（值优先级：Infisical 值 > 随机值 > 默认值 > 空值。required 必须有值）
6. 数据库初始化（`database_manager.init`）
7. 业务管理器初始化（session/collector/curator/reviewer/exporter 逐个 `init`）
8. setting 完成后开始 uvicorn.run

## 密钥管理

1. 密钥注册表不能代码内注册，通过插件 plugin.yaml 的 `secrets` 字段注册
2. Infisical 交互通过 Infisical SDK（services/infisical 插件，可插拔）
3. `_resolve_secret_value` 逻辑：无论如何 infisical_value 是第一优先级，若没有
   infisical_value，则判断是否 required，若 required 则随机，若是 optional 则是默认值
   或空值
4. `self._secrets_cache[name]` 带刷新机制：记录创建时间，超时刷新，外部可通过函数强制刷新

## 插件管理

1. 插件通过 plugins/plugins.yaml 注册，插件 key 为相对 plugins/ 的路径
   ```yaml
   plugins:
     collectors/openclaw:
       enabled: true
     services/infisical:
       enabled: true
   ```
2. `register_hooks` 只做插件加载与钩子注册，不创建文件夹
3. `get_plugin_secrets` 直接从已注册插件的 manifest 中导出密钥定义
4. 插件发现发生在插件管理初始化（`__init__` 时 `_load_registry`），
   业务管理器初始化在其后

## 模块初始化

1. 流程第一步是注册各个 manager，每个 manager 初始化 `__init__` 就是注册，init
2. 创建 `setting_manager`，其可以注册 argparse，保留其他模块注册 argparse 的方法
3. `_load_registry` 在 `plugin_manager` 中（加载 plugins.yaml 注册表）
4. 密钥定义收集在 `plugin_manager.get_plugin_secrets`，初始化在 `secrets_manager.init`
5. `database_manager` 初始化时注册数据库连接

## 路由

1. 所有路由都在 api 文件夹中，包括 health
2. 路由自动注册：`router_loader` 扫描 api/v1 目录下各模块的 `router` 对象

## 编码规范

1. 除了 main, setting 之外其他代码不能出现默认值，例如这个就有问题：
   ```python
   SecretsManager self.secrets_yaml_path = Path(secrets_yaml_path) if secrets_yaml_path else backend_root.parent / "secrets" / "backend.yaml"
   ```
2. 除了 main, setting 之外其他代码不能出现默认值，例如 `DEFAULT_SOCKET_PATH`
3. 要清楚的意识到类/模块中 `_XXX` 变量是告诉其他模块不要调用的（我自己用的），
   它本身没有安全性。不要为了安全用这个。应该是根据其他模块用不用来判断

## Manager 基类（Round 5 新增约定）

1. 业务管理器继承 `managers.base.BaseManager`，统一 `register_arguments`/`init` 生命周期接口
2. 模块级单例模式：`xxx_manager = XxxManager()`，测试直接 import 单例
3. 会话文件解析（jsonl/json）统一走 `core.parsers`（`parse_jsonl_file`/`parse_json_file`），
   业务层不再内嵌解析逻辑
4. API 成功响应统一 `api.v1.common.ok()`，错误统一 `not_found`/`bad_request` 辅助

## Secrets Manager 使用

1. `secrets_manager` 在模块 import 时已创建（单例），main 中执行 `secrets_manager.init(args, plugin_secrets)`
