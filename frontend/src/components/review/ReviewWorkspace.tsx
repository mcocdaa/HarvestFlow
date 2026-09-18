import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Checkbox, Collapse, Divider, Flex, Input, InputNumber, Progress, Rate, Select, Space, Tag, Typography, message } from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  DownOutlined,
  EnterOutlined,
  LeftOutlined,
  RightOutlined,
  UpOutlined,
} from '@ant-design/icons';
import { reviewerApi, sessionApi } from '../../services';
import { useAsyncData, useKeyboardShortcut } from '../../hooks';
import { CopyText, EmptyState, JsonView, MessageBubble, ScoreTag, StatusTag } from '../common';
import { getScoreColor, getScoreLabel, scoreLabels, truncateSessionId } from '../../utils';
import type { ReviewerExtraField, ReviewerExtraFields, ReviewExtras, Session, SessionContent } from '../../types';
import '../../styles/Review.css';

const PREVIEW_COUNT = 4;

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
const MOD_KEY = isMac ? 'Cmd' : 'Ctrl';

interface ExtraFieldInputProps {
  field: ReviewerExtraField;
  value: unknown;
  onChange: (value: unknown) => void;
}

const ExtraFieldInput: React.FC<ExtraFieldInputProps> = ({ field, value, onChange }) => {
  switch (field.type) {
    case 'select':
      return (
        <Select
          allowClear
          style={{ width: '100%' }}
          placeholder={field.placeholder ?? `请选择${field.label}`}
          value={value as string | undefined}
          onChange={(selected) => onChange(selected)}
          options={(field.options ?? []).map((option) => ({ value: option, label: option }))}
        />
      );
    case 'textarea':
      return (
        <Input.TextArea
          rows={2}
          value={value as string | undefined}
          placeholder={field.placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      );
    case 'checkbox':
      return <Checkbox checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />;
    case 'number':
      return (
        <InputNumber
          style={{ width: '100%' }}
          value={value as number | undefined}
          placeholder={field.placeholder}
          onChange={(number) => onChange(number)}
        />
      );
    default:
      return (
        <Input
          value={value as string | undefined}
          placeholder={field.placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      );
  }
};

interface ReviewWorkspaceProps {
  onCurrentChange?: (sessionId: string | null) => void;
}

const ReviewWorkspace: React.FC<ReviewWorkspaceProps> = ({ onCurrentChange }) => {
  const { data, loading, reload } = useAsyncData<{ sessions?: Session[]; total?: number }>(
    () => reviewerApi.getPending(1, 100)
  );
  const [queue, setQueue] = useState<Session[]>([]);
  const [index, setIndex] = useState(0);
  const [score, setScore] = useState(3);
  const [notes, setNotes] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [extras, setExtras] = useState<ReviewExtras>({});

  const { data: extraFieldsData } = useAsyncData<ReviewerExtraFields>(() => reviewerApi.getExtraFields());
  const extraFields = useMemo(() => extraFieldsData?.fields ?? [], [extraFieldsData]);

  useEffect(() => {
    setQueue(data?.sessions ?? []);
    setIndex(0);
    setExpanded(false);
  }, [data]);

  const current = queue[index] ?? null;
  const currentId = current?.session_id ?? null;

  useEffect(() => {
    setExtras({});
  }, [currentId]);

  useEffect(() => {
    onCurrentChange?.(currentId);
  }, [currentId, onCurrentChange]);

  const { data: contentData, loading: contentLoading } = useAsyncData<{ content?: SessionContent }>(
    () => (current ? sessionApi.getSessionContent(current.session_id) : Promise.resolve({ data: {} })),
    [currentId]
  );
  const content = contentData?.content ?? null;
  const messages = useMemo(() => content?.messages ?? [], [content]);
  const visibleMessages = expanded ? messages : messages.slice(0, PREVIEW_COUNT);

  const handleReview = async (approve: boolean) => {
    if (!current || submitting) return;

    for (const field of extraFields) {
      if (!field.required) continue;
      const value = extras[field.name];
      if (value === undefined || value === null || value === '') {
        message.warning(`请填写「${field.label}」`);
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = Object.keys(extras).length > 0 ? extras : undefined;
      if (approve) {
        await reviewerApi.approveSession(current.session_id, notes, score, payload);
        message.success('已通过评审');
      } else {
        await reviewerApi.rejectSession(current.session_id, notes, score, payload);
        message.success('已拒绝');
      }
      const next = queue.filter((item) => item.session_id !== current.session_id);
      setQueue(next);
      setIndex((prev) => Math.min(prev, Math.max(next.length - 1, 0)));
      setNotes('');
      setScore(3);
      setExtras({});
      if (next.length === 0) {
        message.info('审核队列已清空');
        reload();
      }
    } catch {
      // 拦截器已统一提示
    } finally {
      setSubmitting(false);
    }
  };

  useKeyboardShortcut(
    'Enter',
    () => {
      if (current && score && !submitting) handleReview(true);
    },
    true
  );

  useKeyboardShortcut(
    'Backspace',
    () => {
      if (current && !submitting) handleReview(false);
    },
    true
  );

  const progressPercent = queue.length > 0 ? Math.round(((index + 1) / queue.length) * 100) : 0;

  const messageSection = useMemo(() => {
    if (messages.length === 0) {
      return <EmptyState description={loading || contentLoading ? '加载中…' : '暂无对话内容'} />;
    }
    return (
      <Flex vertical gap={16}>
        {visibleMessages.map((msg, i) => (
          <MessageBubble key={i} message={msg} index={i} />
        ))}
        {messages.length > PREVIEW_COUNT && (
          <Button
            type="link"
            icon={expanded ? <UpOutlined /> : <DownOutlined />}
            onClick={() => setExpanded((prev) => !prev)}
          >
            {expanded ? '收起对话' : `展开剩余 ${messages.length - PREVIEW_COUNT} 条`}
          </Button>
        )}
      </Flex>
    );
  }, [messages, visibleMessages, expanded, loading, contentLoading]);

  if (!loading && queue.length === 0) {
    return (
      <Card variant="borderless">
        <EmptyState description="审核队列已清空，去会话页看看新数据吧">
          <Button type="primary" onClick={reload} icon={<RightOutlined />}>
            刷新队列
          </Button>
        </EmptyState>
      </Card>
    );
  }

  return (
    <Flex gap={16} align="flex-start" className="review-workspace">
      <Flex vertical gap={16} className="review-main">
        <Card variant="borderless" className="review-progress-card" loading={loading && queue.length === 0}>
          <Flex justify="space-between" align="center" gap={16} wrap>
            <div className="review-progress">
              <Flex align="center" gap={8} wrap>
                <Typography.Text strong>
                  第 {Math.min(index + 1, queue.length)} / {queue.length} 条
                </Typography.Text>
                {current && <StatusTag status={current.status} />}
                {currentId && <CopyText text={currentId} mono display={<span style={{ fontSize: 12 }}>{truncateSessionId(currentId)}</span>} />}
              </Flex>
              <Progress percent={progressPercent} showInfo={false} size="small" style={{ marginTop: 8 }} />
            </div>
            <Space>
              <Button icon={<LeftOutlined />} disabled={index === 0} onClick={() => setIndex((prev) => prev - 1)}>
                上一个
              </Button>
              <Button
                icon={<RightOutlined />}
                disabled={index >= queue.length - 1}
                onClick={() => setIndex((prev) => prev + 1)}
                iconPosition="end"
              >
                下一个
              </Button>
            </Space>
          </Flex>
        </Card>

        <Card
          variant="borderless"
          title="对话内容"
          loading={contentLoading && messages.length === 0}
        >
          {messageSection}
          {content?.metadata && (
            <Collapse
              ghost
              style={{ marginTop: 16 }}
              items={[
                {
                  key: 'metadata',
                  label: <Typography.Text type="secondary">技术信息</Typography.Text>,
                  children: <JsonView value={content.metadata} maxHeight={280} />,
                },
              ]}
            />
          )}
        </Card>
      </Flex>

      <Card variant="borderless" title="评审操作" className="review-side-panel">
        <Flex vertical gap={16}>
          <div>
            <Flex justify="space-between" align="center" style={{ marginBottom: 8 }}>
              <Typography.Text strong>质量评分</Typography.Text>
              <Tag color={getScoreColor(score)}>{getScoreTagLabel(score)}</Tag>
            </Flex>
            <Rate allowClear value={score} onChange={setScore} tooltips={scoreLabels} />
            {current?.quality_auto_score !== null && current?.quality_auto_score !== undefined && (
              <Flex justify="space-between" align="center" style={{ marginTop: 8 }}>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  自动评分对比
                </Typography.Text>
                <Space size={4}>
                  <ScoreTag score={current.quality_auto_score} />
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {getScoreLabel(current.quality_auto_score)}
                  </Typography.Text>
                </Space>
              </Flex>
            )}
          </div>

          <div>
            <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>
              评审意见
            </Typography.Text>
            <Input.TextArea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="可选，最多 200 字"
              showCount
              maxLength={200}
            />
          </div>

          {extraFields.length > 0 && (
            <div>
              <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>
                插件扩展字段
              </Typography.Text>
              <Flex vertical gap={12}>
                {extraFields.map((field) => (
                  <div key={field.name}>
                    <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>
                      {field.label}
                      {field.required ? ' *' : ''}
                    </Typography.Text>
                    <ExtraFieldInput
                      field={field}
                      value={extras[field.name]}
                      onChange={(value) => setExtras((prev) => ({ ...prev, [field.name]: value }))}
                    />
                  </div>
                ))}
              </Flex>
            </div>
          )}

          <Flex vertical gap={8}>
            <Button
              type="primary"
              size="large"
              block
              icon={<CheckOutlined />}
              loading={submitting}
              disabled={!current || !score}
              onClick={() => handleReview(true)}
            >
              通过评审
            </Button>
            <Button
              danger
              size="large"
              block
              icon={<CloseOutlined />}
              loading={submitting}
              disabled={!current}
              onClick={() => handleReview(false)}
            >
              拒绝
            </Button>
          </Flex>

          <Divider style={{ margin: 0 }} />
          <Flex justify="center" gap={8}>
            <Tag icon={<EnterOutlined />} bordered={false}>
              {MOD_KEY} + Enter 通过
            </Tag>
            <Tag icon={<DeleteOutlined />} bordered={false}>
              {MOD_KEY} + Backspace 拒绝
            </Tag>
          </Flex>
        </Flex>
      </Card>
    </Flex>
  );
};

const getScoreTagLabel = (score: number): string => `${score} · ${getScoreLabel(score)}`;

export default ReviewWorkspace;
