import React, { useState } from 'react';
import { Button, Popconfirm, Space, Table, Tag, Typography, message } from 'antd';
import { CheckOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';
import { reviewerApi } from '../../services';
import { useAsyncData } from '../../hooks';
import { CopyText, EmptyState, ScoreTag, StatusTag } from '../common';
import { formatDateTime, truncateSessionId } from '../../utils';
import { useI18n } from '../../i18n';
import type { BatchReviewResult, Session } from '../../types';

const BatchReviewPanel: React.FC = () => {
  const { locale, t, td } = useI18n();
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
        message.warning(
          locale === 'zh'
            ? `批量${approve ? '通过' : '拒绝'}完成：成功 ${result.success}，失败 ${result.failed}`
            : `Batch ${approve ? 'approve' : 'reject'} finished: ${result.success} succeeded, ${result.failed} failed`
        );
      } else {
        message.success(
          locale === 'zh'
            ? `批量${approve ? '通过' : '拒绝'}完成：共 ${result.success} 条`
            : `Batch ${approve ? 'approved' : 'rejected'} ${result.success} sessions`
        );
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
      title: t('会话', 'Session'),
      dataIndex: 'session_id',
      key: 'session',
      render: (sessionId: string, record: Session) => (
        <Space direction="vertical" size={2}>
          <Typography.Text strong>{td(record.task_type) || t('未分类', 'Uncategorized')}</Typography.Text>
          <CopyText
            text={sessionId}
            mono
            display={<span style={{ fontSize: 12 }}>{truncateSessionId(sessionId)}</span>}
          />
        </Space>
      ),
    },
    {
      title: t('状态', 'Status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <StatusTag status={status} />,
    },
    {
      title: t('自动评分', 'Auto Score'),
      dataIndex: 'quality_auto_score',
      key: 'quality_auto_score',
      width: 100,
      render: (score?: number | null) => <ScoreTag score={score} />,
    },
    {
      title: t('Agent 角色', 'Agent Role'),
      dataIndex: 'agent_role',
      key: 'agent_role',
      width: 140,
      render: (role?: string | null) => (role ? <Tag bordered={false}>{td(role)}</Tag> : <span className="score-empty">-</span>),
    },
    {
      title: t('创建时间', 'Created'),
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
          title={locale === 'zh' ? `批量通过 ${selectedKeys.length} 条会话？` : `Approve ${selectedKeys.length} sessions?`}
          okText={t('确认通过', 'Approve')}
          cancelText={t('取消', 'Cancel')}
          onConfirm={() => handleBatch(true)}
          disabled={selectedKeys.length === 0}
        >
          <Button
            type="primary"
            icon={<CheckOutlined />}
            disabled={selectedKeys.length === 0}
            loading={submitting}
          >
            {locale === 'zh' ? `批量通过（${selectedKeys.length}）` : `Batch Approve (${selectedKeys.length})`}
          </Button>
        </Popconfirm>
        <Popconfirm
          title={locale === 'zh' ? `批量拒绝 ${selectedKeys.length} 条会话？` : `Reject ${selectedKeys.length} sessions?`}
          description={t('拒绝后标记为 rejected，可由人工再次调整。', 'Marked as rejected; can be updated later.')}
          okText={t('确认拒绝', 'Reject')}
          cancelText={t('取消', 'Cancel')}
          okButtonProps={{ danger: true }}
          onConfirm={() => handleBatch(false)}
          disabled={selectedKeys.length === 0}
        >
          <Button danger icon={<CloseOutlined />} disabled={selectedKeys.length === 0} loading={submitting}>
            {locale === 'zh' ? `批量拒绝（${selectedKeys.length}）` : `Batch Reject (${selectedKeys.length})`}
          </Button>
        </Popconfirm>
        <Button icon={<ReloadOutlined />} onClick={reload}>
          {t('刷新', 'Refresh')}
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
        pagination={{ pageSize: 20, showTotal: (total) => (locale === 'zh' ? `共 ${total} 条` : `Total ${total}`) }}
        locale={{ emptyText: <EmptyState description={t('审核队列已清空', 'Review queue is empty')} /> }}
      />
    </div>
  );
};

export default BatchReviewPanel;
