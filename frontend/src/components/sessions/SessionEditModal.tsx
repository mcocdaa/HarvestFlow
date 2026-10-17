import React, { useEffect, useMemo, useState } from 'react';
import { Form, Input, Modal, Rate, Select, message } from 'antd';
import { sessionApi } from '../../services';
import { STATUS_LABELS, STATUS_LABELS_EN } from '../../constants/display';
import { getAllowedStatusTransitions, getStatusLabel } from '../../utils';
import { TAG_CANONICAL_SLUGS, toCanonicalSlug, useI18n } from '../../i18n';
import type { Session, SessionUpdateParams } from '../../types';

interface SessionEditModalProps {
  open: boolean;
  session: Session | null;
  onClose: () => void;
  onSaved: () => void;
}

const SessionEditModal: React.FC<SessionEditModalProps> = ({ open, session, onClose, onSaved }) => {
  const { locale, t, td } = useI18n();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const statusLabels = locale === 'zh' ? STATUS_LABELS : STATUS_LABELS_EN;

  const statusOptions = session
    ? [session.status, ...getAllowedStatusTransitions(session.status)].map((status) => ({
        value: status,
        label:
          status === session.status
            ? locale === 'zh'
              ? `${getStatusLabel(status, locale)}（当前）`
              : `${getStatusLabel(status, locale)} (Current)`
            : getStatusLabel(status, locale),
      }))
    : [];

  const tagOptions = useMemo(() => {
    const rawTags = new Set<string>(TAG_CANONICAL_SLUGS);
    (session?.tags ?? []).forEach((tag) => {
      rawTags.add(toCanonicalSlug(tag, 'tag'));
    });
    return Array.from(rawTags)
      .filter(Boolean)
      .map((slug) => ({
        value: slug,
        label: td(slug) || slug,
      }));
  }, [session?.tags, td]);

  // 当打开弹窗或切换语言时，实时同步表单中的 Agent 角色、任务类型与标签展示文本
  useEffect(() => {
    if (!open || !session) return;
    const currentRole = form.getFieldValue('agent_role') ?? session.agent_role;
    const currentTask = form.getFieldValue('task_type') ?? session.task_type;
    const currentTags: string[] = form.getFieldValue('tags') ?? session.tags ?? [];

    const canonicalRole = currentRole
      ? toCanonicalSlug(String(currentRole), 'role', session.agent_role)
      : undefined;
    const canonicalTask = currentTask
      ? toCanonicalSlug(String(currentTask), 'task', session.task_type)
      : undefined;
    const canonicalTags = Array.isArray(currentTags)
      ? currentTags.map((tag) => toCanonicalSlug(String(tag), 'tag')).filter(Boolean)
      : [];

    form.setFieldsValue({
      agent_role: canonicalRole ? td(canonicalRole) : undefined,
      task_type: canonicalTask ? td(canonicalTask) : undefined,
      tags: canonicalTags,
    });
  }, [open, session, locale, td, form]);

  const handleOk = async () => {
    if (!session) return;
    const values = await form.validateFields();
    const canonicalRole = values.agent_role
      ? toCanonicalSlug(String(values.agent_role), 'role', session.agent_role)
      : values.agent_role;
    const canonicalTask = values.task_type
      ? toCanonicalSlug(String(values.task_type), 'task', session.task_type)
      : values.task_type;
    const canonicalTags = Array.isArray(values.tags)
      ? values.tags.map((tag: string) => toCanonicalSlug(String(tag), 'tag')).filter(Boolean)
      : values.tags;

    const payload: SessionUpdateParams = {
      status: values.status,
      quality_manual_score: values.quality_manual_score ?? undefined,
      agent_role: canonicalRole,
      task_type: canonicalTask,
      tags: canonicalTags,
      tools_used: values.tools_used,
    };
    if (payload.status === session.status) {
      delete payload.status;
    }
    setSubmitting(true);
    try {
      await sessionApi.updateSession(session.session_id, payload);
      message.success(t('会话已更新', 'Session updated'));
      onSaved();
      onClose();
    } catch {
      // 拦截器已统一提示
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      title={t('编辑会话', 'Edit Session')}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={submitting}
      okText={t('保存', 'Save')}
      cancelText={t('取消', 'Cancel')}
      destroyOnHidden
      width={560}
    >
      {session && (
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: session.status,
            quality_manual_score: session.quality_manual_score ?? undefined,
            agent_role: session.agent_role
              ? td(toCanonicalSlug(session.agent_role, 'role', session.agent_role))
              : undefined,
            task_type: session.task_type
              ? td(toCanonicalSlug(session.task_type, 'task', session.task_type))
              : undefined,
            tags: (session.tags ?? []).map((tag) => toCanonicalSlug(tag, 'tag')).filter(Boolean),
            tools_used: session.tools_used ?? [],
          }}
        >
          <Form.Item
            name="status"
            label={t('状态', 'Status')}
            extra={
              locale === 'zh'
                ? `后端仅允许合法流转：${statusLabels.raw} → ${statusLabels.curated} → ${statusLabels.approved}/${statusLabels.rejected}`
                : `Allowed transitions: ${statusLabels.raw} → ${statusLabels.curated} → ${statusLabels.approved}/${statusLabels.rejected}`
            }
          >
            <Select options={statusOptions} />
          </Form.Item>
          <Form.Item name="quality_manual_score" label={t('人工评分', 'Manual Score')}>
            <Rate count={5} />
          </Form.Item>
          <Form.Item name="agent_role" label={t('Agent 角色', 'Agent Role')}>
            <Input placeholder={t('如 后端开发', 'e.g. Backend Engineer')} allowClear />
          </Form.Item>
          <Form.Item name="task_type" label={t('任务类型', 'Task Type')}>
            <Input placeholder={t('如 编码与重构', 'e.g. Coding & Refactoring')} allowClear />
          </Form.Item>
          <Form.Item name="tags" label={t('标签', 'Tags')}>
            <Select
              mode="tags"
              options={tagOptions}
              placeholder={t('输入后回车添加标签', 'Press Enter to add tags')}
              open={false}
              suffixIcon={null}
            />
          </Form.Item>
          <Form.Item name="tools_used" label={t('使用工具', 'Tools Used')}>
            <Select mode="tags" placeholder={t('输入后回车添加工具名', 'Press Enter to add tools')} open={false} suffixIcon={null} />
          </Form.Item>
        </Form>
      )}
    </Modal>
  );
};

export default SessionEditModal;
