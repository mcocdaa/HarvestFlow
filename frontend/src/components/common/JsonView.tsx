import React from 'react';
import { Button } from 'antd';
import { CopyOutlined } from '@ant-design/icons';
import { copyToClipboard } from '../../utils';
import { useI18n } from '../../i18n';

interface JsonViewProps {
  value: unknown;
  maxHeight?: number;
  className?: string;
}

const JsonView: React.FC<JsonViewProps> = ({ value, maxHeight = 320, className }) => {
  const { locale, t, td } = useI18n();
  let text: string;
  try {
    text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  } catch {
    text = String(value);
  }
  const displayText = locale === 'en' ? td(text) : text;

  return (
    <div className={`json-view${className ? ` ${className}` : ''}`}>
      <pre className="json-view-pre flow-mono" style={{ maxHeight }}>
        {displayText}
      </pre>
      <Button
        className="json-view-copy"
        type="text"
        size="small"
        icon={<CopyOutlined />}
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(displayText, t('已复制 JSON', 'Copied JSON'));
        }}
      />
    </div>
  );
};

export default JsonView;
