import React, { useState } from 'react';
import { Button, Card, Segmented, Space } from 'antd';
import { AuditOutlined } from '@ant-design/icons';
import { PageHeader } from '../components';
import { AuditLogDrawer, BatchReviewPanel, ReviewWorkspace } from '../components/review';

const Review: React.FC = () => {
  const [mode, setMode] = useState('single');
  const [auditOpen, setAuditOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  return (
    <div>
      <PageHeader
        title="审核"
        description="对清洗后的会话进行质量评分与通过/拒绝决策"
        extra={
          <Space wrap>
            <Segmented
              options={[
                { value: 'single', label: '逐条评审' },
                { value: 'batch', label: '批量处理' },
              ]}
              value={mode}
              onChange={(value) => setMode(String(value))}
            />
            <Button icon={<AuditOutlined />} onClick={() => setAuditOpen(true)}>
              审计日志
            </Button>
          </Space>
        }
      />
      {mode === 'single' ? (
        <ReviewWorkspace onCurrentChange={setCurrentSessionId} />
      ) : (
        <Card variant="borderless">
          <BatchReviewPanel />
        </Card>
      )}
      <AuditLogDrawer open={auditOpen} onClose={() => setAuditOpen(false)} sessionId={currentSessionId} />
    </div>
  );
};

export default Review;
