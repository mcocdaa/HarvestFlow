import React from 'react';
import { Tag } from 'antd';
import { getStatusColor, getStatusLabel } from '../../utils';

interface StatusTagProps {
  status?: string;
}

const StatusTag: React.FC<StatusTagProps> = ({ status }) => {
  const color = getStatusColor(status);
  return (
    <Tag color={color} className="status-tag">
      <span className="status-tag-dot" />
      {getStatusLabel(status)}
    </Tag>
  );
};

export default StatusTag;
