import { scorePalette } from '../theme/flow-design-theme';

const SCORE_LABELS = ['不可用', '较差', '一般', '良好', '优秀'];
const SCORE_TAGS = ['差', '差', '中', '优', '优'];

export const getScoreLabel = (score: number): string => {
  return SCORE_LABELS[score - 1] || '未知';
};

export const getScoreColor = (score: number): string => {
  return scorePalette[score - 1] || '#CBD5E1';
};

export const getScoreTag = (score: number): string => {
  return SCORE_TAGS[score - 1] || '未知';
};

export const scoreLabels = SCORE_LABELS;
