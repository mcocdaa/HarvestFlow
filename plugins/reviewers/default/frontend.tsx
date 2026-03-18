// @file plugins/reviewers/default/frontend.tsx
// @brief 默认人工审核插件前端组件
// @create 2026-03-18

import React, { useState } from 'react';
import { Card, Button, Tag, Input, Rate } from 'antd';

const { TextArea } = Input;

interface ReviewPanelProps {
  session: any;
  onApprove: (notes: string) => void;
  onReject: (notes: string) => void;
}

const ReviewPanel: React.FC<ReviewPanelProps> = ({ session, onApprove, onReject }) => {
  const [notes, setNotes] = useState('');
  const [score, setScore] = useState(3);

  const handleApprove = () => {
    onApprove(notes);
    setNotes('');
    setScore(3);
  };

  const handleReject = () => {
    onReject(notes);
    setNotes('');
    setScore(3);
  };

  return (
    <Card title="Session Review" size="small">
      <div style={{ marginBottom: 16 }}>
        <strong>Session ID:</strong> {session?.session_id}
      </div>

      <div style={{ marginBottom: 16 }}>
        <strong>Status:</strong> <Tag color="blue">{session?.status}</Tag>
      </div>

      <div style={{ marginBottom: 16 }}>
        <strong>Auto Score:</strong> {session?.quality_auto_score || 'N/A'}
      </div>

      <div style={{ marginBottom: 16 }}>
        <strong>Manual Rating:</strong>
        <div>
          <Rate value={score} onChange={setScore} />
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <strong>Notes:</strong>
        <TextArea
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add review notes..."
        />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <Button type="primary" onClick={handleApprove}>
          Approve
        </Button>
        <Button danger onClick={handleReject}>
          Reject
        </Button>
      </div>
    </Card>
  );
};

export default ReviewPanel;
