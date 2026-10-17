import React, { useState } from 'react';
import { Form, Input, Modal, Rate, Select, message } from 'antd';
import { sessionApi } from '../../services';
import { STATUS_LABELS, STATUS_LABELS_EN } from '../../constants/display';
import { getAllowedStatusTransitions, getStatusLabel } from '../../utils';
import { useI18n } from '../../i18n';
import type { Session, SessionUpdateParams } from '../../types';

interface SessionEditModalProps {
  open: boolean;
  session: Session | null;
  onClose: () => void;
  onSaved: () => void;
}

const SessionEditModal: React.FC<SessionEditModalProps> = ({ open, session, onClose, onSaved }) => {
  const { locale, t } = useI18n();
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

  const handleOk = async () => {
    if (!session) return;
    const values = await form.validateFields();
    const payload: SessionUpdateParams = {
      status: values.status,
      quality_manual_score: values.quality_manual_score ?? undefined,
      agent_role: values.agent_role,
      task_type: values.task_type,
      tags: values.tags,
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
            agent_role: session.agent_role ?? undefined,
            task_type: session.task_type ?? undefined,
            tags: session.tags ?? [],
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
            <Input placeholder={t('如 backend_dev', 'e.g. backend_dev')} allowClear />
          </Form.Item>
          <Form.Item name="task_type" label={t('任务类型', 'Task Type')}>
            <Input placeholder={t('如 coding', 'e.g. coding')} allowClear />
          </Form.Item>
          <Form.Item name="tags" label={t('标签', 'Tags')}>
            <Select mode="tags" placeholder={t('输入后回车添加标签', 'Press Enter to add tags')} open={false} suffixIcon={null} />
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
