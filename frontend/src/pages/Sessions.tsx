import React, { useRef, useState } from 'react';
import { Button, Popconfirm, Segmented, Select, Space, Tag, Tooltip, Typography, message } from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { ProTable } from '@ant-design/pro-components';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { curatorApi, sessionApi } from '../services';
import { CopyText, PageHeader, ScoreTag, StatusTag } from '../components';
import { SessionDrawer, SessionEditModal } from '../components/sessions';
import { SORT_OPTIONS, STATUS_OPTIONS } from '../constants/display';
import { formatDateTime, truncateSessionId } from '../utils';
import type { Session, SessionContent } from '../types';

const STATUS_FILTER_OPTIONS = [{ value: 'all', label: '全部' }, ...STATUS_OPTIONS];

const Sessions: React.FC = () => {
  const actionRef = useRef<ActionType | undefined>(undefined);
  const [status, setStatus] = useState('all');
  const [sort, setSort] = useState('recent');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selected, setSelected] = useState<Session | null>(null);
  const [content, setContent] = useState<SessionContent | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null);

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
      message.success('会话已删除');
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
      const suffix = result.auto_approved ? '，已自动通过' : '';
      message.success(`自动评分 ${result.score ?? '-'} 分（${result.is_high_value ? '高价值' : '普通'}）${suffix}`);
      actionRef.current?.reload();
    } catch {
      // 拦截器已统一提示
    } finally {
      setEvaluatingId(null);
    }
  };

  const columns: ProColumns<Session>[] = [
    {
      title: '会话',
      dataIndex: 'session_id',
      key: 'session',
      width: 260,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          <Typography.Text strong ellipsis style={{ maxWidth: 240 }}>
            {record.task_type || '未分类'}
          </Typography.Text>
          <CopyText
            text={record.session_id}
            mono
            display={<span style={{ fontSize: 12 }}>{truncateSessionId(record.session_id)}</span>}
          />
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (_, record) => <StatusTag status={record.status} />,
    },
    {
      title: '自动评分',
      dataIndex: 'quality_auto_score',
      key: 'quality_auto_score',
      width: 100,
      render: (_, record) => <ScoreTag score={record.quality_auto_score} />,
    },
    {
      title: '人工评分',
      dataIndex: 'quality_manual_score',
      key: 'quality_manual_score',
      width: 100,
      render: (_, record) => <ScoreTag score={record.quality_manual_score} />,
    },
    {
      title: 'Agent 角色',
      dataIndex: 'agent_role',
      key: 'agent_role',
      width: 140,
      render: (_, record) =>
        record.agent_role ? <Tag bordered={false}>{record.agent_role}</Tag> : <span className="score-empty">-</span>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 180,
      render: (_, record) => {
        const tags = record.tags ?? [];
        if (tags.length === 0) return <span className="score-empty">-</span>;
        return (
          <Space size={4} wrap>
            {tags.slice(0, 2).map((tag) => (
              <Tag key={tag} color="blue" bordered={false}>
                {tag}
              </Tag>
            ))}
            {tags.length > 2 && (
              <Tooltip title={tags.slice(2).join('、')}>
                <Tag bordered={false}>+{tags.length - 2}</Tag>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (_, record) => (
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          {formatDateTime(record.created_at)}
        </Typography.Text>
      ),
    },
    {
      title: '操作',
      key: 'option',
      width: 240,
      fixed: 'right',
      render: (_, record) => [
        <Button key="view" type="link" size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
          查看
        </Button>,
        <Button
          key="edit"
          type="link"
          size="small"
          icon={<EditOutlined />}
          onClick={() => {
            setSelected(record);
            setEditOpen(true);
          }}
        >
          编辑
        </Button>,
        record.status === 'raw' && (
          <Button
            key="evaluate"
            type="link"
            size="small"
            icon={<ThunderboltOutlined />}
            loading={evaluatingId === record.session_id}
            onClick={() => handleEvaluate(record)}
          >
            评分
          </Button>
        ),
        <Popconfirm
          key="delete"
          title="删除该会话？"
          description="数据库记录与源文件将一并删除，不可恢复。"
          okText="删除"
          cancelText="取消"
          okButtonProps={{ danger: true }}
          onConfirm={() => handleDelete(record)}
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>,
      ],
    },
  ];

  return (
    <div>
      <PageHeader title="会话" description="全部采集会话的浏览、检索与维护" />
      <ProTable<Session, { status?: string; sort?: string }>
        actionRef={actionRef}
        rowKey="session_id"
        columns={columns}
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
            options={STATUS_FILTER_OPTIONS}
            value={status}
            onChange={(value) => setStatus(String(value))}
          />,
          <Select
            key="sort"
            options={SORT_OPTIONS}
            value={sort}
            onChange={setSort}
            style={{ width: 120 }}
          />,
          <Tooltip key="reload" title="刷新">
            <Button icon={<ReloadOutlined />} onClick={() => actionRef.current?.reload()} />
          </Tooltip>,
        ]}
        pagination={{ defaultPageSize: 20, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
        cardBordered={false}
        scroll={{ x: 1240 }}
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
