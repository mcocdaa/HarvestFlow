import React from 'react';
import { Flex, Typography } from 'antd';

interface PageHeaderProps {
  title: React.ReactNode;
  description?: React.ReactNode;
  tags?: React.ReactNode;
  extra?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, description, tags, extra }) => {
  return (
    <Flex className="page-header" justify="space-between" align="flex-start" gap={16} wrap>
      <div className="page-header-main">
        <Flex align="center" gap={8} wrap>
          <Typography.Title level={3} className="page-header-title">
            {title}
          </Typography.Title>
          {tags}
        </Flex>
        {description && (
          <Typography.Text type="secondary" className="page-header-description">
            {description}
          </Typography.Text>
        )}
      </div>
      {extra && (
        <Flex align="center" gap={8} wrap className="page-header-extra">
          {extra}
        </Flex>
      )}
    </Flex>
  );
};

export default PageHeader;
