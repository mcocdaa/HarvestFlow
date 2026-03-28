import React, { useEffect, useState } from 'react';
import { Card, Button, Tag, Rate, Input, message, Progress, Space, Tooltip, Popconfirm, Collapse } from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  LeftOutlined,
  RightOutlined,
  CopyOutlined,
  ExpandOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';
import { reviewerApi, sessionApi } from '../services';
import { getScoreLabel, getScoreColor, getScoreTag, copyToClipboard, truncateSessionId, scoreLabels } from '../utils';
import { useKeyboardShortcut } from '../hooks';
import type { Session, SessionContent, Message } from '../types';
import '../styles/Review.css';

const { TextArea } = Input;
const { Panel } = Collapse;

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

const Review: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [score, setScore] = useState(3);
  const [notes, setNotes] = useState('');
  const [sessionContent, setSessionContent] = useState<SessionContent | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    loadPendingSessions();
  }, []);

  useEffect(() => {
    if (sessions[selectedIndex]) {
      loadSessionContent(sessions[selectedIndex].session_id);
    }
  }, [selectedIndex]);

  const loadPendingSessions = async () => {
    setLoading(true);
    try {
      const res = await reviewerApi.getPending(1, 20);
      setSessions(res.data.sessions || []);
      if (res.data.sessions?.length > 0 && !sessionContent) {
        loadSessionContent(res.data.sessions[0].session_id);
      }
    } catch (error) {
      console.error('Failed to load pending sessions:', error);
      message.error('加载待评审列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadSessionContent = async (sessionId: string) => {
    setContentLoading(true);
    try {
      const res = await sessionApi.getSessionContent(sessionId);
      setSessionContent(res.data.content || null);
    } catch (error) {
      console.error('Failed to load session content:', error);
      setSessionContent(null);
    } finally {
      setContentLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!sessions[selectedIndex]) return;
    try {
      await reviewerApi.approveSession(sessions[selectedIndex].session_id, notes, score);
      message.success('Session 已通过评审');
      setNotes('');
      setScore(3);
      setSessionContent(null);
      loadPendingSessions();
    } catch (error) {
      message.error('通过评审失败');
    }
  };

  const handleReject = async () => {
    if (!sessions[selectedIndex]) return;
    try {
      await reviewerApi.rejectSession(sessions[selectedIndex].session_id, notes, score);
      message.success('Session 已拒绝');
      setNotes('');
      setScore(3);
      setSessionContent(null);
      loadPendingSessions();
    } catch (error) {
      message.error('拒绝失败');
    }
  };

  const handleCopySessionId = async () => {
    if (sessions[selectedIndex]) {
      await copyToClipboard(sessions[selectedIndex].session_id, 'Session ID 已复制');
    }
  };

  useKeyboardShortcut('Enter', () => {
    if (sessions[selectedIndex] && score) {
      handleApprove();
    }
  }, true);

  useKeyboardShortcut('Backspace', () => {
    if (sessions[selectedIndex]) {
      handleReject();
    }
  }, true);

  const currentSession = sessions[selectedIndex];
  const messages = sessionContent?.messages || [];
  const displayMessages = expanded ? messages : messages.slice(0, 3);

  const handleScoreChange = (value: number) => {
    setScore(value);
    message.info(`已选择 ${value} 分：${getScoreLabel(value)}`);
  };

  const goToPrevious = () => {
    if (selectedIndex > 0) {
      setSelectedIndex(selectedIndex - 1);
    }
  };

  const goToNext = () => {
    if (selectedIndex < sessions.length - 1) {
      setSelectedIndex(selectedIndex + 1);
    }
  };

  const shortSessionId = currentSession?.session_id
    ? truncateSessionId(currentSession.session_id)
    : '';

  return (
    <div className="review-page">
      {/* 顶部进度栏 */}
      <div className="review-header">
        <div className="progress-section">
          <Progress
            percent={sessions.length > 0 ? ((selectedIndex + 1) / sessions.length) * 100 : 0}
            showInfo={false}
            strokeColor="#1890ff"
            trailColor="#f0f0f0"
            size="small"
          />
          <div className="progress-info">
            <div className="progress-text">
              <span className="current-session">Session {selectedIndex + 1}</span>
              <span className="separator">/</span>
              <span className="total-sessions">{sessions.length}</span>
              {currentSession && (
                <Tag color="blue" style={{ marginLeft: 8 }}>{currentSession.status}</Tag>
              )}
            </div>
            <div className="session-id">
              <Tooltip title={currentSession?.session_id || ''}>
                <span className="id-text">{shortSessionId}</span>
              </Tooltip>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={handleCopySessionId}
                disabled={!currentSession}
              />
            </div>
          </div>
        </div>

        <Space>
          <Button
            icon={<LeftOutlined />}
            onClick={goToPrevious}
            disabled={selectedIndex === 0 || loading}
          >
            上一个
          </Button>
          <Button
            type="primary"
            icon={<RightOutlined />}
            onClick={goToNext}
            disabled={selectedIndex === sessions.length - 1 || loading}
          >
            下一个
          </Button>
        </Space>
      </div>

      {/* 主内容区：对话流 */}
      <div className="conversation-container">
        <Card
          className="conversation-card"
          loading={contentLoading}
          title={
            <Space>
              <span>💬 对话内容</span>
              {messages.length > 3 && (
                <Button
                  type="link"
                  size="small"
                  icon={<ExpandOutlined />}
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? '收起' : `查看完整对话 (${messages.length} 条)`}
                </Button>
              )}
            </Space>
          }
        >
          {messages.length === 0 ? (
            <div className="empty-conversation">
              <p>暂无对话内容</p>
            </div>
          ) : (
            <div className="conversation-view">
              {displayMessages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} index={idx} />
              ))}

              {messages.length > 3 && !expanded && (
                <div className="expand-hint">
                  <Button type="link" onClick={() => setExpanded(true)}>
                    展开剩余 {messages.length - 3} 条消息
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* 技术信息折叠面板 */}
          {sessionContent?.metadata && (
            <Collapse className="metadata-collapse" ghost>
              <Panel header="📦 技术信息 (Metadata)" key="metadata">
                <pre className="metadata-json">
                  {JSON.stringify(sessionContent.metadata, null, 2)}
                </pre>
              </Panel>
            </Collapse>
          )}
        </Card>
      </div>

      {/* 右侧悬浮评分面板 */}
      <div className="score-panel-wrapper">
        <Card className="score-panel" title="📊 评审操作">
          <div className="score-section">
            <div className="score-header">
              <span className="score-title">质量评分</span>
              <Tag color={getScoreColor(score)}>{getScoreTag(score)}</Tag>
            </div>

            <Rate
              allowClear
              value={score}
              onChange={handleScoreChange}
              tooltips={scoreLabels}
              className="rating-stars"
            />

            {currentSession?.quality_auto_score && (
              <div className="score-compare">
                <small>
                  AI 评分：<strong>{currentSession.quality_auto_score}</strong>
                  {score > currentSession.quality_auto_score && (
                    <RiseOutlined className="trend-icon trend-up" />
                  )}
                  {score < currentSession.quality_auto_score && (
                    <FallOutlined className="trend-icon trend-down" />
                  )}
                </small>
              </div>
            )}
          </div>

          <div className="notes-section">
            <label className="notes-label">评审意见</label>
            <TextArea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="请输入评审意见（可选）..."
              showCount
              maxLength={200}
              className="notes-input"
            />
          </div>

          <div className="action-buttons">
            <Popconfirm
              title="确认拒绝？"
              description="拒绝后该 Session 将标记为 rejected，不可恢复。"
              onConfirm={handleReject}
              okText="确认拒绝"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button
                danger
                size="large"
                icon={<CloseOutlined />}
                block
                disabled={!currentSession}
              >
                拒绝
              </Button>
            </Popconfirm>

            <Button
              type="primary"
              size="large"
              icon={<CheckOutlined />}
              onClick={handleApprove}
              disabled={!currentSession || !score}
              block
            >
              通过评审
            </Button>
          </div>

          <div className="keyboard-hints">
            <Tag>⌘ + Enter 通过</Tag>
            <Tag>⌘ + ⌫ 拒绝</Tag>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Review;
