import dayjs from 'dayjs';

export const formatDateTime = (value?: string | null): string => {
  if (!value) return '-';
  const date = dayjs(value);
  return date.isValid() ? date.format('YYYY-MM-DD HH:mm') : value;
};

export const formatTime = (value?: string | null): string => {
  if (!value) return '-';
  const date = dayjs(value);
  return date.isValid() ? date.format('MM-DD HH:mm') : value;
};

export const formatPercent = (value: number): string => `${Math.round(value * 100)}%`;
