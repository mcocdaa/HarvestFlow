## Why

在之前的修改中，我不小心通过非终端方式覆写了 Python 文件（如 `plugins/collectors/openclaw/backend.py` 等），导致原有文件内存在中文乱码（GBK/UTF-8 编码冲突导致的类似于 `ä¼šè¯ é‡‡é›†å™¨æ ’ä»` 这样的乱码）。
更重要的是，原计划的子模块解耦并未完全落实：`openclaw-extension` 仍在项目根目录，而不是像约定的那样作为 git submodule 挂载在 `plugins/` 文件夹下。

## What Changes

- **代码回滚与修复**：将由于乱码被破坏的 `plugins/collectors/openclaw/backend.py` 还有 `plugins/curators/openclaw/backend.py` 代码完全恢复到 `origin/main` 的状态，消除所有乱码。我以后不再通过非安全的 `Set-Content`/`edit` 强行篡改已有文件的多语言字符集。
- **配置 Submodule**：
  1. 彻底删除当前的独立文件夹 `openclaw-extension`（及其在当前 git 树中的记录）。
  2. 将远程仓库 `git@github.com:mcocdaa/plugin-openclaw-to-harvestflow.git` 添加为 Git Submodule，并放置在路径 `plugins/plugin-openclaw-to-harvestflow` 或指定目录。

## Capabilities

### New Capabilities
- `extension-submodule-migration`: 将 OpenClaw Extension 项目转变为 `plugins` 目录下的外部 Submodule 引用。

### Modified Capabilities
- `collector-openclaw`: 将之前的代码乱码撤销。
- `curator-openclaw`: 将之前的代码乱码撤销。

## Impact

- 影响项目的文件树（移除了根目录下的 `openclaw-extension/` 文件夹，添加了 `.gitmodules` 以及 `plugins/` 下的子模块）。
- 解决了 Python 后端代码由于错误编码被我强行插入导致的编译或可读性灾难。