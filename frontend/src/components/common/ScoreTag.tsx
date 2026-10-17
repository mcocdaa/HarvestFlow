import React from 'react';
import { Tag } from 'antd';
import { getScoreColor, getScoreLabel, getScoreTag } from '../../utils';
import { useI18n } from '../../i18n';

interface ScoreTagProps {
  score?: number | null;
  showLabel?: boolean;
}

const ScoreTag: React.FC<ScoreTagProps> = ({ score, showLabel = false }) => {
  const { locale } = useI18n();
  if (score === null || score === undefined) {
    return <span className="score-empty">-</span>;
  }
  return (
    <Tag color={getScoreColor(score)} className="score-tag">
      {showLabel ? `${getScoreTag(score, locale)} · ${getScoreLabel(score, locale)}` : score}
    </Tag>
  );
};

export default ScoreTag;
