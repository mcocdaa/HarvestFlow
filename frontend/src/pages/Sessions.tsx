import React, { useRef, useState } from 'react';
import { Button, Popconfirm, Segmented, Select, Space, Tag, Tooltip, Typography, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { ProTable } from '@ant-design/pro-components';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { curatorApi, sessionApi } from '../services';
import { CopyText, PageHeader, ScoreTag, StatusTag } from '../components';
import { SessionDrawer, SessionEditModal } from '../components/sessions';
import { getSortOptions, getStatusOptions } from '../constants/display';
import { formatDateTime, truncateSessionId } from '../utils';
import { useI18n } from '../i18n';
import type { Session, SessionContent } from '../types';

const Sessions: React.FC = () => {
  const { locale, t, td } = useI18n();
  const actionRef = useRef<ActionType | undefined>(undefined);
  const [status, setStatus] = useState('all');
  const [sort, setSort] = useState('recent');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selected, setSelected] = useState<Session | null>(null);
  const [content, setContent] = useState<SessionContent | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null);

  const statusFilterOptions = [
    { value: 'all', label: t('全部', 'All') },
    ...getStatusOptions(locale),
  ];
  const sortOptions = getSortOptions(locale);

  const handleView = async (record: Session) => {
    setSelected(record);
    setContent(null);
    setDrawerOpen(true);
    setContentLoading(true);
    try {
      const res = await sessionApi.getSessionContent(record.session_id);
      setContent((res.data?.content as SessionContent) ?? null);
    } catch {
      setContent(null);
    } finally {
      setContentLoading(false);
    }
  };

  const handleDelete = async (record: Session) => {
    try {
      await sessionApi.deleteSession(record.session_id);
      message.success(t('会话已删除', 'Session deleted'));
      actionRef.current?.reload();
    } catch {
      // 拦截器已统一提示
    }
  };

  const handleEvaluate = async (record: Session) => {
    setEvaluatingId(record.session_id);
    try {
      const res = await curatorApi.evaluate(record.session_id);
      const result = res.data as { score?: number; is_high_value?: boolean; auto_approved?: boolean };
      if (locale === 'zh') {
        const suffix = result.auto_approved ? '，已自动通过' : '';
        message.success(`自动评分 ${result.score ?? '-'} 分（${result.is_high_value ? '高价值' : '普通'}）${suffix}`);
      } else {
        const suffix = result.auto_approved ? ', auto-approved' : '';
        message.success(
          `Auto score ${result.score ?? '-'} (${result.is_high_value ? 'high-value' : 'normal'})${suffix}`
        );
      }
      actionRef.current?.reload();
    } catch {
      // 拦截器已统一提示
    } finally {
      setEvaluatingId(null);
    }
  };

  const columns: ProColumns<Session>[] = [
    {
      title: t('会话', 'Session'),
      dataIndex: 'session_id',
      key: 'session',
      ellipsis: true,
      render: (_, record) => (
        <Space direction="vertical" size={2} style={{ maxWidth: '100%', overflow: 'hidden' }}>
          <Typography.Text strong ellipsis style={{ display: 'block', maxWidth: 185 }}>
            {td(record.task_type) || t('未分类', 'Uncategorized')}
          </Typography.Text>
          <CopyText
            text={record.session_id}
            mono
            display={<span style={{ fontSize: 11 }}>{truncateSessionId(record.session_id)}</span>}
          />
        </Space>
      ),
    },
    {
      title: t('状态', 'Status'),
      dataIndex: 'status',
      key: 'status',
      width: 86,
      render: (_, record) => <StatusTag status={record.status} />,
    },
    {
      title: t('自动评分', 'Auto'),
      dataIndex: 'quality_auto_score',
      key: 'quality_auto_score',
      width: 64,
      render: (_, record) => <ScoreTag score={record.quality_auto_score} />,
    },
    {
      title: t('人工评分', 'Manual'),
      dataIndex: 'quality_manual_score',
      key: 'quality_manual_score',
      width: 64,
      render: (_, record) => <ScoreTag score={record.quality_manual_score} />,
    },
    {
      title: t('Agent 角色', 'Agent Role'),
      dataIndex: 'agent_role',
      key: 'agent_role',
      width: 148,
      render: (_, record) =>
        record.agent_role ? (
          <Tag
            bordered={false}
            style={{
              marginInlineEnd: 0,
              maxWidth: 132,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              verticalAlign: 'bottom',
            }}
          >
            {td(record.agent_role)}
          </Tag>
        ) : (
          <span className="score-empty">-</span>
        ),
    },
    {
      title: t('标签', 'Tags'),
      dataIndex: 'tags',
      key: 'tags',
      width: 118,
      render: (_, record) => {
        const tags = record.tags ?? [];
        if (tags.length === 0) return <span className="score-empty">-</span>;
        return (
          <Space size={4} style={{ whiteSpace: 'nowrap' }}>
            {tags.slice(0, 1).map((tag) => (
              <Tag key={tag} color="blue" bordered={false} style={{ marginInlineEnd: 0 }}>
                {td(tag)}
              </Tag>
            ))}
            {tags.length > 1 && (
              <Tooltip title={tags.slice(1).map((tag) => td(tag)).join(', ')}>
                <Tag bordered={false} style={{ marginInlineEnd: 0 }}>
                  +{tags.length - 1}
                </Tag>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: t('创建时间', 'Created'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 118,
      render: (_, record) => (
        <Typography.Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
          {formatDateTime(record.created_at)}
        </Typography.Text>
      ),
    },
    {
      title: t('操作', 'Actions'),
      key: 'option',
      width: 152,
      render: (_, record) => (
        <Space size={2} style={{ whiteSpace: 'nowrap' }}>
          <Button
            key="view"
            type="link"
            size="small"
            style={{ paddingInline: 4, fontSize: 13 }}
            onClick={() => handleView(record)}
          >
            {t('查看', 'View')}
          </Button>
          <Button
            key="edit"
            type="link"
            size="small"
            style={{ paddingInline: 4, fontSize: 13 }}
            onClick={() => {
              setSelected(record);
              setEditOpen(true);
            }}
          >
            {t('编辑', 'Edit')}
          </Button>
          {record.status === 'raw' && (
            <Button
              key="evaluate"
              type="link"
              size="small"
              style={{ paddingInline: 4, fontSize: 13 }}
              loading={evaluatingId === record.session_id}
              onClick={() => handleEvaluate(record)}
            >
              {t('评分', 'Score')}
            </Button>
          )}
          <Popconfirm
            key="delete"
            title={t('删除该会话？', 'Delete this session?')}
            description={t(
              '数据库记录与源文件将一并删除，不可恢复。',
              'Database record and source file will be permanently deleted.'
            )}
            okText={t('删除', 'Delete')}
            cancelText={t('取消', 'Cancel')}
            okButtonProps={{ danger: true }}
            onConfirm={() => handleDelete(record)}
          >
            <Button type="link" size="small" style={{ paddingInline: 4, fontSize: 13 }} danger>
              {t('删除', 'Delete')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('会话', 'Sessions')}
        description={t(
          '全部采集会话的浏览、检索与维护',
          'Browse, filter, curate, and manage all collected trajectory sessions'
        )}
      />
      <ProTable<Session, { status?: string; sort?: string }>
        actionRef={actionRef}
        rowKey="session_id"
        columns={columns}
        tableLayout="fixed"
        scroll={{ x: 'max-content' }}
        search={false}
        params={{ status: status === 'all' ? undefined : status, sort }}
        request={async (params) => {
          const res = await sessionApi.getSessions({
            page: params.current,
            page_size: params.pageSize,
            status: params.status,
            sort: params.sort,
          });
          const data = res.data as { sessions?: Session[]; total?: number };
          return { data: data.sessions ?? [], total: data.total ?? 0, success: true };
        }}
        options={{ density: false, setting: false, reload: false, fullScreen: false }}
        toolBarRender={() => [
          <Segmented
            key="status"
            options={statusFilterOptions}
            value={status}
            onChange={(value) => setStatus(String(value))}
          />,
          <Select
            key="sort"
            options={sortOptions}
            value={sort}
            onChange={setSort}
            style={{ width: 120 }}
          />,
          <Tooltip key="reload" title={t('刷新', 'Refresh')}>
            <Button icon={<ReloadOutlined />} onClick={() => actionRef.current?.reload()} />
          </Tooltip>,
        ]}
        pagination={{
          defaultPageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => (locale === 'zh' ? `共 ${total} 条` : `Total ${total}`),
        }}
        cardBordered={false}
      />
      <SessionDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        session={selected}
        content={content}
        loading={contentLoading}
      />
      <SessionEditModal
        open={editOpen}
        session={selected}
        onClose={() => setEditOpen(false)}
        onSaved={() => actionRef.current?.reload()}
      />
    </div>
  );
};

export default Sessions;
