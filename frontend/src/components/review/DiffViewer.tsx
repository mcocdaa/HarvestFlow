import React, { useMemo } from 'react';
import { Card, Flex, Space, Tag, Typography } from 'antd';
import { CheckOutlined, CloseOutlined, DiffOutlined } from '@ant-design/icons';

interface DiffViewerProps {
  original: string;
  modified: string;
}

interface DiffLine {
  type: 'unchanged' | 'removed' | 'added';
  text: string;
}

function computeLineDiff(original: string, modified: string): DiffLine[] {
  const origLines = original.split('\n');
  const modLines = modified.split('\n');
  const diff: DiffLine[] = [];

  const maxLen = Math.max(origLines.length, modLines.length);

  for (let i = 0; i < maxLen; i++) {
    const o = origLines[i];
    const m = modLines[i];

    if (o === undefined) {
      diff.push({ type: 'added', text: m });
    } else if (m === undefined) {
      diff.push({ type: 'removed', text: o });
    } else if (o === m) {
      diff.push({ type: 'unchanged', text: o });
    } else {
      diff.push({ type: 'removed', text: o });
      diff.push({ type: 'added', text: m });
    }
  }

  return diff;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ original, modified }) => {
  const diffLines = useMemo(() => computeLineDiff(original, modified), [original, modified]);

  const stats = useMemo(() => {
    let added = 0;
    let removed = 0;
    diffLines.forEach((l) => {
      if (l.type === 'added') added++;
      if (l.type === 'removed') removed++;
    });
    return { added, removed };
  }, [diffLines]);

  return (
    <Card
      size="small"
      variant="borderless"
      className="diff-viewer-card"
      title={
        <Flex justify="space-between" align="center">
          <Space size={6}>
            <DiffOutlined style={{ color: '#2563eb' }} />
            <Typography.Text strong style={{ fontSize: 13 }}>
              修改前后对比 Diff (DPO 偏好对)
            </Typography.Text>
          </Space>
          <Space size={4}>
            <Tag color="error" icon={<CloseOutlined />}>
              -{stats.removed} 删减
            </Tag>
            <Tag color="success" icon={<CheckOutlined />}>
              +{stats.added} 新增
            </Tag>
          </Space>
        </Flex>
      }
    >
      <div className="diff-content-container">
        {diffLines.map((line, idx) => {
          let prefix = '  ';
          let className = 'diff-line unchanged';
          if (line.type === 'removed') {
            prefix = '- ';
            className = 'diff-line removed';
          } else if (line.type === 'added') {
            prefix = '+ ';
            className = 'diff-line added';
          }

          return (
            <div key={idx} className={className}>
              <span className="diff-prefix">{prefix}</span>
              <span className="diff-text">{line.text || ' '}</span>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default DiffViewer;
