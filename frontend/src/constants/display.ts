import type { SessionStatus } from '../types';

export const STATUS_LABELS: Record<SessionStatus, string> = {
  raw: '待清洗',
  curated: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
};

export const STATUS_OPTIONS: { value: SessionStatus; label: string }[] = [
  { value: 'raw', label: '待清洗' },
  { value: 'curated', label: '待审核' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已拒绝' },
];

export const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: 'recent', label: '最新优先' },
  { value: 'oldest', label: '最早优先' },
];

export const ROLE_LABELS: Record<string, string> = {
  user: '用户',
  assistant: 'AI 助手',
  system: '系统',
};

export const PLUGIN_TYPE_LABELS: Record<string, string> = {
  collectors: '采集器',
  curators: '清洗器',
  reviewers: '审核器',
  services: '服务',
  collector: '采集器',
  curator: '清洗器',
  reviewer: '审核器',
  service: '服务',
  unknown: '未知',
};

export const PLUGIN_TYPE_COLORS: Record<string, string> = {
  collectors: '#2563EB',
  curators: '#8B5CF6',
  reviewers: '#10B981',
  services: '#F59E0B',
};

export const PLUGIN_TYPE_ORDER = ['collectors', 'curators', 'reviewers', 'services'];

export const EXPORT_FORMAT_LABELS: Record<string, string> = {
  sharegpt: 'ShareGPT',
  alpaca: 'Alpaca',
  openai: 'OpenAI Messages',
  dpo: 'DPO 对抗偏好对',
};

export const AUDIT_ACTION_LABELS: Record<string, string> = {
  modify: '修改',
  approve: '通过',
  reject: '拒绝',
  auto_approve: '自动通过',
};

export const AUDIT_ACTION_COLORS: Record<string, string> = {
  modify: 'default',
  approve: 'success',
  reject: 'error',
  auto_approve: 'processing',
};

export const OPERATOR_LABELS: Record<string, string> = {
  user: '人工',
  system: '系统',
};

export const DEFAULT_AGENT_ROLES = ['backend_dev', 'req_analyst', 'frontend_dev', 'tester'];

export const DEFAULT_TASK_TYPES = ['debugging', 'coding', 'testing', 'refactoring', 'feature_dev'];
