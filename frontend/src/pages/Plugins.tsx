import React, { useMemo, useState } from 'react';
import { Button, Card, Col, Flex, Modal, Row, Space, Switch, Tabs, Tag, Typography, message } from 'antd';
import {
  ApiOutlined,
  AuditOutlined,
  ExperimentOutlined,
  InboxOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { pluginApi } from '../services';
import { useAsyncData } from '../hooks';
import { CopyText, EmptyState, PageHeader } from '../components';
import { getPluginTypeLabel, PLUGIN_TYPE_COLORS, PLUGIN_TYPE_ORDER } from '../constants/display';
import { useI18n } from '../i18n';
import type { Plugin } from '../types';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  collectors: <InboxOutlined />,
  curators: <ExperimentOutlined />,
  reviewers: <AuditOutlined />,
  services: <ApiOutlined />,
};

const Plugins: React.FC = () => {
  const { locale, t, td } = useI18n();
  const [modal, modalContextHolder] = Modal.useModal();
  const { data, loading, reload } = useAsyncData<{ plugins?: Plugin[] }>(() => pluginApi.getAll());
  const [activeTab, setActiveTab] = useState('all');
  const [togglingKey, setTogglingKey] = useState<string | null>(null);

  const plugins = useMemo(() => data?.plugins ?? [], [data]);

  const counts = useMemo(() => {
    return PLUGIN_TYPE_ORDER.reduce<Record<string, number>>((acc, type) => {
      acc[type] = plugins.filter((plugin) => plugin.plugin_type === type).length;
      return acc;
    }, {});
  }, [plugins]);

  const filtered = useMemo(() => {
    if (activeTab === 'all') return plugins;
    return plugins.filter((plugin) => plugin.plugin_type === activeTab);
  }, [plugins, activeTab]);

  const doToggle = async (plugin: Plugin, enabled: boolean) => {
    setTogglingKey(plugin.key);
    try {
      if (enabled) {
        await pluginApi.enable(plugin.key);
      } else {
        await pluginApi.disable(plugin.key);
      }
      message.success(
        t(
          `插件 ${plugin.name} 已${enabled ? '启用' : '停用'}`,
          `Plugin ${plugin.name} ${enabled ? 'enabled' : 'disabled'}`
        )
      );
      reload();
    } catch {
      // 拦截器已统一提示
    } finally {
      setTogglingKey(null);
    }
  };

  const handleToggle = (plugin: Plugin, checked: boolean) => {
    if (checked) {
      doToggle(plugin, true);
      return;
    }
    modal.confirm({
      title: t(`停用插件 ${plugin.name}？`, `Disable plugin ${plugin.name}?`),
      content: t(
        '停用后将卸载插件模块及其钩子，相关采集/清洗能力会立即失效。',
        'Disabling unloads the plugin module and its hooks; related collection/curation features will stop immediately.'
      ),
      okText: t('停用', 'Disable'),
      cancelText: t('取消', 'Cancel'),
      okButtonProps: { danger: true },
      onOk: () => doToggle(plugin, false),
    });
  };

  const renderGrid = (list: Plugin[]) => {
    if (list.length === 0) {
      return <EmptyState description={t('该分类下暂无插件', 'No plugins in this category')} />;
    }
    return (
      <Row gutter={[16, 16]}>
        {list.map((plugin) => {
          const color = PLUGIN_TYPE_COLORS[plugin.plugin_type] ?? '#2563EB';
          return (
            <Col key={plugin.key} xs={24} md={12} xl={8}>
              <Card
                variant="borderless"
                style={{ height: '100%' }}
                title={
                  <Space>
                    <span className="stat-card-icon" style={{ width: 32, height: 32, fontSize: 16, color, backgroundColor: `${color}1A` }}>
                      {TYPE_ICONS[plugin.plugin_type] ?? <ApiOutlined />}
                    </span>
                    <Typography.Text strong>{plugin.name}</Typography.Text>
                  </Space>
                }
                extra={
                  <Switch
                    checked={plugin.enabled}
                    loading={togglingKey === plugin.key}
                    onChange={(checked) => handleToggle(plugin, checked)}
                  />
                }
              >
                <Flex vertical gap={8}>
                  <Space size={4} wrap>
                    <Tag color={color} bordered={false}>
                      {getPluginTypeLabel(plugin.plugin_type, locale)}
                    </Tag>
                    <Tag bordered={false}>v{plugin.version}</Tag>
                    {plugin.author && <Tag bordered={false}>{plugin.author}</Tag>}
                  </Space>
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0, minHeight: 44 }}>
                    {plugin.description ? td(plugin.description) : t('暂无描述', 'No description')}
                  </Typography.Paragraph>
                  <CopyText text={plugin.key} mono display={<span style={{ fontSize: 12 }}>{plugin.key}</span>} />
                </Flex>
              </Card>
            </Col>
          );
        })}
      </Row>
    );
  };

  return (
    <div>
      {modalContextHolder}
      <PageHeader
        title={t('插件', 'Plugins')}
        description={t(
          '采集器、清洗器、审核器与服务插件的运行状态管理',
          'Manage runtime status of collector, curator, reviewer, and service plugins'
        )}
        extra={
          <Button icon={<ReloadOutlined />} onClick={reload} loading={loading}>
            {t('刷新', 'Refresh')}
          </Button>
        }
      />
      <Card variant="borderless">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'all',
              label: t(`全部（${plugins.length}）`, `All (${plugins.length})`),
            },
            ...PLUGIN_TYPE_ORDER.map((type) => ({
              key: type,
              label: t(
                `${getPluginTypeLabel(type, 'zh')}（${counts[type] ?? 0}）`,
                `${getPluginTypeLabel(type, 'en')} (${counts[type] ?? 0})`
              ),
            })),
          ]}
        />
        {renderGrid(filtered)}
      </Card>
    </div>
  );
};

export default Plugins;
