import React from 'react';
import { Typography } from 'antd';
import type { Message } from '../../types';
import { ROLE_LABELS } from '../../constants/display';
import RoleAvatar from './RoleAvatar';
import JsonView from './JsonView';
import ToolCallList from './ToolCallList';

interface MessageBubbleProps {
  message: Message;
  index: number;
}

const renderContent = (content: unknown): React.ReactNode => {
  if (content === null || content === undefined || content === '') {
    return <Typography.Text type="secondary">（空消息）</Typography.Text>;
  }
  if (typeof content === 'string') {
    return content;
  }
  if (Array.isArray(content)) {
    const texts = content
      .map((item) => {
        if (item && typeof item === 'object' && typeof (item as { text?: unknown }).text === 'string') {
          return (item as { text: string }).text;
        }
        return null;
      })
      .filter((text): text is string => Boolean(text));
    if (texts.length > 0) {
      return texts.join('\n');
    }
  }
  return <JsonView value={content} maxHeight={240} />;
};

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, index }) => {
  return (
    <div className={`message-bubble ${message.role}`}>
      <RoleAvatar role={message.role} className="bubble-avatar" />
      <div className="bubble-content">
        <div className="bubble-header">
          <span className="bubble-role">{ROLE_LABELS[message.role] ?? message.role}</span>
          <span className="bubble-index">#{index + 1}</span>
        </div>
        <div className="bubble-text">{renderContent(message.content)}</div>
        <ToolCallList toolCalls={message.tool_calls} />
      </div>
    </div>
  );
};

export default MessageBubble;
