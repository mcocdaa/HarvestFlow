import React from 'react';
import { Empty, Typography } from 'antd';

interface EmptyStateProps {
  description?: React.ReactNode;
  children?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({ description = '暂无数据', children }) => {
  return (
    <div className="empty-state">
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={<Typography.Text type="secondary">{description}</Typography.Text>}
      >
        {children}
      </Empty>
    </div>
  );
};

export default EmptyState;
