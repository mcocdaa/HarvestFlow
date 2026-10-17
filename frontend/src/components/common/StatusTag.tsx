import React from 'react';
import { Tag } from 'antd';
import { getStatusColor, getStatusLabel } from '../../utils';
import { useI18n } from '../../i18n';

interface StatusTagProps {
  status?: string;
}

const StatusTag: React.FC<StatusTagProps> = ({ status }) => {
  const { locale } = useI18n();
  const color = getStatusColor(status);
  return (
    <Tag color={color} className="status-tag">
      <span className="status-tag-dot" />
      {getStatusLabel(status, locale)}
    </Tag>
  );
};

export default StatusTag;
