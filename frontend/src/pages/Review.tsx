import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Button, Tag, Rate, Input, message } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { reviewerApi } from '../services/api';
import type { Session } from '../types';

const { TextArea } = Input;

const Review: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex] = useState(0);
  const [score, setScore] = useState(3);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    loadPendingSessions();
  }, []);

  const loadPendingSessions = async () => {
    setLoading(true);
    try {
      const res = await reviewerApi.getPending(1, 20);
      setSessions(res.data.sessions || []);
    } catch (error) {
      console.error('Failed to load pending sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!sessions[selectedIndex]) return;
    try {
      await reviewerApi.approveSession(sessions[selectedIndex].session_id, notes);
      message.success('Session approved');
      setNotes('');
      setScore(3);
      loadPendingSessions();
    } catch (error) {
      message.error('Failed to approve session');
    }
  };

  const handleReject = async () => {
    if (!sessions[selectedIndex]) return;
    try {
      await reviewerApi.rejectSession(sessions[selectedIndex].session_id, notes);
      message.success('Session rejected');
      setNotes('');
      setScore(3);
      loadPendingSessions();
    } catch (error) {
      message.error('Failed to reject session');
    }
  };

  const currentSession = sessions[selectedIndex];

  return (
    <div>
      <h1>Review</h1>
      <Row gutter={16}>
        <Col span={16}>
          <Card title="Pending Sessions" loading={loading}>
            {sessions.length === 0 ? (
              <p>No pending sessions to review</p>
            ) : (
              <div>
                <p><strong>Session {selectedIndex + 1} of {sessions.length}</strong></p>
                <p>ID: {currentSession?.session_id}</p>
                <p>Status: <Tag>{currentSession?.status}</Tag></p>
                <p>Auto Score: {currentSession?.quality_auto_score}</p>
              </div>
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Actions">
            <div style={{ marginBottom: 16 }}>
              <p><strong>Manual Rating:</strong></p>
              <Rate value={score} onChange={setScore} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <p><strong>Notes:</strong></p>
              <TextArea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={handleApprove}
              disabled={!currentSession}
              block
              style={{ marginBottom: 8 }}
            >
              Approve
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              onClick={handleReject}
              disabled={!currentSession}
              block
            >
              Reject
            </Button>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Review;
