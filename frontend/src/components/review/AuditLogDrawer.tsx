import React, { useEffect, useState } from 'react';
import { Drawer, Flex, Switch, Table, Tag, Typography } from 'antd';
import { reviewerApi } from '../../services';
import { useAsyncData } from '../../hooks';
import { AUDIT_ACTION_COLORS, AUDIT_ACTION_LABELS, OPERATOR_LABELS } from '../../constants/display';
import { CopyText } from '../common';
import { formatDateTime, truncateSessionId } from '../../utils';
import type { AuditLog } from '../../types';

interface AuditLogDrawerProps {
  open: boolean;
  onClose: () => void;
  sessionId?: string | null;
}

const AuditLogDrawer: React.FC<AuditLogDrawerProps> = ({ open, onClose, sessionId }) => {
  const [sessionOnly, setSessionOnly] = useState(Boolean(sessionId));

  useEffect(() => {
    setSessionOnly(Boolean(sessionId));
  }, [sessionId, open]);

  const { data, loading, reload } = useAsyncData<{ logs?: AuditLog[] }>(
    () =>
      open
        ? reviewerApi.getAuditLogs(sessionOnly && sessionId ? sessionId : undefined)
        : Promise.resolve({ data: {} }),
    [open, sessionOnly, sessionId]
  );

  const logs = data?.logs ?? [];

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          {formatDateTime(value)}
        </Typography.Text>
      ),
    },
    {
      title: '会话',
      dataIndex: 'session_id',
      key: 'session_id',
      render: (value: string) => (
        <CopyText text={value} mono display={<span style={{ fontSize: 12 }}>{truncateSessionId(value)}</span>} />
      ),
    },
    {
      title: '动作',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action: string) => (
        <Tag color={AUDIT_ACTION_COLORS[action] ?? 'default'} bordered={false}>
          {AUDIT_ACTION_LABELS[action] ?? action}
        </Tag>
      ),
    },
    {
      title: '操作者',
      dataIndex: 'operator',
      key: 'operator',
      width: 90,
      render: (operator: string) => OPERATOR_LABELS[operator] ?? operator,
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
      render: (details?: string | null) => details || '-',
    },
  ];

  return (
    <Drawer
      title="审计日志"
      placement="right"
      width={720}
      open={open}
      onClose={onClose}
      extra={
        <Flex align="center" gap={8}>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            仅当前会话
          </Typography.Text>
          <Switch
            size="small"
            checked={sessionOnly}
            disabled={!sessionId}
            onChange={setSessionOnly}
          />
        </Flex>
      }
    >
      <Table<AuditLog>
        rowKey="id"
        columns={columns}
        dataSource={logs}
        loading={loading}
        size="small"
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条（最多展示 100 条）` }}
        onRow={() => ({ onDoubleClick: () => reload() })}
      />
    </Drawer>
  );
};

export default AuditLogDrawer;
