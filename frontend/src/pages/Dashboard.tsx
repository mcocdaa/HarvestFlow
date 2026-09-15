import React, { useState } from 'react';
import { Button, Card, Col, Empty, Flex, Progress, Row, Space, Table, Tag, Tooltip, Typography, message } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  FolderOutlined,
  ReloadOutlined,
  RightOutlined,
  SyncOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip as ChartTooltip } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { curatorApi, sessionApi, statsApi } from '../services';
import { useAsyncData } from '../hooks';
import { statusPalette } from '../theme/flow-design-theme';
import { CopyText, PageHeader, ScoreTag, StatCard, StatusTag } from '../components';
import { truncateSessionId } from '../utils';
import { formatDateTime } from '../utils/format';
import type { CuratorStatus, Session, Stats } from '../types';

const EMPTY_STATS: Stats = {
  total_sessions: 0,
  raw_sessions: 0,
  approved_sessions: 0,
  rejected_sessions: 0,
  avg_auto_score: 0,
  curated_sessions: 0,
  reviewed_sessions: 0,
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [evaluating, setEvaluating] = useState(false);
  const { data: statsData, loading, reload } = useAsyncData<Stats>(() => statsApi.get());
  const { data: recentData, loading: recentLoading, reload: reloadRecent } = useAsyncData<{
    sessions?: Session[];
  }>(() => sessionApi.getSessions({ page: 1, page_size: 5, sort: 'recent' }));
  const { data: curator, reload: reloadCurator } = useAsyncData<CuratorStatus>(() => curatorApi.getStatus());

  const stats = statsData ?? EMPTY_STATS;
  const recentSessions = recentData?.sessions ?? [];
  const passRate =
    stats.reviewed_sessions > 0
      ? Math.round((stats.approved_sessions / stats.reviewed_sessions) * 100)
      : 0;

  const distribution = [
    { name: '待清洗', value: stats.raw_sessions, color: statusPalette.raw },
    { name: '待审核', value: stats.curated_sessions, color: statusPalette.curated },
    { name: '已通过', value: stats.approved_sessions, color: statusPalette.approved },
    { name: '已拒绝', value: stats.rejected_sessions, color: statusPalette.rejected },
  ].filter((item) => item.value > 0);

  const handleReload = () => {
    reload();
    reloadRecent();
    reloadCurator();
  };

  const handleEvaluateAll = async () => {
    setEvaluating(true);
    try {
      const res = await curatorApi.evaluateAll();
      const result = res.data as { total?: number; high_value?: number; low_value?: number; error?: string };
      if (result.error) {
        message.warning(`自动清洗未执行：${result.error}`);
      } else {
        message.success(`自动清洗完成：共 ${result.total ?? 0} 条，高价值 ${result.high_value ?? 0} 条`);
      }
      handleReload();
    } catch {
      // 拦截器已统一提示
    } finally {
      setEvaluating(false);
    }
  };

  const recentColumns = [
    {
      title: '会话',
      dataIndex: 'session_id',
      key: 'session_id',
      render: (sessionId: string, record: Session) => (
        <Flex vertical gap={2}>
          <Typography.Text ellipsis style={{ maxWidth: 220 }}>
            {record.task_type || '未分类'}
          </Typography.Text>
          <CopyText
            text={sessionId}
            mono
            display={<span style={{ fontSize: 12 }}>{truncateSessionId(sessionId)}</span>}
          />
        </Flex>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <StatusTag status={status} />,
    },
    {
      title: '自动评分',
      dataIndex: 'quality_auto_score',
      key: 'quality_auto_score',
      width: 90,
      render: (score?: number | null) => <ScoreTag score={score} />,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          {formatDateTime(value)}
        </Typography.Text>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="概览"
        description="采集、清洗、审核、导出全流程数据一览"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleReload}>
              刷新
            </Button>
            <Tooltip title="对所有待清洗会话运行清洗器自动评分">
              <Button
                type="primary"
                icon={evaluating ? <SyncOutlined spin /> : <ThunderboltOutlined />}
                loading={evaluating}
                onClick={handleEvaluateAll}
              >
                运行自动清洗
              </Button>
            </Tooltip>
          </Space>
        }
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={5}>
          <StatCard title="会话总数" value={stats.total_sessions} icon={<FolderOutlined />} color="#2563EB" loading={loading} />
        </Col>
        <Col xs={24} sm={12} xl={5}>
          <StatCard
            title="待清洗"
            value={stats.raw_sessions}
            icon={<ClockCircleOutlined />}
            color="#F59E0B"
            loading={loading}
            onClick={() => navigate('/sessions')}
          />
        </Col>
        <Col xs={24} sm={12} xl={5}>
          <StatCard
            title="待审核"
            value={stats.curated_sessions}
            icon={<RightOutlined />}
            color="#8B5CF6"
            loading={loading}
            onClick={() => navigate('/review')}
          />
        </Col>
        <Col xs={24} sm={12} xl={5}>
          <StatCard
            title="已通过"
            value={stats.approved_sessions}
            icon={<CheckCircleOutlined />}
            color="#10B981"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} xl={4}>
          <StatCard
            title="已拒绝"
            value={stats.rejected_sessions}
            icon={<CloseCircleOutlined />}
            color="#EF4444"
            loading={loading}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="状态分布" variant="borderless" style={{ height: '100%' }}>
            {distribution.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无会话数据" style={{ padding: '32px 0' }} />
            ) : (
              <div style={{ height: 280 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distribution}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={70}
                      outerRadius={100}
                      paddingAngle={2}
                      strokeWidth={0}
                    >
                      {distribution.map((item) => (
                        <Cell key={item.name} fill={item.color} />
                      ))}
                    </Pie>
                    <ChartTooltip
                      contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0', fontSize: 13 }}
                    />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 13 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Flex vertical gap={16} style={{ height: '100%' }}>
            <Card title="质量与审核" variant="borderless">
              <Row align="middle" gutter={16}>
                <Col span={10}>
                  <Flex vertical align="center" gap={4}>
                    <Progress
                      type="circle"
                      percent={Math.round((stats.avg_auto_score / 5) * 100)}
                      size={96}
                      strokeColor="#2563EB"
                      format={() => <span style={{ fontSize: 18, fontWeight: 600 }}>{stats.avg_auto_score}</span>}
                    />
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      平均自动评分 / 5
                    </Typography.Text>
                  </Flex>
                </Col>
                <Col span={14}>
                  <Flex vertical gap={12}>
                    <div>
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        审核通过率
                      </Typography.Text>
                      <Progress percent={passRate} strokeColor="#10B981" size="small" />
                    </div>
                    <Flex justify="space-between">
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        已审核
                      </Typography.Text>
                      <Typography.Text strong>{stats.reviewed_sessions}</Typography.Text>
                    </Flex>
                    <Flex justify="space-between">
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        审核队列剩余
                      </Typography.Text>
                      <Typography.Text strong>{stats.curated_sessions}</Typography.Text>
                    </Flex>
                  </Flex>
                </Col>
              </Row>
            </Card>
            <Card title="清洗器" variant="borderless" style={{ flex: 1 }}>
              {curator ? (
                <Flex vertical gap={8}>
                  <Flex justify="space-between" align="center">
                    <Typography.Text type="secondary">运行状态</Typography.Text>
                    <Tag color={curator.enabled ? 'success' : 'error'}>
                      {curator.enabled ? '已启用' : '已禁用'}
                    </Tag>
                  </Flex>
                  <Flex justify="space-between" align="center">
                    <Typography.Text type="secondary">自动通过阈值</Typography.Text>
                    <Typography.Text strong>{curator.auto_approve_threshold} 分</Typography.Text>
                  </Flex>
                  {!curator.enabled && (
                    <Typography.Text type="warning" style={{ fontSize: 12 }}>
                      清洗器当前禁用，自动清洗不会执行，请检查后端配置。
                    </Typography.Text>
                  )}
                </Flex>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无法获取清洗器状态" />
              )}
            </Card>
          </Flex>
        </Col>
      </Row>

      <Card
        title="最近会话"
        variant="borderless"
        style={{ marginTop: 16 }}
        extra={
          <Button type="link" onClick={() => navigate('/sessions')}>
            查看全部 <RightOutlined />
          </Button>
        }
      >
        <Table
          columns={recentColumns}
          dataSource={recentSessions}
          rowKey="session_id"
          loading={recentLoading}
          pagination={false}
          size="middle"
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无会话" /> }}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
