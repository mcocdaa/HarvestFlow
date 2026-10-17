import { statusPalette } from '../theme/flow-design-theme';
import { STATUS_LABELS, STATUS_LABELS_EN } from '../constants/display';
import { getStoredLocale } from '../i18n';
import type { Locale } from '../i18n';
import type { SessionStatus } from '../types';

export const getStatusColor = (status?: string): string => {
  return statusPalette[status ?? ''] || statusPalette.raw;
};

export const getStatusLabel = (status?: string, locale: Locale = getStoredLocale()): string => {
  if (!status) return '-';
  const map = locale === 'en' ? STATUS_LABELS_EN : STATUS_LABELS;
  return map[status as keyof typeof STATUS_LABELS] || status;
};

const STATUS_TRANSITIONS: Record<string, SessionStatus[]> = {
  raw: ['curated'],
  curated: ['approved', 'rejected'],
  approved: ['rejected'],
  rejected: ['approved'],
};

export const getAllowedStatusTransitions = (status?: string): SessionStatus[] => {
  if (!status) return [];
  return STATUS_TRANSITIONS[status] ?? [];
};
