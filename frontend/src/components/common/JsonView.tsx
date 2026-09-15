import React from 'react';
import { Button } from 'antd';
import { CopyOutlined } from '@ant-design/icons';
import { copyToClipboard } from '../../utils';

interface JsonViewProps {
  value: unknown;
  maxHeight?: number;
  className?: string;
}

const JsonView: React.FC<JsonViewProps> = ({ value, maxHeight = 320, className }) => {
  let text: string;
  try {
    text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  } catch {
    text = String(value);
  }

  return (
    <div className={`json-view${className ? ` ${className}` : ''}`}>
      <pre className="json-view-pre flow-mono" style={{ maxHeight }}>
        {text}
      </pre>
      <Button
        className="json-view-copy"
        type="text"
        size="small"
        icon={<CopyOutlined />}
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(text, '已复制 JSON');
        }}
      />
    </div>
  );
};

export default JsonView;
