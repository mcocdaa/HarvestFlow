import React, { useEffect, useState } from 'react';
import { Button, Collapse, Descriptions, Drawer, Flex, Space, Tag, Typography } from 'antd';
import { DownOutlined, UpOutlined } from '@ant-design/icons';
import { CopyText, EmptyState, JsonView, MessageBubble, ScoreTag, StatusTag } from '../common';
import { formatDateTime } from '../../utils';
import type { Session, SessionContent } from '../../types';

const PREVIEW_COUNT = 5;

interface SessionDrawerProps {
  open: boolean;
  onClose: () => void;
  session: Session | null;
  content: SessionContent | null;
  loading?: boolean;
}

const SessionDrawer: React.FC<SessionDrawerProps> = ({ open, onClose, session, content, loading }) => {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!open) {
      setExpanded(false);
    }
  }, [open]);

  const messages = content?.messages ?? [];
  const visibleMessages = expanded ? messages : messages.slice(0, PREVIEW_COUNT);

  const descriptionItems = session
    ? [
        { key: 'status', label: '状态', children: <StatusTag status={session.status} /> },
        { key: 'auto', label: '自动评分', children: <ScoreTag score={session.quality_auto_score} showLabel /> },
        { key: 'manual', label: '人工评分', children: <ScoreTag score={session.quality_manual_score} showLabel /> },
        { key: 'role', label: 'Agent 角色', children: session.agent_role || '-' },
        { key: 'task', label: '任务类型', children: session.task_type || '-' },
        { key: 'created', label: '创建时间', children: formatDateTime(session.created_at) },
        { key: 'updated', label: '更新时间', children: formatDateTime(session.updated_at) },
        {
          key: 'tools',
          label: '使用工具',
          span: 2,
          children:
            session.tools_used && session.tools_used.length > 0 ? (
              <Space size={4} wrap>
                {session.tools_used.map((tool) => (
                  <Tag key={tool} bordered={false}>
                    {tool}
                  </Tag>
                ))}
              </Space>
            ) : (
              <span className="score-empty">-</span>
            ),
        },
        {
          key: 'tags',
          label: '标签',
          span: 2,
          children:
            session.tags && session.tags.length > 0 ? (
              <Space size={4} wrap>
                {session.tags.map((tag) => (
                  <Tag key={tag} color="blue" bordered={false}>
                    {tag}
                  </Tag>
                ))}
              </Space>
            ) : (
              <span className="score-empty">-</span>
            ),
        },
      ]
    : [];

  const metadata = content?.metadata;

  return (
    <Drawer
      className="session-drawer"
      placement="right"
      width={640}
      open={open}
      onClose={onClose}
      loading={loading}
      destroyOnHidden
      title={
        session ? (
          <Flex vertical gap={4}>
            <Space size={8} wrap>
              <Typography.Text strong style={{ fontSize: 16 }}>
                {session.task_type || '未分类会话'}
              </Typography.Text>
              <StatusTag status={session.status} />
            </Space>
            <CopyText
              text={session.session_id}
              mono
              display={<span style={{ fontSize: 12 }}>{session.session_id}</span>}
            />
          </Flex>
        ) : null
      }
    >
      {session && (
        <Flex vertical gap={24}>
          <Descriptions
            items={descriptionItems}
            column={2}
            size="small"
            labelStyle={{ color: 'var(--flow-text-secondary)' }}
          />

          <div>
            <Flex justify="space-between" align="center" style={{ marginBottom: 12 }}>
              <Typography.Text strong>对话内容（{messages.length} 条）</Typography.Text>
              {messages.length > PREVIEW_COUNT && (
                <Button
                  type="link"
                  size="small"
                  icon={expanded ? <UpOutlined /> : <DownOutlined />}
                  onClick={() => setExpanded((prev) => !prev)}
                >
                  {expanded ? '收起' : `展开全部 ${messages.length} 条`}
                </Button>
              )}
            </Flex>
            {messages.length === 0 ? (
              <EmptyState description="暂无对话内容" />
            ) : (
              <Flex vertical gap={16}>
                {visibleMessages.map((msg, index) => (
                  <MessageBubble key={index} message={msg} index={index} />
                ))}
              </Flex>
            )}
          </div>

          {(metadata || (content?.tools_used && content.tools_used.length > 0)) && (
            <Collapse
              ghost
              items={[
                {
                  key: 'metadata',
                  label: <Typography.Text type="secondary">技术信息</Typography.Text>,
                  children: (
                    <Flex vertical gap={12}>
                      {metadata && <JsonView value={metadata} maxHeight={320} />}
                      {content?.tools_used && content.tools_used.length > 0 && (
                        <div>
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            采集到的工具调用
                          </Typography.Text>
                          <div style={{ marginTop: 6 }}>
                            <Space size={4} wrap>
                              {content.tools_used.map((tool) => (
                                <Tag key={tool} bordered={false}>
                                  {tool}
                                </Tag>
                              ))}
                            </Space>
                          </div>
                        </div>
                      )}
                    </Flex>
                  ),
                },
              ]}
            />
          )}
        </Flex>
      )}
    </Drawer>
  );
};

export default SessionDrawer;
