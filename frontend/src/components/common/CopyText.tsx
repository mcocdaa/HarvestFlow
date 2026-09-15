import React from 'react';
import { CopyOutlined } from '@ant-design/icons';
import { Tooltip, Typography } from 'antd';
import { copyToClipboard } from '../../utils';

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
  tooltip = '点击复制',
}) => {
  return (
    <Tooltip title={tooltip}>
      <Typography.Text
        className={`copy-text${mono ? ' flow-mono' : ''}${className ? ` ${className}` : ''}`}
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(text);
        }}
      >
        {display ?? text}
        <CopyOutlined className="copy-text-icon" />
      </Typography.Text>
    </Tooltip>
  );
};

export default CopyText;
