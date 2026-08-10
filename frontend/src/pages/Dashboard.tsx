import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { FolderOutlined, CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { statsApi } from '../services';
import type { Stats } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({
    total_sessions: 0,
    raw_sessions: 0,
    approved_sessions: 0,
    rejected_sessions: 0,
    avg_auto_score: 0,
    curated_sessions: 0,
    reviewed_sessions: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await statsApi.get();
      setStats(res.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Dashboard</h1>
      <Row gutter={16}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Total Sessions"
              value={stats.total_sessions || 0}
              prefix={<FolderOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Raw Sessions"
              value={stats.raw_sessions || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#F59E0B' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Approved"
              value={stats.approved_sessions || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#10B981' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Rejected"
              value={stats.rejected_sessions || 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#EF4444' }}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Average Auto Score" loading={loading}>
            <Statistic value={stats.avg_auto_score || 0} precision={1} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Curated Sessions" loading={loading}>
            <Statistic value={stats.curated_sessions || 0} />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Reviewed Sessions" loading={loading}>
            <Statistic value={stats.reviewed_sessions || 0} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
