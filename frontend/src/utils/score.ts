import { scorePalette } from '../theme/flow-design-theme';
import { getStoredLocale } from '../i18n';
import type { Locale } from '../i18n';

const SCORE_LABELS = ['不可用', '较差', '一般', '良好', '优秀'];
const SCORE_LABELS_EN = ['Unusable', 'Poor', 'Fair', 'Good', 'Excellent'];
const SCORE_TAGS = ['差', '差', '中', '优', '优'];
const SCORE_TAGS_EN = ['Low', 'Low', 'Mid', 'High', 'High'];

export const getScoreLabel = (score: number, locale: Locale = getStoredLocale()): string => {
  const list = locale === 'en' ? SCORE_LABELS_EN : SCORE_LABELS;
  return list[score - 1] || (locale === 'en' ? 'Unknown' : '未知');
};

export const getScoreColor = (score: number): string => {
  return scorePalette[score - 1] || '#CBD5E1';
};

export const getScoreTag = (score: number, locale: Locale = getStoredLocale()): string => {
  const list = locale === 'en' ? SCORE_TAGS_EN : SCORE_TAGS;
  return list[score - 1] || (locale === 'en' ? 'Unknown' : '未知');
};

export const getScoreLabels = (locale: Locale = getStoredLocale()): string[] =>
  locale === 'en' ? SCORE_LABELS_EN : SCORE_LABELS;

export const scoreLabels = SCORE_LABELS;
