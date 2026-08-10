import React from 'react';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
  index: number;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, index }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="bubble-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="bubble-content">
        <div className="bubble-header">
          <span className="bubble-role">{isUser ? '用户' : 'AI'}</span>
          <span className="bubble-index">#{index + 1}</span>
        </div>
        <div className="bubble-text">
          {typeof message.content === 'string' ? message.content : JSON.stringify(message.content, null, 2)}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
