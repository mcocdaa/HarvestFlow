import { statusPalette } from '../theme/flow-design-theme';
import { STATUS_LABELS } from '../constants/display';
import type { SessionStatus } from '../types';

export const getStatusColor = (status?: string): string => {
  return statusPalette[status ?? ''] || statusPalette.raw;
};

export const getStatusLabel = (status?: string): string => {
  if (!status) return '-';
  return STATUS_LABELS[status as keyof typeof STATUS_LABELS] || status;
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
