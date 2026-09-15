import React from 'react';
import { Popover, Space, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ToolOutlined } from '@ant-design/icons';
import type { ToolCall } from '../../types';
import JsonView from './JsonView';

interface ToolCallListProps {
  toolCalls?: ToolCall[] | null;
}

const ToolCallList: React.FC<ToolCallListProps> = ({ toolCalls }) => {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <Space size={4} wrap className="tool-call-list">
      {toolCalls.map((call, index) => {
        const record = call as Record<string, unknown>;
        const type = record.type as string | undefined;

        if (type === 'tool_use') {
          const name = (record.name as string) || '工具调用';
          return (
            <Popover
              key={index}
              placement="top"
              trigger="click"
              title={`工具调用 · ${name}`}
              content={<JsonView value={record.input ?? record} maxHeight={260} />}
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
            title={isError ? '工具结果（失败）' : '工具结果'}
            content={<JsonView value={record.content ?? record} maxHeight={260} />}
          >
            <Tag
              icon={isError ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
              color={isError ? 'error' : 'success'}
              className="tool-call-tag"
            >
              {isError ? '工具错误' : '工具结果'}
            </Tag>
          </Popover>
        );
      })}
    </Space>
  );
};

export default ToolCallList;
