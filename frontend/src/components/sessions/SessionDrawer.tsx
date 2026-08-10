import React from 'react';
import { Drawer, Typography, Collapse } from 'antd';
import { CopyOutlined } from '@ant-design/icons';
import { getStatusColor, copyToClipboard } from '../../utils';
import type { Session, SessionContent } from '../../types';
import { MessageBubble } from '../common';

const { Text } = Typography;
const { Panel } = Collapse;

interface SessionDrawerProps {
  visible: boolean;
  onClose: () => void;
  session: Session | null;
  content: SessionContent | null;
}

const SessionDrawer: React.FC<SessionDrawerProps> = ({
  visible,
  onClose,
  session,
  content,
}) => {
  const getFirstMessageSummary = (): string => {
    if (!session?.task_type) return '无摘要信息';
    return session.task_type;
  };

  const renderMessages = () => {
    if (!content?.messages) {
      return <Text className="empty-value">暂无对话内容</Text>;
    }

    return (
      <div className="message-timeline">
        {content.messages.map((msg, index) => (
          <MessageBubble key={index} message={msg} index={index} />
        ))}
      </div>
    );
  };

  const METADATA_KEYS = ['agent_role', 'task_type', 'created_at', 'tools_used', 'tags'];

  const renderMetadata = () => {
    if (!content || Object.keys(content).length === 0) {
      return <Text className="empty-value">暂无元数据</Text>;
    }

    const metadataKeys = METADATA_KEYS.filter(key =>
      content[key] !== undefined && content[key] !== null && content[key] !== ''
    );

    return (
      <Collapse ghost>
        <Panel header="技术详情" key="metadata">
          {metadataKeys.map(key => (
            <div key={key} className="metadata-item">
              <Text className="metadata-label">{key}:</Text>
              <Text className="metadata-value">
                {typeof content[key] === 'object'
                  ? JSON.stringify(content[key])
                  : String(content[key])}
              </Text>
            </div>
          ))}
        </Panel>
      </Collapse>
    );
  };

  return (
    <Drawer
      className="session-drawer"
      title={null}
      placement="right"
      width={480}
      open={visible}
      onClose={onClose}
      destroyOnClose
    >
      {session && (
        <div className="drawer-content">
          <div className="drawer-header">
            <div className="status-badge">
              <div
                className="status-badge-bar"
                style={{ backgroundColor: getStatusColor(session.status) }}
              />
              <span className="status-badge-text">{session.status}</span>
            </div>
            <div className="drawer-title">
              <h2>{getFirstMessageSummary()}</h2>
              <div className="drawer-subtitle">
                <Text className="session-full-id" onClick={() => copyToClipboard(session.session_id)}>
                  ID: {session.session_id} <CopyOutlined />
                </Text>
              </div>
            </div>
          </div>

          <div className="score-cards">
            <div className="score-card">
              <Text className="score-label">自动评分</Text>
              <div className="score-value">
                {session.quality_auto_score !== null && session.quality_auto_score !== undefined ? (
                  session.quality_auto_score
                ) : (
                  <Text className="empty-value">-</Text>
                )}
              </div>
            </div>
            <div className="score-card highlighted">
              <Text className="score-label">人工评分</Text>
              <div className="score-value">
                {session.quality_manual_score !== null && session.quality_manual_score !== undefined ? (
                  session.quality_manual_score
                ) : (
                  <Text className="empty-value">-</Text>
                )}
              </div>
            </div>
          </div>

          <div className="drawer-section">
            <h3 className="section-title">对话内容</h3>
            {renderMessages()}
          </div>

          <div className="drawer-section">
            <div className="section-meta">
              {session.agent_role && (
                <div className="meta-row">
                  <Text className="meta-label">Agent 角色:</Text>
                  <Text className="meta-value">{session.agent_role}</Text>
                </div>
              )}
              {session.task_type && (
                <div className="meta-row">
                  <Text className="meta-label">任务类型:</Text>
                  <Text className="meta-value">{session.task_type}</Text>
                </div>
              )}
              <div className="meta-row">
                <Text className="meta-label">创建时间:</Text>
                <Text className="meta-value">{session.created_at}</Text>
              </div>
            </div>
          </div>

          <div className="drawer-section">
            {renderMetadata()}
          </div>
        </div>
      )}
    </Drawer>
  );
};

export default SessionDrawer;
