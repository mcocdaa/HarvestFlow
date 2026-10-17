import React, { useEffect, useState } from 'react';
import { Drawer, Flex, Switch, Table, Tag, Typography } from 'antd';
import { reviewerApi } from '../../services';
import { useAsyncData } from '../../hooks';
import { AUDIT_ACTION_COLORS, getAuditActionLabel, getOperatorLabel } from '../../constants/display';
import { CopyText } from '../common';
import { formatDateTime, truncateSessionId } from '../../utils';
import { useI18n } from '../../i18n';
import type { AuditLog } from '../../types';

interface AuditLogDrawerProps {
  open: boolean;
  onClose: () => void;
  sessionId?: string | null;
}

const AuditLogDrawer: React.FC<AuditLogDrawerProps> = ({ open, onClose, sessionId }) => {
  const { locale, t } = useI18n();
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
      title: t('时间', 'Time'),
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
      title: t('会话', 'Session'),
      dataIndex: 'session_id',
      key: 'session_id',
      render: (value: string) => (
        <CopyText text={value} mono display={<span style={{ fontSize: 12 }}>{truncateSessionId(value)}</span>} />
      ),
    },
    {
      title: t('动作', 'Action'),
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action: string) => (
        <Tag color={AUDIT_ACTION_COLORS[action] ?? 'default'} bordered={false}>
          {getAuditActionLabel(action, locale)}
        </Tag>
      ),
    },
    {
      title: t('操作者', 'Operator'),
      dataIndex: 'operator',
      key: 'operator',
      width: 90,
      render: (operator: string) => getOperatorLabel(operator, locale),
    },
    {
      title: t('详情', 'Details'),
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
      render: (details?: string | null) => details || '-',
    },
  ];

  return (
    <Drawer
      title={t('审计日志', 'Audit Logs')}
      placement="right"
      width={720}
      open={open}
      onClose={onClose}
      extra={
        <Flex align="center" gap={8}>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            {t('仅当前会话', 'Current Session Only')}
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
        pagination={{
          pageSize: 20,
          showTotal: (total) =>
            locale === 'zh' ? `共 ${total} 条（最多展示 100 条）` : `Total ${total} (up to 100)`,
        }}
        onRow={() => ({ onDoubleClick: () => reload() })}
      />
    </Drawer>
  );
};

export default AuditLogDrawer;
