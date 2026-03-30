# Proposal: HarvestFlow OpenClaw Extension

## Why

HarvestFlow 目前仅通过 Web UI 和 REST API 提供服务，AI Agent 无法直接以工具调用（Tool Calling）方式与其交互。这限制了自动化工作流的构建，Agent 无法自主完成会话采集、评估和审核任务。

本提案旨在开发一个 OpenClaw Extension，使任何 OpenClaw Agent 都能通过标准化的工具接口与 HarvestFlow 后端进行协同工作，实现真正的 Agent-Native 数据流水线。

## 背景与价值

HarvestFlow 是一个 AI Agent 会话数据采集与审核系统，目前通过 Web UI 和 REST API 提供服务。随着 AI Agent 生态的发展，让 Agent 能够直接通过工具调用（Tool Calling）与 HarvestFlow 交互变得至关重要。

本提案旨在开发一个 OpenClaw Extension，使任何 OpenClaw Agent 都能通过标准化的工具接口与 HarvestFlow 后端进行协同工作。

## 核心价值

### 1. Agent-Native 集成
- 允许 AI Agent 直接触发会话扫描、导入、审核等操作
- 无需人工介入即可完成批量数据处理工作流
- 支持 Agent 自主决策的会话管理

### 2. 自动化工作流
- Agent 可以监控文件夹并自动导入新会话
- 自动执行质量评估（Curation）流程
- 批量审核（Approve/Reject）会话

### 3. 扩展性
- 基于 OpenClaw 插件标准，易于安装和配置
- 支持多 Agent 同时访问 HarvestFlow 后端
- 可与其他 OpenClaw 工具链组合使用

## 目标用户

- 使用 OpenClaw 框架的 AI Agent 开发者
- 需要自动化会话数据处理的 MLOps 团队
- 构建自动化数据审核流水线的工程师

## 成功标准

1. Agent 可以通过 4 个核心工具与 HarvestFlow 交互
2. 插件安装简单（npm install + 配置）
3. 支持错误处理和连接状态检查
4. 提供完整的 SKILL.md 文档

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| API 版本不兼容 | 使用显式版本检查，向后兼容设计 |
| 后端服务不可用 | 实现健康检查和优雅降级 |
| 认证安全问题 | 支持 API Key 和 Token 认证 |

## 回滚计划

如需回滚，只需：
1. 删除 `openclaw-extension/` 目录
2. 从 OpenClaw 配置中移除插件引用
3. 重启 Agent 服务

---

*提案日期: 2026-03-29*
