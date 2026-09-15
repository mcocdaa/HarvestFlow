import React from 'react';
import { Tag } from 'antd';
import { getScoreColor, getScoreLabel, getScoreTag } from '../../utils';

interface ScoreTagProps {
  score?: number | null;
  showLabel?: boolean;
}

const ScoreTag: React.FC<ScoreTagProps> = ({ score, showLabel = false }) => {
  if (score === null || score === undefined) {
    return <span className="score-empty">-</span>;
  }
  return (
    <Tag color={getScoreColor(score)} className="score-tag">
      {showLabel ? `${getScoreTag(score)} · ${getScoreLabel(score)}` : score}
    </Tag>
  );
};

export default ScoreTag;
