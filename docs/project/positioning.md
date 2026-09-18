---
title: 项目定位
description: HarvestFlow 差异化能力、目标场景与边界
keywords: [定位, 差异化, 场景, OpenClaw, 插件]
version: "1.0"
---

# 项目定位

HarvestFlow 是**本地化**的 AI Agent 会话数据流水线：把散落在文件里的
Agent 会话，变成可审核、可追溯、可直接用于训练的数据集。

## 1. 一句话定位

> 一个跑在自己机器上的「采集 → 自动评分 → 人工复核 → 导出」闭环，
> 与 OpenClaw 双向打通，评分可解释、操作全留痕。

## 2. 目标用户与场景

| 场景 | 说明 |
|------|------|
| 个人开发者 / 小团队 | 把日常与 Agent 的高价值会话沉淀为 ShareGPT / Alpaca 微调数据 |
| OpenClaw 用户 | 批量解析 OpenClaw v3 导出，按工具调用、决策链质量筛选会话 |
| 数据合规敏感场景 | 数据不出内网：SQLite + 本地文件 + 单机 Docker，无云依赖 |

## 3. 差异化能力（均已实现）

| 能力 | 说明 | 代码入口 |
|------|------|----------|
| 本地优先 | FastAPI + SQLite + 本地文件，无任何云依赖；可选 Bearer 鉴权 | `backend/core/database_manager.py` |
| OpenClaw 双向集成 | 服务端解析 OpenClaw 导出（含 Windows 路径回退）并专用评分；Agent 侧扩展提供 `harvestflow_*` 工具主动上报 | `plugins/collectors/openclaw/`、`plugins/plugin-openclaw-to-harvestflow/` |
| 可解释自动评分 | 评分附 `score_reasons`：工具调用成功、多步决策链、明确输出、消息数 | `plugins/curators/openclaw/backend.py` |
| 状态机 + 唯一落库入口 | `raw → curated → approved/rejected`，流转校验集中在 `apply_review` | `backend/managers/session_manager.py` |
| 全链路审计 | approve / reject / modify 均写审计日志，支持按会话过滤 | `backend/managers/reviewer_manager.py` |
| 插件热插拔 | Collector / Curator / Service 三类插件，before/after 短路钩子，评分算法与编排解耦 | `backend/core/hook_manager.py`、`plugins/README.md` |
| 训练格式导出 | ShareGPT / Alpaca，支持分数/角色/任务/标签筛选，筛选条件随导出历史留存 | `backend/managers/exporter_manager.py` |
| 能力全量上界面 | 全中文 UI，六个页面覆盖后端全部端点 | `frontend/src/pages/` |

## 4. 与相关方案的边界

| 方案 | 与 HarvestFlow 的关系 |
|------|----------------------|
| 云端数据标注平台 | HarvestFlow 不做多租户、配额与人员管理，聚焦单机私有化流水线 |
| 自研采集脚本 | 提供状态机、审计、批量复核与可视化，而非一次性转换脚本 |
| 训练框架（如 LLaMA-Factory） | HarvestFlow 只负责产出数据集，训练在外部完成 |
| OpenClaw 本体 | HarvestFlow 是 OpenClaw 的数据侧车：不运行 Agent，只处理会话数据 |

## 5. 非目标（Non-goals)

- 不做云端 SaaS 与账号体系
- 不做标注任务分发 / 众包协作
- 不做模型训练与推理
- 不内置任意第三方数据源 SDK（通过插件扩展）

## 6. 演进

v1.1 规划（目录监听自动采集、导出下载、Reviewer 插件体系、技术债清理）
见 [future_plan.md](../../future_plan.md)；架构分层见
[architecture_guide.md](architecture_guide.md)。
