import React, { useState } from 'react';
import { Button, Popconfirm, Space, Table, Tag, Typography, message } from 'antd';
import { CheckOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';
import { reviewerApi } from '../../services';
import { useAsyncData } from '../../hooks';
import { CopyText, EmptyState, ScoreTag, StatusTag } from '../common';
import { formatDateTime, truncateSessionId } from '../../utils';
import type { BatchReviewResult, Session } from '../../types';

const BatchReviewPanel: React.FC = () => {
  const { data, loading, reload } = useAsyncData<{ sessions?: Session[]; total?: number }>(
    () => reviewerApi.getPending(1, 100)
  );
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const sessions = data?.sessions ?? [];

  const handleBatch = async (approve: boolean) => {
    setSubmitting(true);
    try {
      const ids = selectedKeys.map(String);
      const res = approve ? await reviewerApi.batchApprove(ids) : await reviewerApi.batchReject(ids);
      const result = res.data as BatchReviewResult;
      if (result.failed > 0) {
        message.warning(`批量${approve ? '通过' : '拒绝'}完成：成功 ${result.success}，失败 ${result.failed}`);
      } else {
        message.success(`批量${approve ? '通过' : '拒绝'}完成：共 ${result.success} 条`);
      }
      setSelectedKeys([]);
      reload();
    } catch {
      // 拦截器已统一提示
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    {
      title: '会话',
      dataIndex: 'session_id',
      key: 'session',
      render: (sessionId: string, record: Session) => (
        <Space direction="vertical" size={2}>
          <Typography.Text strong>{record.task_type || '未分类'}</Typography.Text>
          <CopyText
            text={sessionId}
            mono
            display={<span style={{ fontSize: 12 }}>{truncateSessionId(sessionId)}</span>}
          />
        </Space>
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
      width: 100,
      render: (score?: number | null) => <ScoreTag score={score} />,
    },
    {
      title: 'Agent 角色',
      dataIndex: 'agent_role',
      key: 'agent_role',
      width: 140,
      render: (role?: string | null) => (role ? <Tag bordered={false}>{role}</Tag> : <span className="score-empty">-</span>),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          {formatDateTime(value)}
        </Typography.Text>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Popconfirm
          title={`批量通过 ${selectedKeys.length} 条会话？`}
          okText="确认通过"
          cancelText="取消"
          onConfirm={() => handleBatch(true)}
          disabled={selectedKeys.length === 0}
        >
          <Button
            type="primary"
            icon={<CheckOutlined />}
            disabled={selectedKeys.length === 0}
            loading={submitting}
          >
            批量通过（{selectedKeys.length}）
          </Button>
        </Popconfirm>
        <Popconfirm
          title={`批量拒绝 ${selectedKeys.length} 条会话？`}
          description="拒绝后标记为 rejected，可由人工再次调整。"
          okText="确认拒绝"
          cancelText="取消"
          okButtonProps={{ danger: true }}
          onConfirm={() => handleBatch(false)}
          disabled={selectedKeys.length === 0}
        >
          <Button danger icon={<CloseOutlined />} disabled={selectedKeys.length === 0} loading={submitting}>
            批量拒绝（{selectedKeys.length}）
          </Button>
        </Popconfirm>
        <Button icon={<ReloadOutlined />} onClick={reload}>
          刷新
        </Button>
      </Space>

      <Table<Session>
        rowKey="session_id"
        columns={columns}
        dataSource={sessions}
        loading={loading}
        rowSelection={{
          selectedRowKeys: selectedKeys,
          onChange: setSelectedKeys,
        }}
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        locale={{ emptyText: <EmptyState description="审核队列已清空" /> }}
      />
    </div>
  );
};

export default BatchReviewPanel;
