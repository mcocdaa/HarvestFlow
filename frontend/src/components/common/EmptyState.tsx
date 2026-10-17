import React from 'react';
import { Empty, Typography } from 'antd';
import { useI18n } from '../../i18n';

interface EmptyStateProps {
  description?: React.ReactNode;
  children?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({ description, children }) => {
  const { t } = useI18n();
  return (
    <div className="empty-state">
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={<Typography.Text type="secondary">{description ?? t('暂无数据', 'No data')}</Typography.Text>}
      >
        {children}
      </Empty>
    </div>
  );
};

export default EmptyState;
