---
title: 架构设计笔记
description: 系统架构设计与实现细节记录
keywords: [架构, architecture, 设计决策]
version: "1.0"
---

# 架构设计笔记

## 初始化流程

整个流程具有鲜明的流程化，init 阶段会执行：
1. args 参数解析
2. 插件注册
3. 环境变量注册
4. 密钥注册（此时检查 Infisical 服务是否启动）
5. 密钥检查（有三种值：Infisical值、默认值、随机值、空值。required 必须有值。优先使用 Infisical 值，其次是随机值，再次是默认值，再次是空值）
6. setting 完成后开始 uvicorn.run

## 密钥管理

1. 密钥注册表不能代码内注册，通过 yaml 文件注册
2. Infisical 交互通过 Infisical Agent 实现
3. `_resolve_secret_value` 逻辑：无论如何 infisical_value 是第一优先级，若没有 infisical_value，则判断是否 required，若 required，则随机，若是 optional 则是默认值或空值。required 的默认值没有用到
4. `self._secrets_cache[name]` 不是永久的，其会刷新的，记录其创建时间，当其创建时间超了就刷新，外部可以通过一个函数强制刷新。getsce 默认先返回 self._secrets_cache

## 插件管理

1. 插件通过 plugins/plugins.yaml 注册
   ```yaml
   plugins:
     rating:
       enabled: true
       path: plugins/rating
     knowflow_openclaw:
       enabled: true
       # path 没有设置默认为 plugins/name
   ```
2. `register_plugins` 只能干注册插件的事情，不要创建文件夹
3. `_collect_secret_defs` 直接从已有的插件列表中导出 plugin config 即可。插件管理 load 完之后可能是个 dict, key=name, val=plugin.yaml 的 dict
4. 插件注册是在插件注册一步的，不能在 `_collect_secret_defs` 中收集有哪些插件。有哪些插件应该 setting 中已经获取了。收集插件应该是插件管理服务的事情

## 模块初始化

1. 流程第一步是注册各个 manager，每个 manager 初始化 `__init__` 就是注册，init
2. 创建 `setting_manager`，其可以注册 argparse，保留其他模块注册 argparse 的方法。`setup_settings` 在 `setting_manager` 中
3. `load_plugin_registry` 在 `plugin_manager` 中
4. `register_secrets` 在 `secrets_manager` 中
5. `database` 变成 `database_manager`，其初始化时注册数据库连接

## 路由

1. 所有路由都在 api 文件夹中，包括 health

## 编码规范

1. 除了 main, setting 之外其他代码不能出现默认值，例如这个就有问题：
   ```python
   SecretsManager self.secrets_yaml_path = Path(secrets_yaml_path) if secrets_yaml_path else backend_root.parent / "secrets" / "backend.yaml"
   ```
2. 除了 main, setting 之外其他代码不能出现默认值，例如 `DEFAULT_SOCKET_PATH`
3. 要清楚的意识到类/模块中 `_XXX` 变量是告诉其他模块不要调用的（我自己用的），它本身没有安全性。不要为了安全用这个。应该是根据其他模块用不用来判断

## Secrets Manager 使用

1. `secrets_manager` 直接在 import 模块的时候已经创建了，其他代码例如 main 只需执行 `secrets_manager.initialize`
