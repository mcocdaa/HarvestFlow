## Why

目前的 HarvestFlow OpenClaw 采集器插件（`plugins/collectors/openclaw`）仅支持硬编码的通过特定文件夹结构读取 `sessions.json` 的方式，且依赖硬编码的路径结构（如 `DEFAULT_AGENTS_DIR = "C:/Users/20211/.openclaw/agents"`）和内置在 HarvestFlow 本地的代码读取。
随着我们在 OpenClaw Extension 侧（被作为独立模块/子模块开发）构建了能够通过远程 API 推送会话的 `harvestflow_scan_import` 工具，HarvestFlow 侧的 Collector 应该同时作为服务端，可以被动接收来自 OpenClaw Extension 的推送，甚至可以直接抽离 OpenClaw Extension 作为一个 submodule，保持架构的内外分离，让 HarvestFlow 端代码更纯粹。
这也避免了待会测试时，两个不同方向的接入逻辑导致寻找不到正确文件路径的错误。

## What Changes

- **将 OpenClaw Extension 作为 Submodule 引入**：HarvestFlow 仓将直接把 `openclaw-extension/` 作为 Git submodule 链接（或作为独立的 package 管理），从主工程树中解耦。
- **重构 Python 侧的 Collector & Curator**：
  - 更新 `plugins/collectors/openclaw/backend.py` 逻辑，使其支持直接接收 `session` 导入的 API payload，而不只依赖本地硬编码路径。
  - 审查 `plugins/curators/openclaw/backend.py` 确保它能适应新的 OpenClaw Agent (如 Autoflow/Knowflow 架构下产生的会话日志结构)。
  - 修复可能存在的过时代码引用和兼容性问题。

## Capabilities

### New Capabilities
- `openclaw-extension-submodule`: 把第一阶段构建的扩展分离为 Submodule 或独立构件。

### Modified Capabilities
- `collector-openclaw`: The HarvestFlow-side collector python plugin needs to be refactored to support robust path resolution or API-based ingestion instead of brittle Windows-specific hardcoded paths.
- `curator-openclaw`: The automated AI session scoring logic needs a review and optimization.

## Impact

- 修改 HarvestFlow 的采集器和审核器插件（Python 端）。
- 会话结构、API 路由可能会与新版的 OpenClaw Extension（TypeScript 端）更好地耦合。