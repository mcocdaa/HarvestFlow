/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import { Card, Flex, Space, Switch, Tag, Typography } from 'antd';
import {
  ApiOutlined,
  AuditOutlined,
  ExperimentOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { getPluginTypeLabel, PLUGIN_TYPE_COLORS } from '../../constants/display';
import { useI18n } from '../../i18n';
import type { Plugin } from '../../types';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  collectors: <InboxOutlined />,
  curators: <ExperimentOutlined />,
  reviewers: <AuditOutlined />,
  services: <ApiOutlined />,
};

export interface PluginCardProps {
  plugin: Plugin;
  toggling?: boolean;
  onToggle: (plugin: Plugin, checked: boolean) => void;
}

export const getPluginDisplayName = (plugin: Plugin, td: (text: string | undefined | null) => string): string => {
  if (plugin.name === 'openclaw' && (plugin.key === 'collectors/openclaw' || plugin.key === 'curators/openclaw')) {
    return td(`${plugin.key}:name`);
  }
  return td(plugin.name);
};

export const PluginCard: React.FC<PluginCardProps> = ({ plugin, toggling = false, onToggle }) => {
  const { locale, t, td } = useI18n();
  const color = PLUGIN_TYPE_COLORS[plugin.plugin_type] ?? '#2563EB';
  const displayName = getPluginDisplayName(plugin, td);

  return (
    <Card
      variant="borderless"
      style={{ height: '100%' }}
      title={
        <Flex align="center" gap={8} style={{ minWidth: 0, paddingRight: 8 }}>
          <span
            className="stat-card-icon"
            style={{ width: 32, height: 32, flexShrink: 0, fontSize: 16, color, backgroundColor: `${color}1A` }}
          >
            {TYPE_ICONS[plugin.plugin_type] ?? <ApiOutlined />}
          </span>
          <Typography.Text strong ellipsis={{ tooltip: displayName }} style={{ minWidth: 0 }}>
            {displayName}
          </Typography.Text>
        </Flex>
      }
      extra={
        <Switch
          checked={plugin.enabled}
          loading={toggling}
          onChange={(checked) => onToggle(plugin, checked)}
        />
      }
    >
      <Flex vertical gap={8}>
        <Space size={4} wrap>
          <Tag color={color} bordered={false}>
            {getPluginTypeLabel(plugin.plugin_type, locale)}
          </Tag>
          <Tag bordered={false}>v{plugin.version}</Tag>
          {plugin.author && <Tag bordered={false}>{td(plugin.author)}</Tag>}
        </Space>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0, minHeight: 44 }}>
          {plugin.description ? td(plugin.description) : t('暂无描述', 'No description')}
        </Typography.Paragraph>
      </Flex>
    </Card>
  );
};

export default PluginCard;
