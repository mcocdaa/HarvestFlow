import React, { useEffect, useState } from 'react';
import { Button, Collapse, Descriptions, Drawer, Flex, Space, Tag, Typography } from 'antd';
import { DownOutlined, UpOutlined } from '@ant-design/icons';
import { CopyText, EmptyState, JsonView, MessageBubble, ScoreTag, StatusTag } from '../common';
import { formatDateTime } from '../../utils';
import { useI18n } from '../../i18n';
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
  const { locale, t, td } = useI18n();
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
        { key: 'status', label: t('状态', 'Status'), children: <StatusTag status={session.status} /> },
        { key: 'auto', label: t('自动评分', 'Auto Score'), children: <ScoreTag score={session.quality_auto_score} showLabel /> },
        { key: 'manual', label: t('人工评分', 'Manual Score'), children: <ScoreTag score={session.quality_manual_score} showLabel /> },
        { key: 'role', label: t('Agent 角色', 'Agent Role'), children: td(session.agent_role) || '-' },
        { key: 'task', label: t('任务类型', 'Task Type'), span: 2, children: td(session.task_type) || '-' },
        { key: 'created', label: t('创建时间', 'Created At'), children: formatDateTime(session.created_at) },
        { key: 'updated', label: t('更新时间', 'Updated At'), children: formatDateTime(session.updated_at) },
        {
          key: 'tools',
          label: t('使用工具', 'Tools Used'),
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
          label: t('标签', 'Tags'),
          span: 2,
          children:
            session.tags && session.tags.length > 0 ? (
              <Space size={4} wrap>
                {session.tags.map((tag) => (
                  <Tag key={tag} color="blue" bordered={false}>
                    {td(tag)}
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
                {td(session.task_type) || t('未分类会话', 'Uncategorized Session')}
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
            styles={{ label: { color: 'var(--flow-text-secondary)' } }}
          />

          <div>
            <Flex justify="space-between" align="center" style={{ marginBottom: 12 }}>
              <Typography.Text strong>
                {locale === 'zh' ? `对话内容（${messages.length} 条）` : `Dialogue (${messages.length})`}
              </Typography.Text>
              {messages.length > PREVIEW_COUNT && (
                <Button
                  type="link"
                  size="small"
                  icon={expanded ? <UpOutlined /> : <DownOutlined />}
                  onClick={() => setExpanded((prev) => !prev)}
                >
                  {expanded
                    ? t('收起', 'Collapse')
                    : locale === 'zh'
                      ? `展开全部 ${messages.length} 条`
                      : `Expand All (${messages.length})`}
                </Button>
              )}
            </Flex>
            {messages.length === 0 ? (
              <EmptyState description={t('暂无对话内容', 'No dialogue content')} />
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
                  label: <Typography.Text type="secondary">{t('技术信息', 'Technical Info')}</Typography.Text>,
                  children: (
                    <Flex vertical gap={12}>
                      {metadata && <JsonView value={metadata} maxHeight={320} />}
                      {content?.tools_used && content.tools_used.length > 0 && (
                        <div>
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            {t('采集到的工具调用', 'Collected Tool Calls')}
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
