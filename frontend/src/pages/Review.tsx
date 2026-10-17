import React, { useState } from 'react';
import { Button, Card, Segmented, Space } from 'antd';
import { AuditOutlined } from '@ant-design/icons';
import { PageHeader } from '../components';
import { AuditLogDrawer, BatchReviewPanel, ReviewWorkspace } from '../components/review';
import { useI18n } from '../i18n';

const Review: React.FC = () => {
  const { t } = useI18n();
  const [mode, setMode] = useState('single');
  const [auditOpen, setAuditOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  return (
    <div>
      <PageHeader
        title={t('审核', 'Review')}
        description={t(
          '对清洗后的会话进行质量评分与通过/拒绝决策',
          'Quality scoring, inline DPO editing, and approve/reject decisions for curated sessions'
        )}
        extra={
          <Space wrap>
            <Segmented
              options={[
                { value: 'single', label: t('逐条评审', 'Single Review') },
                { value: 'batch', label: t('批量处理', 'Batch Review') },
              ]}
              value={mode}
              onChange={(value) => setMode(String(value))}
            />
            <Button icon={<AuditOutlined />} onClick={() => setAuditOpen(true)}>
              {t('审计日志', 'Audit Logs')}
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
