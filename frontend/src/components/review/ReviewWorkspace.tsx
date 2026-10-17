import React, { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import {
  Button,
  Card,
  Checkbox,
  Collapse,
  Divider,
  Flex,
  Input,
  InputNumber,
  Progress,
  Rate,
  Select,
  Space,
  Tag,
  Typography,
  message,
  Tooltip,
} from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  DownOutlined,
  DiffOutlined,
  EditOutlined,
  LeftOutlined,
  RightOutlined,
  ToolOutlined,
  UpOutlined,
  UndoOutlined,
  SaveOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { reviewerApi, sessionApi } from '../../services';
import { useAsyncData, useKeyboardShortcut } from '../../hooks';
import { CopyText, EmptyState, JsonView, MessageBubble, ScoreTag, StatusTag } from '../common';
import DiffViewer from './DiffViewer';
import { getScoreColor, getScoreLabel, getScoreLabels, truncateSessionId } from '../../utils';
import { useI18n } from '../../i18n';
import type { Locale } from '../../i18n';
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
  const { locale, td } = useI18n();
  const fieldLabel = td(field.label);
  const fieldPlaceholder = field.placeholder ? td(field.placeholder) : undefined;
  switch (field.type) {
    case 'select':
      return (
        <Select
          allowClear
          style={{ width: '100%' }}
          placeholder={fieldPlaceholder ?? (locale === 'zh' ? `请选择${fieldLabel}` : `Select ${fieldLabel}`)}
          value={value as string | undefined}
          onChange={(selected) => onChange(selected)}
          options={(field.options ?? []).map((option) => ({ value: option, label: td(option) }))}
        />
      );
    case 'textarea':
      return (
        <Input.TextArea
          rows={2}
          value={value as string | undefined}
          placeholder={fieldPlaceholder}
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
          placeholder={fieldPlaceholder}
          onChange={(number) => onChange(number)}
        />
      );
    default:
      return (
        <Input
          value={value as string | undefined}
          placeholder={fieldPlaceholder}
          onChange={(event) => onChange(event.target.value)}
        />
      );
  }
};

interface ReviewWorkspaceProps {
  onCurrentChange?: (sessionId: string | null) => void;
}

const ReviewWorkspace: React.FC<ReviewWorkspaceProps> = ({ onCurrentChange }) => {
  const { locale, t, td } = useI18n();
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
  const [queueSearch, setQueueSearch] = useState('');

  // 工具日志全局展开/折叠状态 (T 键切换)
  const [toolsCollapsed, setToolsCollapsed] = useState(false);

  // 编辑模式状态 (E 键切换)
  const [isEditingAssistant, setIsEditingAssistant] = useState(false);
  const [editedAssistantText, setEditedAssistantText] = useState('');
  const [originalAssistantText, setOriginalAssistantText] = useState('');
  const [assistantModified, setAssistantModified] = useState(false);

  const activeItemRef = useRef<HTMLDivElement | null>(null);

  const { data: extraFieldsData } = useAsyncData<ReviewerExtraFields>(() => reviewerApi.getExtraFields());
  const extraFields = useMemo(() => extraFieldsData?.fields ?? [], [extraFieldsData]);

  useEffect(() => {
    setQueue(data?.sessions ?? []);
    setIndex(0);
    setExpanded(false);
    setIsEditingAssistant(false);
    setAssistantModified(false);
  }, [data]);

  const current = queue[index] ?? null;
  const currentId = current?.session_id ?? null;

  useEffect(() => {
    setExtras({});
    setIsEditingAssistant(false);
    setAssistantModified(false);
    setEditedAssistantText('');
    setOriginalAssistantText('');
  }, [currentId]);

  useEffect(() => {
    onCurrentChange?.(currentId);
  }, [currentId, onCurrentChange]);

  const { data: contentData, loading: contentLoading } = useAsyncData<{ content?: SessionContent }>(
    () => (current ? sessionApi.getSessionContent(current.session_id) : Promise.resolve({ data: {} })),
    [currentId]
  );
  const content = contentData?.content ?? null;
  const rawMessages = useMemo(() => content?.messages ?? [], [content]);

  // 当加载新会话内容时，初始化提取最后一条 assistant 回复以备编辑与 Diff
  useEffect(() => {
    if (rawMessages.length > 0) {
      for (let i = rawMessages.length - 1; i >= 0; i--) {
        if (rawMessages[i].role === 'assistant') {
          const rawContent = rawMessages[i].content;
          let text = '';
          if (typeof rawContent === 'string') {
            text = td(rawContent);
          } else if (Array.isArray(rawContent)) {
            text = rawContent
              .map((item) =>
                item && typeof item === 'object' && typeof (item as { text?: unknown }).text === 'string'
                  ? td((item as { text: string }).text)
                  : ''
              )
              .filter(Boolean)
              .join('\n');
          }
          setOriginalAssistantText(text);
          setEditedAssistantText(text);
          break;
        }
      }
    }
  }, [rawMessages, td]);

  // 计算当前渲染的消息（若已被就地修改，替换最后一条 assistant 回复）
  const messages = useMemo(() => {
    if (!assistantModified || !editedAssistantText) return rawMessages;
    let found = false;
    const cloned = [...rawMessages];
    for (let i = cloned.length - 1; i >= 0; i--) {
      if (cloned[i].role === 'assistant') {
        cloned[i] = { ...cloned[i], content: editedAssistantText };
        found = true;
        break;
      }
    }
    return found ? cloned : rawMessages;
  }, [rawMessages, assistantModified, editedAssistantText]);

  const visibleMessages = expanded ? messages : messages.slice(0, PREVIEW_COUNT);

  // 待审队列检索过滤
  const filteredQueue = useMemo(() => {
    if (!queueSearch.trim()) return queue;
    const kw = queueSearch.toLowerCase();
    return queue.filter(
      (item) =>
        item.session_id.toLowerCase().includes(kw) ||
        (item.agent_role && item.agent_role.toLowerCase().includes(kw)) ||
        (item.task_type && item.task_type.toLowerCase().includes(kw))
    );
  }, [queue, queueSearch]);

  // 提交审核动作
  const handleReview = useCallback(async (approve: boolean) => {
    if (!current || submitting) return;

    for (const field of extraFields) {
      if (!field.required) continue;
      const value = extras[field.name];
      if (value === undefined || value === null || value === '') {
        const fieldLabel = td(field.label);
        message.warning(locale === 'zh' ? `请填写「${fieldLabel}」` : `Please fill in "${fieldLabel}"`);
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload: ReviewExtras = { ...extras };
      // 若修改了回复，写入 review_meta 以支撑 DPO 偏好对导出
      if (assistantModified && originalAssistantText && editedAssistantText) {
        payload['original_response'] = originalAssistantText;
        payload['chosen'] = editedAssistantText;
        payload['rejected'] = originalAssistantText;
        payload['diff_applied'] = true;
      }

      const finalPayload = Object.keys(payload).length > 0 ? payload : undefined;
      if (approve) {
        await reviewerApi.approveSession(current.session_id, notes, score, finalPayload);
        message.success(t('已通过评审', 'Session approved'));
      } else {
        await reviewerApi.rejectSession(current.session_id, notes, score, finalPayload);
        message.success(t('已拒绝', 'Session rejected'));
      }
      const next = queue.filter((item) => item.session_id !== current.session_id);
      setQueue(next);
      setIndex((prev) => Math.min(prev, Math.max(next.length - 1, 0)));
      setNotes('');
      setScore(3);
      setExtras({});
      setIsEditingAssistant(false);
      setAssistantModified(false);
      if (next.length === 0) {
        message.info(t('审核队列已清空', 'Review queue is now empty'));
        reload();
      }
    } catch {
      // 拦截器已统一提示
    } finally {
      setSubmitting(false);
    }
  }, [
    current,
    submitting,
    extraFields,
    extras,
    assistantModified,
    originalAssistantText,
    editedAssistantText,
    notes,
    score,
    queue,
    reload,
    locale,
    t,
    td,
  ]);

  // 保存 Assistant 消息编辑
  const handleSaveAssistantEdit = useCallback(() => {
    if (editedAssistantText !== originalAssistantText) {
      setAssistantModified(true);
      message.success(
        t('已应用修改（已建立 DPO 对抗偏好数据对）', 'Changes applied (DPO preference pair created)')
      );
    }
    setIsEditingAssistant(false);
  }, [editedAssistantText, originalAssistantText, t]);

  const handleCancelAssistantEdit = useCallback(() => {
    setEditedAssistantText(originalAssistantText);
    setIsEditingAssistant(false);
  }, [originalAssistantText]);

  // 全局键盘快捷键 Ergonomics
  // 1. A 或 Cmd+Enter: 通过并下一条
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

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isInput =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable;

      // 在 input/textarea 中，不拦截单键
      if (isInput) {
        return;
      }

      // 1. A 键快速通过
      if (e.key === 'a' || e.key === 'A') {
        e.preventDefault();
        if (current && score && !submitting) handleReview(true);
      }
      // 2. R 键快速拒绝
      else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        if (current && !submitting) handleReview(false);
      }
      // 3. 1 ~ 5 快速设定评分
      else if (['1', '2', '3', '4', '5'].includes(e.key)) {
        e.preventDefault();
        const num = parseInt(e.key, 10);
        setScore(num);
        message.info(
          locale === 'zh'
            ? `评分已设为: ${num} 星 (${getScoreLabel(num, locale)})`
            : `Score set to: ${num} (${getScoreLabel(num, locale)})`
        );
      }
      // 4. J 或 ↓: 队列下一条
      else if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown') {
        e.preventDefault();
        setIndex((prev) => Math.min(prev + 1, queue.length - 1));
      }
      // 5. K 或 ↑: 队列上一条
      else if (e.key === 'k' || e.key === 'K' || e.key === 'ArrowUp') {
        e.preventDefault();
        setIndex((prev) => Math.max(prev - 1, 0));
      }
      // 6. T: 一键折叠/展开全部超长工具调用日志
      else if (e.key === 't' || e.key === 'T') {
        e.preventDefault();
        setToolsCollapsed((prev) => {
          const next = !prev;
          message.info(
            next
              ? t('工具调用日志已折叠', 'Tool call logs collapsed')
              : t('工具调用日志已展开', 'Tool call logs expanded')
          );
          return next;
        });
      }
      // 7. E: 一键进入 Assistant 回复编辑模式
      else if (e.key === 'e' || e.key === 'E') {
        e.preventDefault();
        setIsEditingAssistant((prev) => !prev);
      }
      // 8. Esc: 退出编辑模式
      else if (e.key === 'Escape' && isEditingAssistant) {
        e.preventDefault();
        handleCancelAssistantEdit();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    current,
    score,
    submitting,
    queue.length,
    isEditingAssistant,
    originalAssistantText,
    editedAssistantText,
    handleReview,
    handleCancelAssistantEdit,
    locale,
    t,
  ]);

  const progressPercent = queue.length > 0 ? Math.round(((index + 1) / queue.length) * 100) : 0;

  // 对话流渲染
  const messageSection = useMemo(() => {
    if (messages.length === 0) {
      return (
        <EmptyState
          description={loading || contentLoading ? t('加载中…', 'Loading…') : t('暂无对话内容', 'No dialogue content')}
        />
      );
    }
    return (
      <Flex vertical gap={16}>
        {visibleMessages.map((msg, i) => {
          const isLastAssistant =
            msg.role === 'assistant' &&
            i === messages.map((m) => m.role).lastIndexOf('assistant');

          return (
            <div key={i} className={`message-item-wrapper ${isLastAssistant && assistantModified ? 'edited' : ''}`}>
              <MessageBubble message={msg} index={i} toolsCollapsed={toolsCollapsed} />

              {/* 若为最后一条 Assistant 回复且进入编辑模式 */}
              {isLastAssistant && isEditingAssistant && (
                <div className="assistant-edit-box">
                  <Flex justify="space-between" align="center" wrap="wrap" gap={6} style={{ marginBottom: 8 }}>
                    <Typography.Text strong style={{ color: '#2563eb', fontSize: 13, whiteSpace: 'nowrap' }}>
                      <EditOutlined />{' '}
                      {t('编辑 AI 回复（就地修正，生产 DPO 对齐数据）', 'Edit AI Reply (In-place DPO Refinement)')}
                    </Typography.Text>
                    <Space size={6} style={{ flexShrink: 0 }}>
                      <Button size="small" icon={<UndoOutlined />} onClick={handleCancelAssistantEdit}>
                        {t('放弃修改 (Esc)', 'Discard (Esc)')}
                      </Button>
                      <Button
                        type="primary"
                        size="small"
                        icon={<SaveOutlined />}
                        onClick={handleSaveAssistantEdit}
                      >
                        {t('保存修改并生成 Diff', 'Save & Generate Diff')}
                      </Button>
                    </Space>
                  </Flex>
                  <Input.TextArea
                    rows={4}
                    value={editedAssistantText}
                    onChange={(e) => setEditedAssistantText(e.target.value)}
                    placeholder={t('在此编辑修正 AI 的回复...', 'Edit and refine the Assistant reply here...')}
                  />
                  {/* 实时修改 Diff 对比 */}
                  {editedAssistantText !== originalAssistantText && (
                    <DiffViewer original={originalAssistantText} modified={editedAssistantText} />
                  )}
                </div>
              )}

              {/* 若已保存修改且未处于编辑模式，展示 Diff 提示 */}
              {isLastAssistant && !isEditingAssistant && assistantModified && (
                <div style={{ marginTop: 8 }}>
                  <DiffViewer original={originalAssistantText} modified={editedAssistantText} />
                </div>
              )}
            </div>
          );
        })}

        {messages.length > PREVIEW_COUNT && (
          <Button
            type="link"
            icon={expanded ? <UpOutlined /> : <DownOutlined />}
            onClick={() => setExpanded((prev) => !prev)}
          >
            {expanded
              ? t('收起对话', 'Collapse Dialogue')
              : locale === 'zh'
                ? `展开剩余 ${messages.length - PREVIEW_COUNT} 条`
                : `Show ${messages.length - PREVIEW_COUNT} More`}
          </Button>
        )}
      </Flex>
    );
  }, [
    messages,
    visibleMessages,
    expanded,
    loading,
    contentLoading,
    isEditingAssistant,
    editedAssistantText,
    originalAssistantText,
    assistantModified,
    toolsCollapsed,
    handleCancelAssistantEdit,
    handleSaveAssistantEdit,
    locale,
    t,
  ]);

  if (!loading && queue.length === 0) {
    return (
      <Card variant="borderless">
        <EmptyState
          description={t(
            '审核队列已清空，去会话页看看新数据吧',
            'Review queue is empty. Check Sessions for new data.'
          )}
        >
          <Button type="primary" onClick={reload} icon={<RightOutlined />}>
            {t('刷新队列', 'Refresh Queue')}
          </Button>
        </EmptyState>
      </Card>
    );
  }

  return (
    <div className="review-workspace-3col review-workspace">
      {/* ================= 一、左侧待审会话队列 (20%) ================= */}
      <div className="review-col-queue">
        <Card variant="borderless" className="queue-card">
          <Flex justify="space-between" align="center" style={{ marginBottom: 8 }}>
            <Typography.Text strong>
              {t('待审队列', 'Queue')} ({queue.length})
            </Typography.Text>
            <Tooltip title={t('刷新待审列表', 'Refresh Queue')}>
              <Button size="small" type="text" onClick={reload} icon={<RightOutlined />} />
            </Tooltip>
          </Flex>

          <Input
            size="small"
            placeholder={t('搜索 ID / 角色...', 'Search ID / role...')}
            prefix={<SearchOutlined />}
            value={queueSearch}
            onChange={(e) => setQueueSearch(e.target.value)}
            style={{ marginBottom: 10 }}
            allowClear
          />

          <div className="queue-list-scroll">
            {filteredQueue.map((item) => {
              const itemIdx = queue.findIndex((q) => q.session_id === item.session_id);
              const isActive = itemIdx === index;

              return (
                <div
                  key={item.session_id}
                  ref={isActive ? activeItemRef : null}
                  className={`queue-item ${isActive ? 'active' : ''}`}
                  onClick={() => setIndex(itemIdx)}
                >
                  {isActive && <span className="queue-item-cursor">▶</span>}
                  <Flex justify="space-between" align="center" gap={6} style={{ marginLeft: isActive ? 8 : 0 }}>
                    <Typography.Text
                      strong={isActive}
                      title={item.session_id}
                      style={{
                        fontFamily: 'ui-monospace, monospace',
                        fontSize: 11,
                        color: isActive ? '#2563eb' : '#1e293b',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        minWidth: 0,
                        flex: 1,
                      }}
                    >
                      {truncateSessionId(item.session_id)}
                    </Typography.Text>
                    {item.quality_auto_score !== null && item.quality_auto_score !== undefined && (
                      <ScoreTag score={item.quality_auto_score} />
                    )}
                  </Flex>
                  <Flex justify="space-between" align="center" gap={6} style={{ marginTop: 4, marginLeft: isActive ? 8 : 0 }}>
                    <Typography.Text
                      type="secondary"
                      style={{
                        fontSize: 11,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        minWidth: 0,
                        flex: 1,
                      }}
                    >
                      {td(item.agent_role || 'assistant')}
                    </Typography.Text>
                    <Typography.Text type="secondary" style={{ fontSize: 10, whiteSpace: 'nowrap', flexShrink: 0 }}>
                      #{itemIdx + 1}
                    </Typography.Text>
                  </Flex>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* ================= 二、中间对话流与工具日志 (55%) ================= */}
      <div className="review-col-content review-main">
        {/* 会话顶部进度与快速导航 */}
        <Card variant="borderless" className="review-progress-card" loading={loading && queue.length === 0}>
          <Flex justify="space-between" align="center" gap={12} wrap>
            <div className="review-progress" style={{ flex: 1, minWidth: 200 }}>
              <Flex align="center" gap={8} wrap>
                <Typography.Text strong style={{ whiteSpace: 'nowrap' }}>
                  {locale === 'zh'
                    ? `第 ${Math.min(index + 1, queue.length)} / ${queue.length} 条`
                    : `Item ${Math.min(index + 1, queue.length)} / ${queue.length}`}
                </Typography.Text>
                {current && <StatusTag status={current.status} />}
                {currentId && (
                  <CopyText
                    text={currentId}
                    mono
                    display={<span style={{ fontSize: 12 }}>{truncateSessionId(currentId)}</span>}
                  />
                )}
                {assistantModified && (
                  <Tag color="purple" icon={<DiffOutlined />}>
                    {t('已就地编辑 (含 DPO 对)', 'Edited (DPO Pair)')}
                  </Tag>
                )}
              </Flex>
              <Progress percent={progressPercent} showInfo={false} size="small" style={{ marginTop: 8 }} />
            </div>
            <Space size={8} style={{ flexShrink: 0 }}>
              <Button
                size="small"
                icon={<LeftOutlined />}
                disabled={index === 0}
                onClick={() => setIndex((prev) => Math.max(prev - 1, 0))}
              >
                {t('上一个 (K)', 'Prev (K)')}
              </Button>
              <Button
                size="small"
                icon={<RightOutlined />}
                disabled={index >= queue.length - 1}
                onClick={() => setIndex((prev) => Math.min(prev + 1, queue.length - 1))}
                iconPosition="end"
              >
                {t('下一个 (J)', 'Next (J)')}
              </Button>
            </Space>
          </Flex>
        </Card>

        {/* 对话内容主卡片 */}
        <Card
          variant="borderless"
          title={
            <Flex justify="space-between" align="center">
              <span>{t('对话内容', 'Dialogue')}</span>
              <Space size={8}>
                <Button
                  size="small"
                  icon={<ToolOutlined />}
                  onClick={() => setToolsCollapsed((prev) => !prev)}
                >
                  {toolsCollapsed
                    ? t('展开工具日志 (T)', 'Expand Tools (T)')
                    : t('折叠工具日志 (T)', 'Collapse Tools (T)')}
                </Button>
                <Button
                  size="small"
                  type={isEditingAssistant ? 'primary' : 'default'}
                  icon={<EditOutlined />}
                  onClick={() => setIsEditingAssistant((prev) => !prev)}
                >
                  {isEditingAssistant
                    ? t('退出编辑 (Esc)', 'Exit Edit (Esc)')
                    : t('编辑 AI 回复 (E)', 'Edit Reply (E)')}
                </Button>
              </Space>
            </Flex>
          }
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
                  label: <Typography.Text type="secondary">{t('技术元信息', 'Technical Metadata')}</Typography.Text>,
                  children: <JsonView value={content.metadata} maxHeight={280} />,
                },
              ]}
            />
          )}
        </Card>
      </div>

      {/* ================= 三、右侧悬浮固定决策面板 (25%) ================= */}
      <div className="review-col-decision review-side-panel">
        <Card variant="borderless" title={t('评审决策', 'Decision')} className="decision-card">
          <Flex vertical gap={16}>
            {/* 评分区块 */}
            <div>
              <Flex justify="space-between" align="center" style={{ marginBottom: 6 }}>
                <Typography.Text strong style={{ whiteSpace: 'nowrap' }}>
                  {t('质量评分 (直按 1~5 键)', 'Score (Keys 1~5)')}
                </Typography.Text>
                <Tag color={getScoreColor(score)} style={{ marginInlineEnd: 0 }}>
                  {getScoreTagLabel(score, locale)}
                </Tag>
              </Flex>
              <Rate allowClear value={score} onChange={setScore} tooltips={getScoreLabels(locale)} />
              {current?.quality_auto_score !== null && current?.quality_auto_score !== undefined && (
                <Flex justify="space-between" align="center" style={{ marginTop: 8 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {t('自动评分对比', 'Auto Score')}
                  </Typography.Text>
                  <Space size={4}>
                    <ScoreTag score={current.quality_auto_score} />
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {getScoreLabel(current.quality_auto_score, locale)}
                    </Typography.Text>
                  </Space>
                </Flex>
              )}
            </div>

            {/* 评审意见输入 */}
            <div>
              <Typography.Text strong style={{ display: 'block', marginBottom: 6 }}>
                {t('评审意见', 'Review Notes')}
              </Typography.Text>
              <Input.TextArea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={t('可选评审备注，最多 200 字', 'Optional review notes (max 200 chars)')}
                showCount
                maxLength={200}
              />
            </div>

            {/* 插件扩展字段 */}
            {extraFields.length > 0 && (
              <div>
                <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>
                  {t('插件扩展字段', 'Plugin Fields')}
                </Typography.Text>
                <Flex vertical gap={12}>
                  {extraFields.map((field) => (
                    <div key={field.name}>
                      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>
                        {td(field.label)}
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

            {/* 决策大按钮组 */}
            <Flex vertical gap={10}>
              <Button
                type="primary"
                size="large"
                block
                className="decision-action-btn-approve"
                icon={<CheckOutlined />}
                loading={submitting}
                disabled={!current || !score}
                onClick={() => handleReview(true)}
              >
                {t('通过评审', 'Approve')}
              </Button>
              <Button
                danger
                size="large"
                block
                className="decision-action-btn-reject"
                icon={<CloseOutlined />}
                loading={submitting}
                disabled={!current}
                onClick={() => handleReview(false)}
              >
                {t('拒绝', 'Reject')}
              </Button>
            </Flex>

            <Divider style={{ margin: '4px 0' }} />

            {/* 人体工学快捷键速查面板 */}
            <div className="shortcuts-panel">
              <Typography.Text strong style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                {t('极速全键盘操作指南', 'Keyboard Shortcuts')}
              </Typography.Text>
              <Flex vertical gap={6} style={{ fontSize: 11 }}>
                <Flex justify="space-between" align="center" gap={8}>
                  <kbd className="shortcut-badge">A / {MOD_KEY}+Enter</kbd>
                  <Typography.Text type="secondary" className="shortcut-desc">
                    {t('通过并切下一条', 'Approve & Next')}
                  </Typography.Text>
                </Flex>
                <Flex justify="space-between" align="center" gap={8}>
                  <kbd className="shortcut-badge">R / {MOD_KEY}+Backspace</kbd>
                  <Typography.Text type="secondary" className="shortcut-desc">
                    {t('拒绝并切下一条', 'Reject & Next')}
                  </Typography.Text>
                </Flex>
                <Flex justify="space-between" align="center" gap={8}>
                  <kbd className="shortcut-badge">1 ~ 5</kbd>
                  <Typography.Text type="secondary" className="shortcut-desc">
                    {t('设定质量星级', 'Set Star Rating')}
                  </Typography.Text>
                </Flex>
                <Flex justify="space-between" align="center" gap={8}>
                  <kbd className="shortcut-badge">
                    {locale === 'zh' ? 'J / K 或 ↓ / ↑' : 'J / K / ↓ / ↑'}
                  </kbd>
                  <Typography.Text type="secondary" className="shortcut-desc">
                    {t('在队列中上下切换', 'Prev / Next Item')}
                  </Typography.Text>
                </Flex>
                <Flex justify="space-between" align="center" gap={8}>
                  <kbd className="shortcut-badge">T</kbd>
                  <Typography.Text type="secondary" className="shortcut-desc">
                    {t('折叠/展开工具日志', 'Toggle Tool Logs')}
                  </Typography.Text>
                </Flex>
                <Flex justify="space-between" align="center" gap={8}>
                  <kbd className="shortcut-badge">E</kbd>
                  <Typography.Text type="secondary" className="shortcut-desc">
                    {t('编辑 AI 回复与 Diff', 'Edit & DPO Diff')}
                  </Typography.Text>
                </Flex>
              </Flex>
            </div>
          </Flex>
        </Card>
      </div>
    </div>
  );
};

const getScoreTagLabel = (score: number, locale: Locale): string => `${score} · ${getScoreLabel(score, locale)}`;

export default ReviewWorkspace;
