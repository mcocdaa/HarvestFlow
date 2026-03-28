import React from 'react';
import { Table, Tag, Button, Typography, Space } from 'antd';
import { EyeOutlined, CopyOutlined, RiseOutlined, MinusOutlined } from '@ant-design/icons';
import { getStatusColor, truncateString, copyToClipboard } from '../../utils';
import type { Session } from '../../types';

const { Text } = Typography;

interface SessionTableProps {
  sessions: Session[];
  loading: boolean;
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number, pageSize: number) => void;
  onViewSession: (session: Session) => void;
}

const SessionTable: React.FC<SessionTableProps> = ({
  sessions,
  loading,
  total,
  page,
  pageSize,
  onPageChange,
  onViewSession,
}) => {
  const getSessionSummary = (sessionId: string): string => {
    const session = sessions.find(s => s.session_id === sessionId);
    if (!session) return sessionId;

    return truncateString(sessionId, 8, 4);
  };

  const getFirstMessageSummary = (sessionId: string): string => {
    const session = sessions.find(s => s.session_id === sessionId);
    if (!session?.task_type) return '无摘要信息';
    return session.task_type;
  };

  const columns = [
    {
      title: '会话摘要',
      dataIndex: 'session_id',
      key: 'summary',
      width: 280,
      fixed: 'left' as const,
      render: (sessionId: string, record: Session) => (
        <div className="session-summary">
          <div className="summary-title" onClick={() => onViewSession(record)}>
            {getFirstMessageSummary(sessionId)}
          </div>
          <Text className="session-id" onClick={() => copyToClipboard(sessionId)}>
            {getSessionSummary(sessionId)} <CopyOutlined style={{ fontSize: 12, marginLeft: 4 }} />
          </Text>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <div className="status-indicator">
          <div className="status-bar" style={{ backgroundColor: getStatusColor(status) }} />
          <span className="status-text">{status}</span>
        </div>
      ),
    },
    {
      title: '自动评分',
      dataIndex: 'quality_auto_score',
      key: 'quality_auto_score',
      width: 100,
      render: (score?: number) => (
        <div className="score-display">
          {score !== null && score !== undefined ? (
            <Tag color="blue" style={{ marginRight: 0 }}>{score}</Tag>
          ) : (
            <Text className="empty-value">-</Text>
          )}
        </div>
      ),
    },
    {
      title: '人工评分',
      dataIndex: 'quality_manual_score',
      key: 'quality_manual_score',
      width: 100,
      render: (manualScore?: number, record?: Session) => {
        const autoScore = record?.quality_auto_score;
        const showTrend = manualScore !== null && manualScore !== undefined && autoScore !== null && autoScore !== undefined;

        return (
          <div className="score-display">
            {manualScore !== null && manualScore !== undefined ? (
              <Space size={4}>
                <Tag color={manualScore > (autoScore || 0) ? 'green' : 'default'} style={{ marginRight: 0 }}>
                  {manualScore}
                </Tag>
                {showTrend && manualScore > autoScore && (
                  <RiseOutlined style={{ color: '#52c41a', fontSize: 14 }} />
                )}
                {showTrend && manualScore === autoScore && (
                  <MinusOutlined style={{ color: '#8c8c8c', fontSize: 12 }} />
                )}
              </Space>
            ) : (
              <Text className="empty-value">-</Text>
            )}
          </div>
        );
      },
    },
    {
      title: 'Agent 角色',
      dataIndex: 'agent_role',
      key: 'agent_role',
      width: 150,
      render: (role?: string) => (
        <Text className={role ? 'agent-role' : 'empty-value'}>
          {role || '-'}
        </Text>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => (
        <Text className="create-time">{date}</Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Session) => (
        <Button
          className="view-btn"
          icon={<EyeOutlined />}
          onClick={() => onViewSession(record)}
          size="small"
        >
          查看
        </Button>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={sessions}
      rowKey="session_id"
      loading={loading}
      className="sessions-table"
      pagination={{
        current: page,
        pageSize,
        total,
        onChange: onPageChange,
        showSizeChanger: true,
        showTotal: (total) => `共 ${total} 条`,
      }}
      scroll={{ x: 1200 }}
    />
  );
};

export default SessionTable;
