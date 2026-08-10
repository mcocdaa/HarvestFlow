import React, { useEffect, useState } from 'react';
import { Typography } from 'antd';
import { sessionApi } from '../services';
import { SessionTable, SessionDrawer } from '../components/sessions';
import type { Session, SessionContent, SessionListParams } from '../types';
import '../styles/Sessions.css';

const { Text } = Typography;

const Sessions: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [content, setContent] = useState<SessionContent | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  useEffect(() => {
    loadSessions();
  }, [page, pageSize]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const params: SessionListParams = { page, page_size: pageSize, sort: 'recent' };
      const res = await sessionApi.getSessions(params);
      setSessions(res.data.sessions || []);
      setTotal(res.data.total || 0);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewSession = async (record: Session) => {
    setSelectedSession(record);
    try {
      const res = await sessionApi.getSessionContent(record.session_id);
      setContent(res.data?.content || null);
    } catch (error) {
      console.error('Failed to load content:', error);
      setContent(null);
    }
    setDrawerVisible(true);
  };

  const handlePageChange = (newPage: number, newPageSize: number) => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  return (
    <div className="sessions-page">
      <div className="page-header">
        <div className="header-title">
          <h1>Sessions</h1>
          <Text className="total-count">共 {total} 条会话</Text>
        </div>
      </div>

      <SessionTable
        sessions={sessions}
        loading={loading}
        total={total}
        page={page}
        pageSize={pageSize}
        onPageChange={handlePageChange}
        onViewSession={viewSession}
      />

      <SessionDrawer
        visible={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        session={selectedSession}
        content={content}
      />
    </div>
  );
};

export default Sessions;
