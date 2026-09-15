import React from 'react';
import { Card, Flex, Typography } from 'antd';

interface StatCardProps {
  title: string;
  value: React.ReactNode;
  suffix?: string;
  icon: React.ReactNode;
  color?: string;
  loading?: boolean;
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  suffix,
  icon,
  color = '#2563EB',
  loading = false,
  onClick,
}) => {
  return (
    <Card
      className={`stat-card${onClick ? ' stat-card-clickable' : ''}`}
      loading={loading}
      onClick={onClick}
      variant="borderless"
    >
      <Flex align="center" gap={16}>
        <div
          className="stat-card-icon"
          style={{ color, backgroundColor: `${color}1A` }}
        >
          {icon}
        </div>
        <div className="stat-card-body">
          <Typography.Text type="secondary" className="stat-card-title">
            {title}
          </Typography.Text>
          <div className="stat-card-value">
            {value}
            {suffix && <span className="stat-card-suffix">{suffix}</span>}
          </div>
        </div>
      </Flex>
    </Card>
  );
};

export default StatCard;
