## Context

HarvestFlow 内部有自己基于 Hook 机制的一套插件（Python 编写的 Collector 和 Curator），原本是针对最初直接读取本地 `sessions.json` 而硬编码编写的。
在第一阶段中，我们在该工程下构建了可以独立作为 OpenClaw Extension 的 npm 工程（用于在 OpenClaw Agent 中使用，通过 HTTP POST 提交给 HarvestFlow 后端）。但是：
1. OpenClaw Extension 代码现在还在 HarvestFlow 的子文件夹内，应该剥离为独立的 Github Submodule 或分开管理，以符合诸如 KnowFlow 的解耦形态。
2. HarvestFlow 端的 Python 采集器（`plugins/collectors/openclaw/backend.py`）中有不合理的硬编码（如 `C:/Users/20211/.openclaw/agents` 和 Windows 路径转换）。

## Goals / Non-Goals

**Goals:**
1. 将 `openclaw-extension/` 移出并重构成 Submodule 形态（或独立提交）。
2. 重构 `plugins/collectors/openclaw/backend.py` 优化扫描路径和跨平台支持，不让其在测试中因为找不到文件崩溃。
3. 审查并稍微优化 `plugins/curators/openclaw/backend.py` 中的评分规则和标签解析机制。

**Non-Goals:**
1. 不改变核心的 HarvestFlow Backend 的基础架构（仅仅改插件）。
2. 不重新编写 OpenClaw Extension 的 Typescript 代码（复用之前的成果，只做迁移打包）。

## Decisions

1. **Submodule 化**:
   直接借助 Git 机制，把 `openclaw-extension` 整个目录在主仓库内移除，或者推送到一个独立仓库并以 Submodule 的方式加进来。这样 Agent 用户可以通过 `npm i` 去装它，而不是要拉取整个 HarvestFlow 服务端仓库。
2. **Collector 路径重构**:
   使用 `Pathlib` 或者更通用的基于环境变量的路径发现，允许通过环境变量或者 HarvestFlow 界面配置来动态下发 `agents_dir`，并在代码中去掉对特定 Windows 磁盘符（C:）的假定转换。

## Risks / Trade-offs

- **Submodule 维护成本增加**：拆分代码库意味着如果前后端协议更新，需要发两个 PR 保持同步。 
- **本地测试可能会麻烦**：在子模块机制下，如果独立仓库还没就绪，我们暂时只做到目录清理和准备。为了本次能直接“跑通测试”，优先保证 Python 侧逻辑的无懈可击。