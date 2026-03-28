const SCORE_LABELS = ['Unusable', 'Poor', 'Acceptable', 'Good', 'Excellent'];
const SCORE_COLORS = ['#EF4444', '#EF4444', '#F59E0B', '#10B981', '#10B981'];
const SCORE_TAGS = ['差', '差', '中', '优', '优'];

export const getScoreLabel = (score: number): string => {
  return SCORE_LABELS[score - 1] || 'Unknown';
};

export const getScoreColor = (score: number): string => {
  return SCORE_COLORS[score - 1] || '#d9d9d9';
};

export const getScoreTag = (score: number): string => {
  return SCORE_TAGS[score - 1] || '未知';
};

export const scoreLabels = SCORE_LABELS;
