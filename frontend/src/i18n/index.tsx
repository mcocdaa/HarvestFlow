/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';

export type Locale = 'zh' | 'en';

export const STORAGE_KEY = 'harvestflow_lang';

const LOCALE_CHANGE_EVENT = 'harvestflow:locale-change';

export const getStoredLocale = (): Locale => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === 'en') return 'en';
      if (saved === 'zh') return 'zh';
    }
  } catch {
    // ignore storage errors
  }
  return 'zh';
};

export const MESSAGES: Record<Locale, Record<string, string>> = {
  zh: {
    'nav.dashboard': '概览',
    'nav.sessions': '会话',
    'nav.review': '审核',
    'nav.collect': '采集',
    'nav.export': '导出',
    'nav.plugins': '插件',
    'nav.github': 'GitHub 仓库',
    'status.raw': '待清洗',
    'status.curated': '待审核',
    'status.approved': '已通过',
    'status.rejected': '已拒绝',
    'status.all': '全部',
    'sort.recent': '最新优先',
    'sort.oldest': '最早优先',
    'role.user': '用户',
    'role.assistant': 'AI 助手',
    'role.system': '系统',
    'review.queue': '待审队列',
    'review.searchPlaceholder': '搜索 ID / 角色...',
    'review.prev': '上一个 (K)',
    'review.next': '下一个 (J)',
    'review.dialogue': '对话内容',
    'review.collapseTools': '折叠工具日志 (T)',
    'review.expandTools': '展开工具日志 (T)',
    'review.editReply': '编辑 AI 回复 (E)',
    'review.exitEdit': '退出编辑 (Esc)',
    'review.toolOutput': '工具结果',
    'review.toolError': '工具错误',
    'review.toolCall': '工具调用',
    'review.originalRejected': '原始回复 (Rejected)',
    'review.editedChosen': '修正后回复 (Chosen)',
    'review.decision': '评审决策',
    'review.scoreTitle': '质量评分 (直按 1~5 键)',
    'review.autoScore': '自动评分对比',
    'review.notes': '评审意见',
    'review.notesPlaceholder': '可选评审备注，最多 200 字',
    'review.approve': '通过评审',
    'review.reject': '拒绝',
    'review.shortcutsTitle': '极速全键盘操作指南',
    'review.shortcutApprove': '通过并切下一条',
    'review.shortcutReject': '拒绝并切下一条',
    'review.shortcutStar': '设定质量星级',
    'review.shortcutNav': '在队列中上下切换',
    'review.shortcutTools': '折叠/展开工具日志',
    'review.shortcutEdit': '编辑 AI 回复与 Diff',
  },
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.sessions': 'Sessions',
    'nav.review': 'Review',
    'nav.collect': 'Collector',
    'nav.export': 'Exporter',
    'nav.plugins': 'Plugins',
    'nav.github': 'GitHub Repo',
    'status.raw': 'Raw',
    'status.curated': 'Pending',
    'status.approved': 'Approved',
    'status.rejected': 'Rejected',
    'status.all': 'All',
    'sort.recent': 'Newest',
    'sort.oldest': 'Oldest',
    'role.user': 'User',
    'role.assistant': 'Assistant',
    'role.system': 'System',
    'review.queue': 'Queue',
    'review.searchPlaceholder': 'Search ID / role...',
    'review.prev': 'Prev (K)',
    'review.next': 'Next (J)',
    'review.dialogue': 'Dialogue',
    'review.collapseTools': 'Collapse Tools (T)',
    'review.expandTools': 'Expand Tools (T)',
    'review.editReply': 'Edit Reply (E)',
    'review.exitEdit': 'Exit Edit (Esc)',
    'review.toolOutput': 'Tool Output',
    'review.toolError': 'Tool Error',
    'review.toolCall': 'Tool Call',
    'review.originalRejected': 'Original (Rejected)',
    'review.editedChosen': 'Edited (Chosen)',
    'review.decision': 'Decision',
    'review.scoreTitle': 'Score (Keys 1~5)',
    'review.autoScore': 'Auto Score',
    'review.notes': 'Review Notes',
    'review.notesPlaceholder': 'Optional review notes (max 200 chars)',
    'review.approve': 'Approve',
    'review.reject': 'Reject',
    'review.shortcutsTitle': 'Keyboard Shortcuts',
    'review.shortcutApprove': 'Approve & Next',
    'review.shortcutReject': 'Reject & Next',
    'review.shortcutStar': 'Set Star Rating',
    'review.shortcutNav': 'Prev / Next Item',
    'review.shortcutTools': 'Toggle Tool Logs',
    'review.shortcutEdit': 'Edit & DPO Diff',
  },
};

export const DYNAMIC_EN_EXACT: Record<string, string> = {
  // Plugin names & authors
  'collectors/openclaw:name': 'OpenClaw Collector',
  'curators/openclaw:name': 'OpenClaw Curator',
  openclaw: 'OpenClaw Collector',
  pii_cleaner: 'PII Cleaner',
  'Reviewer Example': 'Score Reviewer',
  'Infisical Service': 'Infisical Secret Service',
  'HarvestFlow Team': 'HarvestFlow Team',
  HarvestFlow: 'HarvestFlow Team',
  default: 'Default Human Reviewer',
  // Agent roles (human-readable English labels)
  code_refactor_agent: 'Code Refactoring Specialist',
  devops_agent: 'SRE & DevOps Specialist',
  db_architect: 'Database Architect',
  security_agent: 'Security Auditor',
  sre_agent: 'SRE Specialist',
  backend_dev: 'Backend Developer',
  frontend_dev: 'Frontend Developer',
  req_analyst: 'Requirements Analyst',
  tester: 'QA Engineer',
  qa_ops: 'QA & Test Specialist',
  security_auditor: 'Security Auditor',
  arch_agent: 'System Architect',
  dba_agent: 'Database Administrator',
  qa_agent: 'QA Engineer',
  data_eng: 'Data Engineer',
  codex: 'Codex Agent',
  'openclaw-tui': 'OpenClaw TUI Agent',
  coding_assistant: 'Coding Assistant',
  assistant: 'AI Assistant',
  unknown: 'Uncategorized',
  'OpenClaw · sre_agent': 'OpenClaw · SRE Specialist',
  'Claude Code · backend_dev': 'Claude Code · Backend Developer',
  'OpenClaw · arch_agent': 'OpenClaw · System Architect',
  'OpenClaw · dba_agent': 'OpenClaw · Database Administrator',
  'Claude Code · qa_agent': 'Claude Code · QA Engineer',
  'OpenClaw · data_eng': 'OpenClaw · Data Engineer',
  // Task types (human-readable English labels)
  coding: 'Code Engineering',
  memory_leak_fix: 'Memory Leak Remediation',
  k8s_deployment_fix: 'K8s Deployment Fix',
  sqlite_optimization: 'SQLite Concurrency Tuning',
  security_audit: 'Security Vulnerability Audit',
  bug_fix: 'Bug Fix',
  bugfix: 'Bug Fix',
  performance_tuning: 'Performance Tuning',
  arch_design: 'Architecture Design',
  debugging: 'Bug Triage & Debugging',
  testing: 'Test Verification',
  refactoring: 'Code Refactoring',
  feature_dev: 'Feature Development',
  feature: 'Feature Development',
  code_generation: 'Code Generation',
  conversation: 'General Conversation',
  // Tags & audit details in English
  security: 'Security',
  sqli: 'SQL Injection',
  sql: 'SQL',
  python: 'Python',
  asyncio: 'AsyncIO',
  fastapi: 'FastAPI',
  'memory-leak': 'Memory Leak',
  k8s: 'K8s',
  production: 'Production',
  oom: 'OOM',
  troubleshooting: 'Troubleshooting',
  sqlite: 'SQLite',
  wal: 'WAL',
  concurrency: 'Concurrency',
  database: 'Database',
  'bug-fix': 'Bug Fix',
  review: 'Code Review',
  deployment: 'Deployment',
  config: 'Configuration',
  optimization: 'Optimization',
  refactor: 'Refactoring',
  documentation: 'Documentation',
  'smoke-test': 'Smoke Test',
  'codex-smoke-reject': 'Codex Smoke Test Rejected',
  'codex-smoke-approve': 'Codex Smoke Test Approved',
  'plugin-smoke': 'Plugin Smoke Test',
  'plugin-ok': 'Plugin Validation Passed',
  'demo-reject': 'Demo Review Rejected',
  'OpenClaw · K8s 零停机滚动升级加固': 'OpenClaw · K8s Zero-Downtime Rolling Upgrade',
  'Claude Code · SQL 注入参数化重构': 'Claude Code · SQLi Parameterized Query Refactor',
  'OpenClaw · Redis 集群脑裂排查': 'OpenClaw · Redis Cluster Split-Brain Diagnosis',
  'OpenClaw · PostgreSQL 死锁索引优化': 'OpenClaw · PostgreSQL Deadlock Index Tuning',
  'Claude Code · gRPC 幂等退避重试策略': 'Claude Code · gRPC Idempotent Backoff Policy',
  'OpenClaw · OpenTelemetry 跨线程上下文传播': 'OpenClaw · OpenTelemetry Context Propagation',
  'Claude Code · E2E 偶发超时排查': 'Claude Code · Flaky E2E Timeout Triage',
  'OpenClaw · Kafka 消费组频繁 Rebalance 调优': 'OpenClaw · Kafka Consumer Rebalance Tuning',
  '示例审核插件 - 贡献扩展字段并在审批前校验（默认停用）':
    'Sample reviewer plugin - adds custom review fields and pre-approval validation (disabled by default)',
  '线上 payment-api 滚动发布出现 502 抖动（值班 SRE: [REDACTED_EMAIL] / [REDACTED_PHONE]）。请排查 k8s/deployment.yaml 并给出零停机修复方案。':
    'Production payment-api hit 502 spikes during rolling deploy (On-call SRE: [REDACTED_EMAIL] / [REDACTED_PHONE]). Please inspect k8s/deployment.yaml and propose a zero-downtime fix.',
  '我先使用 read_file 读取 k8s/deployment.yaml 检查探针与生命周期钩子，再通过 bash 查看 Pod 终止事件时间线。':
    'I will inspect k8s/deployment.yaml with read_file to check probes and lifecycle hooks, then run bash to inspect the Pod termination timeline.',
  '根因定位很清楚！请直接给出可落地的 deployment.yaml 零停机修复清单。':
    'Root cause is clear! Please provide the actionable zero-downtime deployment.yaml checklist.',
  '建议修改 k8s/deployment.yaml 配置：\n1. 将 readinessProbe.periodSeconds 改为 5 秒；\n2. 设置 terminationGracePeriodSeconds: 30；\n3. 重新执行 kubectl apply 即可。':
    'Recommended k8s/deployment.yaml changes:\n1. Set readinessProbe.periodSeconds to 5s;\n2. Set terminationGracePeriodSeconds: 30;\n3. Re-run kubectl apply.',
  '请审计 order_repo.py 中的动态 SQL 拼接并改为参数化查询。':
    'Please audit dynamic SQL concatenation in order_repo.py and convert to parameterized queries.',
  '已定位字符串格式化拼接风险，并替换为 SQLAlchemy 绑定参数查询。':
    'Identified string-formatting SQL risk and replaced with SQLAlchemy bound parameters.',
  '排查 Redis Cluster 主从切换期间锁丢失问题。':
    'Investigate distributed lock loss during Redis Cluster failover.',
  '建议使用 Redlock 或迁移至 etcd 强一致租约锁，并启用 min-replicas-to-write。':
    'Recommend migrating to etcd lease locks or enabling min-replicas-to-write.',
  // Example reviewer plugin fields, options, and validation messages
  '数据质量': 'Data Quality',
  '使用场景': 'Use Case',
  '需要复查': 'Needs Follow-up',
  '请输入该会话的使用场景': 'Enter the use case for this session',
  '请输入使用场景': 'Enter use case',
  '优秀': 'Excellent',
  '良好': 'Good',
  '一般': 'Fair',
  '较差': 'Poor',
  '会话消息不足 2 条，不允许通过': 'Session has fewer than 2 messages and cannot be approved',
  '数据质量标记为「较差」时不允许直接通过': 'Cannot approve directly when Data Quality is marked as Poor',
  // Curated & Demo session messages in harvestflow.db
  '生产集群 redis-sentinel 节点偶发 OOMKilled，排查 memory limit 并修复':
    'Production cluster redis-sentinel nodes hit intermittent OOMKilled; inspect memory limits and fix',
  '已分析 Sentinel 与 Redis 实例日志，正在通过工具查询节点资源分配与历史内存消耗。':
    'Analyzed Sentinel and Redis instance logs; querying node resource allocation and historical memory usage via tools.',
  '确认 Sentinel 监控节点在全量同步时瞬时峰值达到 508MiB 突破 limit 限制。我已生成补丁将资源限制调整为 1GiB。':
    'Confirmed Sentinel monitoring nodes spiked to 508MiB during full sync, exceeding the memory limit. Generated a patch raising the limit to 1GiB.',
  '已将内存上限提升至 1Gi 并配置了 cgroup v2 memory.high 软限制告警阈值，观察 5 分钟后 3 个 Sentinel Pod 均处于 Healthy 状态。':
    'Raised memory limit to 1Gi and configured cgroup v2 memory.high soft-limit alert threshold; all 3 Sentinel Pods remained Healthy after 5 minutes of observation.',
  'FastAPI 批量抓取任务中 aiohttp.ClientSession 出现连接池泄漏，请重构':
    'Connection pool leak in aiohttp.ClientSession during FastAPI batch crawling tasks; please refactor',
  '排查发现每次请求循环都新建了 aiohttp.ClientSession() 而没有放入 async with 上下文，导致 underlying connector 未被关闭。建议在 FastAPI lifespan 中创建全局持久连接池并注入 request.state。':
    'Investigation showed a new aiohttp.ClientSession() was instantiated per request loop outside an async with context, leaving the underlying connector unclosed. Recommend creating a global persistent connection pool in FastAPI lifespan and injecting it via request.state.',
  '检查用户输入搜索接口是否存在 SQL 注入风险并给出修复方案':
    'Audit the user search endpoint for SQL injection risks and provide a remediation plan',
  '原代码使用 string concatenation 拼接 SQL 语句：\n\n这会导致严重的 SQL 注入攻击漏洞，建议改用参数化绑定。':
    'The original code used string concatenation to build SQL queries:\n\nThis introduces a critical SQL injection vulnerability; recommend switching to parameterized bound queries.',
  '为高并发 SQLite 提供读写分离与 WAL 索引优化方案':
    'Provide a read/write separation and WAL index optimization plan for high-concurrency SQLite',
  '推荐方案：1 个专属写连接（配备 RLock 排他锁）+ 4~8 个只读连接池。开启 WAL 模式、normal 同步、64MB 缓存，并针对高频 status 和 created_at 建立复合索引。':
    'Recommended architecture: 1 dedicated write connection (with RLock exclusive lock) + a pool of 4-8 read-only connections. Enable WAL mode, NORMAL synchronous mode, 64MB cache, and create a composite index on high-frequency status and created_at columns.',
  '用户反馈登录接口偶发 500，请排查并修复':
    'Users reported intermittent 500 errors on the login endpoint; please investigate and fix',
  '我先查看 src/auth/login.py 的错误日志': 'I will inspect the error logs for src/auth/login.py first',
  "日志显示 'NoneType' object has no attribute 'id'": "Logs show 'NoneType' object has no attribute 'id'",
  '定位到 user 查询可能返回 None，需要加空值校验': 'Identified that the user query can return None; null check is required',
  '已修改 src/auth/login.py，增加 user is None 分支': 'Updated src/auth/login.py to handle the user is None branch',
  '请补充回归测试': 'Please add regression tests',
  '在 tests/test_login.py 新增空用户用例': 'Added null-user test case in tests/test_login.py',
  '运行 pytest -k login': 'Running pytest -k login',
  '还有其他调用点吗？': 'Are there any other call sites?',
  'grep 到 src/api/session.py 也有同样问题，一并修复':
    'Found the same issue in src/api/session.py via grep and fixed it as well',
  '全部用例通过，共 12 passed': 'All test cases passed (12 passed)',
  '总结：修复两处空指针并补充回归测试': 'Summary: Fixed two null-pointer dereferences and added regression tests',
  '帮我分析登录偶发 500 的根因': 'Help me analyze the root cause of intermittent 500 errors on login',
  '根因：查询用户可能为 None，已修复 src/auth/login.py 并补充回归测试':
    'Root cause: user query may return None; fixed src/auth/login.py and added regression tests',
  // OpenClaw session assistant replies
  '现在让我更新 MEMORY.md 技能清单：': 'Now let me update the skill list in MEMORY.md:',
  '📝 收到指令！开始执行智能技能搜索...\n\n让我先提取核心关键词并搜索相关技能：':
    '📝 Received instructions! Starting intelligent skill search...\n\nLet me extract core keywords and search for relevant skills first:',
  '很好！让我继续搜索更多相关技能：': 'Great! Let me continue searching for more related skills:',
  '📝 收到！开始安装3个核心技能...': '📝 Received! Starting installation of the 3 core skills...',
  '遇到速率限制，让我继续安装其他技能：': 'Hit rate limit; let me continue installing the remaining skills:',
  '第一个技能安装成功！让我继续安装其他技能：': 'First skill installed successfully! Continuing with the remaining skills:',
  '让我查看已安装的技能和更新 TOOLS.md：': 'Let me check the installed skills and update TOOLS.md:',
  '📝 收到指令！开始整理记忆并缩减上下文...\n\n首先让我检查当前 memory 目录的状态：':
    '📝 Received instructions! Starting memory organization and context compaction...\n\nFirst let me inspect the current memory directory status:',
  '现在我来精简这些文件。首先创建 archive 目录并精简 MEMORY.md：':
    'Now I will compact these files. First, creating the archive directory and compacting MEMORY.md:',
  '将原 MEMORY.md 归档：': 'Archiving the original MEMORY.md:',
  '现在写入精简版 MEMORY.md：': 'Writing the compacted MEMORY.md:',
  '现在归档并精简 LEARNINGS.md：': 'Archiving and compacting LEARNINGS.md:',
  '检查精简效果：': 'Checking compaction results:',
  '📝 收到每日自我检查指令！\n\n让我先回顾今日工作并搜索相关记忆：':
    '📝 Received daily self-check instructions!\n\nLet me review today’s work and search related memory records first:',
  '📝 收到记忆整理任务！开始执行...\n\n## 步骤1：检索历史记忆':
    '📝 Received memory organization task! Executing...\n\n## Step 1: Retrieve historical memories',
  '## 步骤2：检查并更新 LEARNINGS.md': '## Step 2: Check and update LEARNINGS.md',
  'LEARNINGS.md 已有较新内容，无需大幅更新。让我检查 ERRORS.md：':
    'LEARNINGS.md is already up to date. Let me check ERRORS.md:',
  '## 步骤3：归档重要知识到 KnowFlow': '## Step 3: Archive key knowledge into KnowFlow',
  '## 步骤4：精简 memory/MEMORY.md': '## Step 4: Compact memory/MEMORY.md',
  '将当前 MEMORY.md 归档，然后创建精简版：': 'Archiving current MEMORY.md and creating the compacted version:',
  '将旧版完整内容归档：': 'Archiving the full previous version:',
  '检查最终精简效果：': 'Checking final compaction results:',
  '现在让我更新MEMORY.md和TOOLS.md，记录本周技能搜索结果：':
    'Now let me update MEMORY.md and TOOLS.md to record this week’s skill search results:',
};

const DYNAMIC_EN_MAP = DYNAMIC_EN_EXACT;

export const DYNAMIC_ZH_EXACT: Record<string, string> = {
  // Plugin names & authors
  'collectors/openclaw:name': 'OpenClaw 采集器',
  'curators/openclaw:name': 'OpenClaw 清洗器',
  openclaw: 'OpenClaw 采集器',
  pii_cleaner: 'PII 隐私清洗器',
  'Reviewer Example': '自动评分审核器',
  'Infisical Service': 'Infisical 密钥服务',
  'HarvestFlow Team': 'HarvestFlow 团队',
  HarvestFlow: 'HarvestFlow 团队',
  default: '默认人工审核器',
  // Plugin descriptions from plugin.yaml
  'OpenClaw Agent session collector - reads from local OpenClaw session files':
    'OpenClaw 会话采集器 — 从本地 OpenClaw 会话目录自动读取轨迹',
  'OpenClaw curator - AI-powered quality assessment':
    'OpenClaw 智能清洗器 — 基于大模型的轨迹质量评分与高价值筛选',
  'PII & Secret Redactor - automatically masks API keys, bearer tokens, phone numbers and emails':
    'PII 与密钥脱敏清洗器 — 自动掩码 API 密钥、Bearer Token、手机号与邮箱',
  'Infisical SDK integration for secrets management': 'Infisical 密钥管理服务集成',
  'Default human reviewer - basic review interface': '默认人工审核器 — 标准会话审核工作台',
  // Task types
  k8s_deployment_fix: 'K8s 部署排障',
  memory_leak_fix: '内存泄漏修复',
  sqlite_optimization: 'SQLite 性能优化',
  security_audit: '安全审计',
  conversation: '通用对话',
  coding: '代码开发',
  debugging: '缺陷调试',
  testing: '测试验证',
  refactoring: '代码重构',
  feature_dev: '功能研发',
  bug_fix: '缺陷修复',
  bugfix: '缺陷修复',
  feature: '新特性',
  performance_tuning: '性能优化',
  arch_design: '架构设计',
  code_generation: '代码生成',
  // Agent roles
  devops_agent: 'SRE 运维专家',
  sre_agent: 'SRE 运维专家',
  code_refactor_agent: '代码重构专家',
  security_agent: '安全审计专家',
  db_architect: '数据库架构师',
  dba_agent: '数据库管理员',
  arch_agent: '系统架构师',
  qa_agent: '质量测试工程师',
  data_eng: '数据工程师',
  backend_dev: '后端研发',
  frontend_dev: '前端研发',
  req_analyst: '需求分析',
  tester: '测试工程师',
  qa_ops: '质量测试',
  security_auditor: '安全审计员',
  assistant: 'AI 助手',
  unknown: '未分类',
  'openclaw-tui': 'OpenClaw 终端助手',
  codex: 'Codex 编程助手',
  coding_assistant: '编程助手',
  'OpenClaw · sre_agent': 'OpenClaw · SRE 运维专家',
  'Claude Code · backend_dev': 'Claude Code · 后端研发',
  'OpenClaw · arch_agent': 'OpenClaw · 系统架构师',
  'OpenClaw · dba_agent': 'OpenClaw · 数据库专家',
  'Claude Code · qa_agent': 'Claude Code · 质量测试',
  'OpenClaw · data_eng': 'OpenClaw · 数据工程师',
  // Session & Export Tags & Audit Log Details
  security: '安全审计',
  sqli: 'SQL 注入',
  sql: 'SQL 查询',
  python: 'Python',
  asyncio: '异步并发',
  fastapi: 'FastAPI',
  'memory-leak': '内存泄漏',
  k8s: 'K8s 容器',
  production: '生产环境',
  oom: '内存溢出',
  troubleshooting: '故障排查',
  sqlite: 'SQLite',
  wal: 'WAL 日志',
  concurrency: '并发控制',
  database: '数据库',
  'bug-fix': '缺陷修复',
  review: '代码审查',
  deployment: '部署运维',
  config: '配置管理',
  optimization: '性能优化',
  refactor: '代码重构',
  documentation: '文档规范',
  'smoke-test': '冒烟测试',
  'codex-smoke-reject': 'Codex 冒烟测试驳回',
  'codex-smoke-approve': 'Codex 冒烟测试通过',
  'plugin-smoke': '插件冒烟测试',
  'plugin-ok': '插件校验通过',
  'demo-reject': '演示测试驳回',
  Test: '测试审核通过',
  // Backend FastAPI error messages
  'No sessions found with the given filters': '未找到符合筛选条件的会话',
  'Session not found': '会话不存在',
  'Failed to import session': '导入会话失败',
  'Export file not found': '导出文件不存在',
  'No files selected': '未选择任何文件',
  'No valid export files found': '未找到有效的导出文件',
  'curator disabled': '清洗器已禁用',
  'collector disabled': '采集器已禁用',
  'Folder path is required': '目录路径不能为空',
  'Folder does not exist': '目录不存在',
  'File not found': '文件不存在',
  'Invalid status': '状态无效',
  'Cannot disable the last active reviewer': '不能停用最后一个启用中的审核器',
};

const DYNAMIC_ZH_MAP = DYNAMIC_ZH_EXACT;

const ZH_PHRASE_REPLACEMENTS: Array<[string, string]> = [
  ['所有虾做自我介绍', 'All agents, please introduce yourselves'],
  ['大家好，我是**需求虾**', 'Hello everyone, I am the **Requirements Analyst Agent**'],
  ['产品需求分析师', 'Product & Requirements Analyst'],
  ['需求虾可执行摘要', 'Requirements Analyst Executive Summary'],
  ['需求虾学习记忆库', 'Requirements Analyst Learning Memory'],
  ['需求虾工具使用笔记', 'Requirements Analyst Tool Usage Notes'],
  ['需求虾错误日志与问题追踪', 'Requirements Analyst Error Log & Issue Tracker'],
  ['需求虾成功经验与最佳实践', 'Requirements Analyst Best Practices'],
  ['需求虾可复用经验摘要', 'Requirements Analyst Reusable Lessons'],
  ['需求虾核心经验', 'Requirements Analyst Core Lesson'],
  ['需求虾', 'Requirements Agent'],
  ['总管虾', 'Coordinator Agent'],
  ['总负责人反馈', 'Lead Coordinator Feedback'],
  ['执行每周技能搜索', 'Run weekly skill search'],
  ['执行每日自我检查', 'Run daily self-check'],
  ['每周技能搜索总结', 'Weekly Skill Search Summary'],
  ['每周技能搜索完成', 'Weekly Skill Search Complete'],
  ['技能搜索结果汇总', 'Skill Search Results Summary'],
  ['自动进化指令', 'Auto-Evolution Directive'],
  ['自动进化完成通知', 'Auto-Evolution Completion Notice'],
  ['自动进化系统初始化', 'Auto-Evolution System Initialization'],
  ['自动进化系统启动', 'Auto-Evolution System Started'],
  ['记忆整理完成汇报', 'Memory Compaction Report'],
  ['记忆整理完成', 'Memory Compaction Complete'],
  ['记忆整理任务', 'Memory Compaction Task'],
  ['整理记忆 / 缩减上下文 - 立即执行', 'Compact Memory / Reduce Context - Execute Immediately'],
  ['核心能力', 'Core Capabilities'],
  ['近期完成任务', 'Recently Completed Tasks'],
  ['参与过的任务', 'Completed Tasks'],
  ['关键决策', 'Key Decisions'],
  ['已安装技能效果评估', 'Installed Skills Evaluation'],
  ['已安装技能', 'Installed Skills'],
  ['待安装技能', 'Pending Skills'],
  ['技能状态', 'Skill Status'],
  ['核心经验', 'Core Lessons'],
  ['学习经验', 'Lessons Learned'],
  ['学习记录列表', 'Learning Records'],
  ['错误记录列表', 'Error Records'],
  ['暂无错误记录', 'No errors recorded'],
  ['功能规格说明书编写', 'Feature specification authoring'],
  ['功能规格说明书', 'Feature Specification'],
  ['产品需求文档', 'Product Requirements Document'],
  ['需求分析核心技能', 'Core requirements analysis skill'],
  ['需求分析', 'Requirements Analysis'],
  ['功能规划', 'Feature Planning'],
  ['原型设计', 'Prototyping'],
  ['验收标准', 'Acceptance Criteria'],
  ['需求确认', 'Requirements Alignment'],
  ['文档同步', 'Documentation Sync'],
  ['变更管理', 'Change Management'],
  ['架构设计', 'Architecture Design'],
  ['技术规格', 'Technical Specification'],
  ['向后兼容', 'Backward Compatibility'],
  ['最佳实践', 'Best Practices'],
  ['最后更新', 'Last Updated'],
  ['已安装', 'Installed'],
  ['待重试', 'Pending Retry'],
  ['速率限制', 'Rate Limited'],
  ['等待限流解除', 'Waiting for rate limit reset'],
  ['限流中', 'Rate limited'],
  ['未使用', 'Unused'],
  ['优秀', 'Excellent'],
  ['良好', 'Good'],
  ['一般', 'Fair'],
  ['较差', 'Poor'],
  ['待办事项', 'Todo Items'],
  ['待办', 'Todo'],
  ['状态', 'Status'],
  ['备注', 'Notes'],
  ['用途', 'Purpose'],
  ['技能名', 'Skill'],
  ['技能', 'Skill'],
  ['优先级', 'Priority'],
  ['核心', 'Core'],
  ['辅助', 'Auxiliary'],
  ['扩展', 'Extended'],
  ['用户', 'User '],
  ['收到', 'Acknowledged'],
  ['完成', 'Completed'],
];

const CJK_CHAR_RE = /[\u3400-\u9fff\uf900-\ufaff]/;

const sanitizeChineseForEnglish = (input: string): string => {
  let out = input;
  for (const [zh, en] of ZH_PHRASE_REPLACEMENTS) {
    if (out.includes(zh)) {
      out = out.split(zh).join(en);
    }
  }
  out = out
    .replace(/，/g, ', ')
    .replace(/。/g, '. ')
    .replace(/：/g, ': ')
    .replace(/；/g, '; ')
    .replace(/！/g, '! ')
    .replace(/？/g, '? ')
    .replace(/（/g, ' (')
    .replace(/）/g, ') ')
    .replace(/「/g, '"')
    .replace(/」/g, '"')
    .replace(/『/g, '"')
    .replace(/』/g, '"')
    .replace(/【/g, '[')
    .replace(/】/g, ']')
    .replace(/、/g, ', ')
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'");

  if (CJK_CHAR_RE.test(out)) {
    out = out.replace(/[\u3400-\u9fff\uf900-\ufaff]+/g, ' ').replace(/[\u3000-\u303f\uff00-\uffef]+/g, ' ');
    out = out.replace(/[ \t]{2,}/g, ' ').trim();
  }
  return out || 'Translated session content';
};

const ACRONYM_MAP: Record<string, string> = {
  sre: 'SRE',
  k8s: 'K8s',
  db: 'DB',
  sql: 'SQL',
  api: 'API',
  pii: 'PII',
  qa: 'QA',
  llm: 'LLM',
  sft: 'SFT',
  dpo: 'DPO',
  io: 'I/O',
};

const formatSnakeCaseToTitle = (slug: string): string =>
  slug
    .split('_')
    .map((word) => ACRONYM_MAP[word.toLowerCase()] || word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

export const translateDynamicText = (text: string | undefined | null, locale: Locale): string => {
  if (!text) return '';
  const trimmed = text.trim();
  if (/^oc_[0-9a-f]{16,}$/i.test(trimmed)) {
    return locale === 'zh' ? 'OpenClaw 助手' : 'OpenClaw Agent';
  }
  if (locale === 'en') {
    if (DYNAMIC_EN_MAP[text]) {
      return DYNAMIC_EN_MAP[text];
    }
    if (DYNAMIC_EN_MAP[trimmed]) {
      return DYNAMIC_EN_MAP[trimmed];
    }
    if (/^[a-z0-9]+(_[a-z0-9]+)+$/.test(trimmed)) {
      return formatSnakeCaseToTitle(trimmed);
    }
    if (CJK_CHAR_RE.test(text)) {
      return sanitizeChineseForEnglish(text);
    }
    return text;
  }
  if (locale === 'zh') {
    if (DYNAMIC_ZH_MAP[text]) {
      return DYNAMIC_ZH_MAP[text];
    }
    if (DYNAMIC_ZH_MAP[trimmed]) {
      return DYNAMIC_ZH_MAP[trimmed];
    }
    if (/^score\s+(\d+(?:\.\d+)?)\s*(>=|<=|>|<|==)\s*threshold\s+(\d+(?:\.\d+)?)$/i.test(trimmed)) {
      return trimmed.replace(
        /^score\s+(\d+(?:\.\d+)?)\s*(>=|<=|>|<|==)\s*threshold\s+(\d+(?:\.\d+)?)$/i,
        '评分 $1 $2 阈值 $3'
      );
    }
    if (/^Plugin\s+'([^']+)'\s+not\s+found$/i.test(trimmed)) {
      return trimmed.replace(/^Plugin\s+'([^']+)'\s+not\s+found$/i, '未找到插件 "$1"');
    }
    if (/^Invalid\s+status\s+transition:\s*(.+)$/i.test(trimmed)) {
      return trimmed.replace(/^Invalid\s+status\s+transition:\s*(.+)$/i, '非法的状态流转：$1');
    }
  }
  return text;
};

export interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  t: (keyOrZh: string, enOrVars?: string | Record<string, string | number>) => string;
  td: (text: string | undefined | null) => string;
}

const LanguageContext = createContext<I18nContextValue | null>(null);

const formatWithLocale = (
  locale: Locale,
  keyOrZh: string,
  enOrVars?: string | Record<string, string | number>
): string => {
  if (typeof enOrVars === 'string') {
    return locale === 'zh' ? keyOrZh : enOrVars;
  }
  const template = MESSAGES[locale]?.[keyOrZh] ?? keyOrZh;
  if (enOrVars && typeof enOrVars === 'object') {
    return Object.entries(enOrVars).reduce(
      (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
      template
    );
  }
  return template;
};

export const LanguageProvider: React.FC<{ children: React.ReactNode; initialLocale?: Locale }> = ({
  children,
  initialLocale,
}) => {
  const parent = useContext(LanguageContext);
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale ?? getStoredLocale());

  const applyLocale = useCallback((next: Locale) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(STORAGE_KEY, next);
      }
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent<Locale>(LOCALE_CHANGE_EVENT, { detail: next }));
      }
    } catch {
      // ignore storage errors
    }
    dayjs.locale(next === 'zh' ? 'zh-cn' : 'en');
    setLocaleState(next);
  }, []);

  const toggleLocale = useCallback(() => {
    const current = getStoredLocale();
    const next: Locale = (locale || current) === 'zh' ? 'en' : 'zh';
    applyLocale(next);
  }, [locale, applyLocale]);

  useEffect(() => {
    dayjs.locale(locale === 'zh' ? 'zh-cn' : 'en');
  }, [locale]);

  useEffect(() => {
    const handler = (event: Event) => {
      const custom = event as CustomEvent<Locale>;
      if (custom.detail === 'zh' || custom.detail === 'en') {
        setLocaleState(custom.detail);
      }
    };
    window.addEventListener(LOCALE_CHANGE_EVENT, handler);
    return () => window.removeEventListener(LOCALE_CHANGE_EVENT, handler);
  }, []);

  const t = useCallback(
    (keyOrZh: string, enOrVars?: string | Record<string, string | number>) =>
      formatWithLocale(locale, keyOrZh, enOrVars),
    [locale]
  );

  const td = useCallback(
    (text: string | undefined | null) => translateDynamicText(text, locale),
    [locale]
  );

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale: applyLocale,
      toggleLocale,
      t,
      td,
    }),
    [locale, applyLocale, toggleLocale, t, td]
  );

  if (parent && initialLocale === undefined) {
    return <>{children}</>;
  }

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export const useI18n = (): I18nContextValue => {
  const ctx = useContext(LanguageContext);
  const [fallbackLocale, setFallbackLocale] = useState<Locale>(() => getStoredLocale());

  useEffect(() => {
    if (ctx) return;
    const handler = (event: Event) => {
      const custom = event as CustomEvent<Locale>;
      if (custom.detail === 'zh' || custom.detail === 'en') {
        setFallbackLocale(custom.detail);
      }
    };
    window.addEventListener(LOCALE_CHANGE_EVENT, handler);
    return () => window.removeEventListener(LOCALE_CHANGE_EVENT, handler);
  }, [ctx]);

  const setLocale = useCallback((next: Locale) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(STORAGE_KEY, next);
      }
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent<Locale>(LOCALE_CHANGE_EVENT, { detail: next }));
      }
    } catch {
      // ignore storage errors
    }
    dayjs.locale(next === 'zh' ? 'zh-cn' : 'en');
    setFallbackLocale(next);
  }, []);

  const toggleLocale = useCallback(() => {
    const next: Locale = fallbackLocale === 'zh' ? 'en' : 'zh';
    setLocale(next);
  }, [fallbackLocale, setLocale]);

  const t = useCallback(
    (keyOrZh: string, enOrVars?: string | Record<string, string | number>) =>
      formatWithLocale(fallbackLocale, keyOrZh, enOrVars),
    [fallbackLocale]
  );

  const td = useCallback(
    (text: string | undefined | null) => translateDynamicText(text, fallbackLocale),
    [fallbackLocale]
  );

  if (ctx) {
    return ctx;
  }

  return {
    locale: fallbackLocale,
    setLocale,
    toggleLocale,
    t,
    td,
  };
};
