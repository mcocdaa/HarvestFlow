import React from 'react';
import { Popover, Space, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ToolOutlined } from '@ant-design/icons';
import type { ToolCall } from '../../types';
import { useI18n } from '../../i18n';
import JsonView from './JsonView';

interface ToolCallListProps {
  toolCalls?: ToolCall[] | null;
  collapsed?: boolean;
}

const ToolCallList: React.FC<ToolCallListProps> = ({ toolCalls, collapsed = false }) => {
  const { t } = useI18n();
  if (!toolCalls || toolCalls.length === 0 || collapsed) return null;

  return (
    <Space size={4} wrap className="tool-call-list">
      {toolCalls.map((call, index) => {
        const record = call as Record<string, unknown>;
        const type = record.type as string | undefined;
        const fnObj = record.function as Record<string, unknown> | undefined;

        if (type === 'tool_use' || type === 'function' || fnObj?.name) {
          const name =
            (record.name as string) ||
            (fnObj?.name as string) ||
            t('工具调用', 'Tool Call');
          const payload = record.input ?? fnObj?.arguments ?? record;
          return (
            <Popover
              key={index}
              placement="top"
              trigger="click"
              title={`${t('工具调用', 'Tool Call')} · ${name}`}
              content={<JsonView value={payload} maxHeight={260} />}
            >
              <Tag icon={<ToolOutlined />} color="processing" className="tool-call-tag">
                {name}
              </Tag>
            </Popover>
          );
        }

        const isError = record.is_error === true;
        return (
          <Popover
            key={index}
            placement="top"
            trigger="click"
            title={isError ? t('工具结果（失败）', 'Tool Output (Failed)') : t('工具结果', 'Tool Output')}
            content={<JsonView value={record.content ?? record} maxHeight={260} />}
          >
            <Tag
              icon={isError ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
              color={isError ? 'error' : 'success'}
              className="tool-call-tag"
            >
              {isError ? t('工具错误', 'Tool Error') : t('工具结果', 'Tool Output')}
            </Tag>
          </Popover>
        );
      })}
    </Space>
  );
};

export default ToolCallList;
