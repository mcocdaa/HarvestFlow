import React, { useState } from 'react';
import { Form, Input, Modal, Rate, Select, message } from 'antd';
import { sessionApi } from '../../services';
import { STATUS_LABELS } from '../../constants/display';
import { getAllowedStatusTransitions, getStatusLabel } from '../../utils';
import type { Session, SessionUpdateParams } from '../../types';

interface SessionEditModalProps {
  open: boolean;
  session: Session | null;
  onClose: () => void;
  onSaved: () => void;
}

const SessionEditModal: React.FC<SessionEditModalProps> = ({ open, session, onClose, onSaved }) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const statusOptions = session
    ? [session.status, ...getAllowedStatusTransitions(session.status)].map((status) => ({
        value: status,
        label:
          status === session.status
            ? `${getStatusLabel(status)}（当前）`
            : getStatusLabel(status),
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
      message.success('会话已更新');
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
      title="编辑会话"
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={submitting}
      okText="保存"
      cancelText="取消"
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
            label="状态"
            extra={`后端仅允许合法流转：${STATUS_LABELS.raw} → ${STATUS_LABELS.curated} → ${STATUS_LABELS.approved}/${STATUS_LABELS.rejected}`}
          >
            <Select options={statusOptions} />
          </Form.Item>
          <Form.Item name="quality_manual_score" label="人工评分">
            <Rate count={5} />
          </Form.Item>
          <Form.Item name="agent_role" label="Agent 角色">
            <Input placeholder="如 backend_dev" allowClear />
          </Form.Item>
          <Form.Item name="task_type" label="任务类型">
            <Input placeholder="如 coding" allowClear />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入后回车添加标签" open={false} suffixIcon={null} />
          </Form.Item>
          <Form.Item name="tools_used" label="使用工具">
            <Select mode="tags" placeholder="输入后回车添加工具名" open={false} suffixIcon={null} />
          </Form.Item>
        </Form>
      )}
    </Modal>
  );
};

export default SessionEditModal;
