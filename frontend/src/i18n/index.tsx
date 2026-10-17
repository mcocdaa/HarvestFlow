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

const DYNAMIC_EN_MAP: Record<string, string> = {
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
};

export const translateDynamicText = (text: string | undefined | null, locale: Locale): string => {
  if (!text) return '';
  if (locale === 'en' && DYNAMIC_EN_MAP[text]) {
    return DYNAMIC_EN_MAP[text];
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
