import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Drawer } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { sessionApi } from '../services/api';
import type { Session, SessionContent, SessionListParams } from '../types';

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
      setContent(res.data);
    } catch (error) {
      console.error('Failed to load content:', error);
      setContent(null);
    }
    setDrawerVisible(true);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      raw: 'default',
      curated: 'processing',
      approved: 'success',
      rejected: 'error',
    };
    return colors[status] || 'default';
  };

  const columns = [
    {
      title: 'Session ID',
      dataIndex: 'session_id',
      key: 'session_id',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>,
    },
    {
      title: 'Auto Score',
      dataIndex: 'quality_auto_score',
      key: 'quality_auto_score',
    },
    {
      title: 'Manual Score',
      dataIndex: 'quality_manual_score',
      key: 'quality_manual_score',
    },
    {
      title: 'Agent Role',
      dataIndex: 'agent_role',
      key: 'agent_role',
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Session) => (
        <Button icon={<EyeOutlined />} onClick={() => viewSession(record)}>
          View
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h1>Sessions</h1>
      <Table
        columns={columns}
        dataSource={sessions}
        rowKey="session_id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p, ps) => {
            setPage(p);
            setPageSize(ps);
          },
        }}
      />
      <Drawer
        title={`Session: ${selectedSession?.session_id}`}
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedSession && (
          <div>
            <p><strong>Status:</strong> <Tag color={getStatusColor(selectedSession.status)}>{selectedSession.status}</Tag></p>
            <p><strong>Auto Score:</strong> {selectedSession.quality_auto_score}</p>
            <p><strong>Manual Score:</strong> {selectedSession.quality_manual_score}</p>
            <p><strong>Agent Role:</strong> {selectedSession.agent_role}</p>
            <p><strong>Task Type:</strong> {selectedSession.task_type}</p>
            <p><strong>Created:</strong> {selectedSession.created_at}</p>
            <hr />
            <h3>Content</h3>
            <pre style={{ maxHeight: 400, overflow: 'auto', background: '#f5f5f5', padding: 10 }}>
              {JSON.stringify(content, null, 2)}
            </pre>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Sessions;
