import { describe, it, expect } from 'vitest';
import {
  formatDateTime,
  getAllowedStatusTransitions,
  getScoreLabel,
  getScoreTag,
  getStatusLabel,
  parseJsonSafe,
  truncateSessionId,
} from '../utils';

describe('display utils', () => {
  it('should map status labels to Chinese', () => {
    expect(getStatusLabel('raw')).toBe('待清洗');
    expect(getStatusLabel('curated')).toBe('待审核');
    expect(getStatusLabel('approved')).toBe('已通过');
    expect(getStatusLabel('rejected')).toBe('已拒绝');
    expect(getStatusLabel(undefined)).toBe('-');
  });

  it('should only allow valid status transitions', () => {
    expect(getAllowedStatusTransitions('raw')).toEqual(['curated']);
    expect(getAllowedStatusTransitions('curated')).toEqual(['approved', 'rejected']);
    expect(getAllowedStatusTransitions('approved')).toEqual(['rejected']);
    expect(getAllowedStatusTransitions('rejected')).toEqual(['approved']);
    expect(getAllowedStatusTransitions('unknown')).toEqual([]);
  });

  it('should map score labels and tags', () => {
    expect(getScoreLabel(1)).toBe('不可用');
    expect(getScoreLabel(5)).toBe('优秀');
    expect(getScoreTag(3)).toBe('中');
  });

  it('should format date time', () => {
    expect(formatDateTime('2026-01-02T03:04:05Z')).toMatch(/2026-01-02/);
    expect(formatDateTime(null)).toBe('-');
    expect(formatDateTime('not-a-date')).toBe('not-a-date');
  });

  it('should truncate long session ids', () => {
    expect(truncateSessionId('12345678901234567890')).toBe('123456789012...7890');
  });

  it('should parse json safely', () => {
    expect(parseJsonSafe<{ a: number }>('{"a":1}')).toEqual({ a: 1 });
    expect(parseJsonSafe('{invalid')).toBeNull();
    expect(parseJsonSafe(null)).toBeNull();
  });
});
