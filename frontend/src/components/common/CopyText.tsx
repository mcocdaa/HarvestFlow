import React from 'react';
import { CopyOutlined } from '@ant-design/icons';
import { Tooltip, Typography } from 'antd';
import { copyToClipboard } from '../../utils';
import { useI18n } from '../../i18n';

interface CopyTextProps {
  text: string;
  display?: React.ReactNode;
  className?: string;
  mono?: boolean;
  tooltip?: string;
}

const CopyText: React.FC<CopyTextProps> = ({
  text,
  display,
  className,
  mono = false,
  tooltip,
}) => {
  const { t } = useI18n();
  return (
    <Tooltip title={tooltip ?? t('点击复制', 'Click to copy')}>
      <Typography.Text
        className={`copy-text${mono ? ' flow-mono' : ''}${className ? ` ${className}` : ''}`}
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(text, t('已复制到剪贴板', 'Copied to clipboard'));
        }}
      >
        {display ?? text}
        <CopyOutlined className="copy-text-icon" />
      </Typography.Text>
    </Tooltip>
  );
};

export default CopyText;
