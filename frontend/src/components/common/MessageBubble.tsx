import React from 'react';
import { Typography } from 'antd';
import type { Message } from '../../types';
import { getRoleLabel } from '../../constants/display';
import { useI18n } from '../../i18n';
import RoleAvatar from './RoleAvatar';
import JsonView from './JsonView';
import ToolCallList from './ToolCallList';

interface MessageBubbleProps {
  message: Message;
  index: number;
  toolsCollapsed?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, index, toolsCollapsed = false }) => {
  const { locale, t, td } = useI18n();

  const renderContent = (content: unknown): React.ReactNode => {
    if (content === null || content === undefined || content === '') {
      return <Typography.Text type="secondary">{t('（空消息）', '(Empty message)')}</Typography.Text>;
    }
    if (typeof content === 'string') {
      return td(content);
    }
    if (Array.isArray(content)) {
      const texts = content
        .map((item) => {
          if (item && typeof item === 'object') {
            const rec = item as { text?: unknown; thinking?: unknown; content?: unknown };
            if (typeof rec.text === 'string') return td(rec.text);
            if (typeof rec.thinking === 'string') return td(rec.thinking);
            if (typeof rec.content === 'string') return td(rec.content);
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

  return (
    <div className={`message-bubble ${message.role}`}>
      <RoleAvatar role={message.role} className="bubble-avatar" />
      <div className="bubble-content">
        <div className="bubble-header">
          <span className="bubble-role">{getRoleLabel(message.role, locale)}</span>
          <span className="bubble-index">#{index + 1}</span>
        </div>
        <div className="bubble-text">{renderContent(message.content)}</div>
        <ToolCallList toolCalls={message.tool_calls} collapsed={toolsCollapsed} />
      </div>
    </div>
  );
};

export default MessageBubble;
